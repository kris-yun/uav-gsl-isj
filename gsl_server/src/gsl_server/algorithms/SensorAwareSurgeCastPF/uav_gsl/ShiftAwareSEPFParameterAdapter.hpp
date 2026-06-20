#pragma once

#include <algorithm>
#include <cmath>
#include <numeric>
#include <string>
#include <vector>

namespace uav_gsl {

struct SAPAPlumeExpert {
  std::string name;
  double plume_sigma_y0{0.45};
  double plume_sigma_y_growth{0.18};
  double downwind_decay_length{3.0};
  double background_hit_probability{0.03};
  double false_hit_probability{0.02};
  double no_hit_temperature{1.0};
  double sensor_gain{1.0};
  double wind_direction_bias_rad{0.0};
};

struct SAPAObservation {
  double pose_x{0.0};
  double pose_y{0.0};
  double wind_u{1.0};
  double wind_v{0.0};
  double gas_ppm{0.0};
  double hit_probability{-1.0};  // if <0, derive from threshold
  double hit_threshold{0.5};
  double confidence{1.0};
};

struct SAPAParticle {
  double x{0.0};
  double y{0.0};
  double weight{1.0};
};

struct SAPAAdapterMetrics {
  double shift_score{0.0};
  double expert_ess{0.0};
  double expert_entropy{0.0};
  double disagreement{0.0};
  int selected_expert_id{0};
  double effective_no_hit_temperature{1.0};
  double effective_plume_width{0.45};
  double effective_background_hit_probability{0.03};
  std::vector<double> alpha;
};

class ShiftAwareSEPFParameterAdapter {
public:
  ShiftAwareSEPFParameterAdapter() { reset(defaultExperts()); }

  explicit ShiftAwareSEPFParameterAdapter(const std::vector<SAPAPlumeExpert>& experts) {
    reset(experts);
  }

  static std::vector<SAPAPlumeExpert> defaultExperts() {
    return {
      {"house01_nominal", 0.45, 0.18, 3.0, 0.03, 0.02, 1.0, 1.0, 0.0},
      {"sparse_broad_lowgain", 1.10, 0.45, 6.0, 0.08, 0.05, 2.5, 0.6, 0.0},
      {"saturated_background", 1.60, 0.75, 8.0, 0.35, 0.25, 4.0, 0.35, 0.0},
      {"narrow_highgain", 0.25, 0.10, 2.0, 0.01, 0.01, 0.8, 1.4, 0.0},
      {"wind_bias_plus", 0.65, 0.25, 4.0, 0.05, 0.03, 1.5, 1.0, 0.35},
      {"wind_bias_minus", 0.65, 0.25, 4.0, 0.05, 0.03, 1.5, 1.0, -0.35}
    };
  }

  void reset(const std::vector<SAPAPlumeExpert>& experts) {
    experts_ = experts;
    const double log_uniform = -std::log(static_cast<double>(std::max<size_t>(1, experts_.size())));
    log_alpha_.assign(experts_.size(), log_uniform);
    hit_hist_.clear();
    gas_hist_.clear();
    wind_hist_.clear();
    metrics_ = SAPAAdapterMetrics{};
    metrics_.alpha = weights();
  }

  void setUpdateParams(double eta, double rho, double alpha_cap) {
    eta_ = eta;
    rho_ = rho;
    alpha_cap_ = alpha_cap;
  }

  double hitProbabilityForSource(double sx, double sy, const SAPAObservation& obs,
                                 const SAPAPlumeExpert& ex) const {
    double norm = std::hypot(obs.wind_u, obs.wind_v);
    double wx = norm > 1e-6 ? obs.wind_u / norm : 1.0;
    double wy = norm > 1e-6 ? obs.wind_v / norm : 0.0;

    const double cb = std::cos(ex.wind_direction_bias_rad);
    const double sb = std::sin(ex.wind_direction_bias_rad);
    const double rwx = cb * wx - sb * wy;
    const double rwy = sb * wx + cb * wy;

    const double dx = obs.pose_x - sx;
    const double dy = obs.pose_y - sy;
    const double downwind = dx * rwx + dy * rwy;
    const double crosswind = -dx * rwy + dy * rwx;

    double plume = 0.0;
    if (downwind > 0.0) {
      const double sigma = std::max(0.05, ex.plume_sigma_y0 + ex.plume_sigma_y_growth * std::sqrt(downwind));
      const double lateral = std::exp(-0.5 * (crosswind / sigma) * (crosswind / sigma));
      const double decay = std::exp(-downwind / std::max(ex.downwind_decay_length, 1e-3));
      plume = ex.sensor_gain * lateral * decay;
    }

    double p = ex.background_hit_probability + (1.0 - ex.background_hit_probability) * (1.0 - std::exp(-plume));
    p = (1.0 - ex.false_hit_probability) * p + ex.false_hit_probability * 0.5;
    return std::clamp(p, 1e-4, 1.0 - 1e-4);
  }

  double mixedHitProbabilityForSource(double sx, double sy, const SAPAObservation& obs) const {
    const auto w = weights();
    double p = 0.0;
    for (size_t k = 0; k < experts_.size(); ++k) {
      p += w[k] * hitProbabilityForSource(sx, sy, obs, experts_[k]);
    }
    return std::clamp(p, 1e-4, 1.0 - 1e-4);
  }

  double logMarginalLikelihood(const std::vector<SAPAParticle>& cloud, const SAPAObservation& obs,
                               const SAPAPlumeExpert& ex) const {
    const double z = observationHit(obs);
    double marginal = 0.0;
    double weight_sum = 0.0;
    for (const auto& particle : cloud) {
      const double p = hitProbabilityForSource(particle.x, particle.y, obs, ex);
      const double like = z >= 0.5 ? p : std::pow(1.0 - p, 1.0 / std::max(ex.no_hit_temperature, 1e-6));
      marginal += particle.weight * like;
      weight_sum += particle.weight;
    }
    if (weight_sum > 1e-12) marginal /= weight_sum;
    return std::log(std::max(marginal, 1e-12));
  }

  SAPAAdapterMetrics observe(const std::vector<SAPAParticle>& cloud, const SAPAObservation& obs) {
    if (experts_.empty()) reset(defaultExperts());
    std::vector<double> lls(experts_.size(), 0.0);
    for (size_t k = 0; k < experts_.size(); ++k) {
      lls[k] = logMarginalLikelihood(cloud, obs, experts_[k]);
    }

    const double z = observationHit(obs);
    const double wind_speed = std::hypot(obs.wind_u, obs.wind_v);
    hit_hist_.push_back(z);
    gas_hist_.push_back(obs.gas_ppm);
    wind_hist_.push_back(wind_speed);
    trimHistory();

    const double hit_rate = mean(hit_hist_);
    const double gas_mean = mean(gas_hist_);
    const double wind_mean = mean(wind_hist_);
    const double shift = std::sqrt(std::pow((hit_rate - 0.05) / 0.05, 2) +
                                   std::pow((gas_mean - 0.18) / 0.12, 2) +
                                   std::pow((wind_mean - 0.48) / 0.30, 2));

    std::vector<double> bonus(experts_.size(), 0.0);
    if (hit_rate < 0.10 && gas_mean < 0.12) {
      for (size_t k = 0; k < experts_.size(); ++k) {
        if (experts_[k].name == "sparse_broad_lowgain" || experts_[k].name == "wind_bias_plus" || experts_[k].name == "wind_bias_minus") bonus[k] += 0.9;
        if (experts_[k].name == "narrow_highgain") bonus[k] -= 0.9;
      }
    }
    if (hit_rate > 0.80 && gas_mean > 0.7) {
      for (size_t k = 0; k < experts_.size(); ++k) {
        if (experts_[k].name == "saturated_background") bonus[k] += 1.2;
        if (experts_[k].name == "narrow_highgain" || experts_[k].name == "house01_nominal") bonus[k] -= 0.6;
      }
    }

    for (size_t k = 0; k < experts_.size(); ++k) {
      log_alpha_[k] = rho_ * log_alpha_[k] + eta_ * (lls[k] + bonus[k]);
    }
    auto alpha = weights();
    for (size_t k = 0; k < alpha.size(); ++k) log_alpha_[k] = std::log(std::max(alpha[k], 1e-12));

    metrics_.alpha = alpha;
    metrics_.selected_expert_id = static_cast<int>(std::distance(alpha.begin(), std::max_element(alpha.begin(), alpha.end())));
    metrics_.expert_ess = expertESS(alpha);
    metrics_.expert_entropy = entropy(alpha);
    metrics_.shift_score = shift;
    metrics_.disagreement = variance(lls);
    metrics_.effective_no_hit_temperature = weightedParam(alpha, [](const SAPAPlumeExpert& e){ return e.no_hit_temperature; });
    metrics_.effective_plume_width = weightedParam(alpha, [](const SAPAPlumeExpert& e){ return e.plume_sigma_y0; });
    metrics_.effective_background_hit_probability = weightedParam(alpha, [](const SAPAPlumeExpert& e){ return e.background_hit_probability; });
    return metrics_;
  }

  std::vector<double> weights() const {
    if (log_alpha_.empty()) return {};
    const double max_log = *std::max_element(log_alpha_.begin(), log_alpha_.end());
    std::vector<double> w(log_alpha_.size(), 0.0);
    double sum = 0.0;
    for (size_t k = 0; k < log_alpha_.size(); ++k) {
      w[k] = std::exp(log_alpha_[k] - max_log);
      sum += w[k];
    }
    for (double& v : w) v /= std::max(sum, 1e-12);

    auto it = std::max_element(w.begin(), w.end());
    if (it != w.end() && *it > alpha_cap_) {
      const size_t imax = static_cast<size_t>(std::distance(w.begin(), it));
      const double excess = *it - alpha_cap_;
      w[imax] = alpha_cap_;
      double rest = 0.0;
      for (size_t k = 0; k < w.size(); ++k) if (k != imax) rest += w[k];
      for (size_t k = 0; k < w.size(); ++k) if (k != imax) w[k] += excess * w[k] / std::max(rest, 1e-12);
      const double s = std::accumulate(w.begin(), w.end(), 0.0);
      for (double& v : w) v /= std::max(s, 1e-12);
    }
    return w;
  }

  const SAPAAdapterMetrics& metrics() const { return metrics_; }
  const std::vector<SAPAPlumeExpert>& experts() const { return experts_; }

private:
  double observationHit(const SAPAObservation& obs) const {
    if (obs.hit_probability >= 0.0) return obs.hit_probability >= 0.5 ? 1.0 : 0.0;
    return obs.gas_ppm >= obs.hit_threshold ? 1.0 : 0.0;
  }

  static double mean(const std::vector<double>& x) {
    if (x.empty()) return 0.0;
    return std::accumulate(x.begin(), x.end(), 0.0) / static_cast<double>(x.size());
  }

  static double variance(const std::vector<double>& x) {
    if (x.empty()) return 0.0;
    const double m = mean(x);
    double v = 0.0;
    for (double a : x) v += (a - m) * (a - m);
    return v / static_cast<double>(x.size());
  }

  static double expertESS(const std::vector<double>& w) {
    double s = 0.0;
    for (double v : w) s += v * v;
    return 1.0 / std::max(s, 1e-12);
  }

  static double entropy(const std::vector<double>& w) {
    double h = 0.0;
    for (double v : w) if (v > 1e-12) h -= v * std::log(v);
    return h;
  }

  template <typename Fn>
  double weightedParam(const std::vector<double>& w, Fn fn) const {
    double y = 0.0;
    for (size_t k = 0; k < experts_.size(); ++k) y += w[k] * fn(experts_[k]);
    return y;
  }

  void trimHistory() {
    const size_t max_hist = 50;
    auto trim = [max_hist](std::vector<double>& v) {
      if (v.size() > max_hist) v.erase(v.begin(), v.begin() + static_cast<long>(v.size() - max_hist));
    };
    trim(hit_hist_);
    trim(gas_hist_);
    trim(wind_hist_);
  }

  std::vector<SAPAPlumeExpert> experts_;
  std::vector<double> log_alpha_;
  std::vector<double> hit_hist_;
  std::vector<double> gas_hist_;
  std::vector<double> wind_hist_;
  SAPAAdapterMetrics metrics_;
  double eta_{0.6};
  double rho_{0.98};
  double alpha_cap_{0.82};
};

}  // namespace uav_gsl
