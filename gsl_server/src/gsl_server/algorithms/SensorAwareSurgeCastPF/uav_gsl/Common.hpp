#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>

namespace uav_gsl {

constexpr double kPi = 3.1415926535897932384626433832795;
constexpr double kTwoPi = 2.0 * kPi;

inline double clamp(double value, double low, double high) {
    return std::max(low, std::min(value, high));
}

inline double wrapAngle(double angle) {
    while (angle > kPi) angle -= kTwoPi;
    while (angle <= -kPi) angle += kTwoPi;
    return angle;
}

inline double logistic(double value) {
    if (value >= 0.0) {
        const double e = std::exp(-value);
        return 1.0 / (1.0 + e);
    }
    const double e = std::exp(value);
    return e / (1.0 + e);
}

struct Vec2 {
    double x{0.0};
    double y{0.0};

    Vec2() = default;
    Vec2(double x_value, double y_value) : x(x_value), y(y_value) {}

    Vec2 operator+(const Vec2& other) const { return {x + other.x, y + other.y}; }
    Vec2 operator-(const Vec2& other) const { return {x - other.x, y - other.y}; }
    Vec2 operator*(double scalar) const { return {x * scalar, y * scalar}; }
    Vec2 operator/(double scalar) const {
        if (std::abs(scalar) < 1e-15) throw std::runtime_error("division by zero");
        return {x / scalar, y / scalar};
    }
};

inline double dot(const Vec2& a, const Vec2& b) { return a.x * b.x + a.y * b.y; }
inline double squaredNorm(const Vec2& value) { return dot(value, value); }
inline double norm(const Vec2& value) { return std::sqrt(squaredNorm(value)); }
inline Vec2 unitFromAngle(double angle) { return {std::cos(angle), std::sin(angle)}; }
inline Vec2 perpendicular(const Vec2& value) { return {-value.y, value.x}; }
inline bool finite(const Vec2& value) { return std::isfinite(value.x) && std::isfinite(value.y); }

struct Bounds2D {
    double min_x{-10.0};
    double max_x{10.0};
    double min_y{-10.0};
    double max_y{10.0};

    bool valid() const { return min_x < max_x && min_y < max_y; }
    bool contains(const Vec2& point) const {
        return point.x >= min_x && point.x <= max_x && point.y >= min_y && point.y <= max_y;
    }
};

}  // namespace uav_gsl
