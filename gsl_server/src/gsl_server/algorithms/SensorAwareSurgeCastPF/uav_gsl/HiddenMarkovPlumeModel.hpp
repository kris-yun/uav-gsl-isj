#pragma once
// HMM-PM: Hidden Markov Plume Model for UAV Gas Source Localization
// Models plume arrival/departure as a 2-state HMM embedded in the particle filter.
// Instead of using static P(gas|source,wind), we model:
//   z(t) in {absent, present} -- hidden plume state at sensor location
//   x(t) = MOX reading -- observation
//   P(z(t+1)|z(t), wind) -- transition driven by wind
//   P(x(t)|z(t), sensor_state) -- emission from SDBE
//
// Scientific basis: In intermittent turbulent plumes, the probability of gas
// arrival depends on whether the sensor is currently IN a plume filament.
// A 2-state HMM captures this: once you detect gas, you are likely to
// continue detecting (self-excitation), and once you miss, you likely
// continue missing (refractory period). This replaces the static
// P(hit|source,wind) = 1 - exp(-gain * ...) assumption.
//
// Cross-domain origin: Speech recognition (Rabiner 1989), EEG spike detection
// Key reference: NeurIPS 2024 (Cumulative Hazard TPP)

#include <cmath>
#include <algorithm>
#include <array>

namespace uav_gsl {

struct HMMDiagnostics {
    double p_present{0.5};        // P(z=present | observations)
    double p_absent{0.5};         // P(z=absent | observations)
    double likelihood_modifier{1.0}; // multiplicative modifier for PF
    double log_likelihood{0.0};   // observation log-likelihood
    int state_estimate{0};        // 0=absent, 1=present
    double transition_stickiness{0.0}; // how "sticky" the current state is
};

class HiddenMarkovPlumeModel {
public:
    struct Config {
        // Transition probabilities (wind-modulated)
        double p_stay_present{0.7};    // P(present->present): high = plume is sticky
        double p_stay_absent{0.85};    // P(absent->absent): high = plume absence is sticky
        double wind_speed_gain{0.5};   // how much wind speed affects transition
        double wind_alignment_gain{0.3}; // how much wind alignment affects transition

        // Emission probabilities
        double p_hit_given_present{0.8};  // P(sensor_hit | plume_present)
        double p_hit_given_absent{0.05};  // P(sensor_hit | plume_absent) = false alarm

        // Smoothing
        double alpha{0.3};  // exponential smoothing for posterior

        // Source likelihood modulation
        double present_boost{1.5};  // boost PF likelihood when plume present
        double absent_suppress{0.3}; // suppress PF likelihood when plume absent
    };

    HiddenMarkovPlumeModel() = default; explicit HiddenMarkovPlumeModel(const Config& c) : cfg_(c) {
        // Initialize with uniform prior
        forward_present_ = 0.5;
        forward_absent_ = 0.5;
    }

    // Main update: given current sensor observation and wind, compute HMM state
    HMMDiagnostics update(bool sensor_hit, double wind_speed, double wind_alignment) {
        HMMDiagnostics diag;

        // 1. Predict: apply transition matrix
        double tp = cfg_.p_stay_present;
        double ta = cfg_.p_stay_absent;

        // Wind modulation: higher wind speed -> more likely to transition
        // (plume filaments arrive/depart faster)
        double wind_factor = std::min(1.0, wind_speed * cfg_.wind_speed_gain);
        // Wind alignment: aligned wind -> plume more likely to persist
        double align_factor = 1.0 + cfg_.wind_alignment_gain * wind_alignment;

        // Modulate transition: stronger wind reduces stickiness
        tp = std::max(0.3, tp - 0.2 * wind_factor);
        ta = std::max(0.3, ta - 0.15 * wind_factor * align_factor);

        // Predict step
        double pred_present = tp * forward_present_ + (1.0 - ta) * forward_absent_;
        double pred_absent = (1.0 - tp) * forward_present_ + ta * forward_absent_;

        // 2. Update: apply emission probabilities
        double e_present, e_absent;
        if (sensor_hit) {
            e_present = cfg_.p_hit_given_present;
            e_absent = cfg_.p_hit_given_absent;
        } else {
            e_present = 1.0 - cfg_.p_hit_given_present;
            e_absent = 1.0 - cfg_.p_hit_given_absent;
        }

        double posterior_present = pred_present * e_present;
        double posterior_absent = pred_absent * e_absent;

        // Normalize
        double total = posterior_present + posterior_absent;
        if (total > 1e-15) {
            posterior_present /= total;
            posterior_absent /= total;
        } else {
            posterior_present = 0.5;
            posterior_absent = 0.5;
        }

        // 3. Smooth (avoid flickering)
        forward_present_ = cfg_.alpha * posterior_present + (1.0 - cfg_.alpha) * forward_present_;
        forward_absent_ = cfg_.alpha * posterior_absent + (1.0 - cfg_.alpha) * forward_absent_;

        // Re-normalize after smoothing
        total = forward_present_ + forward_absent_;
        forward_present_ /= total;
        forward_absent_ /= total;

        // 4. Compute diagnostics
        diag.p_present = forward_present_;
        diag.p_absent = forward_absent_;
        diag.state_estimate = forward_present_ > 0.5 ? 1 : 0;
        diag.transition_stickiness = diag.state_estimate == 1 ? tp : ta;

        // 5. Likelihood modifier for particle filter
        // When plume present: boost likelihood (gas is here, source is nearby)
        // When plume absent: suppress likelihood (no gas, don't update source estimate)
        diag.likelihood_modifier = diag.p_present * cfg_.present_boost
                                 + diag.p_absent * cfg_.absent_suppress;
        diag.likelihood_modifier = std::clamp(diag.likelihood_modifier, 0.1, 3.0);

        // 6. Log-likelihood for diagnostics
        double obs_prob = pred_present * e_present + pred_absent * e_absent;
        diag.log_likelihood = std::log(std::max(1e-15, obs_prob));

        return diag;
    }

    void reset() {
        forward_present_ = 0.5;
        forward_absent_ = 0.5;
    }

private:
    Config cfg_;
    double forward_present_{0.5};
    double forward_absent_{0.5};
};

}  // namespace uav_gsl
