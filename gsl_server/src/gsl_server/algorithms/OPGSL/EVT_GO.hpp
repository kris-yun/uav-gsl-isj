#pragma once
// EVT-GO: Extreme Value Theory Guided Observation
// Source Domain: Financial Risk Management (McNeil et al. 2015) / Climate Extremes (Coles 2001)
// Novel in GSL: No existing work uses EVT for gas concentration peak analysis
//
// Core Idea: Gas concentration peaks near the source follow a Generalized Extreme Value (GEV)
// distribution with different shape parameter xi than peaks far from source.
// By fitting GEV to running top-k peaks, we estimate proximity to source.
//
// Mathematical Foundation:
//   GEV CDF: G(x) = exp{-(1 + xi*(x-mu)/sigma)^{-1/xi}}  for 1+xi*(x-mu)/sigma > 0
//   xi > 0: Fr¨¦chet (heavy tail, close to source - occasional very high peaks)
//   xi = 0: Gumbel (light tail, moderate distance)
//   xi < 0: Weibull (bounded, far from source - peaks are capped)
//
// Key Insight: xi > 0 (heavy tail) indicates proximity to source because
// turbulence creates occasional very high concentration bursts near the source.
// This is analogous to financial returns near market crashes (heavy tails).

#include <deque>
#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>

namespace GSL {
namespace Innovation {

class EVT_GO {
public:
    struct Config {
        int peak_window_size = 30;        // Number of top peaks to track
        double min_samples_for_fit = 15;  // Minimum peaks before EVT fitting
        double xi_prior = 0.0;            // Prior for shape parameter
        double xi_prior_strength = 2.0;   // Prior strength
        double proximity_threshold = 0.1; // xi threshold for "near source"
        double peak_quantile = 0.90;      // Quantile for peak selection
        double decay_rate = 0.99;         // Decay for old peaks
        double exploration_weight = 0.3;  // Weight of EVT signal in exploration
    };

    struct EVTResult {
        double xi = 0.0;           // GEV shape parameter
        double mu = 0.0;           // GEV location
        double sigma = 1.0;        // GEV scale
        double xi_uncertainty = 1.0; // Uncertainty in xi
        double proximity_score = 0.0; // Score [0,1] indicating proximity to source
        double return_level_10 = 0.0; // 10-period return level (expected max in next 10 samples)
        bool is_fitted = false;
        int n_peaks = 0;
    };

    void init(const Config& cfg) {
        cfg_ = cfg;
        peaks_.clear();
        all_readings_.clear();
        result_ = EVTResult();
    }

    // Update with new gas reading
    EVTResult update(double gas_reading, double timestamp) {
        current_time_ = timestamp;
        all_readings_.push_back(gas_reading);

        // Decay old peaks
        for (auto& p : peaks_) p.weight *= cfg_.decay_rate;

        // Select peaks above running quantile
        if (all_readings_.size() >= 10) {
            double q = computeQuantile(cfg_.peak_quantile);
            if (gas_reading > q) {
                peaks_.push_back({gas_reading, timestamp, 1.0});
            }
        }

        // Keep only top-k peaks
        if (peaks_.size() > cfg_.peak_window_size) {
            std::sort(peaks_.begin(), peaks_.end(),
                      [](const Peak& a, const Peak& b) { return a.value > b.value; });
            peaks_.resize(cfg_.peak_window_size);
        }

        // Fit GEV if enough samples
        if (peaks_.size() >= cfg_.min_samples_for_fit) {
            fitGEV();
        }

        return result_;
    }

    // Get exploration weight: higher when xi > 0 (near source)
    double getExplorationWeight() const {
        if (!result_.is_fitted) return cfg_.exploration_weight;
        // Map xi to [0, 1]: xi > 0.2 -> high weight, xi < -0.2 -> low weight
        double w = 0.5 + 0.5 * std::tanh(result_.xi * 5.0);
        return cfg_.exploration_weight * (0.5 + w);
    }

    // Get return level: expected max concentration in next n samples
    double getReturnLevel(int n_periods = 10) const {
        if (!result_.is_fitted) return 0.0;
        return computeReturnLevel(n_periods);
    }

    const EVTResult& result() const { return result_; }

private:
    struct Peak {
        double value;
        double timestamp;
        double weight;
    };

    // Fit GEV using Maximum Likelihood with Bayesian prior on xi
    void fitGEV() {
        std::vector<double> values;
        for (const auto& p : peaks_) {
            for (int i = 0; i < std::max(1, static_cast<int>(p.weight * 5)); ++i) {
                values.push_back(p.value);
            }
        }
        std::sort(values.begin(), values.end());

        int n = values.size();
        if (n < 5) return;

        // Method of L-moments for initial estimates (Hosking 1990)
        double mean = std::accumulate(values.begin(), values.end(), 0.0) / n;

        // Compute L-moments
        double l1 = mean;
        double l2 = 0.0;
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                if (i != j) {
                    l2 += (values[std::max(i,j)] - values[std::min(i,j)]);
                }
            }
        }
        l2 /= (n * (n - 1.0));

        // L-moment estimates for GEV
        double tau3 = 0.0;
        if (l2 > 1e-10) {
            double l3 = 0.0;
            for (int i = 0; i < n; ++i) {
                for (int j = 0; j < n; ++j) {
                    for (int k = 0; k < n; ++k) {
                        if (i != j && j != k && i != k) {
                            double vals[3] = {values[i], values[j], values[k]};
                            std::sort(vals, vals + 3);
                            l3 += vals[2] - 2*vals[1] + vals[0];
                        }
                    }
                }
            }
            l3 /= (n * (n-1.0) * (n-2.0));
            tau3 = l3 / l2;
        }

        // Approximate xi from tau3 (Hosking & Wallis 1997)
        double xi = 0.0;
        if (std::abs(tau3) < 0.3333) {
            xi = (3.0 * tau3 - 1.0) / (1.0 + tau3);  // Simplified
        } else {
            xi = 0.5 * std::copysign(1.0, tau3);
        }

        // Bayesian shrinkage toward prior
        double prior_n = cfg_.xi_prior_strength;
        xi = (n * xi + prior_n * cfg_.xi_prior) / (n + prior_n);

        // Estimate sigma and mu
        double sigma = l2 * xi / (std::tgamma(1.0 - xi) - 1.0 + 1e-10);
        if (sigma < 1e-6) sigma = l2 * 1.5;  // Fallback
        double mu = mean + sigma * (1.0 - std::tgamma(1.0 - xi + 1e-10)) / (xi + 1e-10);

        // Clamp xi to reasonable range
        xi = std::max(-0.5, std::min(0.5, xi));

        result_.xi = xi;
        result_.mu = mu;
        result_.sigma = sigma;
        result_.is_fitted = true;
        result_.n_peaks = n;

        // Compute proximity score: P(xi > 0) using approximate posterior
        double xi_se = 1.0 / std::sqrt(static_cast<double>(n));
        result_.xi_uncertainty = xi_se;
        result_.proximity_score = 0.5 * (1.0 + std::erf(xi / (xi_se * std::sqrt(2.0))));

        // Compute return level
        result_.return_level_10 = computeReturnLevel(10);
    }

    double computeReturnLevel(int n_periods) const {
        if (!result_.is_fitted) return 0.0;
        double p = 1.0 - 1.0 / n_periods;
        double xi = result_.xi;
        double mu = result_.mu;
        double sigma = result_.sigma;

        if (std::abs(xi) < 1e-6) {
            return mu - sigma * std::log(-std::log(p));
        }
        return mu + sigma * (std::pow(-std::log(p), -xi) - 1.0) / xi;
    }

    double computeQuantile(double q) const {
        if (all_readings_.empty()) return 0.0;
        std::vector<double> sorted(all_readings_.end() - std::min((int)all_readings_.size(), 100),
                                    all_readings_.end());
        std::sort(sorted.begin(), sorted.end());
        int idx = static_cast<int>(q * sorted.size());
        idx = std::max(0, std::min(idx, (int)sorted.size() - 1));
        return sorted[idx];
    }

    Config cfg_;
    std::deque<Peak> peaks_;
    std::deque<double> all_readings_;
    EVTResult result_;
    double current_time_ = 0.0;
};

} // namespace Innovation
} // namespace GSL
