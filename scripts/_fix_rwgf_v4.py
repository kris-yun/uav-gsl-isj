cpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/RwgfSupervisor.cpp'
with open(cpp_path, 'r') as f:
    content = f.read()

# Replace the upwind cone update with a concentration-weighted centroid approach
# This works better when wind is unreliable (near-zero)

old_apply = '''void RwgfSupervisor::applyUpwindCone(double pose_x, double pose_y,
                                      double wind_angle_rad, double cone_half_angle_rad,
                                      double boost) {
    // Upwind direction = opposite of wind direction
    // Wind blows FROM wind_angle TO wind_angle + PI
    double upwind_angle = wind_angle_rad + M_PI;

    int pix, piy;
    worldToGrid(pose_x, pose_y, pix, piy);

    // Scan all cells within a reasonable radius
    int max_radius_cells = (int)std::ceil(8.0 / cfg_.cell_size);  // 8m radius
    for (int dy = -max_radius_cells; dy <= max_radius_cells; dy++) {
        for (int dx = -max_radius_cells; dx <= max_radius_cells; dx++) {
            int cx = pix + dx;
            int cy = piy + dy;
            if (!inBounds(cx, cy)) continue;

            double cwx, cwy;
            gridToWorld(cx, cy, cwx, cwy);

            double ddx = cwx - pose_x;
            double ddy = cwy - pose_y;
            double dist = std::sqrt(ddx * ddx + ddy * ddy);
            if (dist < 0.01) continue;  // skip self

            // Angle from pose to cell
            double cell_angle = std::atan2(ddy, ddx);

            // Angular difference from upwind direction
            double angle_diff = cell_angle - upwind_angle;
            // Normalize to [-PI, PI]
            while (angle_diff > M_PI) angle_diff -= 2 * M_PI;
            while (angle_diff < -M_PI) angle_diff += 2 * M_PI;

            if (std::abs(angle_diff) <= cone_half_angle_rad) {
                // Inside cone: boost decreases with distance
                double dist_factor = std::exp(-dist / 5.0);  // 5m decay length
                double angular_factor = 1.0 - std::abs(angle_diff) / cone_half_angle_rad;
                likelihood_[idx(cx, cy)] += boost * dist_factor * angular_factor;
            }
        }
    }
}'''

new_apply = '''void RwgfSupervisor::applyUpwindCone(double pose_x, double pose_y,
                                      double wind_angle_rad, double cone_half_angle_rad,
                                      double boost) {
    // When wind is unreliable, use isotropic Gaussian blob centered on gas hit
    // When wind is reliable, use upwind-biased Gaussian
    // This is a hybrid approach that works in both regimes

    int pix, piy;
    worldToGrid(pose_x, pose_y, pix, piy);

    // Determine if wind is reliable enough to use directional bias
    double wind_speed = std::sqrt(
        std::pow(std::cos(wind_angle_rad), 2) + std::pow(std::sin(wind_angle_rad), 2));
    // wind_speed here is normalized direction, actual speed is in wind_reliability_ema_
    bool use_directional = (wind_reliability_ema_ > 0.4);

    double upwind_angle = wind_angle_rad + M_PI;
    int max_radius_cells = (int)std::ceil(6.0 / cfg_.cell_size);

    for (int dy = -max_radius_cells; dy <= max_radius_cells; dy++) {
        for (int dx = -max_radius_cells; dx <= max_radius_cells; dx++) {
            int cx = pix + dx;
            int cy = piy + dy;
            if (!inBounds(cx, cy)) continue;

            double cwx, cwy;
            gridToWorld(cx, cy, cwx, cwy);

            double ddx = cwx - pose_x;
            double ddy = cwy - pose_y;
            double dist = std::sqrt(ddx * ddx + ddy * ddy);
            if (dist < 0.01) continue;

            // Isotropic Gaussian decay
            double sigma = 2.5;  // 2.5m characteristic scale
            double gaussian = std::exp(-0.5 * dist * dist / (sigma * sigma));

            if (use_directional) {
                // Add upwind bias when wind is reliable
                double cell_angle = std::atan2(ddy, ddx);
                double angle_diff = cell_angle - upwind_angle;
                while (angle_diff > M_PI) angle_diff -= 2 * M_PI;
                while (angle_diff < -M_PI) angle_diff += 2 * M_PI;
                double directional_weight = std::exp(-0.5 * angle_diff * angle_diff / (cone_half_angle_rad * cone_half_angle_rad));
                gaussian *= directional_weight;
            }
            // else: purely isotropic (works for near-zero wind)

            likelihood_[idx(cx, cy)] += boost * gaussian;
        }
    }
}'''

content = content.replace(old_apply, new_apply)

with open(cpp_path, 'w') as f:
    f.write(content)
print('rwgf isotropic gaussian applied')
