cpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp'
with open(cpp_path, 'r') as f:
    content = f.read()

# Change: once we have ANY updates, ALWAYS override (never fall back to PMFS)
old_nav = '''    if (n_updates_ >= 1 && peak_to_mean > cfg_.nav_threshold && nav_dist > cfg_.min_peak_distance) {
        // Navigate toward peak
        double step = std::min(cfg_.nav_step_size, nav_dist);
        out.override_backend = true;
        out.target_x = input.pose_x + nav_dx / nav_dist * step;
        out.target_y = input.pose_y + nav_dy / nav_dist * step;
        out.target_z = cfg_.target_z;
        out.reason = "RWGF_PEAK_NAV";
    } else if (n_updates_ == 0 && step_count_ > 3) {'''

new_nav = '''    // Once we have gas hits, ALWAYS override - never fall back to PMFS
    bool has_gas_memory = (n_updates_ >= 1);
    bool should_navigate = has_gas_memory && peak_to_mean > cfg_.nav_threshold && nav_dist > cfg_.min_peak_distance;

    if (should_navigate) {
        // Navigate toward peak
        double step = std::min(cfg_.nav_step_size, nav_dist);
        out.override_backend = true;
        out.target_x = input.pose_x + nav_dx / nav_dist * step;
        out.target_y = input.pose_y + nav_dy / nav_dist * step;
        out.target_z = cfg_.target_z;
        out.reason = "RWGF_PEAK_NAV";
    } else if (has_gas_memory) {
        // Have gas memory but peak not confident enough - still override
        // Navigate to best known area with some exploration
        double step = std::min(cfg_.nav_step_size, nav_dist);
        out.override_backend = true;
        out.target_x = input.pose_x + nav_dx / std::max(nav_dist, 0.1) * step;
        out.target_y = input.pose_y + nav_dy / std::max(nav_dist, 0.1) * step;
        out.target_z = cfg_.target_z;
        out.reason = "RWGF_LOW_CONF_NAV";
    } else if (n_updates_ == 0 && step_count_ > 3) {'''

content = content.replace(old_nav, new_nav)

# Also update the else clause
old_else = '''    } else {
        out.override_backend = false;
        out.target_x = input.backend_target_x;
        out.target_y = input.backend_target_y;
        out.target_z = input.backend_target_z;
        out.reason = (n_updates_ < 1) ? "RWGF_COLLECTING" : "RWGF_LOW_CONF";
    }'''

new_else = '''    } else {
        out.override_backend = false;
        out.target_x = input.backend_target_x;
        out.target_y = input.backend_target_y;
        out.target_z = input.backend_target_z;
        out.reason = "RWGF_COLLECTING";
    }'''

content = content.replace(old_else, new_else)

with open(cpp_path, 'w') as f:
    f.write(content)
print('rwgf always-override fix applied')
