#pragma once

#include "uav_gsl/Common.hpp"

#include <cmath>
#include <cstdint>
#include <limits>

namespace uav_gsl {

// Sensor-Dynamics Bout Estimator (SDBE)
// Converts a slow, drifting gas-sensor signal into a calibrated soft hit probability.
class SensorBoutEstimator {
public:
    struct Config {
        double tau_rise_s{1.2};
        double tau_decay_s{4.0};
        double signal_smoothing_tau_s{0.25};
        double baseline_tau_s{45.0};
        double noise_tau_s{20.0};
        double minimum_noise_sigma{1e-3};
        double derivative_clip_per_s{50.0};
        double latent_clip{1e6};
        double z_midpoint{3.0};
        double z_temperature{0.75};
        double hit_on_probability{0.70};
        double hit_off_probability{0.35};
        double baseline_update_probability{0.20};
        double minimum_bout_duration_s{0.20};
        double maximum_dt_s{1.0};
    };

    struct Evidence {
        double raw{0.0};
        double filtered{0.0};
        double baseline{0.0};
        double latent_excess{0.0};
        double noise_sigma{0.0};
        double z_score{0.0};
        double hit_probability{0.0};
        double confidence{0.0};
        double estimated_delay_s{0.0};
        bool in_bout{false};
        bool bout_onset{false};
        bool bout_offset{false};
        std::uint64_t completed_bouts{0};
    };

    SensorBoutEstimator() : SensorBoutEstimator(Config{}) {}

    explicit SensorBoutEstimator(const Config& config) : config_(config) {
        validateConfig();
    }

    void reset() {
        initialized_ = false;
        filtered_ = 0.0;
        previous_filtered_ = 0.0;
        baseline_ = 0.0;
        noise_variance_ = config_.minimum_noise_sigma * config_.minimum_noise_sigma;
        hit_probability_ = 0.0;
        in_bout_ = false;
        bout_elapsed_s_ = 0.0;
        completed_bouts_ = 0;
    }

    Evidence update(double raw, double dt_s) {
        if (!std::isfinite(raw)) throw std::invalid_argument("raw gas value must be finite");
        if (!std::isfinite(dt_s) || dt_s <= 0.0) throw std::invalid_argument("dt must be positive");
        const double dt = std::min(dt_s, config_.maximum_dt_s);

        if (!initialized_) {
            initialized_ = true;
            filtered_ = raw;
            previous_filtered_ = raw;
            baseline_ = raw;
            return makeEvidence(raw, 0.0, false, false, config_.tau_rise_s);
        }

        previous_filtered_ = filtered_;
        const double sensor_tau = raw >= filtered_ ? config_.tau_rise_s : config_.tau_decay_s;
        const double smoothing_alpha = 1.0 - std::exp(-dt / config_.signal_smoothing_tau_s);
        filtered_ += smoothing_alpha * (raw - filtered_);

        double derivative = (filtered_ - previous_filtered_) / dt;
        derivative = clamp(derivative, -config_.derivative_clip_per_s, config_.derivative_clip_per_s);

        // Stable inverse of a first-order sensor response: c* ~= y + tau dy/dt.
        const double inverse_tau = derivative >= 0.0 ? config_.tau_rise_s : config_.tau_decay_s;
        const double latent = clamp(filtered_ + inverse_tau * derivative,
                                    -config_.latent_clip,
                                    config_.latent_clip);
        const double latent_excess = std::max(0.0, latent - baseline_);

        const double sigma = std::max(config_.minimum_noise_sigma, std::sqrt(noise_variance_));
        const double z_score = latent_excess / sigma;
        const double temperature = std::max(1e-6, config_.z_temperature);
        const double probability = logistic((z_score - config_.z_midpoint) / temperature);

        // Update baseline/noise only when the previous and current evidence indicate background.
        if (!in_bout_ && hit_probability_ < config_.baseline_update_probability &&
            probability < config_.baseline_update_probability) {
            const double baseline_alpha = 1.0 - std::exp(-dt / config_.baseline_tau_s);
            baseline_ += baseline_alpha * (filtered_ - baseline_);
            const double residual = filtered_ - baseline_;
            const double noise_alpha = 1.0 - std::exp(-dt / config_.noise_tau_s);
            noise_variance_ += noise_alpha * (residual * residual - noise_variance_);
            noise_variance_ = std::max(noise_variance_,
                                       config_.minimum_noise_sigma * config_.minimum_noise_sigma);
        }

        bool onset = false;
        bool offset = false;
        if (!in_bout_ && probability >= config_.hit_on_probability) {
            in_bout_ = true;
            bout_elapsed_s_ = 0.0;
            onset = true;
        }
        if (in_bout_) {
            bout_elapsed_s_ += dt;
            if (probability <= config_.hit_off_probability &&
                bout_elapsed_s_ >= config_.minimum_bout_duration_s) {
                in_bout_ = false;
                offset = true;
                ++completed_bouts_;
                bout_elapsed_s_ = 0.0;
            }
        }

        hit_probability_ = probability;
        return makeEvidence(raw, latent_excess, onset, offset, inverse_tau);
    }

    const Config& config() const { return config_; }

private:
    Config config_;
    bool initialized_{false};
    double filtered_{0.0};
    double previous_filtered_{0.0};
    double baseline_{0.0};
    double noise_variance_{1e-6};
    double hit_probability_{0.0};
    bool in_bout_{false};
    double bout_elapsed_s_{0.0};
    std::uint64_t completed_bouts_{0};

    void validateConfig() const {
        if (config_.tau_rise_s <= 0.0 || config_.tau_decay_s <= 0.0 ||
            config_.signal_smoothing_tau_s <= 0.0 || config_.baseline_tau_s <= 0.0 ||
            config_.noise_tau_s <= 0.0 || config_.minimum_noise_sigma <= 0.0) {
            throw std::invalid_argument("all time constants and noise floor must be positive");
        }
        if (!(0.0 < config_.hit_off_probability &&
              config_.hit_off_probability < config_.hit_on_probability &&
              config_.hit_on_probability < 1.0)) {
            throw std::invalid_argument("hit hysteresis probabilities are invalid");
        }
    }

    Evidence makeEvidence(double raw,
                          double latent_excess,
                          bool onset,
                          bool offset,
                          double delay_s) const {
        const double sigma = std::max(config_.minimum_noise_sigma, std::sqrt(noise_variance_));
        const double z = latent_excess / sigma;
        Evidence evidence;
        evidence.raw = raw;
        evidence.filtered = filtered_;
        evidence.baseline = baseline_;
        evidence.latent_excess = latent_excess;
        evidence.noise_sigma = sigma;
        evidence.z_score = z;
        evidence.hit_probability = hit_probability_;
        evidence.confidence = clamp(std::abs(hit_probability_ - 0.5) * 2.0, 0.0, 1.0);
        evidence.estimated_delay_s = delay_s;
        evidence.in_bout = in_bout_;
        evidence.bout_onset = onset;
        evidence.bout_offset = offset;
        evidence.completed_bouts = completed_bouts_;
        return evidence;
    }
};

}  // namespace uav_gsl
