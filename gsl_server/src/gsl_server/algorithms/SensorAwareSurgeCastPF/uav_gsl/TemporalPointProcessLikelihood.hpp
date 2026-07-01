#pragma once
// TPP-L: Temporal Point Process Likelihood for UAV Gas Source Localization
// Replaces binary/Gaussian observation likelihood with Hawkes-process-based
// conditional intensity that captures plume intermittency and self-excitation.
//
// Scientific basis: Gas arrivals in turbulent indoor environments form
// self-exciting temporal point processes -- each filament arrival increases
// the probability of subsequent arrivals (refractory period + burst structure).
// The Hawkes process naturally models this via:
//   lambda(t) = mu + alpha * sum_{t_i < t} g(t - t_i)
// where mu = background rate, alpha = excitation strength, g = triggering kernel.
//
// Cross-domain origin: Computational neuroscience (neural spike train analysis)
// and quantitative finance (high-frequency trading event modeling).
// Key references: NeurIPS 2024 (Cumulative Hazard TPP), AAAI 2024 (Latent Causal Rules)

#include <deque>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <cstdint>

namespace uav_gsl {

struct TPPDiagnostics {
    double conditional_intensity{0.0};   // lambda(t)
    double background_rate{0.0};         // mu
    double excitation_component{0.0};    // alpha * sum g(t-t_i)
    double inter_bout_interval_s{0.0};   // last IBI
    double mean_ibi_s{0.0};             // mean IBI
    double ibi_cv{0.0};                 // coefficient of variation of IBI (>1 = bursty)
    double tpp_likelihood_modifier{1.0}; // multiplicative modifier for SEPF
    std::size_t bout_count{0};
    double time_since_last_bout_s{0.0};
    double cumhaz{0.0};                 // cumulative hazard (NeurIPS 2024 method)
};

class TemporalPointProcessLikelihood {
public:
    struct Config {
        double background_rate_mu{0.05};      // background bout rate (events/s)
        double excitation_alpha{0.3};          // self-excitation strength [0,1)
        double triggering_decay_beta{2.0};     // exponential kernel decay rate (1/s)
        double refractory_period_s{0.5};       // minimum inter-bout interval
        double observation_window_s{60.0};     // sliding window for IBI statistics
        double likelihood_gain{1.5};           // scaling factor for TPP modifier
        double min_intensity_ratio{0.1};       // floor for lambda/mu ratio
        double max_intensity_ratio{5.0};       // cap for lambda/mu ratio
        bool use_wind_modulation{true};        // modulate mu by wind alignment
        double wind_alignment_gain{0.3};       // how much aligned wind boosts rate
    };

    TemporalPointProcessLikelihood() = default; explicit TemporalPointProcessLikelihood(const Config& c) : cfg_(c) {}

    // Call on every bout onset event
    void onBoutOnset(double timestamp_s) {
        bout_timestamps_.push_back(timestamp_s);

        // Compute IBI
        if (bout_timestamps_.size() >= 2) {
            double ibi = timestamp_s - bout_timestamps_[bout_timestamps_.size() - 2];
            if (ibi >= cfg_.refractory_period_s) {
                recent_ibis_.push_back(ibi);
            }
        }

        // Trim old events outside observation window
        while (!bout_timestamps_.empty() &&
               (timestamp_s - bout_timestamps_.front()) > cfg_.observation_window_s) {
            bout_timestamps_.pop_front();
        }
        while (recent_ibis_.size() > 50) {
            recent_ibis_.pop_front();
        }
    }

    // Compute conditional intensity at current time
    // This is the core Hawkes process computation:
    //   lambda(t) = mu + alpha * sum_{t_i < t} exp(-beta * (t - t_i))
    TPPDiagnostics computeIntensity(double current_time_s, double wind_alignment = 0.0) const {
        TPPDiagnostics diag;
        diag.bout_count = bout_timestamps_.size();

        // Background rate with optional wind modulation
        double mu = cfg_.background_rate_mu;
        if (cfg_.use_wind_modulation && wind_alignment > 0.0) {
            // When wind is aligned (blowing toward source), plume more likely to arrive
            mu *= (1.0 + cfg_.wind_alignment_gain * wind_alignment);
        }
        diag.background_rate = mu;

        // Self-excitation component: sum of exponential kernels
        double excitation = 0.0;
        for (double t_i : bout_timestamps_) {
            double dt = current_time_s - t_i;
            if (dt > 0.0 && dt < cfg_.observation_window_s) {
                // Exponential triggering kernel
                excitation += std::exp(-cfg_.triggering_decay_beta * dt);
            }
        }
        excitation *= cfg_.excitation_alpha;
        diag.excitation_component = excitation;

        // Conditional intensity
        double lambda = mu + excitation;
        diag.conditional_intensity = lambda;

        // Time since last bout
        if (!bout_timestamps_.empty()) {
            diag.time_since_last_bout_s = current_time_s - bout_timestamps_.back();
        }

        // IBI statistics
        if (recent_ibis_.size() >= 2) {
            double sum = std::accumulate(recent_ibis_.begin(), recent_ibis_.end(), 0.0);
            diag.mean_ibi_s = sum / recent_ibis_.size();
            double sq_sum = 0.0;
            for (double ibi : recent_ibis_) {
                sq_sum += (ibi - diag.mean_ibi_s) * (ibi - diag.mean_ibi_s);
            }
            double std_ibi = std::sqrt(sq_sum / recent_ibis_.size());
            diag.ibi_cv = diag.mean_ibi_s > 1e-6 ? std_ibi / diag.mean_ibi_s : 0.0;
        }
        if (!recent_ibis_.empty()) {
            diag.inter_bout_interval_s = recent_ibis_.back();
        }

        // Cumulative hazard (NeurIPS 2024 method)
        // H(t) = integral_0^t lambda(s) ds
        // For Hawkes: H(t) = mu*t + (alpha/beta) * sum [1 - exp(-beta*(t-t_i))]
        double cumhaz = mu * cfg_.observation_window_s;
        for (double t_i : bout_timestamps_) {
            double dt = current_time_s - t_i;
            if (dt > 0.0) {
                cumhaz += (cfg_.excitation_alpha / cfg_.triggering_decay_beta) *
                          (1.0 - std::exp(-cfg_.triggering_decay_beta * dt));
            }
        }
        diag.cumhaz = cumhaz;

        // Likelihood modifier for SEPF
        // When lambda is high (many recent bouts), gas is likely nearby -> boost evidence
        // When lambda is low (no recent bouts), gas is far -> suppress evidence
        double ratio = lambda / std::max(1e-6, mu);
        ratio = std::clamp(ratio, cfg_.min_intensity_ratio, cfg_.max_intensity_ratio);
        diag.tpp_likelihood_modifier = cfg_.likelihood_gain * (ratio - 1.0) + 1.0;
        // Clamp to reasonable range
        diag.tpp_likelihood_modifier = std::clamp(diag.tpp_likelihood_modifier, 0.1, 3.0);

        return diag;
    }

    // Get the number of bouts in the window
    std::size_t boutCount() const { return bout_timestamps_.size(); }

    // Reset state
    void reset() {
        bout_timestamps_.clear();
        recent_ibis_.clear();
    }

private:
    Config cfg_;
    std::deque<double> bout_timestamps_;
    std::deque<double> recent_ibis_;
};

}  // namespace uav_gsl
