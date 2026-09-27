#pragma once

#include "TessCoreV3.hpp"

#include <algorithm>
#include <cmath>
#include <vector>

namespace tessv3 {

struct Sample {
    double value = 0.0;
};

inline double lagOneCorrelation(const std::vector<Sample>& samples, double mean,
                                double variance) {
    if (samples.size() < 3 || !(variance > 0.0)) return 0.0;
    double covariance = 0.0;
    for (std::size_t i = 1; i < samples.size(); ++i) {
        covariance += (samples[i - 1].value - mean) * (samples[i].value - mean);
    }
    covariance /= static_cast<double>(samples.size() - 1);
    return std::clamp(covariance / variance, -0.98, 0.98);
}

inline double effectiveSampleCount(std::size_t raw_count, double lag1,
                                   double max_abs_lag1 = 0.98) {
    if (raw_count == 0) return 0.0;
    const double rho = std::clamp(lag1, -max_abs_lag1, max_abs_lag1);
    const double estimate = static_cast<double>(raw_count) * (1.0 - rho) / (1.0 + rho);
    return std::clamp(estimate, 1.0, static_cast<double>(raw_count));
}

inline LogBlock finalizeBlock(const std::vector<Sample>& samples, double background,
                              bool settle_valid, const BlockConfig& config) {
    LogBlock output;
    output.background = background;
    output.raw_samples = static_cast<int>(samples.size());
    if (samples.empty()) {
        output.reason = "NO_SAMPLES";
        return output;
    }
    if (!settle_valid) {
        output.reason = "INVALID_SETTLE";
        return output;
    }
    for (const auto& sample : samples) {
        if (!std::isfinite(sample.value)) {
            output.reason = "NONFINITE";
            return output;
        }
    }

    double mean = 0.0;
    for (const auto& sample : samples) mean += sample.value;
    mean /= static_cast<double>(samples.size());
    double variance = 0.0;
    for (const auto& sample : samples) {
        const double residual = sample.value - mean;
        variance += residual * residual;
    }
    variance = samples.size() > 1 ? variance / static_cast<double>(samples.size() - 1) : 0.0;
    const double lag1 = lagOneCorrelation(samples, mean, variance);
    const double n_eff = effectiveSampleCount(samples.size(), lag1, config.max_abs_lag1_correlation);

    output.raw_mean = mean;
    output.sample_variance = variance;
    output.lag1_correlation = lag1;
    output.effective_samples = n_eff;
    output.corrected = mean - background;

    if (static_cast<int>(std::floor(n_eff + 1e-12)) < config.min_effective_samples) {
        output.reason = "INSUFFICIENT_EFFECTIVE_SAMPLES";
        return output;
    }
    if (mean >= config.saturation) {
        output.reason = "SATURATED";
        return output;
    }
    if (!(output.corrected >= config.min_corrected)) {
        output.reason = "LOW_SIGNAL";
        return output;
    }
    if (variance < 0.0 || !std::isfinite(variance)) {
        output.reason = "INVALID_VARIANCE";
        return output;
    }

    const double mean_variance = variance / std::max(n_eff, 1.0);
    output.log_variance = std::max(mean_variance / (output.corrected * output.corrected),
                                   config.log_variance_floor);
    output.log_value = std::log(output.corrected);
    output.weight = 1.0 / output.log_variance;
    output.accepted = std::isfinite(output.log_value) && std::isfinite(output.weight) && output.weight > 0.0;
    output.reason = output.accepted ? "ACCEPTED" : "NONFINITE_LOG_BLOCK";
    return output;
}

}  // namespace tessv3
