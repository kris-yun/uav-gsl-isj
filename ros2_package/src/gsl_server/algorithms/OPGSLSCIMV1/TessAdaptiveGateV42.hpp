#pragma once

#include "TessPlannerV4.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <vector>

namespace tessv42 {

struct AdaptiveGateAudit {
    bool adaptive_ready = false;
    int nuisance_dimension = 1;
    int accepted_blocks = 0;
    int loo_refit_count = 0;
    int loo_valid_count = 0;
    bool loo_same_action = false;
    double loo_worst_gain_margin = std::numeric_limits<double>::infinity();
    int loo_best_action_id = -1;
    double adaptive_block_weight_sum = 0.0;
};

inline double numericalMargin(double candidate_rate, double original_rate) {
    return 64.0 * std::numeric_limits<double>::epsilon() *
           std::max({1.0, std::abs(candidate_rate), std::abs(original_rate)});
}

inline AdaptiveGateAudit evaluateLeaveOneBlockOut(
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
    double duration_slack_seconds) {
    AdaptiveGateAudit audit;
    audit.nuisance_dimension = linear_drift ? 2 : 1;
    audit.accepted_blocks = static_cast<int>(full_history_weight.size());
    for (const double weight : full_history_weight) {
        if (std::isfinite(weight) && weight > 0.0) {
            audit.adaptive_block_weight_sum += weight;
        }
    }
    const std::size_t minimum_blocks =
        static_cast<std::size_t>(audit.nuisance_dimension + 2);
    const std::size_t block_count = full_history_weight.size();
    if (block_count < minimum_blocks ||
        full_history_time_basis.size() != block_count ||
        full_scores.empty() || action_meta.size() != full_scores.size() ||
        candidate_best_action_id <= 0 ||
        static_cast<std::size_t>(candidate_best_action_id) >= full_scores.size()) {
        return audit;
    }

    const auto& full_original = full_scores.front();
    const auto& full_candidate = full_scores[static_cast<std::size_t>(
        candidate_best_action_id)];
    const double original_duration = action_meta.front().duration;
    const bool full_candidate_legal =
        full_candidate.supported &&
        full_candidate.robust_gain_rate > 0.0 &&
        full_candidate.robust_valid_probability >= p_valid_min &&
        action_meta[static_cast<std::size_t>(candidate_best_action_id)].duration <=
            original_duration + duration_slack_seconds;
    const double full_margin =
        full_candidate.robust_gain_rate - full_original.robust_gain_rate;
    if (!full_original.supported || !full_candidate_legal ||
        !(full_margin > numericalMargin(
            full_candidate.robust_gain_rate,
            full_original.robust_gain_rate))) {
        return audit;
    }

    audit.loo_best_action_id = candidate_best_action_id;
    audit.loo_same_action = true;
    audit.loo_refit_count = static_cast<int>(block_count);
    bool every_margin_positive = true;

    for (std::size_t omitted = 0; omitted < block_count; ++omitted) {
        std::vector<double> history_time_basis = full_history_time_basis;
        std::vector<double> history_weight = full_history_weight;
        history_time_basis.erase(history_time_basis.begin() +
                                 static_cast<std::ptrdiff_t>(omitted));
        history_weight.erase(history_weight.begin() +
                             static_cast<std::ptrdiff_t>(omitted));

        std::vector<tessv4::Scenario> scenarios = full_scenarios;
        bool shapes_valid = true;
        for (auto& scenario : scenarios) {
            for (auto& history : scenario.history_by_region) {
                if (history.size() != block_count) {
                    shapes_valid = false;
                    break;
                }
                history.erase(history.begin() +
                              static_cast<std::ptrdiff_t>(omitted));
            }
            if (!shapes_valid) break;
        }
        if (!shapes_valid) {
            audit.loo_same_action = false;
            continue;
        }

        std::vector<tessv4::ActionScore> scores;
        scores.reserve(action_meta.size());
        for (const auto& action : action_meta) {
            scores.push_back(tessv4::evaluateAction(
                scenarios, region_xy, history_time_basis, history_weight,
                action, linear_drift, raw_valid_threshold));
        }
        if (scores.empty() || !scores.front().supported ||
            static_cast<std::size_t>(candidate_best_action_id) >= scores.size() ||
            !scores[static_cast<std::size_t>(candidate_best_action_id)].supported) {
            audit.loo_same_action = false;
            continue;
        }
        ++audit.loo_valid_count;

        int loo_best_id = 0;
        double loo_best_rate = scores.front().robust_gain_rate;
        for (std::size_t action_id = 1; action_id < scores.size(); ++action_id) {
            const bool legal =
                scores[action_id].supported &&
                scores[action_id].robust_gain_rate > 0.0 &&
                scores[action_id].robust_valid_probability >= p_valid_min &&
                action_meta[action_id].duration <=
                    original_duration + duration_slack_seconds;
            if (legal && scores[action_id].robust_gain_rate > loo_best_rate) {
                loo_best_id = static_cast<int>(action_id);
                loo_best_rate = scores[action_id].robust_gain_rate;
            }
        }

        const double candidate_rate =
            scores[static_cast<std::size_t>(candidate_best_action_id)]
                .robust_gain_rate;
        const double original_rate = scores.front().robust_gain_rate;
        const double margin = candidate_rate - original_rate;
        audit.loo_worst_gain_margin =
            std::min(audit.loo_worst_gain_margin, margin);
        if (loo_best_id != candidate_best_action_id) {
            audit.loo_same_action = false;
        }
        if (!(margin > numericalMargin(candidate_rate, original_rate))) {
            every_margin_positive = false;
        }
    }

    audit.adaptive_ready =
        audit.loo_valid_count == audit.loo_refit_count &&
        audit.loo_same_action && every_margin_positive &&
        std::isfinite(audit.loo_worst_gain_margin);
    return audit;
}

}  // namespace tessv42
