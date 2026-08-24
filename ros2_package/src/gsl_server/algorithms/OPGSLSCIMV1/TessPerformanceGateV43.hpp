#pragma once

#include "TessAdaptiveGateV42.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <vector>

namespace tessv43 {

struct PerformanceGateAudit {
    double advantage_median = -std::numeric_limits<double>::infinity();
    double advantage_mad_or_se = std::numeric_limits<double>::infinity();
    double advantage_lcb = -std::numeric_limits<double>::infinity();
    double relative_advantage = -std::numeric_limits<double>::infinity();
    double switching_cost_equivalent = std::numeric_limits<double>::infinity();
    double scim_information_rate_original =
        -std::numeric_limits<double>::infinity();
    double scim_information_rate_candidate =
        -std::numeric_limits<double>::infinity();
    bool performance_alignment_pass = false;
    bool new_evidence_since_commit = false;
    bool preemption_allowed = false;
    bool takeover_gate_pass = false;
    const char* takeover_block_reason = "V43_NOT_EVALUATED";
};

inline double median(std::vector<double> values) {
    if (values.empty()) return std::numeric_limits<double>::quiet_NaN();
    std::sort(values.begin(), values.end());
    const std::size_t middle = values.size() / 2;
    if (values.size() % 2U == 1U) return values[middle];
    return 0.5 * (values[middle - 1] + values[middle]);
}

inline PerformanceGateAudit evaluatePerformanceSignificance(
    const std::vector<double>& loo_advantages,
    double full_original_rate,
    double full_candidate_rate,
    double source_resolution_mse,
    double candidate_duration,
    double original_goal_x,
    double original_goal_y,
    double candidate_goal_x,
    double candidate_goal_y,
    double posterior_map_x,
    double posterior_map_y,
    double scim_information_rate_original,
    double scim_information_rate_candidate,
    bool new_evidence_since_commit,
    bool commitment_active) {
    PerformanceGateAudit audit;
    audit.new_evidence_since_commit = new_evidence_since_commit;
    audit.preemption_allowed = !commitment_active || new_evidence_since_commit;
    audit.scim_information_rate_original =
        scim_information_rate_original;
    audit.scim_information_rate_candidate =
        scim_information_rate_candidate;
    if (loo_advantages.empty() || !(candidate_duration > 0.0) ||
        !(source_resolution_mse > 0.0) ||
        !std::isfinite(full_original_rate) ||
        !std::isfinite(full_candidate_rate)) {
        audit.takeover_block_reason = "V43_INVALID_SIGNIFICANCE_INPUT";
        return audit;
    }

    audit.advantage_median = median(loo_advantages);
    std::vector<double> deviations;
    deviations.reserve(loo_advantages.size());
    for (const double value : loo_advantages) {
        if (!std::isfinite(value)) {
            audit.takeover_block_reason = "V43_NONFINITE_LOO_ADVANTAGE";
            return audit;
        }
        deviations.push_back(std::abs(value - audit.advantage_median));
    }
    // 1.4826 * MAD is the robust Gaussian-equivalent spread.  The
    // source-grid quantisation MSE supplies an online, experiment-independent
    // minimum meaningful localisation improvement; it is not a tuned margin.
    audit.advantage_mad_or_se = 1.4826 * median(deviations);
    audit.switching_cost_equivalent =
        source_resolution_mse / candidate_duration;
    audit.advantage_lcb = audit.advantage_median -
        audit.advantage_mad_or_se - audit.switching_cost_equivalent;
    const double scale = std::max({
        std::abs(full_original_rate),
        std::abs(full_candidate_rate),
        audit.switching_cost_equivalent,
        tessv42::numericalMargin(full_candidate_rate, full_original_rate)});
    audit.relative_advantage = audit.advantage_lcb / scale;

    const double original_map_distance = std::hypot(
        original_goal_x - posterior_map_x,
        original_goal_y - posterior_map_y);
    const double candidate_map_distance = std::hypot(
        candidate_goal_x - posterior_map_x,
        candidate_goal_y - posterior_map_y);
    const bool map_alignment_pass =
        std::isfinite(original_map_distance) &&
        std::isfinite(candidate_map_distance) &&
        candidate_map_distance <= original_map_distance;
    const bool scim_information_alignment_pass =
        std::isfinite(scim_information_rate_original) &&
        std::isfinite(scim_information_rate_candidate) &&
        scim_information_rate_candidate >
            scim_information_rate_original +
            tessv42::numericalMargin(
                scim_information_rate_candidate,
                scim_information_rate_original);
    audit.performance_alignment_pass =
        map_alignment_pass && scim_information_alignment_pass;

    if (!(audit.advantage_lcb > 0.0)) {
        audit.takeover_block_reason = "V43_ADVANTAGE_LCB_NOT_POSITIVE";
    } else if (!map_alignment_pass) {
        audit.takeover_block_reason = "V43_SCIM_MAP_ALIGNMENT_FAILED";
    } else if (!scim_information_alignment_pass) {
        audit.takeover_block_reason =
            "V43_SCIM_INFORMATION_RATE_NOT_IMPROVED";
    } else if (!audit.preemption_allowed) {
        audit.takeover_block_reason = "V43_NO_NEW_EVIDENCE_SINCE_COMMIT";
    } else {
        audit.takeover_gate_pass = true;
        audit.takeover_block_reason = "V43_TAKEOVER_GATE_PASS";
    }
    return audit;
}

inline double sourceResolutionMse(const std::vector<tessv4::Point2>& sources) {
    if (sources.size() < 2U) return 0.0;
    std::vector<double> nearest_squared;
    nearest_squared.reserve(sources.size());
    for (std::size_t left = 0; left < sources.size(); ++left) {
        double nearest = std::numeric_limits<double>::infinity();
        for (std::size_t right = 0; right < sources.size(); ++right) {
            if (left == right) continue;
            const double distance_squared =
                tessv4::squaredDistance(sources[left], sources[right]);
            if (distance_squared > 0.0) {
                nearest = std::min(nearest, distance_squared);
            }
        }
        if (std::isfinite(nearest)) nearest_squared.push_back(nearest);
    }
    if (nearest_squared.empty()) return 0.0;
    // For a uniform 2-D grid cell, E[dx^2 + dy^2] = h^2 / 6.
    return median(nearest_squared) / 6.0;
}

struct GateResult {
    tessv42::AdaptiveGateAudit evidence;
    PerformanceGateAudit performance;
    std::vector<double> loo_advantages;
};

inline GateResult evaluatePerformanceAlignedGate(
    const std::vector<tessv4::Scenario>& full_scenarios,
    const std::vector<tessv4::Point2>& region_xy,
    const std::vector<double>& full_history_time_basis,
    const std::vector<double>& full_history_weight,
    const std::vector<tessv4::ActionMeta>& action_meta,
    const std::vector<tessv4::ActionScore>& full_scores,
    int candidate_best_action_id,
    bool linear_drift,
    double raw_valid_threshold,
    double p_valid_min,
    double duration_slack_seconds,
    double source_resolution_mse,
    double original_goal_x,
    double original_goal_y,
    double candidate_goal_x,
    double candidate_goal_y,
    double posterior_map_x,
    double posterior_map_y,
    double scim_information_rate_original,
    double scim_information_rate_candidate,
    bool new_evidence_since_commit,
    bool commitment_active) {
    GateResult result;
    result.evidence = tessv42::evaluateLeaveOneBlockOut(
        full_scenarios, region_xy, full_history_time_basis,
        full_history_weight, action_meta, full_scores,
        candidate_best_action_id, linear_drift, raw_valid_threshold,
        p_valid_min, duration_slack_seconds);
    if (!result.evidence.adaptive_ready) {
        result.performance.takeover_block_reason = "V43_AEG_NOT_READY";
        return result;
    }

    const std::size_t block_count = full_history_weight.size();
    const std::size_t candidate =
        static_cast<std::size_t>(candidate_best_action_id);
    result.loo_advantages.reserve(block_count);
    for (std::size_t omitted = 0; omitted < block_count; ++omitted) {
        std::vector<double> time_basis = full_history_time_basis;
        std::vector<double> weight = full_history_weight;
        time_basis.erase(time_basis.begin() +
                         static_cast<std::ptrdiff_t>(omitted));
        weight.erase(weight.begin() + static_cast<std::ptrdiff_t>(omitted));
        std::vector<tessv4::Scenario> scenarios = full_scenarios;
        for (auto& scenario : scenarios) {
            for (auto& history : scenario.history_by_region) {
                history.erase(history.begin() +
                              static_cast<std::ptrdiff_t>(omitted));
            }
        }
        const auto original_score = tessv4::evaluateAction(
            scenarios, region_xy, time_basis, weight, action_meta.front(),
            linear_drift, raw_valid_threshold);
        const auto candidate_score = tessv4::evaluateAction(
            scenarios, region_xy, time_basis, weight, action_meta[candidate],
            linear_drift, raw_valid_threshold);
        if (!original_score.supported || !candidate_score.supported) {
            result.performance.takeover_block_reason =
                "V43_LOO_SCORE_UNSUPPORTED";
            return result;
        }
        result.loo_advantages.push_back(
            candidate_score.robust_gain_rate -
            original_score.robust_gain_rate);
    }
    result.performance = evaluatePerformanceSignificance(
        result.loo_advantages,
        full_scores.front().robust_gain_rate,
        full_scores[candidate].robust_gain_rate,
        source_resolution_mse,
        action_meta[candidate].duration,
        original_goal_x, original_goal_y,
        candidate_goal_x, candidate_goal_y,
        posterior_map_x, posterior_map_y,
        scim_information_rate_original,
        scim_information_rate_candidate,
        new_evidence_since_commit, commitment_active);
    return result;
}

}  // namespace tessv43
