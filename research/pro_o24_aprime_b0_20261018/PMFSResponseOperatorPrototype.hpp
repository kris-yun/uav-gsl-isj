#pragma once
// Scientific prototype, isolated from frozen 2024 O24 source.
// Requires C++17; it is deliberately NOT a replacement physical simulator.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace pmfs_a_prime_prototype {

struct NativeHitObservation {
    std::vector<double> observed_hit_probability;
    std::vector<double> confidence;
    std::vector<std::uint8_t> is_free;
};

inline double nativeO24Score(const NativeHitObservation& obs,
                             const std::vector<float>& candidate_hit,
                             double source_discrimination_power=0.2) {
    const std::size_t n=obs.observed_hit_probability.size();
    if(obs.confidence.size()!=n || obs.is_free.size()!=n || candidate_hit.size()!=n ||
       !std::isfinite(source_discrimination_power) || source_discrimination_power<0)
        throw std::invalid_argument("Hit vector / confidence / mask identity invalid");
    double p=1.0;
    for(std::size_t i=0;i<n;i++) {
        if(!obs.is_free[i]) continue;
        const double m=obs.observed_hit_probability[i];
        const double c=obs.confidence[i];
        const double q=static_cast<double>(candidate_hit[i]);
        if(!(std::isfinite(m)&&std::isfinite(q)&&std::isfinite(c))||m<0||m>1||
           q<0||q>1||c<0||c>1) throw std::invalid_argument("Invalid free hit statistics");
        p*=1.0-c*source_discrimination_power*std::abs(m-q);
    }
    return p;
}

struct PpmObservation {
    std::vector<std::string> window_ids;  // matched after clock reconciliation
    std::vector<double> observed_ppm;
    std::vector<double> sigma_ppm;        // positive calibrated uncertainty
};
struct PpmCandidate {
    std::vector<std::string> window_ids;  // exactly corresponding receptor-time windows
    std::vector<double> response_ppm_per_release;
    std::string source_id;
};
struct PhysicalProvenance {
    std::string scene_id;
    std::string wind_input; // "measured_or_estimated" for deployable path
    std::string release_unit; // "mg/s" etc; not "hit" or "unknown"
    std::string sensor_operator; // "calibrated_linear_ppm"
    std::string physical_clock;
    std::string forward_solver_id;
    std::string calibration_id;
};

inline void verifyPpmInputs(const PpmObservation& obs, const PpmCandidate& c,
                            const PhysicalProvenance& meta, bool deployment=true) {
    const std::size_t n=obs.window_ids.size();
    if(n==0||n!=obs.observed_ppm.size()||n!=obs.sigma_ppm.size()||
       n!=c.response_ppm_per_release.size()||obs.window_ids!=c.window_ids||
       c.source_id.empty()) throw std::invalid_argument("Ppm response windows not matched");
    if(meta.scene_id.empty()||meta.forward_solver_id.empty()||
       meta.physical_clock.empty()||meta.calibration_id.empty()||
       meta.release_unit.empty()||meta.release_unit=="unknown"||meta.release_unit=="hit"||
       meta.sensor_operator!="calibrated_linear_ppm"||
       (deployment && meta.wind_input!="measured_or_estimated"))
        throw std::invalid_argument("Physical provenance or deployable wind missing");
    for(std::size_t i=0;i<n;i++)
        if(obs.window_ids[i].empty()||!std::isfinite(obs.observed_ppm[i])||
           !std::isfinite(obs.sigma_ppm[i])||!std::isfinite(c.response_ppm_per_release[i])||
           obs.observed_ppm[i]<0||obs.sigma_ppm[i]<=0||c.response_ppm_per_release[i]<0)
            throw std::invalid_argument("Invalid ppm, uncertainty, or physical response");
}

struct PpmScore {
    double best_positive_release;
    double log_likelihood_without_shared_normalizing_constant;
};

inline PpmScore scoreMatchedPpm(const PpmObservation& obs,const PpmCandidate& c,
                                const PhysicalProvenance& meta,
                                bool deployment=true) {
    verifyPpmInputs(obs,c,meta,deployment);
    double numer=0,denom=0;
    for(std::size_t i=0;i<obs.window_ids.size();++i){
        const double w=1.0/(obs.sigma_ppm[i]*obs.sigma_ppm[i]);
        numer+=w*c.response_ppm_per_release[i]*obs.observed_ppm[i];
        denom+=w*c.response_ppm_per_release[i]*c.response_ppm_per_release[i];
    }
    const double q=denom>0?std::max(0.0,numer/denom):0.0;
    double ll=0;
    for(std::size_t i=0;i<obs.window_ids.size();++i){
        const double r=(obs.observed_ppm[i]-q*c.response_ppm_per_release[i])/obs.sigma_ppm[i];
        ll-=0.5*r*r;
    }
    return {q,ll};
}
}
