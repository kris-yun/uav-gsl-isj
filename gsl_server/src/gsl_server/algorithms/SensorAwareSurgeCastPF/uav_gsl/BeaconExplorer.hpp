#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace uav_gsl {

struct BeaconObservation {
  double x{0.0};
  double y{0.0};
  double gas_ppm{0.0};
  bool hit{false};
  double wind_dir_flow_to_rad{0.0};
  double t{0.0};
};

struct BeaconCandidate {
  double x{0.0};
  double y{0.0};
  double path_cost_m{0.0};
  double invalid_goal_risk{0.0};
  double timeout_risk{0.0};
};

struct BeaconScore {
  BeaconCandidate candidate;
  double score{-std::numeric_limits<double>::infinity()};
  double p_hit{0.5};
  double uncertainty{0.0};
  double boundary_score{0.0};
  double visibility_gain{0.0};
  double coverage_gain{0.0};
  std::string selected_reason{"none"};
};

struct BeaconConfig {
  double lengthscale_m{1.5};
  double alpha0{1.0};
  double beta0{1.0};
  double boundary_tau{0.5};
  double estraddle_beta{1.5};
  double estraddle_power{2.0};
  int min_hits_for_support{3};
  int min_nohits_for_support{8};
  double min_boundary_support{0.25};
  int min_visibility_bins{3};
  int visibility_bin_count{8};
  double w_boundary{2.0};
  double w_uncertainty{1.0};
  double w_visibility{1.0};
  double w_coverage{0.8};
  double w_cost{0.15};
  double w_risk{1.0};
};

class BeaconExplorer {
 public:
  explicit BeaconExplorer(BeaconConfig cfg = {}) : cfg_(cfg) {}

  void addObservation(const BeaconObservation& obs) { observations_.push_back(obs); }

  std::pair<double, double> predictHitAndUncertainty(double x, double y) const {
    double alpha = cfg_.alpha0;
    double beta = cfg_.beta0;
    for (const auto& obs : observations_) {
      const double w = kernel(x, y, obs.x, obs.y);
      alpha += w * (obs.hit ? 1.0 : 0.0);
      beta += w * (obs.hit ? 0.0 : 1.0);
    }
    const double denom = std::max(alpha + beta, 1e-12);
    const double p = alpha / denom;
    const double var = (alpha * beta) / std::max(denom * denom * (denom + 1.0), 1e-12);
    return {p, std::sqrt(std::max(0.0, var))};
  }

  double boundarySupport() const {
    if (observations_.empty()) return 0.0;
    int supported = 0;
    for (const auto& obs : observations_) {
      bool opposite = false;
      for (const auto& other : observations_) {
        if (other.hit == obs.hit) continue;
        const double d = std::hypot(obs.x - other.x, obs.y - other.y);
        if (d <= 2.5 * cfg_.lengthscale_m) {
          opposite = true;
          break;
        }
      }
      if (opposite) ++supported;
    }
    return static_cast<double>(supported) / static_cast<double>(observations_.size());
  }

  int angularVisibilityBins() const {
    if (observations_.size() < 2) return 0;
    double cx = 0.0, cy = 0.0;
    for (const auto& o : observations_) { cx += o.x; cy += o.y; }
    cx /= static_cast<double>(observations_.size());
    cy /= static_cast<double>(observations_.size());
    std::vector<bool> bins(static_cast<size_t>(cfg_.visibility_bin_count), false);
    constexpr double kPi = 3.14159265358979323846;
    for (const auto& o : observations_) {
      const double a = std::atan2(o.y - cy, o.x - cx);
      int b = static_cast<int>(((a + kPi) / (2.0 * kPi)) * cfg_.visibility_bin_count);
      b = std::max(0, std::min(cfg_.visibility_bin_count - 1, b));
      bins[static_cast<size_t>(b)] = true;
    }
    return static_cast<int>(std::count(bins.begin(), bins.end(), true));
  }

  bool supportReady() const {
    int hits = 0;
    for (const auto& o : observations_) if (o.hit) ++hits;
    const int nohits = static_cast<int>(observations_.size()) - hits;
    return hits >= cfg_.min_hits_for_support &&
           nohits >= cfg_.min_nohits_for_support &&
           boundarySupport() >= cfg_.min_boundary_support &&
           angularVisibilityBins() >= cfg_.min_visibility_bins;
  }

  BeaconScore scoreCandidate(const BeaconCandidate& c) const {
    const auto [p, u] = predictHitAndUncertainty(c.x, c.y);
    const double d = std::abs(p - cfg_.boundary_tau);
    const double boundary = -std::pow(d, cfg_.estraddle_power) + cfg_.estraddle_beta * u;
    const double vis = visibilityGain(c);
    const double cov = coverageGain(c);
    const double risk = c.invalid_goal_risk + c.timeout_risk;
    const double score = cfg_.w_boundary * boundary + cfg_.w_uncertainty * u +
                         cfg_.w_visibility * vis + cfg_.w_coverage * cov -
                         cfg_.w_cost * c.path_cost_m - cfg_.w_risk * risk;
    BeaconScore s;
    s.candidate = c;
    s.score = score;
    s.p_hit = p;
    s.uncertainty = u;
    s.boundary_score = boundary;
    s.visibility_gain = vis;
    s.coverage_gain = cov;
    s.selected_reason = (boundary >= std::max(vis, cov)) ? "boundary" : ((vis >= cov) ? "visibility" : "coverage");
    return s;
  }

  std::optional<BeaconScore> select(const std::vector<BeaconCandidate>& candidates) const {
    if (candidates.empty()) return std::nullopt;
    BeaconScore best;
    for (const auto& c : candidates) {
      auto s = scoreCandidate(c);
      if (s.score > best.score) best = s;
    }
    return best;
  }

 private:
  double kernel(double x, double y, double ox, double oy) const {
    const double d2 = (x - ox) * (x - ox) + (y - oy) * (y - oy);
    const double l2 = std::max(cfg_.lengthscale_m * cfg_.lengthscale_m, 1e-12);
    return std::exp(-0.5 * d2 / l2);
  }

  double evidenceMass(double x, double y) const {
    double m = 0.0;
    for (const auto& obs : observations_) m += kernel(x, y, obs.x, obs.y);
    return m;
  }

  double coverageGain(const BeaconCandidate& c) const { return 1.0 / (1.0 + evidenceMass(c.x, c.y)); }

  double visibilityGain(const BeaconCandidate& c) const {
    if (observations_.empty()) return 1.0;
    double nearest = std::numeric_limits<double>::infinity();
    for (const auto& o : observations_) nearest = std::min(nearest, std::hypot(c.x - o.x, c.y - o.y));
    return std::min(1.0, nearest / std::max(3.0 * cfg_.lengthscale_m, 1e-9));
  }

  BeaconConfig cfg_;
  std::vector<BeaconObservation> observations_;
};

}  // namespace uav_gsl
