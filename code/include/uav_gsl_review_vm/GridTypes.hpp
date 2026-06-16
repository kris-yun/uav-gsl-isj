#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace uav_gsl_review {

struct Vec2 {
    double x{0.0};
    double y{0.0};
};

inline double sqr(double v) { return v * v; }

inline double distance(const Vec2& a, const Vec2& b) {
    return std::sqrt(sqr(a.x - b.x) + sqr(a.y - b.y));
}

struct GridSpec {
    int width{0};
    int height{0};
    double resolution{1.0};
    double origin_x{0.0};
    double origin_y{0.0};

    int size() const { return width * height; }

    bool valid() const {
        return width > 0 && height > 0 && resolution > 0.0;
    }

    int index(int i, int j) const {
        return j * width + i;
    }

    bool inside(int i, int j) const {
        return i >= 0 && j >= 0 && i < width && j < height;
    }

    std::pair<int, int> ij(int idx) const {
        return {idx % width, idx / width};
    }

    std::pair<int, int> worldToIJ(double x, double y) const {
        const int i = static_cast<int>(std::floor((x - origin_x) / resolution));
        const int j = static_cast<int>(std::floor((y - origin_y) / resolution));
        return {i, j};
    }

    Vec2 ijToWorld(double i, double j) const {
        // Cell center convention.
        return Vec2{origin_x + (i + 0.5) * resolution,
                    origin_y + (j + 0.5) * resolution};
    }
};

struct HitSample {
    double x{0.0};
    double y{0.0};
    double concentration{0.0};
    double wind_speed{0.0};
    // Radians. Must be audited: either flow-to or flow-from depending on config.
    double wind_direction_rad{0.0};
};

inline bool isFree(const std::vector<int>& free_mask, int idx) {
    // Empty mask means all cells are free. Otherwise nonzero = free.
    return free_mask.empty() || (idx >= 0 && idx < static_cast<int>(free_mask.size()) && free_mask[idx] != 0);
}

inline void requireGridAndMask(const GridSpec& grid, const std::vector<int>& free_mask) {
    if (!grid.valid()) {
        throw std::invalid_argument("GridSpec is invalid");
    }
    if (!free_mask.empty() && static_cast<int>(free_mask.size()) != grid.size()) {
        throw std::invalid_argument("free_mask size does not match grid size");
    }
}

inline double angleWrapPi(double a) {
    while (a > M_PI) a -= 2.0 * M_PI;
    while (a < -M_PI) a += 2.0 * M_PI;
    return a;
}

} // namespace uav_gsl_review
