#pragma once
#include <deque>
#include <cmath>
#include <numeric>
#include <algorithm>

namespace uav_gsl {

// Posterior Contraction Rate Declaration (PCR-D)
// Theory: Ghosal & van der Vaart (2017) - posterior contracts at rate O(1/sqrt(N))
// When observed contraction rate is statistically indistinguishable from zero,
// more data will not improve the estimate -> declare convergence.
class PosteriorContractionDeclaration {
public:
    struct Config {
        std::size_t particle_count{1500};   // N: number of particles
        double window_seconds{8.0};         // sliding window duration
        double min_declare_seconds{10.0};   // minimum time before declaring
        double significance_level{0.05};    // alpha for t-test
        int min_snapshots{4};               // minimum snapshots in window
        double min_cov_trace{0.1};          // minimum cov trace to avoid degenerate
    };

    struct Snapshot {
        double time_s;
        double cov_trace;   // trace of posterior covariance
        double entropy;     // approximate posterior entropy
    };

    explicit PosteriorContractionDeclaration(const Config& cfg) : config_(cfg) {
        // Theoretical minimum contraction rate: sigma / sqrt(N)
        // For unit-variance Gaussian, the posterior variance variance ~ 2*sigma^4 / N
        // We use 1/sqrt(N) as the scale for the minimum detectable change
        noise_std_ = 1.0 / std::sqrt(static_cast<double>(config_.particle_count));
    }

    void addSnapshot(double time_s, double cov_trace, double entropy) {
        snapshots_.push_back({time_s, cov_trace, entropy});
        // Remove old snapshots outside window
        while (!snapshots_.empty() &&
               time_s - snapshots_.front().time_s > config_.window_seconds) {
            snapshots_.pop_front();
        }
    }

    // Returns true if posterior has converged (should declare)
    bool shouldDeclare(double elapsed_s) const {
        if (elapsed_s < config_.min_declare_seconds) return false;
        if (static_cast<int>(snapshots_.size()) < config_.min_snapshots) return false;

        // Compute contraction rate via linear regression on log(cov_trace)
        // H(t) = a + b*t, we test H0: b >= 0 (no contraction) vs H1: b < 0
        double n = static_cast<double>(snapshots_.size());
        double sum_t = 0, sum_y = 0, sum_tt = 0, sum_ty = 0;
        double t0 = snapshots_.front().time_s;

        for (const auto& s : snapshots_) {
            double t = s.time_s - t0;
            double y = std::log(std::max(s.cov_trace, config_.min_cov_trace));
            sum_t += t;
            sum_y += y;
            sum_tt += t * t;
            sum_ty += t * y;
        }

        double denom = n * sum_tt - sum_t * sum_t;
        if (std::abs(denom) < 1e-12) return false;

        double slope = (n * sum_ty - sum_t * sum_y) / denom;

        // Compute residual standard error
        double intercept = (sum_y - slope * sum_t) / n;
        double ss_res = 0;
        for (const auto& s : snapshots_) {
            double t = s.time_s - t0;
            double y = std::log(std::max(s.cov_trace, config_.min_cov_trace));
            double residual = y - (intercept + slope * t);
            ss_res += residual * residual;
        }
        double se_slope = std::sqrt(ss_res / (n - 2.0)) / std::sqrt(sum_tt - sum_t * sum_t / n);

        if (se_slope < 1e-12) return false;

        // One-sided t-test: H0: slope >= 0, H1: slope < 0
        // t-statistic = slope / se_slope
        double t_stat = slope / se_slope;

        // For small samples, use t-distribution critical value
        // For df >= 3 and alpha=0.05, one-sided critical value ~ -2.35 (df=3), -1.65 (large)
        double df = n - 2.0;
        double t_critical = (df < 10) ? -2.0 - 0.5 * (10.0 - df) / 10.0 : -1.645;

        // Also check: is the observed contraction rate smaller than the theoretical minimum?
        // If yes, the posterior has effectively converged
        bool rate_below_noise = (std::abs(slope) < noise_std_);

        // Declare if: slope is NOT significantly negative (posterior stopped contracting)
        // AND the posterior has been stable for the entire window
        bool not_contracting = (t_stat > t_critical);  // cannot reject H0: no contraction
        bool stable_cov = coefficientOfVariation() < 0.15;  // CV < 15% means stable

        return (not_contracting || rate_below_noise) && stable_cov;
    }

    double currentContractionRate() const {
        if (snapshots_.size() < 3) return 0.0;
        double n = static_cast<double>(snapshots_.size());
        double sum_t = 0, sum_y = 0, sum_tt = 0, sum_ty = 0;
        double t0 = snapshots_.front().time_s;
        for (const auto& s : snapshots_) {
            double t = s.time_s - t0;
            double y = std::log(std::max(s.cov_trace, config_.min_cov_trace));
            sum_t += t; sum_y += y; sum_tt += t * t; sum_ty += t * y;
        }
        double denom = n * sum_tt - sum_t * sum_t;
        if (std::abs(denom) < 1e-12) return 0.0;
        return (n * sum_ty - sum_t * sum_y) / denom;
    }

    double currentEntropy() const {
        if (snapshots_.empty()) return 0.0;
        return snapshots_.back().entropy;
    }

private:
    Config config_;
    std::deque<Snapshot> snapshots_;
    double noise_std_{0.026};  // 1/sqrt(1500)

    double coefficientOfVariation() const {
        if (snapshots_.size() < 2) return 1.0;
        std::vector<double> values;
        for (const auto& s : snapshots_) values.push_back(s.cov_trace);
        double mean = std::accumulate(values.begin(), values.end(), 0.0) / values.size();
        if (mean < 1e-12) return 1.0;
        double sq_sum = 0;
        for (double v : values) sq_sum += (v - mean) * (v - mean);
        return std::sqrt(sq_sum / values.size()) / mean;
    }
};

}  // namespace uav_gsl
