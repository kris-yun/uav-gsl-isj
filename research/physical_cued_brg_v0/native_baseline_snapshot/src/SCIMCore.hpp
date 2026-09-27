#pragma once

// SCIM-GSL V1 mathematical core.  This file deliberately has no ROS
// dependency so the dual-posterior and spatial-planner contracts can be
// tested before the ROS adapter is compiled.

#include <gsl_server/algorithms/OPGSLScientificV31/OPGSLScientificV31.hpp>

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace GSL::SCIM {

struct PosteriorDiagnostics {
    double predictive_hit_probability = 0.5;
    double map_entropy = 0.0;
    double confidence_entropy = 0.0;
    double omega = 1.0;
};

struct MemoryCellSnapshot {
    std::int64_t cell_id = 0;
    int visit_episodes = 0;
    double last_visit_time = -std::numeric_limits<double>::infinity();
    double contrast_iact = 1.0;
    double omega = 1.0;
    double accumulated_discrimination = 0.0;
    double acquisition_exposure = 0.0;
    bool correlation_estimable = false;
};

struct ActionScore {
    OPGSLV3::FeasibleAction action;
    std::int64_t target_cell = 0;
    double qbar = 0.0;
    double discrimination = 0.0;
    double j_cell = 0.0;
    double a_cell = 0.0;
    double omega_cell = 1.0;
    double delta_a = 0.0;
    double delta_i = 0.0;
    double path_length = std::numeric_limits<double>::infinity();
    double predicted_navigation_seconds = std::numeric_limits<double>::infinity();
    bool path_valid = false;
    double cycle_time = std::numeric_limits<double>::infinity();
    double utility = -std::numeric_limits<double>::infinity();
    bool selected = false;
};

struct PlannerDecision {
    std::vector<ActionScore> ranked;
    std::optional<ActionScore> selected;
    bool spatial_memory_active = false;
    bool spatial_contrast_active = false;
    bool inactive_warning = false;
    double effective_hits = 0.0;
    std::string mode = "acquisition";
    std::string reason = "no_feasible_action";
};

// Spatial p_d estimator for adaptive per-candidate miss weighting.
struct SpatialPdEstimator {
    static constexpr int MAX_HISTORY = 100;
    std::vector<double> hist_x, hist_y;
    std::vector<int> hist_event;
    double sigma = 3.0;
    void record(double x, double y, int ev) {
        hist_x.push_back(x); hist_y.push_back(y); hist_event.push_back(ev);
        if ((int)hist_x.size() > MAX_HISTORY) {
            hist_x.erase(hist_x.begin()); hist_y.erase(hist_y.begin()); hist_event.erase(hist_event.begin());
        }
    }
    void compute(const double* cx, const double* cy, int nc, double* pd) const {
        const int T = (int)hist_x.size();
        if (T == 0) { for (int k = 0; k < nc; ++k) pd[k] = 0.5; return; }
        const double inv2s2 = 1.0 / (2.0 * sigma * sigma);
        for (int k = 0; k < nc; ++k) {
            double num = 0.0, den = 0.0;
            for (int i = 0; i < T; ++i) {
                double dx = hist_x[i] - cx[k]; double dy = hist_y[i] - cy[k];
                double w = std::exp(-(dx*dx + dy*dy) * inv2s2);
                num += w * hist_event[i]; den += w;
            }
            pd[k] = (den > 1e-10) ? std::min(1.0 - 1e-6, std::max(1e-6, num / den)) : 0.5;
        }
    }
};

class DualPosterior final {
public:
    double miss_weight = 1.0;
    std::vector<double> precomputed_q;
    void clearPrecomputedQ() { precomputed_q.clear(); }
    SpatialPdEstimator pd_estimator;
    bool use_adaptive_pd = false;
    // CAT: Continuous Adaptive Tempering
    double cat_delta = 0.0;   // tempering strength (0=disabled)
    double cat_gamma = 2.0;   // concentration sensitivity
    double cat_alpha_min = 0.3; // minimum alpha
    double cat_current_alpha = 1.0; // current alpha (computed each step)

    void computeCatAlpha() {
        // Compute posterior entropy
        std::vector<double> probs(log_map_.size());
        double max_log = *std::max_element(log_map_.begin(), log_map_.end());
        double sum_exp = 0.0;
        for (std::size_t i = 0; i < log_map_.size(); ++i) {
            probs[i] = std::exp(log_map_[i] - max_log);
            sum_exp += probs[i];
        }
        double entropy = 0.0;
        for (std::size_t i = 0; i < log_map_.size(); ++i) {
            double p = probs[i] / sum_exp;
            if (p > 1e-30) entropy -= p * std::log(p);
        }
        double max_entropy = std::log(static_cast<double>(log_map_.size()));
        double concentration = std::max(0.0, 1.0 - entropy / max_entropy);
        cat_current_alpha = std::max(cat_alpha_min, 1.0 - cat_delta * std::pow(concentration, cat_gamma));
    }

public:
    void initialize(const OPGSLV3::GridSpec& spec,
                    std::vector<bool> valid_mask,
                    OPGSLV3::ObservationModelParameters model,
                    bool enable_ncl = false);

    PosteriorDiagnostics update(const OPGSLV3::ObservationContext& observation,
                                bool detected,
                                double omega);

    double predictiveHitProbability(
        const OPGSLV3::ObservationContext& observation) const;

    OPGSLV3::PosteriorSummary mapSummary(double credible_mass) const;
    OPGSLV3::PosteriorSummary confidenceSummary(double credible_mass) const;
    const std::vector<double>& mapProbabilities() const noexcept { return map_p_; }
    const std::vector<double>& confidenceProbabilities() const noexcept {
        return confidence_p_;
    }
    OPGSLV3::SourcePoint sourceAtValidIndex(std::size_t index) const;
    std::size_t validSourceCount() const noexcept { return sources_.size(); }
    const OPGSLV3::GridSpec& spec() const noexcept { return spec_; }
    bool initialized() const noexcept { return initialized_; }

private:
    OPGSLV3::GridSpec spec_;
    OPGSLV3::ObservationModelParameters model_;
    std::vector<OPGSLV3::SourcePoint> sources_;
    std::vector<double> log_map_;
    std::vector<double> log_conf_;
    std::vector<double> map_p_;
    std::vector<double> confidence_p_;
    double dx_ = 0.0;
    double dy_ = 0.0;
    double dz_ = 0.0;
    bool initialized_ = false;
    bool ncl_enabled_ = false;
    std::vector<double> ncl_log_joint_;
    std::vector<double> ncl_alpha_{-2.0, -1.0, 0.0, 1.0, 2.0};
    std::vector<double> ncl_beta_{0.0, 0.5, 1.0, 2.0};

    static void normalize(std::vector<double>& log_values);
    static std::vector<double> probabilities(const std::vector<double>& log_values);
    OPGSLV3::PosteriorSummary summarize(const std::vector<double>& probabilities,
                                        double credible_mass) const;
    void refreshProbabilities();
    std::size_t nclIndex(std::size_t source, std::size_t alpha, std::size_t beta) const;
    std::vector<double> nclG(const OPGSLV3::ObservationContext& observation) const;
    double nclProbability(std::size_t source, std::size_t alpha, std::size_t beta,
                          const std::vector<double>& g) const;
};

class SpatialInformationPlanner final {
public:
    void initialize(double x_min, double x_max, double y_min, double y_max,
                    double cell_size, std::size_t min_history,
                    std::size_t candidate_cap);

    double omegaAt(double x, double y) const;
    MemoryCellSnapshot snapshotAt(double x, double y) const;
    std::vector<MemoryCellSnapshot> snapshots() const;
    std::size_t uniqueCells() const noexcept { return cells_.size(); }
    double effectiveHits() const noexcept { return effective_hits_; }
    bool spatialMemoryInactive() const noexcept { return spatial_memory_inactive_; }
    void clearInactiveWarning() noexcept { spatial_memory_inactive_ = false; }

    // D(a) is evaluated using the current MAP posterior.  The executed action
    // is then accumulated in its target cell without modifying pi_map.
    double discrimination(const OPGSLV3::ObservationContext& action,
                          const DualPosterior& posterior,
                          const OPGSLV3::ObservationModelParameters& model) const;
    void recordExecuted(const OPGSLV3::ObservationContext& action,
                        bool detected, double discrimination_value,
                        double sim_time);

    PlannerDecision choose(
        const std::vector<OPGSLV3::FeasibleAction>& actions,
        double current_x, double current_y, double current_z,
        const OPGSLV3::ObservationContext& current_context,
        const DualPosterior& posterior,
        const OPGSLV3::ObservationModelParameters& model,
        double horizontal_speed_mps, double vertical_speed_mps,
        double measurement_dwell_seconds) const;

    double actionDifferenceRate(const PlannerDecision& baseline,
                                const PlannerDecision& candidate) const;

private:
    struct Cell {
        MemoryCellSnapshot state;
        std::deque<double> contrast_sequence;
    };

    double x_min_ = -5.0;
    double x_max_ = 5.0;
    double y_min_ = -5.0;
    double y_max_ = 5.0;
    double cell_size_ = 1.0;
    std::size_t min_history_ = 4;
    std::size_t candidate_cap_ = 64;
    double effective_hits_ = 0.0;
    mutable bool spatial_memory_inactive_ = false;
    std::unordered_map<std::int64_t, Cell> cells_;

    std::int64_t key(double x, double y) const;
    Cell& getOrCreate(double x, double y);
    static double integratedAutocorrelation(const std::deque<double>& values);
    static double jsDivergence(double q_i, double q_j);
    static double safeLog1pRatio(double numerator, double denominator);
};

}  // namespace GSL::SCIM
