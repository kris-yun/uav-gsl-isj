cpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp'
with open(cpp_path, 'r') as f:
    content = f.read()

# 1. Lower gas threshold from 0.01 to 0.001
content = content.replace(
    'if (input.gas_concentration > 0.01) {',
    'if (input.gas_concentration > 0.001) {'
)

# 2. Change COLLECTING mode to allow override when we have ANY updates
old_collecting = '''    if (n_updates_ >= 2 && peak_to_mean > cfg_.nav_threshold && nav_dist > cfg_.min_peak_distance) {
        // Navigate toward peak
        double step = std::min(cfg_.nav_step_size, nav_dist);
        out.override_backend = true;
        out.target_x = input.pose_x + nav_dx / nav_dist * step;
        out.target_y = input.pose_y + nav_dy / nav_dist * step;
        out.target_z = cfg_.target_z;
        out.reason = "RWGF_PEAK_NAV";
    } else {
        out.override_backend = false;
        out.target_x = input.backend_target_x;
        out.target_y = input.backend_target_y;
        out.target_z = input.backend_target_z;
        out.reason = (n_updates_ < 2) ? "RWGF_COLLECTING" : "RWGF_LOW_CONF";
    }'''

new_collecting = '''    if (n_updates_ >= 1 && peak_to_mean > cfg_.nav_threshold && nav_dist > cfg_.min_peak_distance) {
        // Navigate toward peak
        double step = std::min(cfg_.nav_step_size, nav_dist);
        out.override_backend = true;
        out.target_x = input.pose_x + nav_dx / nav_dist * step;
        out.target_y = input.pose_y + nav_dy / nav_dist * step;
        out.target_z = cfg_.target_z;
        out.reason = "RWGF_PEAK_NAV";
    } else if (n_updates_ == 0 && step_count_ > 3) {
        // Exploration mode: when no gas hits, do crosswind sweeps
        // Perpendicular to wind direction to maximize plume crossing
        double wind_angle = std::atan2(input.wind_y, input.wind_x);
        double cross_angle = wind_angle + M_PI / 2.0;
        // Alternate direction each step
        if (step_count_ % 2 == 0) cross_angle += M_PI;
        double explore_dist = 3.0;
        out.override_backend = true;
        out.target_x = input.pose_x + explore_dist * std::cos(cross_angle);
        out.target_y = input.pose_y + explore_dist * std::sin(cross_angle);
        out.target_z = cfg_.target_z;
        // Clamp to bounds
        out.target_x = std::max(cfg_.x_min, std::min(cfg_.x_max, out.target_x));
        out.target_y = std::max(cfg_.y_min, std::min(cfg_.y_max, out.target_y));
        out.reason = "RWGF_CROSSWIND_EXPLORE";
    } else {
        out.override_backend = false;
        out.target_x = input.backend_target_x;
        out.target_y = input.backend_target_y;
        out.target_z = input.backend_target_z;
        out.reason = (n_updates_ < 1) ? "RWGF_COLLECTING" : "RWGF_LOW_CONF";
    }'''

content = content.replace(old_collecting, new_collecting)

with open(cpp_path, 'w') as f:
    f.write(content)
print('rwgf code updated v2')
