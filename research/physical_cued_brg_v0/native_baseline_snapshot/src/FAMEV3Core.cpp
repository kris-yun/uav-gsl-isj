#include "FAMEV3Core.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <limits>
#include <stdexcept>

namespace GSL::FAMEV3 {
namespace { constexpr double kEps = 1e-15; }

double NonSpatialNullExpert::predictive() const noexcept { return alpha_ / (alpha_ + beta_); }
void NonSpatialNullExpert::observe(bool event) noexcept { if (event) ++alpha_; else ++beta_; }

double FrozenSpatialExpert::predictive(const Candidate& c, double x, double y, double z) const noexcept {
    const double dx = x - c.x, dy = y - c.y, dz = z - c.z;
    const double d = std::sqrt(dx * dx + dy * dy + dz * dz);
    return 1.0 / (1.0 + std::exp(-std::clamp(kIntercept - kDistanceSlope * d, -60.0, 60.0)));
}

double JointSourceModelPosterior::clamp(double value) noexcept {
    return std::clamp(value, kEps, 1.0 - kEps);
}

double JointSourceModelPosterior::bernoulliLogLikelihood(bool event, double q) noexcept {
    q = clamp(q);
    return event ? std::log(q) : std::log1p(-q);
}

double JointSourceModelPosterior::bernoulliJensenShannon(double q_left, double q_right) noexcept {
    q_left = clamp(q_left); q_right = clamp(q_right);
    const double mid = clamp(0.5 * (q_left + q_right));
    const auto kl = [](double p, double q) {
        return p * std::log(p / q) + (1.0 - p) * std::log((1.0 - p) / (1.0 - q));
    };
    return 0.5 * (kl(q_left, mid) + kl(q_right, mid));
}

void JointSourceModelPosterior::initialize(std::vector<Candidate> candidates) {
    if (candidates.empty()) throw std::invalid_argument("FAME V3 requires candidates");
    candidates_ = std::move(candidates);
    const double source_prior = 1.0 / static_cast<double>(candidates_.size());
    state_.xi_m0.assign(candidates_.size(), 0.5 * source_prior);
    state_.xi_m1.assign(candidates_.size(), 0.5 * source_prior);
    state_.omega_m0 = state_.omega_m1 = 0.5;
    initialized_ = true;
}

double JointSourceModelPosterior::predictive(const PredictiveField& field) const noexcept {
    if (field.q_m1.size() != state_.xi_m1.size()) return std::numeric_limits<double>::quiet_NaN();
    double p = 0.0;
    for (std::size_t i = 0; i < state_.xi_m1.size(); ++i) {
        p += state_.xi_m0[i] * field.q_m0 + state_.xi_m1[i] * field.q_m1[i];
    }
    return clamp(p);
}

UpdateResult JointSourceModelPosterior::update(NonSpatialNullExpert& null_expert,
                                               const FrozenSpatialExpert& spatial_expert,
                                               double x, double y, double z, bool event) {
    if (!initialized_) throw std::logic_error("FAME V3 posterior not initialized");
    UpdateResult out;
    out.pre = state_;
    out.predictive.q_m0 = null_expert.predictive();
    out.predictive.q_m1.reserve(candidates_.size());
    for (const Candidate& c : candidates_) out.predictive.q_m1.push_back(spatial_expert.predictive(c, x, y, z));
    out.p_event = predictive(out.predictive);
    for (std::size_t i = 0; i < candidates_.size(); ++i) {
        const double l0 = std::exp(bernoulliLogLikelihood(event, out.predictive.q_m0));
        const double l1 = std::exp(bernoulliLogLikelihood(event, out.predictive.q_m1[i]));
        state_.xi_m0[i] *= l0;
        state_.xi_m1[i] *= l1;
    }
    null_expert.observe(event);
    double normalizer = std::accumulate(state_.xi_m0.begin(), state_.xi_m0.end(), 0.0) +
                        std::accumulate(state_.xi_m1.begin(), state_.xi_m1.end(), 0.0);
    if (!(normalizer > 0.0) || !std::isfinite(normalizer)) throw std::runtime_error("invalid joint normalizer");
    for (double& v : state_.xi_m0) v /= normalizer;
    for (double& v : state_.xi_m1) v /= normalizer;
    state_.omega_m0 = std::accumulate(state_.xi_m0.begin(), state_.xi_m0.end(), 0.0);
    state_.omega_m1 = std::accumulate(state_.xi_m1.begin(), state_.xi_m1.end(), 0.0);
    out.post = state_;
    return out;
}

double JointSourceModelPosterior::sourceRisk(const std::vector<double>& mass,
                                             const std::vector<Candidate>& candidates) {
    double mx = 0.0, my = 0.0, mz = 0.0;
    for (std::size_t i = 0; i < mass.size(); ++i) { mx += mass[i] * candidates[i].x; my += mass[i] * candidates[i].y; mz += mass[i] * candidates[i].z; }
    double r = 0.0;
    for (std::size_t i = 0; i < mass.size(); ++i) { const double dx = candidates[i].x - mx, dy = candidates[i].y - my, dz = candidates[i].z - mz; r += mass[i] * (dx * dx + dy * dy + dz * dz); }
    return r;
}

RiskResult JointSourceModelPosterior::exactRiskReduction(const PredictiveField& field) const {
    if (!initialized_ || field.q_m1.size() != candidates_.size()) throw std::invalid_argument("FAME V3 risk dimensions");
    const double p1 = predictive(field), p0 = 1.0 - p1;
    std::vector<double> source(state_.xi_m0.size());
    for (std::size_t i = 0; i < source.size(); ++i) source[i] = state_.xi_m0[i] + state_.xi_m1[i];
    RiskResult out; out.prior = sourceRisk(source, candidates_);
    double expected = 0.0;
    for (bool event : {false, true}) {
        const double py = event ? p1 : p0;
        std::vector<double> post(source.size());
        for (std::size_t i = 0; i < post.size(); ++i) {
            const double q0 = event ? field.q_m0 : 1.0 - field.q_m0;
            const double q1 = event ? field.q_m1[i] : 1.0 - field.q_m1[i];
            post[i] = (state_.xi_m0[i] * q0 + state_.xi_m1[i] * q1) / clamp(py);
        }
        expected += py * sourceRisk(post, candidates_);
    }
    out.expected_after = expected;
    out.delta = out.prior - expected;
    // The binary closed form uses the same complete joint posterior and is an invariant.
    std::vector<double> mu0(3, 0.0), mu1(3, 0.0);
    for (std::size_t i = 0; i < candidates_.size(); ++i) {
        const double q0 = field.q_m0, q1 = field.q_m1[i];
        const double w0 = state_.xi_m0[i] * (1.0 - q0) + state_.xi_m1[i] * (1.0 - q1);
        const double w1 = state_.xi_m0[i] * q0 + state_.xi_m1[i] * q1;
        mu0[0] += w0 * candidates_[i].x; mu0[1] += w0 * candidates_[i].y; mu0[2] += w0 * candidates_[i].z;
        mu1[0] += w1 * candidates_[i].x; mu1[1] += w1 * candidates_[i].y; mu1[2] += w1 * candidates_[i].z;
    }
    for (double& v : mu0) v /= clamp(p0);
    for (double& v : mu1) v /= clamp(p1);
    const double dx = mu1[0] - mu0[0], dy = mu1[1] - mu0[1], dz = mu1[2] - mu0[2];
    out.binary_delta = p0 * p1 * (dx * dx + dy * dy + dz * dz);
    return out;
}
}  // namespace GSL::FAMEV3
