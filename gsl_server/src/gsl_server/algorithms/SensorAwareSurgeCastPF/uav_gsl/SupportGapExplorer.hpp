#pragma once
#include <array>
#include <cmath>
#include <limits>
#include <string>
#include <vector>
#include <algorithm>

namespace uav_gsl {

struct Pose2D {
  double x{0.0};
  double y{0.0};
};

struct SageObservation {
  Pose2D pose;
  double gas_ppm{0.0};
  double wind_dir_flow_to_rad{0.0};
  double confidence{1.0};
};

struct SageCandidate {
  Pose2D waypoint;
  std::string kind;
  double radius_m{0.0};
  double score{-std::numeric_limits<double>::infinity()};
  double predicted_hit_probability{0.5};
};

struct SageDiagnostics {
  double rank_score{0.0};
  double visibility_score{0.0};
  double boundary_support{0.0};
  double support_gap{1.0};
  double hit_rate{0.0};
  bool sparse_regime{false};
  bool saturated_regime{false};
};

struct SageParams {
  double tau_gap{0.62};
  double plume_sigma_y0{0.65};
  double plume_sigma_y_growth{0.18};
  double downwind_decay_m{8.0};
  double hit_threshold_ppm{0.5};
  double logistic_temp{0.20};
  int angular_bins{8};
  std::vector<double> candidate_radii_m{1.5, 3.0, 5.0, 7.0};
  double w_rank{1.5};
  double w_boundary{1.0};
  double w_visibility{0.8};
  double w_cost{0.08};
  double min_score{0.05};
};

class SupportGapExplorer {
 public:
  explicit SupportGapExplorer(SageParams params = SageParams()) : params_(std::move(params)) {}

  double expectedConcentration(const Pose2D& source, const Pose2D& sensor, double wind_dir) const {
    const double dx = sensor.x - source.x;
    const double dy = sensor.y - source.y;
    const double c = std::cos(wind_dir);
    const double s = std::sin(wind_dir);
    const double xw = c * dx + s * dy;
    const double yw = -s * dx + c * dy;
    if (xw < -0.25) return 0.02;
    const double sigma = params_.plume_sigma_y0 + params_.plume_sigma_y_growth * std::max(0.0, xw);
    const double lateral = std::exp(-0.5 * (yw / std::max(1e-3, sigma)) * (yw / std::max(1e-3, sigma)));
    const double decay = std::exp(-std::max(0.0, xw) / params_.downwind_decay_m);
    return 2.0 * lateral * decay + 0.02;
  }

  double hitProbability(const Pose2D& source, const Pose2D& sensor, double wind_dir) const {
    const double mu = expectedConcentration(source, sensor, wind_dir);
    double z = (mu - params_.hit_threshold_ppm) / std::max(1e-3, params_.logistic_temp);
    z = std::max(-40.0, std::min(40.0, z));
    return 1.0 / (1.0 + std::exp(-z));
  }

  SageDiagnostics diagnose(const Pose2D& source, const std::vector<SageObservation>& obs) const {
    SageDiagnostics d;
    if (obs.empty()) return d;
    int hits = 0;
    std::vector<int> seen(params_.angular_bins, 0), hit_bins(params_.angular_bins, 0), nohit_bins(params_.angular_bins, 0);
    for (const auto& o : obs) {
      const double a = std::atan2(o.pose.y - source.y, o.pose.x - source.x);
      int b = static_cast<int>(((a + M_PI) / (2.0 * M_PI)) * params_.angular_bins) % params_.angular_bins;
      if (b < 0) b += params_.angular_bins;
      seen[b] = 1;
      if (o.gas_ppm >= params_.hit_threshold_ppm) { hit_bins[b] = 1; ++hits; }
      else { nohit_bins[b] = 1; }
    }
    int n_seen = 0, n_boundary = 0;
    for (int i = 0; i < params_.angular_bins; ++i) {
      n_seen += seen[i];
      n_boundary += (hit_bins[i] && nohit_bins[i]) ? 1 : 0;
    }
    d.hit_rate = static_cast<double>(hits) / std::max<size_t>(1, obs.size());
    d.sparse_regime = d.hit_rate < 0.08;
    d.saturated_regime = d.hit_rate > 0.85;
    d.visibility_score = static_cast<double>(n_seen) / std::max(1, params_.angular_bins);
    d.boundary_support = static_cast<double>(n_boundary) / std::max(1, params_.angular_bins);

    // Lightweight rank proxy: angular spread of likelihood-sensitive observations.
    double c2 = 0.0, s2 = 0.0, weight_sum = 0.0;
    for (const auto& o : obs) {
      const double p = hitProbability(source, o.pose, o.wind_dir_flow_to_rad);
      const double sens = std::max(0.0, 4.0 * p * (1.0 - p)) * std::max(0.0, o.confidence);
      const double a = std::atan2(o.pose.y - source.y, o.pose.x - source.x);
      c2 += sens * std::cos(2.0 * a);
      s2 += sens * std::sin(2.0 * a);
      weight_sum += sens;
    }
    if (weight_sum > 1e-9) {
      const double anis = std::sqrt(c2*c2 + s2*s2) / weight_sum;
      d.rank_score = std::max(0.0, std::min(1.0, 1.0 - anis));
    } else {
      d.rank_score = 0.0;
    }
    const double relaxed_boundary = (!d.sparse_regime && !d.saturated_regime) ? std::max(d.boundary_support, 0.2) : d.boundary_support;
    const double core = std::min(d.rank_score, std::min(d.visibility_score, relaxed_boundary));
    d.support_gap = 1.0 - core;
    return d;
  }

  std::vector<SageCandidate> generateCandidates(const Pose2D& source, const Pose2D& current, double wind_dir) const {
    std::vector<SageCandidate> out;
    const double wx = std::cos(wind_dir), wy = std::sin(wind_dir);
    const double cx = -wy, cy = wx;
    auto add = [&](double x, double y, const std::string& kind, double r) {
      if (std::hypot(x - current.x, y - current.y) > 0.5) out.push_back({{x,y}, kind, r});
    };
    for (double r : params_.candidate_radii_m) {
      add(source.x + cx*r, source.y + cy*r, "crosswind_left_boundary", r);
      add(source.x - cx*r, source.y - cy*r, "crosswind_right_boundary", r);
      add(source.x + wx*r, source.y + wy*r, "downwind_validation", r);
      add(source.x - wx*r, source.y - wy*r, "upwind_validation", r);
    }
    const double r = params_.candidate_radii_m.empty() ? 5.0 : params_.candidate_radii_m.back();
    for (int k = 0; k < params_.angular_bins; ++k) {
      const double a = 2.0 * M_PI * static_cast<double>(k) / static_cast<double>(params_.angular_bins);
      add(source.x + std::cos(a)*r, source.y + std::sin(a)*r, "angular_visibility_probe", r);
    }
    return out;
  }

  SageCandidate scoreCandidate(SageCandidate cand, const Pose2D& source, const Pose2D& current,
                               const std::vector<SageObservation>& obs, double wind_dir) const {
    const double p_hit = hitProbability(source, cand.waypoint, wind_dir);
    const double branch_balance = 4.0 * p_hit * (1.0 - p_hit);
    int seen_bin = 0;
    const double ca = std::atan2(cand.waypoint.y - source.y, cand.waypoint.x - source.x);
    int cb = static_cast<int>(((ca + M_PI) / (2.0 * M_PI)) * params_.angular_bins) % params_.angular_bins;
    if (cb < 0) cb += params_.angular_bins;
    for (const auto& o : obs) {
      int b = static_cast<int>(((std::atan2(o.pose.y-source.y,o.pose.x-source.x)+M_PI)/(2.0*M_PI))*params_.angular_bins) % params_.angular_bins;
      if (b < 0) b += params_.angular_bins;
      if (b == cb) { seen_bin = 1; break; }
    }
    const double novelty = seen_bin ? 0.25 : 1.0;
    const double cost = std::hypot(cand.waypoint.x - current.x, cand.waypoint.y - current.y);
    cand.predicted_hit_probability = p_hit;
    cand.score = params_.w_boundary * branch_balance + params_.w_visibility * novelty - params_.w_cost * cost;
    return cand;
  }

  bool select(const Pose2D& source, const Pose2D& current, const std::vector<SageObservation>& obs,
              double wind_dir, SageCandidate* selected, SageDiagnostics* diag,
              std::vector<SageCandidate>* candidates = nullptr) const {
    SageDiagnostics d = diagnose(source, obs);
    if (diag) *diag = d;
    if (d.support_gap <= params_.tau_gap) return false;
    auto cands = generateCandidates(source, current, wind_dir);
    for (auto& c : cands) c = scoreCandidate(c, source, current, obs, wind_dir);
    std::sort(cands.begin(), cands.end(), [](const auto& a, const auto& b){ return a.score > b.score; });
    if (candidates) *candidates = cands;
    if (cands.empty() || cands.front().score < params_.min_score) return false;
    if (selected) *selected = cands.front();
    return true;
  }

  const SageParams& getParams() const { return params_; }
 private:
  SageParams params_;
};

}  // namespace uav_gsl
