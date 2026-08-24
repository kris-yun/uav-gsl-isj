#pragma once

#include "TessCoreV4.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace tessv4 {

struct Point2 {
    double x = 0.0;
    double y = 0.0;
};

inline double squaredDistance(const Point2& left, const Point2& right) {
    const double dx = left.x - right.x;
    const double dy = left.y - right.y;
    return dx * dx + dy * dy;
}

struct SourceRegion {
    std::vector<std::size_t> members;
    Point2 centroid;
    double marginal_mass = 0.0;
};

struct RegionPartition {
    std::vector<SourceRegion> regions;
    std::vector<std::size_t> assignment;
    double total_mass = 0.0;
    bool valid = false;
};

inline std::vector<double> normalizeMass(const std::vector<double>& input) {
    std::vector<double> output(input.size(), 0.0);
    double total = 0.0;
    for (std::size_t i = 0; i < input.size(); ++i) {
        output[i] = std::max(0.0, input[i]);
        total += output[i];
    }
    if (!(total > 0.0)) {
        if (output.empty()) return output;
        std::fill(output.begin(), output.end(), 1.0 / static_cast<double>(output.size()));
        return output;
    }
    for (double& value : output) value /= total;
    return output;
}

// Deterministic weighted k-means partition.  Unlike top-k truncation, every
// candidate belongs to exactly one region and all source probability mass is
// preserved.  Seed selection is weighted farthest-first, followed by fixed
// deterministic Lloyd iterations.
inline RegionPartition buildMassPreservingRegions(
    const std::vector<double>& marginal_weights,
    const std::vector<Point2>& source_xy,
    std::size_t maximum_regions,
    int lloyd_iterations = 12) {
    RegionPartition output;
    const std::size_t n = source_xy.size();
    if (n < 2 || marginal_weights.size() != n || maximum_regions < 2) return output;
    const auto weights = normalizeMass(marginal_weights);
    const std::size_t k = std::min(maximum_regions, n);

    std::vector<std::size_t> seeds;
    seeds.reserve(k);
    seeds.push_back(static_cast<std::size_t>(std::distance(
        weights.begin(), std::max_element(weights.begin(), weights.end()))));
    while (seeds.size() < k) {
        std::size_t best = n;
        double best_score = -1.0;
        for (std::size_t i = 0; i < n; ++i) {
            if (std::find(seeds.begin(), seeds.end(), i) != seeds.end()) continue;
            double nearest = std::numeric_limits<double>::infinity();
            for (const auto seed : seeds) nearest = std::min(nearest, squaredDistance(source_xy[i], source_xy[seed]));
            const double score = (weights[i] + 1.0 / static_cast<double>(n)) * nearest;
            if (score > best_score + 1e-15 ||
                (std::abs(score - best_score) <= 1e-15 && i < best)) {
                best = i;
                best_score = score;
            }
        }
        if (best == n) break;
        seeds.push_back(best);
    }
    if (seeds.size() < 2) return output;

    std::vector<Point2> centroids;
    centroids.reserve(seeds.size());
    for (const auto seed : seeds) centroids.push_back(source_xy[seed]);
    std::vector<std::size_t> assignment(n, 0U);

    for (int iteration = 0; iteration < std::max(1, lloyd_iterations); ++iteration) {
        for (std::size_t i = 0; i < n; ++i) {
            std::size_t best_region = 0;
            double best_distance = squaredDistance(source_xy[i], centroids[0]);
            for (std::size_t region = 1; region < centroids.size(); ++region) {
                const double distance = squaredDistance(source_xy[i], centroids[region]);
                if (distance < best_distance - 1e-15) {
                    best_distance = distance;
                    best_region = region;
                }
            }
            assignment[i] = best_region;
        }

        std::vector<double> mass(centroids.size(), 0.0);
        std::vector<double> x(centroids.size(), 0.0), y(centroids.size(), 0.0);
        for (std::size_t i = 0; i < n; ++i) {
            const auto region = assignment[i];
            mass[region] += weights[i];
            x[region] += weights[i] * source_xy[i].x;
            y[region] += weights[i] * source_xy[i].y;
        }
        for (std::size_t region = 0; region < centroids.size(); ++region) {
            if (mass[region] > 0.0) {
                centroids[region].x = x[region] / mass[region];
                centroids[region].y = y[region] / mass[region];
            }
        }
    }

    output.regions.assign(centroids.size(), SourceRegion{});
    output.assignment = assignment;
    for (std::size_t i = 0; i < n; ++i) {
        auto& region = output.regions[assignment[i]];
        region.members.push_back(i);
        region.marginal_mass += weights[i];
        region.centroid.x += weights[i] * source_xy[i].x;
        region.centroid.y += weights[i] * source_xy[i].y;
    }
    output.regions.erase(std::remove_if(output.regions.begin(), output.regions.end(),
        [](const SourceRegion& region) { return region.members.empty() || !(region.marginal_mass > 0.0); }),
        output.regions.end());
    if (output.regions.size() < 2) return RegionPartition{};
    for (auto& region : output.regions) {
        region.centroid.x /= region.marginal_mass;
        region.centroid.y /= region.marginal_mass;
        output.total_mass += region.marginal_mass;
    }
    if (std::abs(output.total_mass - 1.0) > 1e-10) return RegionPartition{};
    output.valid = true;
    return output;
}

struct ActionMeta {
    int id = -1;
    bool hard_valid = false;
    double path_length = std::numeric_limits<double>::infinity();
    double navigation_seconds = std::numeric_limits<double>::infinity();
    double dwell_seconds = 0.0;
    double duration = 0.0;
    int revisit = 0;
    double future_time_basis = 0.0;
    double future_sensor_log_variance = 0.0;
    double shared_model_log_variance = 0.0;
    double future_log_variance = 1.0;
};

struct Scenario {
    // All arrays use the same mass-preserving region ordering.
    std::vector<std::vector<double>> history_by_region;
    std::vector<std::vector<double>> future_raw_by_action;
    std::vector<std::vector<double>> future_log_by_action;
    std::vector<double> region_mass;
    std::vector<ProfileResult> region_profile;
    // Exact source-mass mixture probability, computed before regional
    // compression from every candidate and its source-specific profile.
    std::vector<double> valid_probability_by_action;
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
    double region_mass_sum = 0.0;
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

inline ScenarioActionScore evaluateScenarioAction(
    const Scenario& scenario,
    const std::vector<Point2>& region_xy,
    const std::vector<double>& history_time_basis,
    const std::vector<double>& history_weight,
    const ActionMeta& action,
    bool linear_drift,
    double raw_valid_threshold) {
    ScenarioActionScore output;
    (void)raw_valid_threshold;  // validity was computed exactly from all sources upstream
    const std::size_t region_count = region_xy.size();
    if (!action.hard_valid || region_count < 2 ||
        scenario.history_by_region.size() != region_count ||
        scenario.region_mass.size() != region_count ||
        scenario.region_profile.size() != region_count ||
        action.id < 0 || static_cast<std::size_t>(action.id) >= scenario.future_log_by_action.size() ||
        scenario.future_log_by_action[action.id].size() != region_count ||
        static_cast<std::size_t>(action.id) >= scenario.future_raw_by_action.size() ||
        scenario.future_raw_by_action[action.id].size() != region_count ||
        static_cast<std::size_t>(action.id) >= scenario.support_by_action.size() ||
        scenario.support_by_action[action.id].size() != region_count ||
        static_cast<std::size_t>(action.id) >= scenario.valid_probability_by_action.size() ||
        !(action.duration > 0.0) || !(action.future_log_variance > 0.0)) {
        return output;
    }

    output.region_mass_sum = std::accumulate(scenario.region_mass.begin(), scenario.region_mass.end(), 0.0);
    if (std::abs(output.region_mass_sum - 1.0) > 1e-10) return output;
    for (std::size_t region = 0; region < region_count; ++region) {
        if (!scenario.support_by_action[action.id][region] ||
            scenario.history_by_region[region].size() != history_weight.size() ||
            !scenario.region_profile[region].valid ||
            scenario.region_mass[region] < 0.0) return output;
    }

    for (std::size_t left = 0; left < region_count; ++left) {
        for (std::size_t right = left + 1; right < region_count; ++right) {
            const double pair_weight = scenario.region_mass[left] * scenario.region_mass[right];
            if (!(pair_weight > 0.0)) continue;
            const auto profile = pairProfile(scenario.history_by_region[left],
                                             scenario.history_by_region[right],
                                             history_time_basis, history_weight,
                                             linear_drift);
            if (!profile.valid) return ScenarioActionScore{};
            const double future_difference = scenario.future_log_by_action[action.id][left] -
                                             scenario.future_log_by_action[action.id][right];
            const auto increment = exactIncrement(profile, future_difference,
                                                  action.future_time_basis,
                                                  action.future_log_variance);
            if (!increment.valid) return ScenarioActionScore{};
            PairContribution contribution;
            contribution.left = static_cast<int>(left);
            contribution.right = static_cast<int>(right);
            contribution.source_pair_weight = pair_weight;
            contribution.spatial_distance_squared = squaredDistance(region_xy[left], region_xy[right]);
            contribution.current_separation = profile.objective;
            contribution.separation_increment = increment.delta_separation;
            contribution.error_reduction = pairErrorReduction(profile.objective, increment.delta_separation);
            contribution.innovation = increment.innovation;
            contribution.weighted_gain = pair_weight * contribution.spatial_distance_squared *
                                         contribution.error_reduction;
            output.pair_gain += contribution.weighted_gain;
            output.pairs.push_back(contribution);
        }
    }

    // p_valid is computed from the complete source mixture before regional
    // compression, using source-specific profiled scale/drift.  Regional
    // averaging is therefore not allowed to turn a bimodal valid/invalid
    // mixture into one artificial mean prediction.
    output.valid_probability = std::clamp(
        scenario.valid_probability_by_action[action.id], 0.0, 1.0);
    output.expected_gain = output.valid_probability * output.pair_gain;
    output.gain_rate = output.expected_gain / action.duration;
    output.supported = std::isfinite(output.gain_rate);
    return output;
}

inline ActionScore evaluateAction(const std::vector<Scenario>& scenarios,
                                  const std::vector<Point2>& region_xy,
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
        auto score = evaluateScenarioAction(scenario, region_xy, history_time_basis,
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
        output.robust_valid_probability = std::min(output.robust_valid_probability, score.valid_probability);
        output.robust_expected_gain = std::min(output.robust_expected_gain, score.expected_gain);
        output.robust_gain_rate = std::min(output.robust_gain_rate, score.gain_rate);
        output.scenario.push_back(std::move(score));
    }
    output.supported = true;
    return output;
}

}  // namespace tessv4
