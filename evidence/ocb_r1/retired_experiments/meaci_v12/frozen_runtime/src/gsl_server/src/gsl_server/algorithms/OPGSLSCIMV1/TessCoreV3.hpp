#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace tessv3 {

constexpr double kTiny = 1e-15;

struct BlockConfig {
    double min_corrected = 1e-6;
    double saturation = std::numeric_limits<double>::infinity();
    int min_effective_samples = 3;
    double log_variance_floor = 1e-4;
    double max_abs_lag1_correlation = 0.98;
};

struct LogBlock {
    bool accepted = false;
    std::string reason;
    double raw_mean = std::numeric_limits<double>::quiet_NaN();
    double background = std::numeric_limits<double>::quiet_NaN();
    double corrected = std::numeric_limits<double>::quiet_NaN();
    double log_value = std::numeric_limits<double>::quiet_NaN();
    double log_variance = std::numeric_limits<double>::quiet_NaN();
    double weight = std::numeric_limits<double>::quiet_NaN();
    double sample_variance = std::numeric_limits<double>::quiet_NaN();
    double lag1_correlation = std::numeric_limits<double>::quiet_NaN();
    double effective_samples = 0.0;
    int raw_samples = 0;
};

inline double normalCdf(double x) {
    return 0.5 * (1.0 + std::erf(x / std::sqrt(2.0)));
}

inline double logSumExp(const std::vector<double>& values) {
    if (values.empty()) return -std::numeric_limits<double>::infinity();
    const double maximum = *std::max_element(values.begin(), values.end());
    if (!std::isfinite(maximum)) return maximum;
    double sum = 0.0;
    for (const double value : values) sum += std::exp(value - maximum);
    return maximum + std::log(std::max(sum, kTiny));
}

inline std::vector<double> softmaxLog(const std::vector<double>& log_weights) {
    if (log_weights.empty()) return {};
    const double normalizer = logSumExp(log_weights);
    std::vector<double> weights(log_weights.size(), 0.0);
    if (!std::isfinite(normalizer)) {
        const double uniform = 1.0 / static_cast<double>(log_weights.size());
        std::fill(weights.begin(), weights.end(), uniform);
        return weights;
    }
    double sum = 0.0;
    for (std::size_t i = 0; i < log_weights.size(); ++i) {
        weights[i] = std::exp(log_weights[i] - normalizer);
        sum += weights[i];
    }
    if (!(sum > 0.0)) throw std::runtime_error("softmax produced zero mass");
    for (double& value : weights) value /= sum;
    return weights;
}

inline double entropy(const std::vector<double>& probabilities) {
    double value = 0.0;
    for (const double probability : probabilities) {
        if (probability > 0.0) value -= probability * std::log(probability);
    }
    return value;
}

struct ProfileResult {
    double objective = std::numeric_limits<double>::infinity();
    std::array<double, 2> eta{{0.0, 0.0}};
    std::array<double, 4> Ainv{{0.0, 0.0, 0.0, 0.0}};
    int dim = 1;
    bool valid = false;
};

inline void validateWeightedInputs(const std::vector<double>& response,
                                   const std::vector<double>& time_basis,
                                   const std::vector<double>& weights,
                                   bool linear_drift) {
    if (response.empty() || response.size() != weights.size() ||
        (linear_drift && time_basis.size() != response.size())) {
        throw std::invalid_argument("weighted profile shape mismatch");
    }
    for (std::size_t k = 0; k < response.size(); ++k) {
        if (!std::isfinite(response[k]) || !std::isfinite(weights[k]) || !(weights[k] > 0.0) ||
            (linear_drift && !std::isfinite(time_basis[k]))) {
            throw std::invalid_argument("weighted profile contains invalid value");
        }
    }
}

inline ProfileResult weightedProfile(const std::vector<double>& response,
                                     const std::vector<double>& time_basis,
                                     const std::vector<double>& weights,
                                     bool linear_drift) {
    validateWeightedInputs(response, time_basis, weights, linear_drift);
    double a00 = 0.0, a01 = 0.0, a11 = 0.0, b0 = 0.0, b1 = 0.0;
    for (std::size_t k = 0; k < response.size(); ++k) {
        const double t = linear_drift ? time_basis[k] : 0.0;
        a00 += weights[k];
        a01 += weights[k] * t;
        a11 += weights[k] * t * t;
        b0 += weights[k] * response[k];
        b1 += weights[k] * t * response[k];
    }

    ProfileResult output;
    output.dim = linear_drift ? 2 : 1;
    if (!linear_drift) {
        if (!(a00 > kTiny)) return output;
        output.Ainv = {{1.0 / a00, 0.0, 0.0, 0.0}};
        output.eta = {{b0 / a00, 0.0}};
    } else {
        const double determinant = a00 * a11 - a01 * a01;
        const double scale = std::max({std::abs(a00 * a11), std::abs(a01 * a01), 1.0});
        if (!(determinant > 1e-12 * scale)) return output;
        output.Ainv = {{a11 / determinant, -a01 / determinant,
                        -a01 / determinant, a00 / determinant}};
        output.eta = {{(a11 * b0 - a01 * b1) / determinant,
                       (-a01 * b0 + a00 * b1) / determinant}};
    }

    output.objective = 0.0;
    for (std::size_t k = 0; k < response.size(); ++k) {
        const double fitted = output.eta[0] + (linear_drift ? output.eta[1] * time_basis[k] : 0.0);
        const double residual = response[k] - fitted;
        output.objective += weights[k] * residual * residual;
    }
    output.valid = std::isfinite(output.objective);
    return output;
}

inline ProfileResult candidateProfile(const std::vector<double>& observed,
                                      const std::vector<double>& model,
                                      const std::vector<double>& time_basis,
                                      const std::vector<double>& weights,
                                      bool linear_drift) {
    if (observed.size() != model.size()) throw std::invalid_argument("candidate profile shape mismatch");
    std::vector<double> residual(observed.size());
    for (std::size_t k = 0; k < observed.size(); ++k) residual[k] = observed[k] - model[k];
    return weightedProfile(residual, time_basis, weights, linear_drift);
}

inline ProfileResult pairProfile(const std::vector<double>& left,
                                 const std::vector<double>& right,
                                 const std::vector<double>& time_basis,
                                 const std::vector<double>& weights,
                                 bool linear_drift) {
    if (left.size() != right.size()) throw std::invalid_argument("pair profile shape mismatch");
    std::vector<double> difference(left.size());
    for (std::size_t k = 0; k < left.size(); ++k) difference[k] = left[k] - right[k];
    return weightedProfile(difference, time_basis, weights, linear_drift);
}

struct Increment {
    double delta_separation = 0.0;
    double innovation = 0.0;
    double leverage = 0.0;
    bool valid = false;
};

inline Increment exactIncrement(const ProfileResult& pair_profile,
                                double future_difference,
                                double future_time_basis,
                                double future_log_variance) {
    if (!pair_profile.valid || !(future_log_variance > 0.0) ||
        !std::isfinite(future_difference) || !std::isfinite(future_time_basis)) {
        return {};
    }
    const double future_weight = 1.0 / future_log_variance;
    const double b0 = 1.0;
    const double b1 = pair_profile.dim == 2 ? future_time_basis : 0.0;
    const double innovation = future_difference - b0 * pair_profile.eta[0] - b1 * pair_profile.eta[1];
    const double leverage = b0 * (pair_profile.Ainv[0] * b0 + pair_profile.Ainv[1] * b1) +
                            b1 * (pair_profile.Ainv[2] * b0 + pair_profile.Ainv[3] * b1);
    const double denominator = 1.0 + future_weight * leverage;
    if (!(denominator > 0.0) || !std::isfinite(denominator)) return {};
    Increment output;
    output.innovation = innovation;
    output.leverage = leverage;
    output.delta_separation = std::max(0.0, future_weight * innovation * innovation / denominator);
    output.valid = std::isfinite(output.delta_separation);
    return output;
}

inline double pairError(double separation) {
    return normalCdf(-0.5 * std::sqrt(std::max(0.0, separation)));
}

inline double pairErrorReduction(double separation, double increment) {
    const double reduction = pairError(separation) - pairError(separation + std::max(0.0, increment));
    return std::max(0.0, reduction);
}

struct TimeNormalization {
    std::vector<double> history;
    double center = 0.0;
    double scale = 1.0;

    double transform(double time) const { return (time - center) / scale; }
};

inline TimeNormalization normalizeTimes(const std::vector<double>& times,
                                        const std::vector<double>& weights) {
    if (times.empty() || times.size() != weights.size()) throw std::invalid_argument("time shape mismatch");
    double weight_sum = 0.0;
    double weighted_mean = 0.0;
    double minimum = times.front(), maximum = times.front();
    for (std::size_t k = 0; k < times.size(); ++k) {
        if (!(weights[k] > 0.0) || !std::isfinite(times[k])) throw std::invalid_argument("invalid time input");
        weight_sum += weights[k];
        weighted_mean += weights[k] * times[k];
        minimum = std::min(minimum, times[k]);
        maximum = std::max(maximum, times[k]);
    }
    TimeNormalization output;
    output.center = weighted_mean / weight_sum;
    output.scale = std::max(1.0, maximum - minimum);
    output.history.resize(times.size());
    for (std::size_t k = 0; k < times.size(); ++k) output.history[k] = output.transform(times[k]);
    return output;
}

struct ScenarioProfile {
    std::vector<ProfileResult> candidate;
    std::vector<double> source_weight;
    double log_evidence = -std::numeric_limits<double>::infinity();
    bool valid = false;
};

inline ScenarioProfile profileScenario(const std::vector<double>& observed,
                                       const std::vector<std::vector<double>>& model_by_source,
                                       const std::vector<double>& time_basis,
                                       const std::vector<double>& weights,
                                       bool linear_drift,
                                       const std::vector<double>& prior,
                                       double prior_power) {
    if (model_by_source.empty()) return {};
    if (!prior.empty() && prior.size() != model_by_source.size()) {
        throw std::invalid_argument("prior shape mismatch");
    }
    ScenarioProfile output;
    output.candidate.reserve(model_by_source.size());
    std::vector<double> log_weights(model_by_source.size(), -std::numeric_limits<double>::infinity());
    for (std::size_t source = 0; source < model_by_source.size(); ++source) {
        const auto profile = candidateProfile(observed, model_by_source[source], time_basis, weights, linear_drift);
        output.candidate.push_back(profile);
        if (!profile.valid) continue;
        const double prior_value = prior.empty() ? 1.0 / static_cast<double>(model_by_source.size())
                                                 : std::max(prior[source], kTiny);
        log_weights[source] = -0.5 * profile.objective + prior_power * std::log(prior_value);
    }
    output.log_evidence = logSumExp(log_weights);
    output.source_weight = softmaxLog(log_weights);
    output.valid = std::isfinite(output.log_evidence);
    return output;
}

inline std::vector<double> modelAverageSourceWeights(const std::vector<ScenarioProfile>& scenarios) {
    if (scenarios.empty()) return {};
    std::vector<double> scenario_log_evidence;
    scenario_log_evidence.reserve(scenarios.size());
    for (const auto& scenario : scenarios) scenario_log_evidence.push_back(scenario.log_evidence);
    const auto scenario_weight = softmaxLog(scenario_log_evidence);
    std::size_t source_count = 0;
    for (const auto& scenario : scenarios) source_count = std::max(source_count, scenario.source_weight.size());
    std::vector<double> marginal(source_count, 0.0);
    for (std::size_t h = 0; h < scenarios.size(); ++h) {
        for (std::size_t source = 0; source < scenarios[h].source_weight.size(); ++source) {
            marginal[source] += scenario_weight[h] * scenarios[h].source_weight[source];
        }
    }
    const double sum = std::accumulate(marginal.begin(), marginal.end(), 0.0);
    if (sum > 0.0) for (double& value : marginal) value /= sum;
    return marginal;
}

}  // namespace tessv3
