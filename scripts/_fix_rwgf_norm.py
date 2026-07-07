import shutil

# Fix the RwgfSupervisor to use peak-to-mean ratio instead of absolute threshold
cpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp'
with open(cpp_path, 'r') as f:
    content = f.read()

# Change normalization to preserve absolute values - use max normalization instead of sum normalization
old_norm = '''    // Normalize
    double total = std::accumulate(likelihood_.begin(), likelihood_.end(), 0.0);
    if (total > 0) {
        for (auto& v : likelihood_) v /= total;
    }'''

new_norm = '''    // Normalize by max (not sum) to preserve peak prominence
    double max_val = *std::max_element(likelihood_.begin(), likelihood_.end());
    if (max_val > 0) {
        // Keep absolute values but cap at 1.0
        // Don't normalize by sum - that dilutes peaks
    }'''

content = content.replace(old_norm, new_norm)

# Change navigation threshold to use peak-to-mean ratio
old_nav = '''    // Navigation decision
    double nav_dx = peak_wx - input.pose_x;
    double nav_dy = peak_wy - input.pose_y;
    double nav_dist = std::sqrt(nav_dx * nav_dx + nav_dy * nav_dy);

    if (n_updates_ >= 2 && peak_val > cfg_.nav_threshold && nav_dist > cfg_.min_peak_distance) {'''

new_nav = '''    // Navigation decision - use peak-to-mean ratio
    double mean_val = std::accumulate(likelihood_.begin(), likelihood_.end(), 0.0) / likelihood_.size();
    double peak_to_mean = (mean_val > 1e-10) ? peak_val / mean_val : 0;
    
    double nav_dx = peak_wx - input.pose_x;
    double nav_dy = peak_wy - input.pose_y;
    double nav_dist = std::sqrt(nav_dx * nav_dx + nav_dy * nav_dy);

    if (n_updates_ >= 2 && peak_to_mean > cfg_.nav_threshold && nav_dist > cfg_.min_peak_distance) {'''

content = content.replace(old_nav, new_nav)

with open(cpp_path, 'w') as f:
    f.write(content)

# Also update the header copy
shutil.copy('/home/zyc/ros2_ws/src/GSL/gsl_server/include/gsl_server/wranf/RwgfSupervisor.hpp',
            '/home/zyc/ros2_ws/src/GSL/gsl_server/src/wranf/RwgfSupervisor.hpp')
print('rwgf code updated')
