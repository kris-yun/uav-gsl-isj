#pragma once

#include "uav_gsl/Common.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>

namespace uav_gsl {

// Soft-Evidence Particle Filter (SEPF)
// Uses continuous hit probability, explicit no-hit evidence, wind uncertainty,
// and a delay-compensated sensing position.
class SoftEvidenceParticleFilter {
public:
    struct Config {
        std::size_t particle_count{1500};
        Bounds2D bounds{};
        double release_min{0.25};
        double release_max{3.0};
        double background_hit_probability{0.01};
        double plume_gain{2.0};
        double crosswind_sigma_base_m{0.35};
        double crosswind_sigma_growth{0.30};
        double downwind_decay_length_m{15.0};
        double downwind_distance_offset_m{0.40};
        double downwind_power{1.0};
        double minimum_wind_speed_for_model{0.03};
        double default_wind_sigma_rad{15.0 * kPi / 180.0};
        int wind_quadrature_points{5};
        double minimum_probability{1e-8};
        double resample_ess_ratio{0.45};
        double jitter_position_sigma_m{0.20};
        double jitter_release_fraction{0.08};
        double jitter_wind_bias_rad{2.0 * kPi / 180.0};
        double maximum_wind_bias_rad{35.0 * kPi / 180.0};
        std::uint64_t random_seed{1};
    };

    struct Particle {
        Vec2 source{};
        double release{1.0};
        double wind_bias_rad{0.0};
        double weight{0.0};
    };

    struct Observation {
        Vec2 sensing_position{};  // Position at t - estimated sensor delay.
        double hit_probability{0.0};
        double evidence_confidence{1.0};
        double wind_flow_to_rad{0.0};
        double wind_speed{0.0};
        double wind_sigma_rad{-1.0};
        double dt_s{1.0};
    };

    struct Estimate {
        Vec2 mean{};
        Vec2 map{};
        double covariance_xx{0.0};
        double covariance_xy{0.0};
        double covariance_yy{0.0};
        double covariance_trace{0.0};
        double effective_sample_size{0.0};
        std::size_t updates{0};
    };

    using FreeSpacePredicate = std::function<bool(const Vec2&)>;
    using PredictiveLikelihoodFn = std::function<double(const Particle&, const Observation&)>;

    SoftEvidenceParticleFilter() : SoftEvidenceParticleFilter(Config{}) {}

    explicit SoftEvidenceParticleFilter(const Config& config)
        : config_(config), rng_(config.random_seed) {
        validateConfig();
    }

    void initializeUniform(const FreeSpacePredicate& is_free = {}) {
        particles_.clear();
        particles_.reserve(config_.particle_count);
        std::uniform_real_distribution<double> x_distribution(config_.bounds.min_x,
                                                               config_.bounds.max_x);
        std::uniform_real_distribution<double> y_distribution(config_.bounds.min_y,
                                                               config_.bounds.max_y);
        std::uniform_real_distribution<double> release_distribution(config_.release_min,
                                                                     config_.release_max);
        std::uniform_real_distribution<double> bias_distribution(-config_.maximum_wind_bias_rad,
                                                                  config_.maximum_wind_bias_rad);

        std::size_t attempts = 0;
        const std::size_t maximum_attempts = config_.particle_count * 200;
        while (particles_.size() < config_.particle_count && attempts++ < maximum_attempts) {
            const Vec2 source{x_distribution(rng_), y_distribution(rng_)};
            if (is_free && !is_free(source)) continue;
            particles_.push_back({source,
                                  release_distribution(rng_),
                                  bias_distribution(rng_),
                                  1.0 / static_cast<double>(config_.particle_count)});
        }
        if (particles_.size() != config_.particle_count) {
            throw std::runtime_error("could not initialize enough free-space particles");
        }
        updates_ = 0;
        estimate_history_.clear();
    }

    Estimate update(const Observation& observation,
                    const FreeSpacePredicate& is_free = {},
                    const PredictiveLikelihoodFn& custom_likelihood = {}) {
        if (particles_.empty()) throw std::runtime_error("particle filter is not initialized");
        validateObservation(observation);

        std::vector<double> log_weights(particles_.size());
        double maximum_log_weight = -std::numeric_limits<double>::infinity();
        for (std::size_t i = 0; i < particles_.size(); ++i) {
            const double predicted = custom_likelihood
                ? custom_likelihood(particles_[i], observation)
                : predictedHitProbability(particles_[i], observation);
            const double soft_log_likelihood =
                observation.hit_probability * std::log(predicted) +
                (1.0 - observation.hit_probability) * std::log(1.0 - predicted);
            const double confidence = clamp(observation.evidence_confidence, 0.0, 1.0);
            const double prior_log = std::log(std::max(config_.minimum_probability,
                                                       particles_[i].weight));
            log_weights[i] = prior_log + confidence * soft_log_likelihood;
            maximum_log_weight = std::max(maximum_log_weight, log_weights[i]);
        }

        double sum = 0.0;
        for (std::size_t i = 0; i < particles_.size(); ++i) {
            particles_[i].weight = std::exp(log_weights[i] - maximum_log_weight);
            sum += particles_[i].weight;
        }
        if (!std::isfinite(sum) || sum <= 0.0) {
            const double uniform = 1.0 / static_cast<double>(particles_.size());
            for (auto& particle : particles_) particle.weight = uniform;
        } else {
            for (auto& particle : particles_) particle.weight /= sum;
        }

        ++updates_;
        Estimate current = estimate();
        if (current.effective_sample_size <
            config_.resample_ess_ratio * static_cast<double>(particles_.size())) {
            systematicResample(is_free);
            current = estimate();
        }
        estimate_history_.push_back(current.mean);
        if (estimate_history_.size() > 30) estimate_history_.erase(estimate_history_.begin());
        return current;
    }

    Estimate estimate() const {
        if (particles_.empty()) throw std::runtime_error("particle filter is not initialized");
        Estimate result;
        result.updates = updates_;
        const Particle* map_particle = &particles_.front();
        double squared_weight_sum = 0.0;
        for (const auto& particle : particles_) {
            result.mean = result.mean + particle.source * particle.weight;
            squared_weight_sum += particle.weight * particle.weight;
            if (particle.weight > map_particle->weight) map_particle = &particle;
        }
        result.map = map_particle->source;
        for (const auto& particle : particles_) {
            const Vec2 delta = particle.source - result.mean;
            result.covariance_xx += particle.weight * delta.x * delta.x;
            result.covariance_xy += particle.weight * delta.x * delta.y;
            result.covariance_yy += particle.weight * delta.y * delta.y;
        }
        result.covariance_trace = result.covariance_xx + result.covariance_yy;
        result.effective_sample_size = squared_weight_sum > 0.0 ? 1.0 / squared_weight_sum : 0.0;
        return result;
    }

    bool declarationReady(std::size_t minimum_updates,
                          std::size_t independent_bouts,
                          std::size_t minimum_bouts,
                          double maximum_covariance_trace,
                          double maximum_recent_drift_m,
                          std::size_t stability_window = 8) const {
        if (updates_ < minimum_updates || independent_bouts < minimum_bouts ||
            estimate_history_.size() < stability_window) {
            return false;
        }
        const Estimate current = estimate();
        if (current.covariance_trace > maximum_covariance_trace) return false;
        const Vec2& newest = estimate_history_.back();
        const Vec2& oldest = estimate_history_[estimate_history_.size() - stability_window];
        return norm(newest - oldest) <= maximum_recent_drift_m;
    }

    const std::vector<Particle>& particles() const { return particles_; }
    const Config& config() const { return config_; }

private:
    Config config_;
    std::mt19937_64 rng_;
    std::vector<Particle> particles_;
    std::size_t updates_{0};
    std::vector<Vec2> estimate_history_;

    void validateConfig() const {
        if (config_.particle_count < 50 || !config_.bounds.valid() ||
            config_.release_min <= 0.0 || config_.release_max <= config_.release_min ||
            config_.background_hit_probability <= 0.0 ||
            config_.background_hit_probability >= 1.0 ||
            config_.crosswind_sigma_base_m <= 0.0 ||
            config_.downwind_decay_length_m <= 0.0 ||
            config_.wind_quadrature_points < 1 ||
            config_.minimum_probability <= 0.0 ||
            config_.resample_ess_ratio <= 0.0 || config_.resample_ess_ratio >= 1.0) {
            throw std::invalid_argument("particle-filter configuration is invalid");
        }
    }

    static void validateObservation(const Observation& observation) {
        if (!finite(observation.sensing_position) ||
            !std::isfinite(observation.hit_probability) ||
            !std::isfinite(observation.evidence_confidence) ||
            !std::isfinite(observation.wind_flow_to_rad) ||
            !std::isfinite(observation.wind_speed) ||
            !std::isfinite(observation.dt_s) || observation.dt_s <= 0.0 ||
            observation.hit_probability < 0.0 || observation.hit_probability > 1.0) {
            throw std::invalid_argument("invalid particle-filter observation");
        }
    }

    double predictedHitProbability(const Particle& particle,
                                   const Observation& observation) const {
        const double sigma = observation.wind_sigma_rad > 0.0
                                 ? observation.wind_sigma_rad
                                 : config_.default_wind_sigma_rad;
        const int points = config_.wind_quadrature_points;
        double weighted_probability = 0.0;
        double weight_sum = 0.0;
        for (int index = 0; index < points; ++index) {
            const double centered = points == 1
                                        ? 0.0
                                        : (2.0 * index / static_cast<double>(points - 1) - 1.0);
            const double offset = centered * 2.0 * sigma;
            const double quadrature_weight = std::exp(-0.5 * std::pow(offset / std::max(sigma, 1e-6), 2));
            const double direction = wrapAngle(observation.wind_flow_to_rad +
                                               particle.wind_bias_rad + offset);
            weighted_probability += quadrature_weight *
                                    singleDirectionHitProbability(particle, observation, direction);
            weight_sum += quadrature_weight;
        }
        const double probability = weighted_probability / std::max(weight_sum, 1e-12);
        return clamp(probability,
                     config_.minimum_probability,
                     1.0 - config_.minimum_probability);
    }

    double singleDirectionHitProbability(const Particle& particle,
                                         const Observation& observation,
                                         double flow_to_direction) const {
        const Vec2 displacement = observation.sensing_position - particle.source;
        const Vec2 along_wind = unitFromAngle(flow_to_direction);
        const Vec2 cross_wind = perpendicular(along_wind);
        const double downwind = dot(displacement, along_wind);
        const double crosswind = dot(displacement, cross_wind);
        if (downwind <= 0.0 || observation.wind_speed < config_.minimum_wind_speed_for_model) {
            return config_.background_hit_probability;
        }

        const double width = config_.crosswind_sigma_base_m +
                             config_.crosswind_sigma_growth *
                                 std::sqrt(downwind / std::max(observation.wind_speed, 0.05));
        const double lateral = std::exp(-0.5 * crosswind * crosswind / (width * width));
        const double axial = std::exp(-downwind / config_.downwind_decay_length_m) /
                             std::pow(downwind + config_.downwind_distance_offset_m,
                                      config_.downwind_power);
        const double rate = std::max(0.0, config_.plume_gain * particle.release * lateral * axial);
        const double plume_hit = 1.0 - std::exp(-rate * observation.dt_s);
        return config_.background_hit_probability +
               (1.0 - config_.background_hit_probability) * plume_hit;
    }

    void systematicResample(const FreeSpacePredicate& is_free) {
        std::vector<double> cumulative(particles_.size());
        cumulative[0] = particles_[0].weight;
        for (std::size_t i = 1; i < particles_.size(); ++i) {
            cumulative[i] = cumulative[i - 1] + particles_[i].weight;
        }
        cumulative.back() = 1.0;

        std::uniform_real_distribution<double> start_distribution(
            0.0, 1.0 / static_cast<double>(particles_.size()));
        const double start = start_distribution(rng_);
        std::normal_distribution<double> position_noise(0.0, config_.jitter_position_sigma_m);
        std::normal_distribution<double> release_noise(0.0, config_.jitter_release_fraction);
        std::normal_distribution<double> bias_noise(0.0, config_.jitter_wind_bias_rad);

        std::vector<Particle> resampled;
        resampled.reserve(particles_.size());
        std::size_t source_index = 0;
        for (std::size_t i = 0; i < particles_.size(); ++i) {
            const double target = start + i / static_cast<double>(particles_.size());
            while (source_index + 1 < cumulative.size() && cumulative[source_index] < target) {
                ++source_index;
            }
            Particle candidate = particles_[source_index];
            bool accepted = false;
            for (int attempt = 0; attempt < 30 && !accepted; ++attempt) {
                Particle proposed = candidate;
                proposed.source.x += position_noise(rng_);
                proposed.source.y += position_noise(rng_);
                proposed.release *= std::max(0.1, 1.0 + release_noise(rng_));
                proposed.release = clamp(proposed.release,
                                         config_.release_min,
                                         config_.release_max);
                proposed.wind_bias_rad = clamp(proposed.wind_bias_rad + bias_noise(rng_),
                                                -config_.maximum_wind_bias_rad,
                                                config_.maximum_wind_bias_rad);
                if (config_.bounds.contains(proposed.source) &&
                    (!is_free || is_free(proposed.source))) {
                    candidate = proposed;
                    accepted = true;
                }
            }
            candidate.weight = 1.0 / static_cast<double>(particles_.size());
            resampled.push_back(candidate);
        }
        particles_.swap(resampled);
    }
};

}  // namespace uav_gsl
