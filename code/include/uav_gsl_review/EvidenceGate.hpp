#pragma once

#include "uav_gsl_review/GridTypes.hpp"
#include "uav_gsl_review/MapMath.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace uav_gsl_review {

struct EvidenceGateConfig {
    int min_iterations{5};
    int min_hit_count{5};
    double min_hit_mass{0.0};
    double min_hit_bbox_diag_m{0.75};
    double min_wind_coherence{0.25};
    double max_posterior_entropy_norm{0.98};
    double min_posterior_peak_ratio{0.005};

    // If true, the gate can reject PMFS convergence when gas evidence is absent.
    bool reject_no_hit_convergence{true};
};

struct EvidenceSummary {
    int iterations{0};
    int hit_count{0};
    double hit_mass{0.0};
    double hit_bbox_diag_m{0.0};
    double hit_rms_radius_m{0.0};
    double wind_coherence{0.0};
    double mean_wind_speed{0.0};
    double mean_wind_direction_rad{0.0};
    double posterior_entropy_norm{1.0};
    double posterior_peak_ratio{0.0};
    double posterior_variance_m2{std::numeric_limits<double>::quiet_NaN()};
    Vec2 hit_centroid{0.0, 0.0};
    bool has_hit_centroid{false};
};

struct EvidenceDecision {
    bool allow_declaration{false};
    bool force_exploration{true};
    std::string reason;
};

class EvidenceGate {
public:
    explicit EvidenceGate(EvidenceGateConfig cfg = {}) : cfg_(cfg) {}

    EvidenceSummary summarize(const std::vector<double>& posterior,
                              const std::vector<int>& free_mask,
                              const GridSpec& grid,
                              const std::vector<HitSample>& hits,
                              int iterations) const {
        requireGridAndMask(grid, free_mask);
        EvidenceSummary s;
        s.iterations = iterations;

        double min_x = std::numeric_limits<double>::infinity();
        double min_y = std::numeric_limits<double>::infinity();
        double max_x = -std::numeric_limits<double>::infinity();
        double max_y = -std::numeric_limits<double>::infinity();

        double sx = 0.0, sy = 0.0, mass = 0.0;
        double wind_sin = 0.0, wind_cos = 0.0, wind_speed = 0.0;

        for (const auto& h : hits) {
            if (!(h.concentration > 0.0)) continue;
            ++s.hit_count;
            const double w = std::max(0.0, h.concentration);
            mass += w;
            sx += w * h.x;
            sy += w * h.y;
            min_x = std::min(min_x, h.x);
            min_y = std::min(min_y, h.y);
            max_x = std::max(max_x, h.x);
            max_y = std::max(max_y, h.y);
            wind_sin += std::sin(h.wind_direction_rad);
            wind_cos += std::cos(h.wind_direction_rad);
            wind_speed += h.wind_speed;
        }

        s.hit_mass = mass;
        if (mass > 1e-15) {
            s.hit_centroid = Vec2{sx / mass, sy / mass};
            s.has_hit_centroid = true;
        }

        if (s.hit_count > 0) {
            s.hit_bbox_diag_m = std::sqrt(sqr(max_x - min_x) + sqr(max_y - min_y));
            double rss = 0.0;
            for (const auto& h : hits) {
                rss += sqr(h.x - s.hit_centroid.x) + sqr(h.y - s.hit_centroid.y);
            }
            s.hit_rms_radius_m = std::sqrt(rss / std::max(1, s.hit_count));
            const double ms = wind_sin / s.hit_count;
            const double mc = wind_cos / s.hit_count;
            s.wind_coherence = std::sqrt(ms * ms + mc * mc);
            s.mean_wind_direction_rad = std::atan2(ms, mc);
            s.mean_wind_speed = wind_speed / s.hit_count;
        }

        std::vector<double> p = posterior;
        if (static_cast<int>(p.size()) == grid.size() && normalizeFree(p, free_mask)) {
            s.posterior_entropy_norm = normalizedEntropy(p, free_mask);
            const int peak_idx = argmaxFree(p, free_mask);
            if (peak_idx >= 0) {
                const double total = sumFree(p, free_mask);
                s.posterior_peak_ratio = (total > 0.0) ? p[peak_idx] / total : 0.0;
            }
            s.posterior_variance_m2 = varianceAroundExpected(p, grid, free_mask);
        }

        return s;
    }

    EvidenceDecision decide(const EvidenceSummary& s,
                            bool pmfs_convergence_pass) const {
        EvidenceDecision d;
        std::ostringstream why;

        const bool iter_ok = s.iterations >= cfg_.min_iterations;
        const bool hit_count_ok = s.hit_count >= cfg_.min_hit_count;
        const bool hit_mass_ok = s.hit_mass >= cfg_.min_hit_mass;
        const bool coverage_ok = s.hit_bbox_diag_m >= cfg_.min_hit_bbox_diag_m;
        const bool wind_ok = (s.hit_count == 0) ? false : (s.wind_coherence >= cfg_.min_wind_coherence);
        const bool entropy_ok = s.posterior_entropy_norm <= cfg_.max_posterior_entropy_norm;
        const bool peak_ok = s.posterior_peak_ratio >= cfg_.min_posterior_peak_ratio;

        if (!pmfs_convergence_pass) {
            d.allow_declaration = false;
            d.force_exploration = false;
            d.reason = "pmfs_not_converged";
            return d;
        }

        why << "pmfs_converged";
        if (!iter_ok) why << "|low_iterations";
        if (!hit_count_ok) why << "|low_hit_count";
        if (!hit_mass_ok) why << "|low_hit_mass";
        if (!coverage_ok) why << "|low_hit_coverage";
        if (!wind_ok) why << "|low_wind_coherence";
        if (!entropy_ok) why << "|high_entropy";
        if (!peak_ok) why << "|low_peak_ratio";

        const bool evidence_ok = iter_ok && hit_count_ok && hit_mass_ok && coverage_ok && wind_ok && entropy_ok && peak_ok;
        if (evidence_ok) {
            d.allow_declaration = true;
            d.force_exploration = false;
            why << "|allow";
        } else {
            d.allow_declaration = false;
            d.force_exploration = cfg_.reject_no_hit_convergence;
            why << "|reject_declaration";
        }

        d.reason = why.str();
        return d;
    }

    // A simple coverage-biased target. This is intentionally conservative: it does not replace
    // a real planner, but gives the VM integrator a non-GT fallback goal when EGS rejects declaration.
    Vec2 suggestExplorationTarget(const std::vector<double>& posterior,
                                  const std::vector<int>& free_mask,
                                  const GridSpec& grid,
                                  const Vec2& current,
                                  double min_distance_m = 1.0) const {
        requireGridAndMask(grid, free_mask);
        std::vector<double> p = posterior;
        if (static_cast<int>(p.size()) != grid.size() || !normalizeFree(p, free_mask)) {
            p = uniformFreeMap(grid, free_mask);
        }

        int best_idx = -1;
        double best_score = -std::numeric_limits<double>::infinity();

        for (int idx = 0; idx < grid.size(); ++idx) {
            if (!isFree(free_mask, idx)) continue;
            auto [i, j] = grid.ij(idx);
            Vec2 c = grid.ijToWorld(i, j);
            const double d = distance(c, current);
            if (d < min_distance_m) continue;
            // Prefer cells with non-negligible posterior mass and far enough from current.
            const double dist_bonus = std::min(1.0, d / std::max(min_distance_m, 1e-6));
            const double score = std::log(p[idx] + 1e-12) + 0.25 * dist_bonus;
            if (score > best_score) {
                best_score = score;
                best_idx = idx;
            }
        }

        if (best_idx < 0) return current;
        auto [bi, bj] = grid.ij(best_idx);
        return grid.ijToWorld(bi, bj);
    }

private:
    EvidenceGateConfig cfg_;
};

} // namespace uav_gsl_review
