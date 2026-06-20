#pragma once

#include "uav_gsl/Common.hpp"
#include "uav_gsl/SoftEvidenceParticleFilter.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <functional>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace uav_gsl {

// AV-RISE: Anisotropic-Visibility Risk-oriented Sampling.
// This planner is meant to replace IASC in a single-module ablation, not to be
// combined with SDBE/IASC until it proves useful against M3 SEPF-only.
class AnisotropicVisibilityRiskSampler {
public:
    struct Config {
        double step_short_m{0.75};
        double step_long_m{1.8};
        double boundary_p_min{0.15};
        double boundary_p_max{0.85};
        double alpha_risk{1.0};
        double beta_logdet{0.25};
        double gamma_boundary{0.35};
        double delta_visibility{0.35};
        double lambda_path{0.10};
        double lambda_invalid{10.0};
        int visibility_bins{16};
        double memory_decay{0.97};
        double plume_gain{1.8};
        double sigma_m{0.65};
        double decay_m{12.0};
        double background_hit_probability{0.01};
    };

    struct Candidate {
        Vec2 point{};
        std::string label{};
        bool valid{true};
    };

    struct Score {
        Candidate candidate{};
        double total_score{-std::numeric_limits<double>::infinity()};
        double risk_gain{0.0};
        double logdet_gain{0.0};
        double boundary_score{0.0};
        double visibility_novelty{0.0};
        double path_cost{0.0};
        double p_hit{0.0};
        bool valid{false};
    };

    struct Diagnostics {
        std::size_t candidate_count{0};
        std::size_t valid_candidate_count{0};
        std::size_t invalid_candidate_count{0};
        Score selected{};
    };

    using GoalValidityPredicate = std::function<bool(const Vec2&)>;

    AnisotropicVisibilityRiskSampler() : AnisotropicVisibilityRiskSampler(Config{}) {}

    explicit AnisotropicVisibilityRiskSampler(const Config& config)
        : config_(config), visibility_memory_(static_cast<std::size_t>(std::max(4, config.visibility_bins)), 0.0) {
        validateConfig();
    }

    void reset() {
        std::fill(visibility_memory_.begin(), visibility_memory_.end(), 0.0);
        diagnostics_ = Diagnostics{};
    }

    Diagnostics diagnostics() const { return diagnostics_; }

    std::vector<Candidate> makeCandidates(
        const Vec2& robot,
        double wind_flow_to_rad,
        const std::vector<SoftEvidenceParticleFilter::Particle>& particles) const {
        const Vec2 mean = posteriorMean(particles);
        const double upwind = wrapAngle(wind_flow_to_rad + kPi);
        const double to_mean = std::atan2(mean.y - robot.y, mean.x - robot.x);
        std::vector<std::pair<double, std::pair<std::string, double>>> headings = {
            {upwind, {"upwind_short", config_.step_short_m}},
            {upwind, {"upwind_long", config_.step_long_m}},
            {wrapAngle(upwind + kPi / 2.0), {"cross_left", config_.step_short_m}},
            {wrapAngle(upwind - kPi / 2.0), {"cross_right", config_.step_short_m}},
            {to_mean, {"posterior_mean", config_.step_short_m}},
            {wrapAngle(to_mean + kPi / 2.0), {"posterior_boundary_left", config_.step_long_m}},
            {wrapAngle(to_mean - kPi / 2.0), {"posterior_boundary_right", config_.step_long_m}},
        };
        std::vector<Candidate> out;
        out.reserve(headings.size());
        for (const auto& h : headings) {
            out.push_back({robot + Vec2{std::cos(h.first), std::sin(h.first)} * h.second.second,
                           h.second.first,
                           true});
        }
        return out;
    }

    Score select(
        const Vec2& robot,
        double wind_flow_to_rad,
        const std::vector<SoftEvidenceParticleFilter::Particle>& particles,
        const GoalValidityPredicate& is_goal_valid = {}) {
        if (particles.empty()) throw std::invalid_argument("AV-RISE requires particles");
        auto candidates = makeCandidates(robot, wind_flow_to_rad, particles);
        diagnostics_ = Diagnostics{};
        diagnostics_.candidate_count = candidates.size();
        Score best;
        for (auto& candidate : candidates) {
            if (is_goal_valid) candidate.valid = is_goal_valid(candidate.point);
            Score score = scoreCandidate(robot, wind_flow_to_rad, particles, candidate);
            if (candidate.valid) ++diagnostics_.valid_candidate_count;
            else ++diagnostics_.invalid_candidate_count;
            if (score.total_score > best.total_score) best = score;
        }
        diagnostics_.selected = best;
        if (best.valid) updateVisibilityMemory(best.candidate.point - posteriorMean(particles));
        return best;
    }

    Score scoreCandidate(
        const Vec2& robot,
        double wind_flow_to_rad,
        const std::vector<SoftEvidenceParticleFilter::Particle>& particles,
        const Candidate& candidate) const {
        Score s;
        s.candidate = candidate;
        s.valid = candidate.valid;
        s.path_cost = norm(candidate.point - robot);
        if (!candidate.valid) {
            s.total_score = -config_.lambda_invalid - config_.lambda_path * s.path_cost;
            return s;
        }
        const double prior_risk = expectedRisk(particles);
        const double prior_logdet = logdetCovariance(particles);
        s.p_hit = predictiveHitProbability(particles, candidate.point, wind_flow_to_rad);
        const auto hit_post = branchPosterior(particles, candidate.point, wind_flow_to_rad, 1.0);
        const auto miss_post = branchPosterior(particles, candidate.point, wind_flow_to_rad, 0.0);
        const double exp_risk = s.p_hit * expectedRisk(hit_post) + (1.0 - s.p_hit) * expectedRisk(miss_post);
        const double exp_logdet = s.p_hit * logdetCovariance(hit_post) + (1.0 - s.p_hit) * logdetCovariance(miss_post);
        s.risk_gain = prior_risk - exp_risk;
        s.logdet_gain = prior_logdet - exp_logdet;

        const double mid = 0.5 * (config_.boundary_p_min + config_.boundary_p_max);
        const double half = 0.5 * (config_.boundary_p_max - config_.boundary_p_min);
        s.boundary_score = std::max(0.0, 1.0 - std::abs(s.p_hit - mid) / std::max(1e-6, half));
        s.visibility_novelty = visibilityNovelty(candidate.point - posteriorMean(particles));
        s.total_score = config_.alpha_risk * s.risk_gain +
                        config_.beta_logdet * s.logdet_gain +
                        config_.gamma_boundary * s.boundary_score +
                        config_.delta_visibility * s.visibility_novelty -
                        config_.lambda_path * s.path_cost;
        return s;
    }

private:
    Config config_{};
    std::vector<double> visibility_memory_;
    Diagnostics diagnostics_{};

    static double square(double x) { return x * x; }

    static double clamp(double x, double lo, double hi) {
        return std::max(lo, std::min(hi, x));
    }

    Vec2 posteriorMean(const std::vector<SoftEvidenceParticleFilter::Particle>& particles) const {
        Vec2 mean{};
        double sum = 0.0;
        for (const auto& p : particles) {
            const double w = std::max(0.0, p.weight);
            mean = mean + p.source * w;
            sum += w;
        }
        return sum > 0.0 ? mean * (1.0 / sum) : mean;
    }

    double expectedRisk(const std::vector<SoftEvidenceParticleFilter::Particle>& particles) const {
        const Vec2 mean = posteriorMean(particles);
        double sum = 0.0;
        double risk = 0.0;
        for (const auto& p : particles) {
            const double w = std::max(0.0, p.weight);
            risk += w * norm(p.source - mean);
            sum += w;
        }
        return sum > 0.0 ? risk / sum : 0.0;
    }

    double logdetCovariance(const std::vector<SoftEvidenceParticleFilter::Particle>& particles) const {
        const Vec2 mean = posteriorMean(particles);
        double sum = 0.0;
        double xx = 0.0, xy = 0.0, yy = 0.0;
        for (const auto& p : particles) {
            const double w = std::max(0.0, p.weight);
            const Vec2 d = p.source - mean;
            xx += w * d.x * d.x;
            xy += w * d.x * d.y;
            yy += w * d.y * d.y;
            sum += w;
        }
        if (sum > 0.0) { xx /= sum; xy /= sum; yy /= sum; }
        const double det = std::max(1e-12, xx * yy - xy * xy);
        return std::log(det + 1e-12);
    }

    double particleHitProbability(const SoftEvidenceParticleFilter::Particle& particle,
                                  const Vec2& sensing_position,
                                  double wind_flow_to_rad) const {
        const Vec2 delta = sensing_position - particle.source;
        const double flow = wrapAngle(wind_flow_to_rad + particle.wind_bias_rad);
        const double downwind = delta.x * std::cos(flow) + delta.y * std::sin(flow);
        const double crosswind = -delta.x * std::sin(flow) + delta.y * std::cos(flow);
        double p = config_.background_hit_probability;
        if (downwind >= -0.4) {
            const double down = std::max(0.0, downwind + 0.4);
            const double sigma = config_.sigma_m + 0.15 * down;
            p += particle.release * config_.plume_gain * std::exp(-down / config_.decay_m) *
                 std::exp(-0.5 * square(crosswind / std::max(1e-6, sigma)));
        }
        return clamp(p, config_.background_hit_probability, 0.95);
    }

    double predictiveHitProbability(const std::vector<SoftEvidenceParticleFilter::Particle>& particles,
                                    const Vec2& sensing_position,
                                    double wind_flow_to_rad) const {
        double sum = 0.0;
        double p_sum = 0.0;
        for (const auto& p : particles) {
            const double w = std::max(0.0, p.weight);
            p_sum += w * particleHitProbability(p, sensing_position, wind_flow_to_rad);
            sum += w;
        }
        return sum > 0.0 ? clamp(p_sum / sum, config_.background_hit_probability, 0.95) : config_.background_hit_probability;
    }

    std::vector<SoftEvidenceParticleFilter::Particle> branchPosterior(
        const std::vector<SoftEvidenceParticleFilter::Particle>& particles,
        const Vec2& sensing_position,
        double wind_flow_to_rad,
        double z) const {
        std::vector<SoftEvidenceParticleFilter::Particle> out = particles;
        double sum = 0.0;
        for (auto& p : out) {
            const double ph = particleHitProbability(p, sensing_position, wind_flow_to_rad);
            const double likelihood = z * ph + (1.0 - z) * (1.0 - ph);
            p.weight = std::max(0.0, p.weight) * std::max(1e-12, likelihood);
            sum += p.weight;
        }
        if (sum <= 0.0 || !std::isfinite(sum)) {
            const double uniform = 1.0 / static_cast<double>(out.size());
            for (auto& p : out) p.weight = uniform;
        } else {
            for (auto& p : out) p.weight /= sum;
        }
        return out;
    }

    std::size_t directionBin(const Vec2& direction) const {
        const double angle = std::atan2(direction.y, direction.x);
        const double unit = (wrapAngle(angle) + kPi) / (2.0 * kPi);
        return static_cast<std::size_t>(std::floor(unit * visibility_memory_.size())) % visibility_memory_.size();
    }

    double visibilityNovelty(const Vec2& direction) const {
        if (visibility_memory_.empty()) return 1.0;
        return 1.0 / (1.0 + visibility_memory_[directionBin(direction)]);
    }

    void updateVisibilityMemory(const Vec2& direction) {
        if (visibility_memory_.empty()) return;
        for (double& v : visibility_memory_) v *= config_.memory_decay;
        visibility_memory_[directionBin(direction)] += 1.0;
    }

    void validateConfig() const {
        if (config_.step_short_m <= 0.0 || config_.step_long_m < config_.step_short_m ||
            config_.boundary_p_min < 0.0 || config_.boundary_p_max > 1.0 ||
            config_.boundary_p_min >= config_.boundary_p_max ||
            config_.visibility_bins < 4 || config_.memory_decay < 0.0 || config_.memory_decay > 1.0 ||
            config_.sigma_m <= 0.0 || config_.decay_m <= 0.0 ||
            config_.background_hit_probability <= 0.0 || config_.background_hit_probability >= 0.5) {
            throw std::invalid_argument("invalid AV-RISE config");
        }
    }
};

}  // namespace uav_gsl
