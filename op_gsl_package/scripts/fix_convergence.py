#!/usr/bin/env python3
"""Fix WC_RIF_GSL.cpp: replace fixed convergence with adaptive MAP stability."""
import sys

path = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/WC_RIF_GSL.cpp'

with open(path, 'r') as f:
    content = f.read()

# Find and replace the early convergence block
old = """    if (elapsed_time_ > convergence_min_time_ && gas_hit_count_ >= convergence_min_hits_) {
        float est_x, est_y;
        getMAP(est_x, est_y);
        float dx = est_x - currentRobotPosition.x;
        float dy = est_y - currentRobotPosition.y;
        float dist = std::sqrt(dx*dx + dy*dy);

        float H = entropy();
        float H_max = std::log(float(n_cells_ * n_cells_));
        float conc = 1.0f - H / H_max;  // normalized certainty

        if (conc > 0.5f && dist < 1.5f) {
            GSL_INFO("WC-RIF convergence: MAP=({:.2f},{:.2f}) dist={:.2f} conc={:.2f}", est_x, est_y, dist, conc);
            currentResult = GSLResult::Success;
            return GSLResult::Success;
        }
    }"""

new = """    // Adaptive convergence: MAP stability check
    {
        float est_x, est_y;
        getMAP(est_x, est_y);
        map_history_.push_back({est_x, est_y});
        if (map_history_.size() > (size_t)stability_window_) map_history_.pop_front();

        if (map_history_.size() >= (size_t)stability_window_ && gas_hit_count_ >= convergence_min_hits_) {
            float max_movement = 0.0f;
            for (size_t i = 1; i < map_history_.size(); ++i) {
                float dx_m = map_history_[i].first - map_history_[i-1].first;
                float dy_m = map_history_[i].second - map_history_[i-1].second;
                float movement = std::sqrt(dx_m*dx_m + dy_m*dy_m);
                max_movement = std::max(max_movement, movement);
            }
            if (max_movement < stability_threshold_) {
                float dx_r = est_x - currentRobotPosition.x;
                float dy_r = est_y - currentRobotPosition.y;
                float dist_r = std::sqrt(dx_r*dx_r + dy_r*dy_r);
                if (dist_r < 3.0f) {
                    GSL_INFO("WC-RIF adaptive convergence: MAP=({:.2f},{:.2f}) max_move={:.3f} dist={:.2f} elapsed={:.1f}",
                            est_x, est_y, max_movement, dist_r, elapsed_time_);
                    currentResult = GSLResult::Success;
                    return GSLResult::Success;
                }
            }
        }
    }"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('SUCCESS: Replaced convergence with adaptive MAP stability')
else:
    print('WARNING: Old block not found')
    # Show what we're looking for
    if 'convergence_min_time_' in content:
        idx = content.index('convergence_min_time_')
        print(f'Found at position {idx}')
        print(content[idx-50:idx+200])
