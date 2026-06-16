#pragma once

#include "uav_gsl_review/EvidenceGate.hpp"
#include "uav_gsl_review/GridTypes.hpp"
#include "uav_gsl_review/MapMath.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

namespace uav_gsl_review {

struct DirectionalDeconvConfig {
    int min_hits{5};
    double min_concentration{0.0};

    int rl_iterations{10};
    int psf_size{9};

    // PSF shape in grid cells. Downwind sigma should usually be larger than upwind.
    double sigma_upwind_cells{1.0};
    double sigma_downwind_cells{3.0};
    double sigma_crosswind_cells{1.5};

    // Observation map construction from all hits.
    int hit_splat_radius_cells{2};
    double hit_splat_sigma_cells{1.0};
    double hit_weight_exponent{1.0};

    // PMFS posterior as prior. 0 disables prior, 1 multiplies by posterior once.
    double pmfs_prior_power{1.0};

    // Direction handling.
    bool wind_vector_is_flow_to{true};
    double min_wind_speed{0.01};

    // Output validity.
    double min_peak_mass_ratio{0.0};
    double max_entropy_norm{1.0};

    // Use hit-level wind samples to estimate PSF direction.
    bool use_hit_wind_average{true};
};

struct DirectionalDeconvResult {
    bool valid{false};
    std::string reason;

    Vec2 peak_estimate{0.0, 0.0};
    Vec2 expected_estimate{0.0, 0.0};

    int hit_count{0};
    double hit_mass{0.0};
    double wind_coherence{0.0};
    double mean_wind_speed{0.0};
    double mean_wind_direction_rad{0.0};

    double peak_mass_ratio{0.0};
    double entropy_norm{1.0};

    std::vector<double> observation_map;
    std::vector<double> restored_map;
    std::vector<double> fused_map;
};

class DirectionalDeconvRefiner {
public:
    explicit DirectionalDeconvRefiner(DirectionalDeconvConfig cfg = {}) : cfg_(cfg) {}

    DirectionalDeconvResult refine(const std::vector<double>& pmfs_posterior,
                                   const std::vector<int>& free_mask,
                                   const GridSpec& grid,
                                   const std::vector<HitSample>& hits) const {
        requireGridAndMask(grid, free_mask);
        DirectionalDeconvResult r;

        if (static_cast<int>(pmfs_posterior.size()) != grid.size()) {
            r.reason = "posterior_size_mismatch";
            return r;
        }

        // 1) Build all-hit observation map. This is the main difference from peak-blob SDR.
        r.observation_map.assign(grid.size(), 0.0);
        double sin_acc = 0.0, cos_acc = 0.0, speed_acc = 0.0;
        for (const auto& h : hits) {
            if (!(h.concentration > cfg_.min_concentration)) continue;
            auto [i, j] = grid.worldToIJ(h.x, h.y);
            if (!grid.inside(i, j)) continue;
            const int idx = grid.index(i, j);
            if (!isFree(free_mask, idx)) continue;

            ++r.hit_count;
            const double w = std::pow(std::max(0.0, h.concentration - cfg_.min_concentration), cfg_.hit_weight_exponent);
            const double mass = (w > 0.0) ? w : std::max(0.0, h.concentration);
            r.hit_mass += mass;

            splatGaussian(r.observation_map, grid, free_mask, Vec2{h.x, h.y}, mass,
                          cfg_.hit_splat_sigma_cells, cfg_.hit_splat_radius_cells);
            sin_acc += std::sin(h.wind_direction_rad);
            cos_acc += std::cos(h.wind_direction_rad);
            speed_acc += h.wind_speed;
        }

        if (r.hit_count < cfg_.min_hits) {
            r.reason = "too_few_hits";
            return r;
        }
        if (!normalizeFree(r.observation_map, free_mask)) {
            r.reason = "empty_observation_map";
            return r;
        }

        const double mean_sin = sin_acc / r.hit_count;
        const double mean_cos = cos_acc / r.hit_count;
        r.wind_coherence = std::sqrt(mean_sin * mean_sin + mean_cos * mean_cos);
        r.mean_wind_direction_rad = std::atan2(mean_sin, mean_cos);
        r.mean_wind_speed = speed_acc / r.hit_count;

        if (r.mean_wind_speed < cfg_.min_wind_speed) {
            r.reason = "wind_speed_too_low";
            return r;
        }

        // 2) Directional PSF.
        int k = std::max(3, cfg_.psf_size);
        if (k % 2 == 0) ++k;
        const auto psf = buildDirectionalPsf(k,
                                             r.mean_wind_direction_rad,
                                             cfg_.wind_vector_is_flow_to,
                                             cfg_.sigma_upwind_cells,
                                             cfg_.sigma_downwind_cells,
                                             cfg_.sigma_crosswind_cells);
        const auto psf_mirror = mirrorPsf(psf, k);

        // 3) Richardson-Lucy inverse restoration.
        // Initialize with a normalized PMFS posterior to retain PMFS evidence but do not use GT.
        r.restored_map = pmfs_posterior;
        if (!normalizeFree(r.restored_map, free_mask)) {
            r.restored_map = uniformFreeMap(grid, free_mask);
        }

        for (int iter = 0; iter < cfg_.rl_iterations; ++iter) {
            auto conv = convolveMasked(r.restored_map, psf, grid, free_mask, k);
            std::vector<double> ratio(grid.size(), 0.0);
            for (int idx = 0; idx < grid.size(); ++idx) {
                if (!isFree(free_mask, idx)) continue;
                ratio[idx] = r.observation_map[idx] / std::max(conv[idx], 1e-12);
            }
            auto corr = convolveMasked(ratio, psf_mirror, grid, free_mask, k);
            for (int idx = 0; idx < grid.size(); ++idx) {
                if (!isFree(free_mask, idx)) {
                    r.restored_map[idx] = 0.0;
                    continue;
                }
                r.restored_map[idx] *= corr[idx];
            }
            normalizeFree(r.restored_map, free_mask);
        }

        // 4) Fuse restored map with PMFS posterior as a prior. This prevents hit map alone from
        // drifting into physically impossible areas but must be ablated.
        r.fused_map = r.restored_map;
        if (cfg_.pmfs_prior_power > 0.0) {
            std::vector<double> prior = pmfs_posterior;
            if (normalizeFree(prior, free_mask)) {
                for (int idx = 0; idx < grid.size(); ++idx) {
                    if (!isFree(free_mask, idx)) continue;
                    r.fused_map[idx] = r.restored_map[idx] * std::pow(std::max(prior[idx], 1e-15),
                                                                      cfg_.pmfs_prior_power);
                }
                normalizeFree(r.fused_map, free_mask);
            }
        }

        const int peak_idx = argmaxFree(r.fused_map, free_mask);
        if (peak_idx < 0) {
            r.reason = "no_free_peak";
            return r;
        }

        const double total = sumFree(r.fused_map, free_mask);
        r.peak_mass_ratio = (total > 0.0) ? r.fused_map[peak_idx] / total : 0.0;
        r.entropy_norm = normalizedEntropy(r.fused_map, free_mask);
        auto [pi, pj] = grid.ij(peak_idx);
        r.peak_estimate = grid.ijToWorld(pi, pj);
        r.expected_estimate = expectedValue(r.fused_map, grid, free_mask);

        if (r.peak_mass_ratio < cfg_.min_peak_mass_ratio) {
            r.reason = "low_peak_mass_ratio";
            return r;
        }
        if (r.entropy_norm > cfg_.max_entropy_norm) {
            r.reason = "high_refined_entropy";
            return r;
        }

        r.valid = true;
        r.reason = "ok";
        return r;
    }

private:
    DirectionalDeconvConfig cfg_;
};

} // namespace uav_gsl_review
