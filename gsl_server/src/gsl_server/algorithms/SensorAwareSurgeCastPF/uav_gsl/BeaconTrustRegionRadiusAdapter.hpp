#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <string>
#include <tuple>
#include <vector>

namespace uav_gsl {

enum class BeaconTRRegime {
  EarlyBootstrap,
  NominalSupported,
  SparseUnsupported,
  SaturatedUnsupported
};

struct BeaconTREvidenceState {
  int total_samples = 0;
  int sepf_update_count = 0;
  double hit_rate_recent = 0.0;
  int boundary_count_recent = 0;
  bool support_ready = false;
  double anisotropic_visibility_score = 0.0;
  double coverage_score = 0.0;
};

struct BeaconTRCandidate {
  double x = 0.0;
  double y = 0.0;
  double radius_m = 0.0;
  std::string family;
  double p_hit = 0.5;
  double uncertainty = 0.0;
  double visibility_gain = 0.0;
  double coverage_gain = 0.0;
  double path_cost_m = 0.0;
  double invalid_goal_risk = 0.0;
  double timeout_risk = 0.0;
  double revisit_penalty = 0.0;
};

struct BeaconTRWeights {
  double boundary = 2.0;
  double uncertainty = 1.0;
  double visibility = 1.5;
  double coverage = 1.0;
  double branch = 1.0;
  double global_bonus = 0.5;
  double cost = 0.35;
  double invalid = 8.0;
  double timeout = 3.0;
  double oscillation = 2.0;
};

struct BeaconTRSelection {
  BeaconTRCandidate candidate;
  BeaconTRRegime regime = BeaconTRRegime::EarlyBootstrap;
  double score = -std::numeric_limits<double>::infinity();
  std::string radius_ladder_id;
};

class BeaconTrustRegionRadiusAdapter {
 public:
  std::vector<double> local_radii{1.0, 1.5, 2.0};
  std::vector<double> medium_radii{1.5, 2.5, 3.5};
  std::vector<double> global_radii{2.0, 3.5, 5.0};
  int min_samples = 10;
  int min_updates = 5;
  int min_boundary_count = 3;
  double sparse_hit_rate = 0.15;
  double saturated_hit_rate = 0.85;
  BeaconTRWeights weights;
  mutable double cached_hit_rate_ = 0.0;

  BeaconTRRegime classifyRegime(const BeaconTREvidenceState& e) const {
    if (e.total_samples < min_samples || e.sepf_update_count < min_updates) {
      return BeaconTRRegime::EarlyBootstrap;
    }
    if (e.support_ready && e.hit_rate_recent >= sparse_hit_rate && e.hit_rate_recent <= saturated_hit_rate) {
      return BeaconTRRegime::NominalSupported;
    }
    if (e.hit_rate_recent > saturated_hit_rate && e.boundary_count_recent < min_boundary_count) {
      return BeaconTRRegime::SaturatedUnsupported;
    }
    if (e.hit_rate_recent < sparse_hit_rate || e.boundary_count_recent < min_boundary_count) {
      return BeaconTRRegime::SparseUnsupported;
    }
    cached_hit_rate_ = e.hit_rate_recent;
    return BeaconTRRegime::NominalSupported;
  }

  std::pair<std::string, std::vector<double>> radiusLadder(BeaconTRRegime r) const {
    if (r == BeaconTRRegime::NominalSupported) return {"local", local_radii};
    if (r == BeaconTRRegime::SparseUnsupported) return {"global", global_radii};
    if (r == BeaconTRRegime::SaturatedUnsupported) {
      std::vector<double> merged = medium_radii;
      merged.insert(merged.end(), global_radii.begin(), global_radii.end());
      std::sort(merged.begin(), merged.end());
      merged.erase(std::unique(merged.begin(), merged.end()), merged.end());
      return {"medium_global", merged};
    }
    return {"medium", medium_radii};
  }

  static double branchBalance(double p_hit) {
    const double p = std::clamp(p_hit, 0.0, 1.0);
    return 4.0 * p * (1.0 - p);
  }

  static double boundaryGain(double p_hit, double uncertainty, double tau = 0.5) {
    return std::max(0.0, 1.0 - 2.0 * std::abs(p_hit - tau)) + uncertainty;
  }

  double score(const BeaconTRCandidate& c, BeaconTRRegime regime) const {
    const bool global_candidate = c.family.rfind("global", 0) == 0;
    const bool unsupported = regime == BeaconTRRegime::SparseUnsupported || regime == BeaconTRRegime::SaturatedUnsupported;
    const double global_bonus = (global_candidate && unsupported) ? 1.0 : 0.0;
    return weights.boundary * boundaryGain(c.p_hit, c.uncertainty)
        + weights.uncertainty * c.uncertainty
        + weights.visibility * c.visibility_gain
        + weights.coverage * c.coverage_gain
        + weights.branch * branchBalance(c.p_hit)
        + weights.global_bonus * global_bonus
        - weights.cost * c.path_cost_m
        - weights.invalid * c.invalid_goal_risk
        - weights.timeout * c.timeout_risk
        - weights.oscillation * c.revisit_penalty;
  }

  std::optional<BeaconTRSelection> select(
      const BeaconTREvidenceState& evidence,
      const std::vector<BeaconTRCandidate>& candidates) const {
    const auto regime = classifyRegime(evidence);
    auto [ladder_id, radii] = radiusLadder(regime);
    BeaconTRSelection best;
    best.regime = regime;
    best.radius_ladder_id = ladder_id;
    bool found = false;
    for (const auto& c : candidates) {
      bool allowed = false;
      for (double r : radii) {
        if (std::abs(c.radius_m - r) < 1e-6) {
          allowed = true;
          break;
        }
      }
      if (!allowed) continue;
      const double s = score(c, regime);
      if (!found || s > best.score) {
        best.candidate = c;
        best.score = s;
        found = true;
      }
    }
    if (!found) return std::nullopt;
    return best;
  }
};

}  // namespace uav_gsl
