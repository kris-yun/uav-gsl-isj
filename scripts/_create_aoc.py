hpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/include/gsl_server/wranf/RwgfSupervisor.hpp'
cpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp'

# Create AOC (Adaptive Override Controller) as a new mode of RwgfSupervisor
# This replaces the RWGF approach with a simpler, more effective strategy

hpp_content = '''#ifndef RWGF_SUPERVISOR_HPP
#define RWGF_SUPERVISOR_HPP

#include <vector>
#include <string>
#include <fstream>
#include <cmath>
#include <deque>

namespace uav_gsl_rwgf {

struct RwgfConfig {
    bool enabled = false;
    // Grid
    double cell_size = 0.3;
    double x_min = -7.6, x_max = 1.2;
    double y_min = -7.9, y_max = 3.5;
    double target_z = 1.0;
    // AOC: Adaptive Override Controller
    int convergence_check_window = 10;     // steps to monitor
    double gas_hit_rate_threshold = 0.2;   // below this -> PMFS likely failing
    double concentration_trend_threshold = -0.01; // negative trend -> losing plume
    int min_steps_before_override = 5;     // don't override too early
    double override_cooldown = 5.0;        // seconds between overrides
    double explore_step_size = 3.0;        // step size for exploration
    double crosswind_explore_dist = 4.0;   // crosswind exploration distance
    // Log
    std::string log_file = "/tmp/rwgf_supervisor_log.csv";
};

struct RwgfOutput {
    bool override_backend = false;
    double target_x = 0, target_y = 0, target_z = 0;
    double gas_hit_rate = 0;
    double avg_concentration = 0;
    double concentration_trend = 0;
    int n_gas_hits = 0;
    int n_steps = 0;
    const char* reason = "AOC_IDLE";
};

class RwgfSupervisor {
public:
    explicit RwgfSupervisor(const RwgfConfig& cfg);
    ~RwgfSupervisor();

    void reset();

    struct Input {
        double time_sec = 0;
        double pose_x = 0, pose_y = 0, pose_z = 0;
        double gas_concentration = 0;
        double wind_x = 0, wind_y = 0;
        double backend_target_x = 0, backend_target_y = 0, backend_target_z = 0;
        bool pmfs_declared_convergence = false;
        int step = 0;
    };

    RwgfOutput process(const Input& input);
    const RwgfConfig& config() const { return cfg_; }
    bool enabled() const { return cfg_.enabled; }

private:
    RwgfConfig cfg_;
    int step_count_ = 0;
    int gas_hit_count_ = 0;
    double last_override_time_ = -100;
    std::deque<double> concentration_history_;
    std::deque<bool> gas_hit_history_;
    std::deque<double> pose_x_history_, pose_y_history_;
    std::ofstream log_stream_;

    void openLog();
    void logRow(const Input& in, const RwgfOutput& out);
};

}  // namespace uav_gsl_rwgf

#endif
'''

cpp_content = '''#include <gsl_server/wranf/RwgfSupervisor.hpp>
#include <algorithm>
#include <numeric>
#include <iomanip>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace uav_gsl_rwgf {

RwgfSupervisor::RwgfSupervisor(const RwgfConfig& cfg) : cfg_(cfg) {}
RwgfSupervisor::~RwgfSupervisor() { if (log_stream_.is_open()) log_stream_.close(); }

void RwgfSupervisor::reset() {
    step_count_ = 0;
    gas_hit_count_ = 0;
    last_override_time_ = -100;
    concentration_history_.clear();
    gas_hit_history_.clear();
    pose_x_history_.clear();
    pose_y_history_.clear();
}

RwgfOutput RwgfSupervisor::process(const Input& input) {
    step_count_++;
    RwgfOutput out;
    out.n_steps = step_count_;

    // Track gas hits
    bool is_gas_hit = (input.gas_concentration > 0.001);
    if (is_gas_hit) gas_hit_count_++;
    out.n_gas_hits = gas_hit_count_;

    // Maintain sliding window
    concentration_history_.push_back(input.gas_concentration);
    gas_hit_history_.push_back(is_gas_hit);
    pose_x_history_.push_back(input.pose_x);
    pose_y_history_.push_back(input.pose_y);

    int window = cfg_.convergence_check_window;
    while ((int)concentration_history_.size() > window) {
        concentration_history_.pop_front();
        gas_hit_history_.pop_front();
        pose_x_history_.pop_front();
        pose_y_history_.pop_front();
    }

    // Compute metrics
    int n = concentration_history_.size();
    double hit_rate = 0;
    double avg_conc = 0;
    double trend = 0;

    if (n > 0) {
        int hits = 0;
        double sum = 0;
        for (int i = 0; i < n; i++) {
            if (gas_hit_history_[i]) hits++;
            sum += concentration_history_[i];
        }
        hit_rate = (double)hits / n;
        avg_conc = sum / n;

        // Linear trend of concentration
        if (n >= 3) {
            double sum_x = 0, sum_y = 0, sum_xy = 0, sum_xx = 0;
            for (int i = 0; i < n; i++) {
                sum_x += i;
                sum_y += concentration_history_[i];
                sum_xy += i * concentration_history_[i];
                sum_xx += i * i;
            }
            double denom = n * sum_xx - sum_x * sum_x;
            if (std::abs(denom) > 1e-10) {
                trend = (n * sum_xy - sum_x * sum_y) / denom;
            }
        }
    }

    out.gas_hit_rate = hit_rate;
    out.avg_concentration = avg_conc;
    out.concentration_trend = trend;

    // AOC Decision: Should we override PMFS?
    bool should_override = false;
    const char* reason = "AOC_PASS";

    // Condition 1: PMFS converging too quickly without enough gas evidence
    if (step_count_ >= cfg_.min_steps_before_override &&
        step_count_ <= 20 &&
        hit_rate < cfg_.gas_hit_rate_threshold &&
        !input.pmfs_declared_convergence) {
        // PMFS is moving but not finding gas -> likely wrong direction
        should_override = true;
        reason = "AOC_LOW_HIT_RATE";
    }

    // Condition 2: Concentration is dropping (losing plume)
    if (step_count_ >= cfg_.min_steps_before_override &&
        n >= 5 &&
        trend < cfg_.concentration_trend_threshold &&
        avg_conc < 0.05) {
        should_override = true;
        reason = "AOC_PLUME_LOSS";
    }

    // Condition 3: No gas hits at all after initial exploration
    if (step_count_ >= 10 &&
        gas_hit_count_ == 0) {
        should_override = true;
        reason = "AOC_NO_GAS";
    }

    // Cooldown check
    if (should_override && (input.time_sec - last_override_time_) < cfg_.override_cooldown) {
        should_override = false;
        reason = "AOC_COOLDOWN";
    }

    if (should_override) {
        // Generate exploration target
        // Strategy: crosswind sweep from current position
        double wind_angle = std::atan2(input.wind_y, input.wind_x);
        
        // Determine sweep direction based on step count
        double sweep_angle;
        if (step_count_ % 4 < 2) {
            sweep_angle = wind_angle + M_PI / 2;  // crosswind right
        } else {
            sweep_angle = wind_angle - M_PI / 2;  // crosswind left
        }

        double dist = cfg_.crosswind_explore_dist;
        out.override_backend = true;
        out.target_x = input.pose_x + dist * std::cos(sweep_angle);
        out.target_y = input.pose_y + dist * std::sin(sweep_angle);
        out.target_z = cfg_.target_z;

        // Clamp to bounds
        out.target_x = std::max(cfg_.x_min, std::min(cfg_.x_max, out.target_x));
        out.target_y = std::max(cfg_.y_min, std::min(cfg_.y_max, out.target_y));

        last_override_time_ = input.time_sec;
        out.reason = reason;
    } else {
        out.override_backend = false;
        out.target_x = input.backend_target_x;
        out.target_y = input.backend_target_y;
        out.target_z = input.backend_target_z;
        out.reason = reason;
    }

    openLog();
    logRow(input, out);
    return out;
}

void RwgfSupervisor::openLog() {
    if (!log_stream_.is_open() && !cfg_.log_file.empty()) {
        log_stream_.open(cfg_.log_file, std::ios::out | std::ios::trunc);
        log_stream_ << "step,time,px,py,gas,wind_speed,"
                    << "hit_rate,avg_conc,trend,n_hits,n_steps,"
                    << "override,tx,ty,reason" << std::endl;
    }
}

void RwgfSupervisor::logRow(const Input& in, const RwgfOutput& out) {
    if (!log_stream_.is_open()) return;
    double ws = std::sqrt(in.wind_x * in.wind_x + in.wind_y * in.wind_y);
    log_stream_ << step_count_ << "," << std::fixed << std::setprecision(3)
                << in.time_sec << "," << in.pose_x << "," << in.pose_y << ","
                << in.gas_concentration << "," << ws << ","
                << out.gas_hit_rate << "," << out.avg_concentration << ","
                << out.concentration_trend << "," << out.n_gas_hits << "," << out.n_steps << ","
                << out.override_backend << "," << out.target_x << "," << out.target_y << ","
                << out.reason << std::endl;
}

}  // namespace uav_gsl_rwgf
'''

with open(hpp_path, 'w') as f:
    f.write(hpp_content)
with open(cpp_path, 'w') as f:
    f.write(cpp_content)

# Copy to wranf directory
import shutil
shutil.copy(hpp_path, '/home/zyc/ros2_ws/src/GSL/gsl_server/src/wranf/RwgfSupervisor.hpp')
shutil.copy(cpp_path, '/home/zyc/ros2_ws/src/GSL/gsl_server/src/wranf/RwgfSupervisor.cpp')

print('AOC supervisor created')
