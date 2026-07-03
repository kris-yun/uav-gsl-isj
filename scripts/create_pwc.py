#!/usr/bin/env python3
"""Create PWC (Plume Wind Correction) module files."""

# 1. Header file
hpp_content = """#pragma once
#include <cmath>
#include <vector>
#include <fstream>

namespace uav_gsl_pwc {

struct Config {
    bool enabled{false};
    // Correction model: distance = alpha * wind_speed + beta
    double alpha{50.0};     // wind speed scaling (m / (m/s))
    double beta{0.5};       // base correction distance (m)
    double max_correction{5.0};  // max allowed correction (m)
    double min_wind{0.005};  // minimum wind speed to apply correction (m/s)
    // Adaptive: scale correction by plume spread
    bool use_adaptive{true};
    double plume_scale_factor{1.0};
    std::string log_file{"/tmp/pwc_log.csv"};
};

struct Output {
    double corrected_x{0};
    double corrected_y{0};
    double original_x{0};
    double original_y{0};
    double correction_distance{0};
    double wind_speed{0};
    double wind_direction{0};
    bool applied{false};
};

class PwcCorrector {
public:
    explicit PwcCorrector(const Config& cfg);
    ~PwcCorrector();

    // Apply PWC correction to source estimate
    // wind_x/y: wind velocity at source estimate location
    // plume_spread: estimated plume spread (from probability map)
    Output correct(double source_x, double source_y,
                   double wind_x, double wind_y,
                   double plume_spread);

    const Config& config() const { return cfg_; }

private:
    Config cfg_;
    std::ofstream log_stream_;
    int step_count_{0};
};

}  // namespace uav_gsl_pwc
"""

# 2. Implementation file
cpp_content = """#include <gsl_server/pwc/PwcCorrector.hpp>
#include <cmath>
#include <iomanip>

namespace uav_gsl_pwc {

PwcCorrector::PwcCorrector(const Config& cfg) : cfg_(cfg) {
    if (!cfg_.log_file.empty()) {
        log_stream_.open(cfg_.log_file);
        if (log_stream_.is_open()) {
            log_stream_ << "step,orig_x,orig_y,corr_x,corr_y,wind_spd,wind_dir,corr_dist,applied\\n";
        }
    }
}

PwcCorrector::~PwcCorrector() {
    if (log_stream_.is_open()) log_stream_.close();
}

Output PwcCorrector::correct(double source_x, double source_y,
                              double wind_x, double wind_y,
                              double plume_spread) {
    Output out;
    out.original_x = source_x;
    out.original_y = source_y;
    out.corrected_x = source_x;
    out.corrected_y = source_y;

    double wind_speed = std::sqrt(wind_x * wind_x + wind_y * wind_y);
    out.wind_speed = wind_speed;
    out.wind_direction = std::atan2(wind_y, wind_x);

    if (!cfg_.enabled || wind_speed < cfg_.min_wind) {
        out.applied = false;
        // Log
        if (log_stream_.is_open()) {
            log_stream_ << step_count_ << ","
                        << source_x << "," << source_y << ","
                        << source_x << "," << source_y << ","
                        << wind_speed << "," << out.wind_direction << ","
                        << 0 << "," << 0 << "\\n";
        }
        step_count_++;
        return out;
    }

    // Compute correction distance
    double correction_dist;
    if (cfg_.use_adaptive) {
        // Adaptive: correction proportional to wind_speed * plume_spread
        // Physical basis: plume travel distance ~ wind_speed * spread_time
        // spread_time ~ plume_spread / wind_speed (dimensional analysis)
        // So correction ~ plume_spread (geometric scaling)
        correction_dist = cfg_.alpha * wind_speed + cfg_.beta;
        // Scale by plume spread if available
        if (plume_spread > 0.1) {
            correction_dist *= (plume_spread / 2.0) * cfg_.plume_scale_factor;
        }
    } else {
        correction_dist = cfg_.alpha * wind_speed + cfg_.beta;
    }

    // Clamp
    correction_dist = std::min(correction_dist, cfg_.max_correction);
    correction_dist = std::max(correction_dist, 0.0);

    // Apply UPWIND correction: source is upwind of plume peak
    // upwind direction = -wind_vector / |wind|
    double ux = -wind_x / wind_speed;
    double uy = -wind_y / wind_speed;

    out.corrected_x = source_x + ux * correction_dist;
    out.corrected_y = source_y + uy * correction_dist;
    out.correction_distance = correction_dist;
    out.applied = true;

    // Log
    if (log_stream_.is_open()) {
        log_stream_ << step_count_ << ","
                    << source_x << "," << source_y << ","
                    << out.corrected_x << "," << out.corrected_y << ","
                    << wind_speed << "," << out.wind_direction << ","
                    << correction_dist << "," << 1 << "\\n";
    }
    step_count_++;
    return out;
}

}  // namespace uav_gsl_pwc
"""

# Write files
hpp_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/include/gsl_server/pwc/PwcCorrector.hpp"
cpp_path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PwcCorrector.cpp"

import os
os.makedirs(os.path.dirname(hpp_path), exist_ok=True)

with open(hpp_path, 'w') as f:
    f.write(hpp_content)
print(f"Wrote {hpp_path}")

with open(cpp_path, 'w') as f:
    f.write(cpp_content)
print(f"Wrote {cpp_path}")
