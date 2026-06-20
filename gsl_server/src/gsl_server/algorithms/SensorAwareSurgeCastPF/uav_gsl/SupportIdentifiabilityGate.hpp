#pragma once

#include <array>
#include <cmath>
#include <string>
#include <vector>

#include "ShiftAwareSEPFParameterAdapter.hpp"

namespace uav_gsl {

struct SAPAPosteriorSummary {
  double mean_x{0.0};
  double mean_y{0.0};
  double cov_trace{0.0};
  double particle_ess{0.0};
};

struct SupportMetrics {
  double fisher_xx{0.0};
  double fisher_xy{0.0};
  double fisher_yy{0.0};
  double lambda_min{0.0};
  double lambda_max{0.0};
  double condition_number{1e12};
  double support_score{0.0};
  int observations_used{0};
};

struct DeclarationDecision {
  bool allowed{false};
  std::string reason{"not_evaluated"};
  SupportMetrics support;
};

class SupportIdentifiabilityGate {
public:
  void reset() { observations_.clear(); }

  void addObservation(const SAPAObservation& obs) {
    observations_.push_back(obs);
    if (observations_.size() > max_observations_) {
      observations_.erase(observations_.begin(), observations_.begin() + static_cast<long>(observations_.size() - max_observations_));
    }
  }

  SupportMetrics compute(const SAPAPosteriorSummary& posterior,
                         const ShiftAwareSEPFParameterAdapter& adapter) const {
    SupportMetrics m;
    const double eps = 1e-3;
    for (const auto& obs : observations_) {
      std::array<double, 2> grad{};
      for (int d = 0; d < 2; ++d) {
        double sxp = posterior.mean_x;
        double syp = posterior.mean_y;
        double sxm = posterior.mean_x;
        double sym = posterior.mean_y;
        if (d == 0) { sxp += eps; sxm -= eps; }
        if (d == 1) { syp += eps; sym -= eps; }
        const double pp = adapter.mixedHitProbabilityForSource(sxp, syp, obs);
        const double pm = adapter.mixedHitProbabilityForSource(sxm, sym, obs);
        const bool hit = obs.hit_probability >= 0.0 ? obs.hit_probability >= 0.5 : obs.gas_ppm >= obs.hit_threshold;
        const double lp = hit ? std::log(std::max(pp, 1e-9)) : std::log(std::max(1.0 - pp, 1e-9));
        const double lm = hit ? std::log(std::max(pm, 1e-9)) : std::log(std::max(1.0 - pm, 1e-9));
        grad[d] = (lp - lm) / (2.0 * eps);
      }
      const double c = std::max(0.05, std::min(1.0, obs.confidence));
      m.fisher_xx += c * grad[0] * grad[0];
      m.fisher_xy += c * grad[0] * grad[1];
      m.fisher_yy += c * grad[1] * grad[1];
      ++m.observations_used;
    }

    const double tr = m.fisher_xx + m.fisher_yy;
    const double det = m.fisher_xx * m.fisher_yy - m.fisher_xy * m.fisher_xy;
    const double disc = std::sqrt(std::max(0.0, tr * tr - 4.0 * det));
    m.lambda_min = 0.5 * (tr - disc);
    m.lambda_max = 0.5 * (tr + disc);
    m.condition_number = m.lambda_max / std::max(m.lambda_min, 1e-12);
    m.support_score = tr > 0.0 ? m.lambda_min / (tr + 1e-12) : 0.0;
    return m;
  }

  DeclarationDecision evaluate(const SAPAPosteriorSummary& posterior,
                               const ShiftAwareSEPFParameterAdapter& adapter,
                               double shift_score,
                               double expert_ess) const {
    DeclarationDecision d;
    d.support = compute(posterior, adapter);
    if (expert_ess < expert_ess_min_) {
      d.allowed = false; d.reason = "expert_collapse"; return d;
    }
    if (d.support.observations_used < min_observations_) {
      d.allowed = false; d.reason = "too_few_observations"; return d;
    }
    if (d.support.support_score < support_min_) {
      d.allowed = false; d.reason = "support_low"; return d;
    }
    if (d.support.condition_number > condition_max_) {
      d.allowed = false; d.reason = "support_rank_deficient"; return d;
    }
    if (shift_score > shift_high_ && posterior.cov_trace > shifted_cov_max_) {
      d.allowed = false; d.reason = "shift_high_and_uncertain"; return d;
    }
    if (posterior.cov_trace > cov_max_) {
      d.allowed = false; d.reason = "posterior_cov_high"; return d;
    }
    d.allowed = true;
    d.reason = "allowed";
    return d;
  }

  void setThresholds(double support_min, double condition_max, double cov_max, double shifted_cov_max,
                     double shift_high, double expert_ess_min, int min_observations) {
    support_min_ = support_min;
    condition_max_ = condition_max;
    cov_max_ = cov_max;
    shifted_cov_max_ = shifted_cov_max;
    shift_high_ = shift_high;
    expert_ess_min_ = expert_ess_min;
    min_observations_ = min_observations;
  }

private:
  std::vector<SAPAObservation> observations_;
  size_t max_observations_{300};
  double support_min_{0.03};
  double condition_max_{200.0};
  double cov_max_{3.0};
  double shifted_cov_max_{0.4};
  double shift_high_{10.0};
  double expert_ess_min_{1.5};
  int min_observations_{20};
};

}  // namespace uav_gsl
