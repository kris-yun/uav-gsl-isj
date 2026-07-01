#pragma once
// CUSUM-BCD: Cumulative Sum Bayesian Change Point Detection
// Inspired by financial time series anomaly detection (Tartakovsky et al. 2014)
// and radar CFAR signal processing
// Purpose: Adaptive gas hit detection replacing fixed threshold

#include <deque>
#include <cmath>
#include <algorithm>

namespace GSL {
namespace Innovation {

class CUSUM_BCD {
public:
    struct Config {
        double baseline_window_s = 30.0;    // Window for baseline estimation
        double cusum_threshold = 4.0;       // CUSUM alarm threshold (in sigma units)
        double decay_rate = 0.95;           // Exponential decay for baseline adaptation
        double min_baseline_samples = 10;   // Minimum samples before detection
        double false_alarm_rate = 0.01;     // Target false alarm rate
    };

    struct Detection {
        bool is_hit = false;           // Whether gas is detected
        double confidence = 0.0;       // Detection confidence [0,1]
        double cusum_statistic = 0.0;  // Current CUSUM statistic
        double baseline_mean = 0.0;    // Current baseline estimate
        double baseline_std = 1.0;     // Current baseline std estimate
        double snr = 0.0;              // Signal-to-noise ratio
    };

    void init(const Config& cfg) { cfg_ = cfg; reset(); }

    void reset() {
        samples_.clear();
        baseline_mean_ = 0.0;
        baseline_var_ = 1.0;
        cusum_pos_ = 0.0;
        cusum_neg_ = 0.0;
        n_samples_ = 0;
        in_plume_ = false;
        plume_start_time_ = 0.0;
        current_time_ = 0.0;
    }

    Detection update(double gas_reading, double timestamp) {
        current_time_ = timestamp;
        samples_.push_back(gas_reading);
        n_samples_++;

        Detection det;

        // Phase 1: Collect baseline
        if (n_samples_ < cfg_.min_baseline_samples) {
            updateBaseline(gas_reading);
            det.baseline_mean = baseline_mean_;
            det.baseline_std = std::sqrt(baseline_var_);
            return det;
        }

        // Phase 2: CUSUM detection
        updateBaseline(gas_reading);

        double mu0 = baseline_mean_;
        double sigma = std::sqrt(baseline_var_);
        if (sigma < 1e-6) sigma = 1e-6;

        // Standardized deviation
        double z = (gas_reading - mu0) / sigma;

        // One-sided CUSUM for positive deviation (gas presence)
        cusum_pos_ = std::max(0.0, cusum_pos_ + z - 0.5);  // slack=0.5
        cusum_neg_ = std::max(0.0, cusum_neg_ - z - 0.5);

        det.cusum_statistic = cusum_pos_;
        det.baseline_mean = mu0;
        det.baseline_std = sigma;
        det.snr = z;

        // Detection decision
        if (cusum_pos_ > cfg_.cusum_threshold) {
            det.is_hit = true;
            det.confidence = std::min(1.0, cusum_pos_ / (2.0 * cfg_.cusum_threshold));

            if (!in_plume_) {
                in_plume_ = true;
                plume_start_time_ = current_time_;
            }

            // Reset CUSUM after detection (allows re-detection)
            cusum_pos_ *= 0.5;
        } else {
            det.is_hit = false;
            det.confidence = 0.0;

            if (in_plume_ && cusum_neg_ > cfg_.cusum_threshold) {
                in_plume_ = false;
                cusum_neg_ *= 0.5;
            }
        }

        return det;
    }

    bool inPlume() const { return in_plume_; }
    double baselineSNR() const { return std::sqrt(baseline_var_) > 1e-6 ? baseline_mean_ / std::sqrt(baseline_var_) : 0; }

private:
    void updateBaseline(double val) {
        // Exponential moving average for baseline adaptation
        double alpha = 1.0 - cfg_.decay_rate;
        baseline_mean_ = cfg_.decay_rate * baseline_mean_ + alpha * val;
        double diff = val - baseline_mean_;
        baseline_var_ = cfg_.decay_rate * baseline_var_ + alpha * diff * diff;

        // Keep baseline var from collapsing
        baseline_var_ = std::max(baseline_var_, 1e-8);
    }

    Config cfg_;
    std::deque<double> samples_;
    double baseline_mean_ = 0.0;
    double baseline_var_ = 1.0;
    double cusum_pos_ = 0.0;
    double cusum_neg_ = 0.0;
    int n_samples_ = 0;
    bool in_plume_ = false;
    double plume_start_time_ = 0.0;
    double current_time_ = 0.0;
};

} // namespace Innovation
} // namespace GSL
