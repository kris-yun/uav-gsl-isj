#pragma once

#include "uav_gsl/Common.hpp"
#include "uav_gsl/SoftEvidenceParticleFilter.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>

namespace uav_gsl {

// Knowledge-Bounded Test-Time Mixture Evidence likelihood.
// This class is intentionally header-only so it can be integrated into the
// existing SensorAwareSurgeCastPF target without adding a new library target.
class TestTimeMixturePlumeLikelihood {
public:
    enum class Expert : std::size_t {
        Advection = 0,
        Filament = 1,
        Wake = 2,
        Background = 3,
        Count = 4
    };

    struct Config {
        double background_hit_probability{0.01};
        double plume_gain{2.0};
        double crosswind_sigma_base_m{0.35};
        double crosswind_sigma_growth{0.30};
        double downwind_decay_length_m{15.0};
        double downwind_offset_m{0.40};
        double minimum_wind_speed{0.03};
        double router_learning_rate{0.08};
        double router_temperature{0.75};
        double log_likelihood_clip{6.0};
        double disagreement_penalty{7.0};
        double confidence_floor{0.15};
        double confidence_ceiling{1.0};
        double minimum_probability{1e-8};
    };

    struct Diagnostics {
        std::array<double, 4> router_weights{{0.25, 0.25, 0.25, 0.25}};
        std::array<double, 4> posterior_mean_expert_probability{{0.0, 0.0, 0.0, 0.0}};
        double expert_disagreement{0.0};
        double knowledge_confidence{1.0};
        double router_entropy{0.0};
        std::size_t update_count{0};
    };

    TestTimeMixturePlumeLikelihood() : TestTimeMixturePlumeLikelihood(Config{}) {}

    explicit TestTimeMixturePlumeLikelihood(const Config& config)
        : config_(config) {
        validateConfig();
        logits_.fill(0.0);
        refreshRouterWeights();
    }

    void reset() {
        logits_.fill(0.0);
        diagnostics_ = Diagnostics{};
        refreshRouterWeights();
    }

    Diagnostics diagnostics() const { return diagnostics_; }

    std::array<double, 4> expertProbabilities(
        const SoftEvidenceParticleFilter::Particle& particle,
        const SoftEvidenceParticleFilter::Observation& observation) const {
        validateObservation(observation);
        const Vec2 delta = observation.sensing_position - particle.source;
        const double flow_to = wrapAngle(observation.wind_flow_to_rad + particle.wind_bias_rad);
        const double downwind = delta.x * std::cos(flow_to) + delta.y * std::sin(flow_to);
        const double crosswind = -delta.x * std::sin(flow_to) + delta.y * std::cos(flow_to);
        const double wind_scale = std::max(config_.minimum_wind_speed, observation.wind_speed);
        const double down = std::max(0.0, downwind + config_.downwind_offset_m);
        const double sigma = config_.crosswind_sigma_base_m + config_.crosswind_sigma_growth * down;

        double advection = config_.background_hit_probability +
            particle.release * config_.plume_gain * std::exp(-down / config_.downwind_decay_length_m) *
            std::exp(-0.5 * square(crosswind / std::max(1e-6, sigma)));
        if (downwind < -config_.downwind_offset_m) advection *= 0.15;

        const double filament_sigma = 1.75 * sigma + 0.15 * std::sqrt(1.0 + down);
        double filament = config_.background_hit_probability +
            0.75 * particle.release * config_.plume_gain * std::exp(-down / (1.8 * config_.downwind_decay_length_m)) *
            std::exp(-std::abs(crosswind) / std::max(1e-6, filament_sigma));
        if (downwind < -1.0) filament *= 0.35;

        const double wake_sigma = 2.5 * sigma + 0.5 / wind_scale;
        double wake = config_.background_hit_probability +
            0.35 * particle.release * config_.plume_gain * std::exp(-down / (2.2 * config_.downwind_decay_length_m)) *
            std::exp(-0.5 * square(crosswind / std::max(1e-6, wake_sigma)));
        if (observation.wind_speed < 0.15) wake *= 1.25;

        const double background = config_.background_hit_probability + 0.04;

        return {{clampProb(advection, 0.98),
                 clampProb(filament, 0.95),
                 clampProb(wake, 0.90),
                 clamp(background, config_.background_hit_probability, 0.25)}};
    }

    double predictiveHitProbability(
        const SoftEvidenceParticleFilter::Particle& particle,
        const SoftEvidenceParticleFilter::Observation& observation) const {
        const auto probs = expertProbabilities(particle, observation);
        double p = 0.0;
        for (std::size_t e = 0; e < probs.size(); ++e) {
            p += diagnostics_.router_weights[e] * probs[e];
        }
        return clamp(p, config_.minimum_probability, 1.0 - config_.minimum_probability);
    }

    Diagnostics updateRouter(
        const std::vector<SoftEvidenceParticleFilter::Particle>& particles,
        const SoftEvidenceParticleFilter::Observation& observation) {
        if (particles.empty()) throw std::invalid_argument("KB-TME requires particles");
        validateObservation(observation);
        std::array<double, 4> scores{{0.0, 0.0, 0.0, 0.0}};
        std::array<double, 4> mean_probs{{0.0, 0.0, 0.0, 0.0}};
        double weight_sum = 0.0;
        for (const auto& p : particles) weight_sum += std::max(0.0, p.weight);
        if (weight_sum <= 0.0) weight_sum = 1.0;

        const double z = clamp(observation.hit_probability, 0.0, 1.0);
        for (const auto& particle : particles) {
            const double w = std::max(0.0, particle.weight) / weight_sum;
            const auto probs = expertProbabilities(particle, observation);
            for (std::size_t e = 0; e < probs.size(); ++e) {
                const double p = clamp(probs[e], config_.minimum_probability, 1.0 - config_.minimum_probability);
                const double ll = z * std::log(p) + (1.0 - z) * std::log(1.0 - p);
                scores[e] += w * clamp(ll, -config_.log_likelihood_clip, config_.log_likelihood_clip);
                mean_probs[e] += w * p;
            }
        }
        for (std::size_t e = 0; e < logits_.size(); ++e) {
            logits_[e] = (1.0 - config_.router_learning_rate) * logits_[e] +
                         config_.router_learning_rate * scores[e];
        }
        refreshRouterWeights();

        double mixture_mean = 0.0;
        for (std::size_t e = 0; e < mean_probs.size(); ++e) {
            mixture_mean += diagnostics_.router_weights[e] * mean_probs[e];
        }
        double disagreement = 0.0;
        for (std::size_t e = 0; e < mean_probs.size(); ++e) {
            disagreement += diagnostics_.router_weights[e] * square(mean_probs[e] - mixture_mean);
        }
        diagnostics_.posterior_mean_expert_probability = mean_probs;
        diagnostics_.expert_disagreement = disagreement;
        diagnostics_.knowledge_confidence = clamp(observation.evidence_confidence *
                                                  std::exp(-config_.disagreement_penalty * disagreement),
                                                  config_.confidence_floor,
                                                  config_.confidence_ceiling);
        ++diagnostics_.update_count;
        return diagnostics_;
    }

private:
    Config config_{};
    std::array<double, 4> logits_{{0.0, 0.0, 0.0, 0.0}};
    Diagnostics diagnostics_{};

    static double square(double x) { return x * x; }

    static double clamp(double x, double lo, double hi) {
        return std::max(lo, std::min(hi, x));
    }

    double clampProb(double p, double hi) const {
        return clamp(p, config_.background_hit_probability, hi);
    }

    void refreshRouterWeights() {
        const double temperature = std::max(1e-6, config_.router_temperature);
        double max_logit = -std::numeric_limits<double>::infinity();
        for (double l : logits_) max_logit = std::max(max_logit, l / temperature);
        double sum = 0.0;
        for (std::size_t e = 0; e < logits_.size(); ++e) {
            diagnostics_.router_weights[e] = std::exp(logits_[e] / temperature - max_logit);
            sum += diagnostics_.router_weights[e];
        }
        if (sum <= 0.0 || !std::isfinite(sum)) {
            diagnostics_.router_weights = {{0.25, 0.25, 0.25, 0.25}};
        } else {
            for (double& w : diagnostics_.router_weights) w /= sum;
        }
        diagnostics_.router_entropy = 0.0;
        for (double w : diagnostics_.router_weights) {
            if (w > 0.0) diagnostics_.router_entropy -= w * std::log(w);
        }
    }

    void validateConfig() const {
        if (config_.background_hit_probability <= 0.0 ||
            config_.background_hit_probability >= 0.5 ||
            config_.plume_gain <= 0.0 ||
            config_.crosswind_sigma_base_m <= 0.0 ||
            config_.crosswind_sigma_growth < 0.0 ||
            config_.downwind_decay_length_m <= 0.0 ||
            config_.router_learning_rate <= 0.0 ||
            config_.router_learning_rate > 1.0 ||
            config_.router_temperature <= 0.0 ||
            config_.minimum_probability <= 0.0) {
            throw std::invalid_argument("invalid KB-TME config");
        }
    }

    static void validateObservation(const SoftEvidenceParticleFilter::Observation& obs) {
        if (!finite(obs.sensing_position) ||
            !std::isfinite(obs.hit_probability) || obs.hit_probability < 0.0 || obs.hit_probability > 1.0 ||
            !std::isfinite(obs.evidence_confidence) ||
            !std::isfinite(obs.wind_flow_to_rad) ||
            !std::isfinite(obs.wind_speed)) {
            throw std::invalid_argument("invalid KB-TME observation");
        }
    }
};

}  // namespace uav_gsl
