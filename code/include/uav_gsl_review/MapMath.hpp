#pragma once

#include "uav_gsl_review/GridTypes.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

namespace uav_gsl_review {

inline double sumFree(const std::vector<double>& map,
                      const std::vector<int>& free_mask) {
    double s = 0.0;
    for (int idx = 0; idx < static_cast<int>(map.size()); ++idx) {
        if (isFree(free_mask, idx)) {
            s += std::max(0.0, map[idx]);
        }
    }
    return s;
}

inline bool normalizeFree(std::vector<double>& map,
                          const std::vector<int>& free_mask,
                          double eps = 1e-15) {
    double s = sumFree(map, free_mask);
    if (!(s > eps) || !std::isfinite(s)) return false;
    for (int idx = 0; idx < static_cast<int>(map.size()); ++idx) {
        if (isFree(free_mask, idx)) map[idx] = std::max(0.0, map[idx]) / s;
        else map[idx] = 0.0;
    }
    return true;
}

inline std::vector<double> uniformFreeMap(const GridSpec& grid,
                                          const std::vector<int>& free_mask) {
    requireGridAndMask(grid, free_mask);
    std::vector<double> out(grid.size(), 0.0);
    int n_free = 0;
    for (int idx = 0; idx < grid.size(); ++idx) {
        if (isFree(free_mask, idx)) ++n_free;
    }
    if (n_free <= 0) return out;
    const double p = 1.0 / static_cast<double>(n_free);
    for (int idx = 0; idx < grid.size(); ++idx) {
        if (isFree(free_mask, idx)) out[idx] = p;
    }
    return out;
}

inline double normalizedEntropy(const std::vector<double>& map,
                                const std::vector<int>& free_mask) {
    const double eps = 1e-15;
    int n_free = 0;
    double H = 0.0;
    for (int idx = 0; idx < static_cast<int>(map.size()); ++idx) {
        if (!isFree(free_mask, idx)) continue;
        ++n_free;
        const double p = std::max(map[idx], eps);
        H -= p * std::log(p);
    }
    if (n_free <= 1) return 0.0;
    return std::max(0.0, std::min(1.0, H / std::log(static_cast<double>(n_free))));
}

inline int argmaxFree(const std::vector<double>& map,
                      const std::vector<int>& free_mask) {
    int best = -1;
    double best_v = -std::numeric_limits<double>::infinity();
    for (int idx = 0; idx < static_cast<int>(map.size()); ++idx) {
        if (!isFree(free_mask, idx)) continue;
        if (map[idx] > best_v) {
            best_v = map[idx];
            best = idx;
        }
    }
    return best;
}

inline Vec2 expectedValue(const std::vector<double>& map,
                          const GridSpec& grid,
                          const std::vector<int>& free_mask) {
    double sx = 0.0;
    double sy = 0.0;
    double m = 0.0;
    for (int idx = 0; idx < grid.size(); ++idx) {
        if (!isFree(free_mask, idx)) continue;
        auto [i, j] = grid.ij(idx);
        Vec2 c = grid.ijToWorld(i, j);
        const double p = std::max(0.0, map[idx]);
        sx += p * c.x;
        sy += p * c.y;
        m += p;
    }
    if (m <= 1e-15) return Vec2{};
    return Vec2{sx / m, sy / m};
}

inline double varianceAroundExpected(const std::vector<double>& map,
                                     const GridSpec& grid,
                                     const std::vector<int>& free_mask) {
    Vec2 mu = expectedValue(map, grid, free_mask);
    double v = 0.0;
    double m = 0.0;
    for (int idx = 0; idx < grid.size(); ++idx) {
        if (!isFree(free_mask, idx)) continue;
        auto [i, j] = grid.ij(idx);
        Vec2 c = grid.ijToWorld(i, j);
        const double p = std::max(0.0, map[idx]);
        v += p * (sqr(c.x - mu.x) + sqr(c.y - mu.y));
        m += p;
    }
    if (m <= 1e-15) return std::numeric_limits<double>::quiet_NaN();
    return v / m;
}

inline std::vector<double> convolveMasked(const std::vector<double>& image,
                                          const std::vector<double>& psf,
                                          const GridSpec& grid,
                                          const std::vector<int>& free_mask,
                                          int k) {
    const int k2 = k / 2;
    std::vector<double> out(grid.size(), 0.0);

    for (int j = 0; j < grid.height; ++j) {
        for (int i = 0; i < grid.width; ++i) {
            const int idx = grid.index(i, j);
            if (!isFree(free_mask, idx)) continue;
            double v = 0.0;
            for (int dj = -k2; dj <= k2; ++dj) {
                for (int di = -k2; di <= k2; ++di) {
                    const int ni = i - di;
                    const int nj = j - dj;
                    if (!grid.inside(ni, nj)) continue;
                    const int nidx = grid.index(ni, nj);
                    if (!isFree(free_mask, nidx)) continue;
                    const int pidx = (dj + k2) * k + (di + k2);
                    v += image[nidx] * psf[pidx];
                }
            }
            out[idx] = v;
        }
    }
    return out;
}

inline std::vector<double> mirrorPsf(const std::vector<double>& psf, int k) {
    std::vector<double> out(psf.size(), 0.0);
    for (int j = 0; j < k; ++j) {
        for (int i = 0; i < k; ++i) {
            out[j * k + i] = psf[(k - 1 - j) * k + (k - 1 - i)];
        }
    }
    return out;
}

inline std::vector<double> buildDirectionalPsf(int k,
                                               double wind_direction_rad,
                                               bool wind_vector_is_flow_to,
                                               double sigma_upwind_cells,
                                               double sigma_downwind_cells,
                                               double sigma_crosswind_cells) {
    if (k < 3) k = 3;
    if (k % 2 == 0) ++k;
    const int k2 = k / 2;

    // Downwind is the direction in which gas travels away from the source.
    // If wind_direction_rad is flow-to, downwind = wind_direction_rad.
    // If it is flow-from, downwind = wind_direction_rad + pi.
    const double downwind = wind_vector_is_flow_to ? wind_direction_rad : wind_direction_rad + M_PI;
    const double cw = std::cos(downwind);
    const double sw = std::sin(downwind);

    std::vector<double> psf(k * k, 0.0);
    double s = 0.0;
    for (int dj = -k2; dj <= k2; ++dj) {
        for (int di = -k2; di <= k2; ++di) {
            const double along = di * cw + dj * sw;
            const double across = -di * sw + dj * cw;
            const double sigma_along = (along >= 0.0) ? sigma_downwind_cells : sigma_upwind_cells;
            const double val = std::exp(-0.5 * (sqr(along / std::max(1e-6, sigma_along)) +
                                                sqr(across / std::max(1e-6, sigma_crosswind_cells))));
            psf[(dj + k2) * k + (di + k2)] = val;
            s += val;
        }
    }
    if (s > 0.0) {
        for (double& v : psf) v /= s;
    }
    return psf;
}

inline void splatGaussian(std::vector<double>& map,
                          const GridSpec& grid,
                          const std::vector<int>& free_mask,
                          const Vec2& xy,
                          double mass,
                          double sigma_cells,
                          int radius_cells) {
    auto [ci, cj] = grid.worldToIJ(xy.x, xy.y);
    if (!grid.inside(ci, cj)) return;
    const double denom = 2.0 * std::max(1e-6, sigma_cells * sigma_cells);
    for (int dj = -radius_cells; dj <= radius_cells; ++dj) {
        for (int di = -radius_cells; di <= radius_cells; ++di) {
            const int i = ci + di;
            const int j = cj + dj;
            if (!grid.inside(i, j)) continue;
            const int idx = grid.index(i, j);
            if (!isFree(free_mask, idx)) continue;
            const double v = mass * std::exp(-(di * di + dj * dj) / denom);
            map[idx] += v;
        }
    }
}

} // namespace uav_gsl_review
