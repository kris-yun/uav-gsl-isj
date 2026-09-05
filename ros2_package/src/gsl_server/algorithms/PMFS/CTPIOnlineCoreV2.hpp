#pragma once
// Versioned, ROS-independent core. Legacy R4 code is intentionally untouched.
// Grid ordering matches Grid2DMetadata: x + y*nx (NOT numpy's x-major order).
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <deque>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace GSL::ctpi_v2
{
inline void require(bool ok, const char* error)
{
    if (!ok) throw std::invalid_argument(error);
}

struct StepAudit
{
    size_t substeps = 0;
    double initialSum = 0, finalSum = 0, injectedSum = 0;
    double minimum = 0, maxOutgoingRate = 0;
};

class Transport
{
    struct Face { size_t a, b; bool horizontal; };
    size_t nx_, ny_;
    double dx_, diffusion_;
    std::vector<unsigned char> free_;
    std::vector<Face> faces_;
public:
    // Solid and exterior boundaries are no-flux. This is an explicit NEW
    // model contract, not a claim of parity with the legacy absorbing mask.
    Transport(size_t nx, size_t ny, double dx, double diffusion,
              std::vector<unsigned char> free)
        : nx_(nx), ny_(ny), dx_(dx), diffusion_(diffusion), free_(std::move(free))
    {
        require(nx>0 && ny>0 && nx<=std::numeric_limits<size_t>::max()/ny && free_.size()==nx*ny,
                "CTPI_V2_GRID_SIZE");
        require(std::isfinite(dx) && dx>0 && std::isfinite(diffusion) && diffusion>=0,
                "CTPI_V2_DISCRETIZATION");
        for (size_t y=0; y<ny; ++y) for (size_t x=0; x<nx; ++x)
        {
            const size_t a=x+y*nx;
            if (!free_[a]) continue;
            if (x+1<nx && free_[a+1]) faces_.push_back({a,a+1,true});
            if (y+1<ny && free_[a+nx]) faces_.push_back({a,a+nx,false});
        }
    }

    StepAudit advance(std::vector<double>& concentration,
                      const std::vector<double>& u, const std::vector<double>& v,
                      double duration, size_t source, double sourceRate=1.) const
    {
        const size_t n=free_.size();
        require(concentration.size()==n && u.size()==n && v.size()==n, "CTPI_V2_FIELD_SIZE");
        require(std::isfinite(duration) && duration>0 && std::isfinite(sourceRate) && sourceRate>=0,
                "CTPI_V2_TIME_OR_SOURCE_RATE");
        require(source<n && free_[source], "CTPI_V2_SOURCE_NOT_FREE");
        StepAudit audit;
        for (size_t i=0; i<n; ++i)
        {
            require(std::isfinite(concentration[i]) && concentration[i]>=0,
                    "CTPI_V2_INVALID_CONCENTRATION");
            require(std::isfinite(u[i]) && std::isfinite(v[i]), "CTPI_V2_INVALID_WIND");
            require(free_[i] || concentration[i]==0, "CTPI_V2_SOLID_CONCENTRATION");
            audit.initialSum+=concentration[i];
        }
        const double diffusionRate=diffusion_/(dx_*dx_);
        std::vector<double> outgoing(n,0.), rates;
        rates.reserve(faces_.size());
        for (const auto& f:faces_)
        {
            const auto& w=f.horizontal?u:v;
            const double rate=(w[f.a]/2.+w[f.b]/2.)/dx_;
            require(std::isfinite(rate), "CTPI_V2_WIND_RATE_OVERFLOW");
            rates.push_back(rate);
            outgoing[f.a]+=std::max(rate,0.)+diffusionRate;
            outgoing[f.b]+=std::max(-rate,0.)+diffusionRate;
        }
        audit.maxOutgoingRate=*std::max_element(outgoing.begin(),outgoing.end());
        const double requiredSteps=std::ceil(duration*audit.maxOutgoingRate);
        // Resource/invalid-input guard, not a physical model parameter.
        require(std::isfinite(requiredSteps) && requiredSteps<=1000000., "CTPI_V2_SUBSTEP_LIMIT");
        audit.substeps=std::max<size_t>(1,static_cast<size_t>(requiredSteps));
        const double dt=duration/static_cast<double>(audit.substeps);
        std::vector<double> next(n);
        for (size_t step=0; step<audit.substeps; ++step)
        {
            // Convex nonnegative update: never clip negative concentrations.
            for (size_t i=0; i<n; ++i)
            {
                double retained=1.-dt*outgoing[i];
                require(retained>=-32*std::numeric_limits<double>::epsilon(), "CTPI_V2_CFL_VIOLATION");
                // Only coefficient round-off (not state clipping) is rounded.
                next[i]=std::max(retained,0.)*concentration[i];
            }
            for (size_t j=0; j<faces_.size(); ++j)
            {
                const auto& f=faces_[j]; const double r=rates[j];
                next[f.b]+=dt*(std::max(r,0.)+diffusionRate)*concentration[f.a];
                next[f.a]+=dt*(std::max(-r,0.)+diffusionRate)*concentration[f.b];
            }
            next[source]+=sourceRate*dt;
            concentration.swap(next);
        }
        audit.injectedSum=sourceRate*duration;
        audit.minimum=*std::min_element(concentration.begin(),concentration.end());
        for (double c:concentration)
        {
            require(std::isfinite(c) && c>=0, "CTPI_V2_NUMERIC_STATE_INVALID");
            audit.finalSum+=c;
        }
        require(std::abs(audit.finalSum-audit.initialSum-audit.injectedSum)
                <=1e-10*std::max(1.,audit.initialSum+audit.injectedSum), "CTPI_V2_MASS_BALANCE");
        return audit;
    }
};

class Fopdt
{
    double time_=0., state_=0., tau_, dead_;
    std::deque<std::pair<double,double>> history_{{0.,0.}};
public:
    Fopdt(double tau=1.2,double dead=0.4):tau_(tau),dead_(dead)
    {
        require(std::isfinite(tau)&&tau>0&&std::isfinite(dead)&&dead>=0,"CTPI_V2_SENSOR_CONFIG");
    }
    double step(double input,double dt)
    {
        require(std::isfinite(input)&&input>=0&&std::isfinite(dt)&&dt>0,"CTPI_V2_SENSOR_INPUT");
        time_+=dt;
        history_.emplace_back(time_,input);
        const double query=time_-dead_;
        double delayed=0.;
        if (query>0.)
        {
            while (history_.size()>2 && history_[1].first<query) history_.pop_front();
            if (query>=history_.back().first) delayed=history_.back().second;
            else
            {
                for (size_t i=1;i<history_.size();++i)
                {
                    if (query<=history_[i].first)
                    {
                        const auto [a,x]=history_[i-1]; const auto [b,y]=history_[i];
                        delayed=x+(query-a)/(b-a)*(y-x); break;
                    }
                }
            }
        }
        const double alpha=std::exp(-dt/tau_);
        state_=alpha*state_+(1.-alpha)*delayed;
        return std::clamp(state_,0.,1e6); // SAME measurement saturation as sensor contract.
    }
};

// Boundary between M2 and M1: issue predictions BEFORE consuming observations.
// Keeps delayed sensor state during motion as well as measurement stops.
// A complete, separately qualified likelihood must consume these blocks;
// this class deliberately does not invent likelihood temperatures or priors.
struct ObservationBlock
{
    double firstStamp=0,lastStamp=0,observedMean=0;
    size_t samples=0;
    std::vector<double> predictedMean;
};

class ObservationStream
{
    std::vector<Fopdt> sensors_;
    double previousStamp_=0.;
    bool awaiting_=false;
    std::vector<double> pending_;
    ObservationBlock block_;
public:
    explicit ObservationStream(size_t candidates):sensors_(candidates)
    {
        require(candidates>0,"CTPI_V2_NO_CANDIDATES");
        block_.predictedMean.assign(candidates,0.);
    }
    const std::vector<double>& predict(double stamp, double windAvailableAt,
                                        const std::vector<double>& concentration)
    {
        require(!awaiting_,"CTPI_V2_OBSERVATION_NOT_CONSUMED");
        require(std::isfinite(stamp)&&stamp>previousStamp_,"CTPI_V2_NONMONOTONE_SAMPLE");
        require(std::isfinite(windAvailableAt)&&windAvailableAt>=0&&windAvailableAt<=previousStamp_,
                "CTPI_V2_NONCAUSAL_WIND");
        require(concentration.size()==sensors_.size(),"CTPI_V2_CANDIDATE_COUNT");
        const double dt=stamp-previousStamp_;
        // The authorized sensor cadence is 0.2 s from simulator t=0. A late
        // attachment or missed message must not silently reset sensor history.
        require(std::abs(dt-0.2)<=1e-9,"CTPI_V2_SAMPLE_GAP_OR_MISSING_START_HISTORY");
        // Fail before mutating any candidate state.
        for(double c:concentration) require(std::isfinite(c)&&c>=0,"CTPI_V2_SENSOR_INPUT");
        pending_.resize(sensors_.size());
        for(size_t i=0;i<sensors_.size();++i) pending_[i]=sensors_[i].step(concentration[i],dt);
        previousStamp_=stamp; awaiting_=true;
        return pending_;
    }
    void observe(double measured,bool inMeasurementBlock)
    {
        require(awaiting_,"CTPI_V2_PREDICTION_REQUIRED");
        require(std::isfinite(measured)&&measured>=0,"CTPI_V2_OBSERVATION_INVALID");
        if(inMeasurementBlock)
        {
            if(!block_.samples) block_.firstStamp=previousStamp_;
            block_.lastStamp=previousStamp_;
            ++block_.samples;
            block_.observedMean+=measured;
            for(size_t i=0;i<pending_.size();++i) block_.predictedMean[i]+=pending_[i];
        }
        awaiting_=false;
    }
    ObservationBlock finishBlock()
    {
        require(!awaiting_&&block_.samples>0,"CTPI_V2_EMPTY_OR_PENDING_BLOCK");
        auto result=block_;
        result.observedMean/=static_cast<double>(result.samples);
        for(double& p:result.predictedMean) p/=static_cast<double>(result.samples);
        block_=ObservationBlock{}; block_.predictedMean.assign(sensors_.size(),0.);
        return result;
    }
};
} // namespace GSL::ctpi_v2
