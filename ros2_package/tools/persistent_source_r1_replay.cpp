// Persistent-source PMFS R1 mechanism ablation.
// Source-blind: reads only frozen observations/candidate geometry/ground-truth wind.
// Requires the current research PMFS code that exposes EventKeyedTransportRng
// and Simulations::runPointForwardReplay().
#include <gsl_server/algorithms/Common/Grid2D.hpp>
#include <gsl_server/algorithms/PMFS/PMFSLib.hpp>
#include <gsl_server/algorithms/PMFS/internal/EventKeyedRng.hpp>
#include <gsl_server/algorithms/PMFS/internal/Simulations.hpp>
#include <opencv2/core.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using namespace GSL;
using namespace GSL::PMFS_internal;

namespace {
using Row = std::map<std::string,std::string>;

std::vector<std::string> split(const std::string& line) {
    std::vector<std::string> out; size_t b=0;
    while (true) {
        size_t e=line.find(',',b);
        out.push_back(line.substr(b,e==std::string::npos?e:e-b));
        if(e==std::string::npos) break;
        b=e+1;
    }
    return out;
}
std::vector<Row> csv(const fs::path& p) {
    std::ifstream in(p); if(!in) throw std::runtime_error("cannot open "+p.string());
    std::string line; if(!std::getline(in,line)) throw std::runtime_error("empty "+p.string());
    if(!line.empty()&&line.back()=='\r') line.pop_back();
    auto h=split(line); std::vector<Row> rows;
    while(std::getline(in,line)) {
        if(!line.empty()&&line.back()=='\r') line.pop_back();
        if(line.empty()) continue;
        auto v=split(line); if(v.size()!=h.size()) throw std::runtime_error("CSV shape "+p.string());
        Row r; for(size_t i=0;i<h.size();++i) r.emplace(h[i],v[i]);
        rows.push_back(std::move(r));
    }
    return rows;
}
double d(const Row&r,const char*k){return std::stod(r.at(k));}
int integer(const Row&r,const char*k){return std::stoi(r.at(k));}

constexpr uint64_t GLOBAL_SEED=20260926ULL;
constexpr uint64_t TRANSPORT_STREAM=0x50535452414E5350ULL;   // "PSTRANSP"
constexpr uint64_t RESAMPLED_SOURCE_STREAM=0x52534D504C535243ULL; // "RSMPLSRC"
constexpr uint64_t PERSISTENT_SOURCE_STREAM=0x5052535352434452ULL; // "PRSSRCDR"
constexpr int K=8;
constexpr int M=8;

struct Candidate {
    std::string id;
    Vector2Int origin;
    Vector2Int size;
    double cx=0, cy=0;
};

class Replay : public Simulations {
public:
    using Simulations::Simulations;

    long double scoreResampled(const Utils::NQA::Node& leaf, int replica) {
        EventKeyedTransportRng sourceRng(EventKey{
            GLOBAL_SEED,1,static_cast<uint64_t>(replica),RESAMPLED_SOURCE_STREAM});
        EventKeyedTransportRng transportRng(EventKey{
            GLOBAL_SEED,1,static_cast<uint64_t>(replica),TRANSPORT_STREAM});
        std::vector<float> map(measuredHitProb.data.size(),0.0f);
        SimulationSource source(&leaf, measuredHitProb.metadata, &sourceRng);
        simulateSourceInPosition(source,map,true,settings.iterationsToRecord,
                                 settings.deltaTime,settings.noiseSTDev,nullptr,&transportRng);
        applyBlur(map);
        return sourceProbFromMaps(measuredHitProb,map);
    }

    long double scorePoint(const Vector2& point, int replica) {
        EventKeyedTransportRng transportRng(EventKey{
            GLOBAL_SEED,1,static_cast<uint64_t>(replica),TRANSPORT_STREAM});
        std::vector<float> map(measuredHitProb.data.size(),0.0f);
        runPointForwardReplay(point,map,settings.iterationsToRecord,
                              settings.deltaTime,settings.noiseSTDev,&transportRng);
        applyBlur(map);
        return sourceProbFromMaps(measuredHitProb,map);
    }

private:
    void applyBlur(std::vector<float>& map) {
        if(settings.blurSigmaX<=0 && settings.blurSigmaY<=0) return;
        cv::Mat image(map);
        image=image.reshape(1,measuredHitProb.metadata.dimensions.y);
        blurHitMap(image);
    }
};

Vector2 persistentPoint(const Candidate& c, const Grid2DMetadata& meta, int m) {
    EventKeyedTransportRng sourceRng(EventKey{
        GLOBAL_SEED,1,static_cast<uint64_t>(m),PERSISTENT_SOURCE_STREAM});
    Vector2 start=meta.indicesToCoordinates(c.origin.x,c.origin.y,false);
    Vector2 end=meta.indicesToCoordinates(c.origin.x+c.size.x,c.origin.y+c.size.y,false);
    const double qx=sourceRng.unitAt(0,0);
    const double qy=sourceRng.unitAt(0,1);
    return Vector2(static_cast<float>(start.x+qx*(end.x-start.x)),
                   static_cast<float>(start.y+qy*(end.y-start.y)));
}
long double mean(const std::vector<long double>& x) {
    return std::accumulate(x.begin(),x.end(),0.0L)/static_cast<long double>(x.size());
}
} // namespace

int main(int argc,char**argv) {
    try {
        if(argc!=3) throw std::runtime_error(
            "usage: persistent_source_r1_replay SNAPSHOT_DIR OUTPUT_DIR");
        fs::path run(argv[1]),out(argv[2]);
        if(fs::exists(out)) throw std::runtime_error("output exists; refusing overwrite");

        auto snapshot=csv(run/"measured_map_at_update.csv");
        auto candidatesCsv=csv(run/"frozen_candidate_geometry.csv");
        auto events=csv(run/"measurement_events.csv");
        auto windRows=csv(run/"wind_source_update.csv");
        if(snapshot.empty()||candidatesCsv.empty()||events.empty()||windRows.empty())
            throw std::runtime_error("incomplete frozen R1 inputs");
        if(integer(snapshot[0],"source_update_id")!=1) throw std::runtime_error("not source update 1");

        Grid2DMetadata meta;
        meta.dimensions=Vector2Int(integer(snapshot[0],"grid_width"),integer(snapshot[0],"grid_height"));
        meta.cellSize=static_cast<float>(d(snapshot[0],"cell_size"));
        meta.origin=Vector2(static_cast<float>(d(snapshot[0],"origin_x")),
                            static_cast<float>(d(snapshot[0],"origin_y")));
        meta.scale=3;
        const size_t n=static_cast<size_t>(meta.dimensions.x)*meta.dimensions.y;
        if(snapshot.size()!=n) throw std::runtime_error("snapshot size mismatch");

        std::vector<Occupancy> occ(n);
        std::vector<HitProbability> live(n),measured(n);
        meta.numFreeCells=0;
        for(size_t i=0;i<n;++i) {
            const auto&r=snapshot[i];
            if(integer(r,"cell_index")!=static_cast<int>(i)) throw std::runtime_error("snapshot order mismatch");
            occ[i]=r.at("occupancy")=="Free"?Occupancy::Free:Occupancy::Obstacle;
            if(occ[i]==Occupancy::Free) ++meta.numFreeCells;
            live[i].logOdds=d(r,"log_odds");
            live[i].confidence=d(r,"confidence");
            live[i].omega=d(r,"omega");
            live[i].distanceFromRobot=d(r,"distance_from_robot");
            live[i].originalPropagationDirection=Vector2(
                static_cast<float>(d(r,"propagation_x")),
                static_cast<float>(d(r,"propagation_y")));
        }

        const long long updateStamp=std::stoll(windRows[0].at("steady_ns"));
        HitProbabilitySettings hit;
        hit.localEstimationWindowSize=2;
        hit.maxUpdatesPerStop=5;
        hit.prior=0.3;
        hit.kernelSigma=1.5;
        hit.kernelStretchConstant=1.5;
        hit.confidenceMeasurementWeight=1.0;
        hit.confidenceSigmaSpatial=1.0;
        for(auto&hp:measured){hp.auxWeight=-1;hp.setProbability(hit.prior);}
        Grid2D<HitProbability> hitGrid(measured,occ,meta);
        VisibilityMap visibility(meta.dimensions.x,meta.dimensions.y,5);
        for(int x=0;x<meta.dimensions.x;++x) for(int y=0;y<meta.dimensions.y;++y) {
            Vector2Int ij(x,y);
            if(!hitGrid.freeAt(x,y)){visibility.emplace(ij,{});continue;}
            std::vector<Vector2Int> visible;
            for(int row=std::max(0,y-5);row<=std::min(meta.dimensions.y-1,y+5);++row)
              for(int col=std::max(0,x-5);col<=std::min(meta.dimensions.x-1,x+5);++col) {
                Vector2Int cell(col,row);
                if(cell==ij||GridUtils::PathFree(meta,occ,meta.indicesToCoordinates(ij),
                   meta.indicesToCoordinates(cell))) visible.push_back(cell);
              }
            visibility.emplace(ij,visible);
        }
        int eventCount=0;
        for(const auto&e:events) {
            if(std::stoll(e.at("steady_ns"))>updateStamp) continue;
            Vector2Int cell(integer(e,"robot_i"),integer(e,"robot_j"));
            PMFSLib::EstimateHitProbabilities(hitGrid,visibility,hit,integer(e,"hit")!=0,
                d(e,"wind_direction"),d(e,"wind_speed"),cell);
            ++eventCount;
        }
        double maxLO=0,maxConf=0;
        for(size_t i=0;i<n;++i) if(occ[i]==Occupancy::Free) {
            maxLO=std::max(maxLO,std::abs(measured[i].logOdds-live[i].logOdds));
            maxConf=std::max(maxConf,std::abs(measured[i].confidence-live[i].confidence));
        }
        if(maxLO>1e-6||maxConf>1e-6) throw std::runtime_error("R1 C hit-map replay mismatch");

        std::vector<Vector2> wind(n,Vector2(0,0));
        std::vector<bool> seen(n,false);
        for(const auto&r:windRows) {
            int idx=integer(r,"cell_index");
            if(idx<0||static_cast<size_t>(idx)>=n||seen[idx]||occ[idx]!=Occupancy::Free)
                throw std::runtime_error("invalid wind index");
            seen[idx]=true;
            wind[idx]=Vector2(static_cast<float>(d(r,"internal_u")),
                              static_cast<float>(d(r,"internal_v")));
        }
        for(size_t i=0;i<n;++i)
            if((occ[i]==Occupancy::Free)!=seen[i]) throw std::runtime_error("incomplete wind grid");

        SimulationSettings settings;
        settings.useWindGroundTruth=true;
        settings.maxRegionSize=5;
        settings.sourceDiscriminationPower=0.3;
        settings.refineFraction=0.1;
        settings.minWarmupIterations=200;
        settings.maxWarmupIterations=500;
        settings.iterationsToRecord=200;
        settings.deltaTime=0.1;
        settings.noiseSTDev=0.5;
        settings.blurSigmaX=1.5;
        settings.blurSigmaY=1.5;

        std::vector<double> posterior(n,1.0/meta.numFreeCells);
        Replay replay(Grid2D<HitProbability>(measured,occ,meta),
                      Grid2D<double>(posterior,occ,meta),
                      Grid2D<Vector2>(wind,occ,meta),settings);
        std::vector<std::vector<uint8_t>> occupancyMap(meta.dimensions.x,
            std::vector<uint8_t>(meta.dimensions.y,0));
        for(int x=0;x<meta.dimensions.x;++x) for(int y=0;y<meta.dimensions.y;++y)
            occupancyMap[x][y]=hitGrid.freeAt(x,y)?1:0;
        replay.initializeMap(occupancyMap);
        replay.visibilityMap=&visibility;

        std::vector<Candidate> candidates;
        std::vector<Utils::NQA::Node> leaves;
        for(const auto&r:candidatesCsv) {
            Candidate c;
            c.origin=Vector2Int(integer(r,"origin_i"),integer(r,"origin_j"));
            c.size=Vector2Int(integer(r,"size_i"),integer(r,"size_j"));
            c.id="quadtree_"+std::to_string(c.origin.x)+"_"+std::to_string(c.origin.y)+"_"+
                 std::to_string(c.size.x)+"_"+std::to_string(c.size.y);
            if(r.at("candidate_id")!=c.id) throw std::runtime_error("candidate ID mismatch");
            c.cx=d(r,"center_x"); c.cy=d(r,"center_y");
            candidates.push_back(c);
            leaves.emplace_back(nullptr,c.origin,c.size,occupancyMap);
        }

        fs::create_directories(out);
        std::ofstream longOut(out/"scores_long.csv");
        longOut<<"mode,candidate_id,source_sample,replica,source_x,source_y,score\n";
        std::ofstream sampleOut(out/"persistent_source_samples.csv");
        sampleOut<<"candidate_id,source_sample,source_x,source_y,qx,qy\n";
        std::ofstream summary(out/"candidate_summary.csv");
        summary<<"candidate_id,origin_i,origin_j,size_i,size_j,center_x,center_y,"
                  "resampled_mean,fixed_center_mean,persistent_marginal_mean\n";
        longOut<<std::setprecision(21); sampleOut<<std::setprecision(21); summary<<std::setprecision(21);

        for(size_t i=0;i<candidates.size();++i) {
            const auto&c=candidates[i];
            std::vector<long double> resampled,center,persistent;
            resampled.reserve(K); center.reserve(K); persistent.reserve(M*K);

            for(int r=0;r<K;++r) {
                auto s=replay.scoreResampled(leaves[i],r);
                resampled.push_back(s);
                longOut<<"resampled,"<<c.id<<",-1,"<<r<<",nan,nan,"<<s<<"\n";

                auto cs=replay.scorePoint(Vector2(static_cast<float>(c.cx),static_cast<float>(c.cy)),r);
                center.push_back(cs);
                longOut<<"fixed_center,"<<c.id<<",-1,"<<r<<","<<c.cx<<","<<c.cy<<","<<cs<<"\n";
            }

            Vector2 start=meta.indicesToCoordinates(c.origin.x,c.origin.y,false);
            Vector2 end=meta.indicesToCoordinates(c.origin.x+c.size.x,c.origin.y+c.size.y,false);
            for(int m=0;m<M;++m) {
                EventKeyedTransportRng sourceRng(EventKey{
                    GLOBAL_SEED,1,static_cast<uint64_t>(m),PERSISTENT_SOURCE_STREAM});
                const double qx=sourceRng.unitAt(0,0), qy=sourceRng.unitAt(0,1);
                Vector2 p=Vector2(static_cast<float>(start.x+qx*(end.x-start.x)),
                                  static_cast<float>(start.y+qy*(end.y-start.y)));
                sampleOut<<c.id<<","<<m<<","<<p.x<<","<<p.y<<","<<qx<<","<<qy<<"\n";
                for(int r=0;r<K;++r) {
                    auto ps=replay.scorePoint(p,r);
                    persistent.push_back(ps);
                    longOut<<"persistent,"<<c.id<<","<<m<<","<<r<<","<<p.x<<","<<p.y<<","<<ps<<"\n";
                }
            }
            summary<<c.id<<","<<c.origin.x<<","<<c.origin.y<<","<<c.size.x<<","<<c.size.y<<","
                   <<c.cx<<","<<c.cy<<","<<mean(resampled)<<","<<mean(center)<<","<<mean(persistent)<<"\n";
        }

        std::ofstream audit(out/"source_blind_audit.txt");
        audit<<"contract=PERSISTENT_SOURCE_PMFS_R1_V0\n"
             <<"truth_read=false\n"
             <<"event_count="<<eventCount<<"\n"
             <<"candidate_count="<<candidates.size()<<"\n"
             <<"K="<<K<<"\nM="<<M<<"\n"
             <<"global_seed="<<GLOBAL_SEED<<"\n"
             <<"transport_stream="<<TRANSPORT_STREAM<<"\n"
             <<"resampled_source_stream="<<RESAMPLED_SOURCE_STREAM<<"\n"
             <<"persistent_source_stream="<<PERSISTENT_SOURCE_STREAM<<"\n"
             <<"max_hit_map_log_odds_diff="<<std::setprecision(17)<<maxLO<<"\n"
             <<"max_hit_map_confidence_diff="<<maxConf<<"\n";
        std::cout<<"PERSISTENT_SOURCE_R1_SOURCE_BLIND_COMPLETE candidates="
                 <<candidates.size()<<" K="<<K<<" M="<<M<<"\n";
        return 0;
    } catch(const std::exception&e) {
        std::cerr<<"PERSISTENT_SOURCE_R1_FAILED: "<<e.what()<<"\n";
        return 1;
    }
}
