#pragma once

#include "TessCoreV3.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <vector>

namespace tessv3 {

struct Point2 {
    double x = 0.0;
    double y = 0.0;
};

inline double squaredDistance(const Point2& left, const Point2& right) {
    const double dx = left.x - right.x;
    const double dy = left.y - right.y;
    return dx * dx + dy * dy;
}

struct ActionMeta {
    int id = -1;
    bool hard_valid = false;
    double duration = 0.0;
    int revisit = 0;
    double future_time_basis = 0.0;
    double future_log_variance = 1.0;
};

struct Scenario {
    // All arrays use the same selected-source ordering.
    std::vector<std::vector<double>> history_by_source;
    // Raw physical sensor output for validity; log values remain fingerprint-only.
    std::vector<std::vector<double>> future_raw_by_action;
    std::vector<std::vector<double>> future_by_action;
    std::vector<double> source_weight;
    std::vector<ProfileResult> source_profile;
    std::vector<std::vector<bool>> support_by_action;
};

struct PairContribution {
    int left = -1;
    int right = -1;
    double source_pair_weight = 0.0;
    double spatial_distance_squared = 0.0;
    double current_separation = 0.0;
    double separation_increment = 0.0;
    double error_reduction = 0.0;
    double weighted_gain = 0.0;
    double innovation = 0.0;
};

struct ScenarioActionScore {
    double pair_gain = 0.0;
    double valid_probability = 0.0;
    double expected_gain = 0.0;
    double gain_rate = 0.0;
    bool supported = false;
    std::vector<PairContribution> pairs;
};

struct ActionScore {
    int id = -1;
    bool supported = false;
    double robust_pair_gain = -std::numeric_limits<double>::infinity();
    double robust_valid_probability = 0.0;
    double robust_expected_gain = -std::numeric_limits<double>::infinity();
    double robust_gain_rate = -std::numeric_limits<double>::infinity();
    std::vector<ScenarioActionScore> scenario;
};

inline double normalizedWeightSum(const std::vector<double>& weights) {
    double sum = 0.0;
    for (const double value : weights) sum += std::max(0.0, value);
    return sum;
}

inline ScenarioActionScore evaluateScenarioAction(const Scenario& scenario,
                                                  const std::vector<Point2>& source_xy,
                                                  const std::vector<double>& history_time_basis,
                                                  const std::vector<double>& history_weight,
                                                  const ActionMeta& action,
                                                  bool linear_drift,
                                                  double raw_valid_threshold) {
    ScenarioActionScore output;
    const std::size_t source_count = source_xy.size();
    if (!action.hard_valid || source_count < 2 ||
        scenario.history_by_source.size() != source_count ||
        scenario.source_weight.size() != source_count ||
        scenario.source_profile.size() != source_count ||
        action.id < 0 || static_cast<std::size_t>(action.id) >= scenario.future_by_action.size() ||
        scenario.future_by_action[action.id].size() != source_count ||
        static_cast<std::size_t>(action.id) >= scenario.future_raw_by_action.size() ||
        scenario.future_raw_by_action[action.id].size() != source_count ||
        static_cast<std::size_t>(action.id) >= scenario.support_by_action.size() ||
        scenario.support_by_action[action.id].size() != source_count ||
        !(action.duration > 0.0) || !(action.future_log_variance > 0.0)) {
        return output;
    }

    for (std::size_t source = 0; source < source_count; ++source) {
        if (!scenario.support_by_action[action.id][source] ||
            scenario.history_by_source[source].size() != history_weight.size() ||
            !scenario.source_profile[source].valid) {
            return output;
        }
    }

    const double weight_sum = normalizedWeightSum(scenario.source_weight);
    if (!(weight_sum > 0.0)) return output;
    std::vector<double> normalized(source_count, 0.0);
    for (std::size_t source = 0; source < source_count; ++source) {
        normalized[source] = std::max(0.0, scenario.source_weight[source]) / weight_sum;
    }

    double pair_mass = 0.0;
    for (std::size_t left = 0; left < source_count; ++left) {
        for (std::size_t right = left + 1; right < source_count; ++right) {
            pair_mass += normalized[left] * normalized[right];
        }
    }
    if (!(pair_mass > 0.0)) return output;

    // Keep the theoretical posterior pair mass pi_i*pi_j.  Do not divide by
    // the sum over retained pairs: that would rescale physical scenarios by a
    // scenario-dependent truncation constant and break the robust objective.
    for (std::size_t left = 0; left < source_count; ++left) {
        for (std::size_t right = left + 1; right < source_count; ++right) {
            const double pair_weight = normalized[left] * normalized[right];
            if (!(pair_weight > 0.0)) continue;
            const auto profile = pairProfile(scenario.history_by_source[left],
                                             scenario.history_by_source[right],
                                             history_time_basis, history_weight,
                                             linear_drift);
            if (!profile.valid) return ScenarioActionScore{};
            const double future_difference = scenario.future_by_action[action.id][left] -
                                             scenario.future_by_action[action.id][right];
            const auto increment = exactIncrement(profile, future_difference,
                                                  action.future_time_basis,
                                                  action.future_log_variance);
            if (!increment.valid) return ScenarioActionScore{};
            const double reduction = pairErrorReduction(profile.objective,
                                                        increment.delta_separation);
            PairContribution contribution;
            contribution.left = static_cast<int>(left);
            contribution.right = static_cast<int>(right);
            contribution.source_pair_weight = pair_weight;
            contribution.spatial_distance_squared = squaredDistance(source_xy[left], source_xy[right]);
            contribution.current_separation = profile.objective;
            contribution.separation_increment = increment.delta_separation;
            contribution.error_reduction = reduction;
            contribution.innovation = increment.innovation;
            contribution.weighted_gain = pair_weight * contribution.spatial_distance_squared * reduction;
            output.pair_gain += contribution.weighted_gain;
            output.pairs.push_back(contribution);
        }
    }

    output.valid_probability = 0.0;
    for (std::size_t source = 0; source < source_count; ++source) {
        // Validity is defined in raw concentration units.  Do not feed the
        // log-floor value used by the fingerprint into this decision.
        const double raw = scenario.future_raw_by_action[action.id][source];
        output.valid_probability += normalized[source] *
            ((std::isfinite(raw) && raw >= raw_valid_threshold) ? 1.0 : 0.0);
    }
    output.valid_probability = std::clamp(output.valid_probability, 0.0, 1.0);
    output.expected_gain = output.valid_probability * output.pair_gain;
    output.gain_rate = output.expected_gain / action.duration;
    output.supported = std::isfinite(output.gain_rate);
    return output;
}

inline ActionScore evaluateAction(const std::vector<Scenario>& scenarios,
                                  const std::vector<Point2>& source_xy,
                                  const std::vector<double>& history_time_basis,
                                  const std::vector<double>& history_weight,
                                  const ActionMeta& action,
                                  bool linear_drift,
                                  double raw_valid_threshold) {
    ActionScore output;
    output.id = action.id;
    if (scenarios.empty()) return output;
    output.robust_pair_gain = std::numeric_limits<double>::infinity();
    output.robust_valid_probability = std::numeric_limits<double>::infinity();
    output.robust_expected_gain = std::numeric_limits<double>::infinity();
    output.robust_gain_rate = std::numeric_limits<double>::infinity();
    for (const auto& scenario : scenarios) {
        auto score = evaluateScenarioAction(scenario, source_xy, history_time_basis,
                                            history_weight, action, linear_drift,
                                            raw_valid_threshold);
        if (!score.supported) {
            output.scenario.push_back(std::move(score));
            output.supported = false;
            output.robust_pair_gain = -std::numeric_limits<double>::infinity();
            output.robust_valid_probability = 0.0;
            output.robust_expected_gain = -std::numeric_limits<double>::infinity();
            output.robust_gain_rate = -std::numeric_limits<double>::infinity();
            return output;
        }
        output.robust_pair_gain = std::min(output.robust_pair_gain, score.pair_gain);
        output.robust_valid_probability = std::min(output.robust_valid_probability,
                                                   score.valid_probability);
        output.robust_expected_gain = std::min(output.robust_expected_gain,
                                               score.expected_gain);
        output.robust_gain_rate = std::min(output.robust_gain_rate, score.gain_rate);
        output.scenario.push_back(std::move(score));
    }
    output.supported = true;
    return output;
}

inline std::vector<std::size_t> selectSpatiallyDiverseCandidates(
    const std::vector<std::vector<double>>& scenario_weights,
    const std::vector<double>& marginal_weights,
    const std::vector<Point2>& source_xy,
    std::size_t maximum_candidates,
    double nms_radius) {
    if (source_xy.empty() || maximum_candidates == 0 || marginal_weights.size() != source_xy.size()) return {};
    std::vector<double> importance(source_xy.size(), 0.0);
    for (std::size_t i = 0; i < source_xy.size(); ++i) importance[i] = marginal_weights[i];
    for (const auto& weights : scenario_weights) {
        if (weights.size() != source_xy.size()) throw std::invalid_argument("scenario weight shape mismatch");
        for (std::size_t i = 0; i < weights.size(); ++i) importance[i] = std::max(importance[i], weights[i]);
    }

    std::vector<std::size_t> order(source_xy.size());
    std::iota(order.begin(), order.end(), 0U);
    std::stable_sort(order.begin(), order.end(), [&](std::size_t left, std::size_t right) {
        if (std::abs(importance[left] - importance[right]) > 1e-15) return importance[left] > importance[right];
        return marginal_weights[left] > marginal_weights[right];
    });

    std::vector<std::size_t> selected;
    const double nms_squared = nms_radius * nms_radius;
    for (const auto index : order) {
        bool separated = true;
        for (const auto previous : selected) {
            if (squaredDistance(source_xy[index], source_xy[previous]) < nms_squared) {
                separated = false;
                break;
            }
        }
        if (separated) selected.push_back(index);
        if (selected.size() >= maximum_candidates) break;
    }
    return selected;
}

}  // namespace tessv3
