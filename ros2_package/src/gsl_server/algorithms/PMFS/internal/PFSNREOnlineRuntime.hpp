#pragma once

#include "gsl_server/algorithms/PMFS/internal/PFDEIPredictiveProvider.hpp"
#include "gsl_server/algorithms/PMFS/internal/PFSNREInference.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace GSL::PMFS_internal::pfsnre
{
    struct CandidateGeometry
    {
        std::string id;
        double cx = 0.0;
        double cy = 0.0;
        double width = 0.0;
        double height = 0.0;
        std::size_t freeCount = 0;
        std::vector<std::pair<double,double>> freeCells;
    };

    struct RuntimeResult
    {
        std::vector<long double> carrierMass;
        std::vector<float> logits;
        double wallTimeS = 0.0;
        std::size_t rawSamples = 0;
        std::size_t blocks = 0;
    };

    class OnlineRuntime
    {
    public:
        OnlineRuntime(const pfdei::PredictiveProvider& provider,
                      std::vector<CandidateGeometry> geometry,
                      const std::filesystem::path& modelPath,
                      const std::filesystem::path& outputDirectory = {})
            : provider_(provider), geometry_(std::move(geometry)), outputDirectory_(outputDirectory)
        {
            if (geometry_.size() != provider_.sourceCount())
                throw std::invalid_argument("PF-SNRE provider/geometry source count mismatch");
            if (provider_.memberCount() != 8)
                throw std::invalid_argument("PF-SNRE V2 requires exactly 8 predictive members");
            if (geometry_.size() < 2)
                throw std::invalid_argument("PF-SNRE requires at least two source carriers");
            for (std::size_t s=0;s<geometry_.size();++s)
            {
                const auto& g=geometry_[s];
                if (g.id != provider_.sourceId(s) || g.freeCount==0 || g.freeCells.size()!=g.freeCount ||
                    !(g.width>0.0) || !(g.height>0.0) || !std::isfinite(g.cx) || !std::isfinite(g.cy))
                    throw std::invalid_argument("PF-SNRE invalid/misaligned candidate geometry");
            }
            initializeNormalization();
            model_.load(modelPath.string());
            if (!outputDirectory_.empty()) std::filesystem::create_directories(outputDirectory_);
        }

        void recordRawSample(const pfdei::SampleContext& context, float measuredPpm,
                             bool acceptedByStopAndMeasure, std::size_t acceptedCountAfter,
                             std::size_t stopIndex)
        {
            if (!std::isfinite(measuredPpm) || measuredPpm < 0.0f)
                throw std::runtime_error("PF-SNRE invalid measured ppm");
            if (!raw_.empty())
            {
                const double dt=context.timeS-raw_.back().context.timeS;
                if (std::abs(dt-kSensorDtS)>kSensorDtToleranceS)
                    throw std::runtime_error("PF-SNRE raw sensor cadence drift from frozen 0.2 s contract");
            }
            raw_.push_back({context, measuredPpm});
            if (!acceptedByStopAndMeasure) return;
            if (acceptedCountAfter<1 || acceptedCountAfter>kSamplesPerBlock)
                throw std::runtime_error("PF-SNRE accepted StopAndMeasure count outside 1..10");
            if (acceptedCountAfter==1)
            {
                if (!pending_.empty()) throw std::runtime_error("PF-SNRE unfinished block before new block");
                pendingStopIndex_=stopIndex;
            }
            if (pendingStopIndex_!=stopIndex || pending_.size()+1!=acceptedCountAfter)
                throw std::runtime_error("PF-SNRE accepted callback/block ordering drift");
            pending_.push_back(raw_.size()-1);
            if (acceptedCountAfter==kSamplesPerBlock)
            {
                Block b;
                std::copy(pending_.begin(),pending_.end(),b.rawIndex.begin());
                b.stopIndex=stopIndex;
                b.withinStop = (!blocks_.empty() && blocks_.back().stopIndex==stopIndex) ? blocks_.back().withinStop+1 : 0;
                if (b.withinStop>=kBlocksPerStop)
                    throw std::runtime_error("PF-SNRE more than 8 completed blocks at one stop");
                b.stopX=context.x; b.stopY=context.y;
                blocks_.push_back(b);
                pending_.clear();
            }
        }

        std::size_t rawSampleCount() const { return raw_.size(); }
        std::size_t blockCount() const { return blocks_.size(); }

        RuntimeResult infer(std::size_t sourceUpdateId)
        {
            if (!pending_.empty()) throw std::runtime_error("PF-SNRE source update encountered partial sensing block");
            if (blocks_.empty()) throw std::runtime_error("PF-SNRE source update has no completed sensing blocks");
            if (raw_.size()<3) throw std::runtime_error("PF-SNRE source update has insufficient raw history");

            const auto started=std::chrono::steady_clock::now();
            const std::size_t B=blocks_.size(), M=provider_.memberCount(), S=provider_.sourceCount();
            std::vector<float> observation(B*kSamplesPerBlock);
            for (std::size_t b=0;b<B;++b)
                for (std::size_t k=0;k<kSamplesPerBlock;++k)
                    observation[b*kSamplesPerBlock+k]=logMeasurement(raw_.at(blocks_[b].rawIndex[k]).measuredPpm);

            std::vector<pfdei::SampleContext> contexts;
            contexts.reserve(raw_.size());
            for (const auto& r:raw_) contexts.push_back(r.context);

            std::vector<float> logits(S,0.0f);
            std::vector<float> prediction(B*M*kSamplesPerBlock);
            for (std::size_t s=0;s<S;++s)
            {
                for (std::size_t m=0;m<M;++m)
                {
                    const auto physical=provider_.physicalSeries(s,m,contexts);
                    if (physical.size()!=contexts.size())
                        throw std::runtime_error("PF-SNRE predictive physical-series length mismatch");
                    const auto measured=forwardFrozenSensor(physical);
                    for (std::size_t b=0;b<B;++b)
                        for (std::size_t k=0;k<kSamplesPerBlock;++k)
                            prediction[(b*M+m)*kSamplesPerBlock+k]=logMeasurement(measured.at(blocks_[b].rawIndex[k]));
                }
                const auto candidate=candidateFeatures(s);
                const auto context=blockContext(s);
                logits[s]=model_.forward(observation,prediction,context,candidate,B,M);
            }

            std::vector<long double> logMass(S);
            long double maxLog=-std::numeric_limits<long double>::infinity();
            for (std::size_t s=0;s<S;++s)
            {
                const long double prior=provider_.geometryPriorMass(s);
                if (!(prior>0.0L) || !std::isfinite(static_cast<double>(prior)))
                    throw std::runtime_error("PF-SNRE invalid runtime geometry prior");
                logMass[s]=std::log(prior)+static_cast<long double>(logits[s]);
                maxLog=std::max(maxLog,logMass[s]);
            }
            long double sum=0.0L;
            std::vector<long double> mass(S);
            for (std::size_t s=0;s<S;++s){mass[s]=std::exp(logMass[s]-maxLog);sum+=mass[s];}
            if (!(sum>0.0L) || !std::isfinite(static_cast<double>(sum)))
                throw std::runtime_error("PF-SNRE posterior normalization failed");
            for (auto& p:mass) p/=sum;

            RuntimeResult result;
            result.carrierMass=mass; result.logits=logits; result.rawSamples=raw_.size(); result.blocks=B;
            result.wallTimeS=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
            if (!outputDirectory_.empty()) writeResult(sourceUpdateId,result);
            return result;
        }

        const std::vector<CandidateGeometry>& geometry() const { return geometry_; }

    private:
        static constexpr std::size_t kSamplesPerBlock=10;
        static constexpr std::size_t kBlocksPerStop=8;
        static constexpr double kSensorDtS=0.2;
        static constexpr double kSensorDtToleranceS=1e-5;
        static constexpr double kSensorTauS=1.2;
        static constexpr std::size_t kSensorDelaySamples=2;

        struct RawSample { pfdei::SampleContext context; float measuredPpm; };
        struct Block
        {
            std::array<std::size_t,kSamplesPerBlock> rawIndex{};
            std::size_t stopIndex=0;
            std::size_t withinStop=0;
            double stopX=0.0, stopY=0.0;
        };

        const pfdei::PredictiveProvider& provider_;
        std::vector<CandidateGeometry> geometry_;
        PFSNREInference model_;
        std::filesystem::path outputDirectory_;
        std::vector<RawSample> raw_;
        std::vector<Block> blocks_;
        std::vector<std::size_t> pending_;
        std::size_t pendingStopIndex_=0;
        std::array<double,2> xyCenter_{};
        std::array<double,2> xyScale_{};

        void initializeNormalization()
        {
            double xmin=geometry_[0].cx,xmax=xmin,ymin=geometry_[0].cy,ymax=ymin;
            for (const auto& g:geometry_){xmin=std::min(xmin,g.cx);xmax=std::max(xmax,g.cx);ymin=std::min(ymin,g.cy);ymax=std::max(ymax,g.cy);}
            xyCenter_={0.5*(xmin+xmax),0.5*(ymin+ymax)};
            xyScale_={xmax-xmin,ymax-ymin};
            if (xyScale_[0]<=1e-6 || xyScale_[1]<=1e-6)
                throw std::runtime_error("PF-SNRE carrier support must span x and y");
        }

        static float logMeasurement(double value)
        {
            if (!(value>=0.0) || !std::isfinite(value)) throw std::runtime_error("PF-SNRE log transform input invalid");
            return static_cast<float>(std::log1p(value/0.1));
        }

        static std::vector<double> forwardFrozenSensor(const std::vector<double>& physical)
        {
            const double alpha=std::exp(-kSensorDtS/kSensorTauS);
            double state=0.0;
            std::vector<double> measured(physical.size(),0.0);
            for (std::size_t k=0;k<physical.size();++k)
            {
                const double delayed=k<kSensorDelaySamples?0.0:physical[k-kSensorDelaySamples];
                if (!(delayed>=0.0) || !std::isfinite(delayed)) throw std::runtime_error("PF-SNRE physical prediction invalid");
                state=alpha*state+(1.0-alpha)*delayed;
                measured[k]=state; // frozen gain=1, baseline=0, noise=0, no finite saturation
            }
            return measured;
        }

        std::array<float,5> candidateFeatures(std::size_t s) const
        {
            const auto& g=geometry_.at(s);
            return {
                static_cast<float>((g.cx-xyCenter_[0])/xyScale_[0]),
                static_cast<float>((g.cy-xyCenter_[1])/xyScale_[1]),
                static_cast<float>(g.width/xyScale_[0]),
                static_cast<float>(g.height/xyScale_[1]),
                static_cast<float>(std::log1p(static_cast<double>(g.freeCount))/std::log(5.0))
            };
        }

        std::vector<float> blockContext(std::size_t s) const
        {
            const auto& g=geometry_.at(s);
            std::size_t maxStop=0; for(const auto& b:blocks_) maxStop=std::max(maxStop,b.stopIndex);
            const double denom=static_cast<double>(std::max<std::size_t>(maxStop,1));
            std::vector<float> out(blocks_.size()*6);
            for (std::size_t b=0;b<blocks_.size();++b)
            {
                const auto& z=blocks_[b]; const std::size_t q=b*6;
                out[q+0]=static_cast<float>((z.stopX-xyCenter_[0])/xyScale_[0]);
                out[q+1]=static_cast<float>((z.stopY-xyCenter_[1])/xyScale_[1]);
                out[q+2]=static_cast<float>((g.cx-z.stopX)/xyScale_[0]);
                out[q+3]=static_cast<float>((g.cy-z.stopY)/xyScale_[1]);
                out[q+4]=static_cast<float>(2.0*static_cast<double>(z.withinStop)/7.0-1.0);
                out[q+5]=static_cast<float>(static_cast<double>(z.stopIndex)/denom);
            }
            return out;
        }

        void writeResult(std::size_t updateId,const RuntimeResult& result) const
        {
            const auto path=outputDirectory_/("pf_snre_posterior_update_"+padded(updateId)+".csv");
            std::ofstream f(path);
            if(!f) throw std::runtime_error("PF-SNRE posterior trace open failed");
            f<<"source_index,source_id,prior_mass,logit,posterior_mass,centroid_x,centroid_y,free_count,provider_provenance,wall_time_s,raw_samples,blocks\n";
            f<<std::setprecision(17);
            for(std::size_t s=0;s<geometry_.size();++s)
                f<<s<<','<<geometry_[s].id<<','<<static_cast<double>(provider_.geometryPriorMass(s))<<','<<result.logits[s]<<','
                 <<static_cast<double>(result.carrierMass[s])<<','<<geometry_[s].cx<<','<<geometry_[s].cy<<','<<geometry_[s].freeCount<<','
                 <<provider_.provenanceHash()<<','<<result.wallTimeS<<','<<result.rawSamples<<','<<result.blocks<<'\n';
        }

        static std::string padded(std::size_t value)
        {
            std::ostringstream ss; ss<<std::setw(4)<<std::setfill('0')<<value; return ss.str();
        }
    };
}
