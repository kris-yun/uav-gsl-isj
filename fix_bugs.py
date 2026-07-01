import re

path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# Bug 3 fix: zero concentration weight -0.05 -> 0.001
code = code.replace("weight = -0.05f;", "weight = 0.001f;  // Bug3 fix: weak positive, not negative")

# Bug 4 fix: z-grid resolution 10 -> 30
code = code.replace("nz_ = 10;", "nz_ = 30;  // Bug4 fix: finer z resolution (0.13m vs 0.4m)")

# Bug 6 fix: NBV step size 0.8 -> 1.5, reduce z candidates
code = code.replace(
    "float step = 0.8f;",
    "float step = 1.5f;  // Bug6 fix: larger step for faster NBV"
)
code = code.replace(
    "for (float dz = -0.5f; dz <= 1.5f; dz += 0.3f) {",
    "for (float dz = -0.5f; dz <= 1.5f; dz += 0.6f) {  // Bug6 fix: fewer z candidates"
)

# Bug 2 fix: dynamic search radius centered on MAP
old_search = """    float search_radius = 3.0f;
    float step = 1.5f;  // Bug6 fix: larger step for faster NBV"""
new_search = """    // Bug2 fix: dynamic search radius centered on MAP, not just robot
    float dist_to_map = std::sqrt((map_x-robot_x)*(map_x-robot_x) + (map_y-robot_y)*(map_y-robot_y));
    float search_radius = std::max(3.0f, dist_to_map * 1.2f + 2.0f);
    float step = 1.5f;  // Bug6 fix: larger step for faster NBV"""
code = code.replace(old_search, new_search)

# Bug 2 fix part 2: also search around MAP, not just robot
old_candidate = """                float cx = std::clamp(robot_x + dx, x_min_ + 0.5f, x_max_ - 0.5f);
                float cy = std::clamp(robot_y + dy, y_min_ + 0.5f, y_max_ - 0.5f);"""
new_candidate = """                // Bug2: search around midpoint of robot and MAP
                float center_x = 0.5f * robot_x + 0.5f * map_x;
                float center_y = 0.5f * robot_y + 0.5f * map_y;
                float cx = std::clamp(center_x + dx, x_min_ + 0.5f, x_max_ - 0.5f);
                float cy = std::clamp(center_y + dy, y_min_ + 0.5f, y_max_ - 0.5f);"""
code = code.replace(old_candidate, new_candidate)

# Bug 5 fix: surge-to-MAP fuse with field peak
old_surge = """            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            float to_map_x = map_x - cx;
            float to_map_y = map_y - cy;"""
new_surge = """            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            // Bug5 fix: fuse posterior MAP with field estimator peak
            auto surge_field = field_estimator_.computeField();
            float fused_x = 0.6f * map_x + 0.4f * surge_field.peak_x;
            float fused_y = 0.6f * map_y + 0.4f * surge_field.peak_y;
            float to_map_x = fused_x - cx;
            float to_map_y = fused_y - cy;"""
code = code.replace(old_surge, new_surge)

# Bug 1 fix: add cross-wind exploration in sdnbvStep
# Insert after the posterior update block, before surge-cast
old_sdnbv = """    // SURGE-CAST: if wind > 0.3 and we have hits, move toward MAP
    if (ws > 0.3f && gas_hit_count_ > 3 && step_count_ > 3) {"""
new_sdnbv = """    // Bug1 fix: cross-wind exploration to break x-lock
    // Every 4th step, force a cross-wind movement to collect diverse observations
    if (step_count_ > 2 && step_count_ % 4 == 0 && ws > 0.1f) {
        float wn = std::sqrt(wx*wx + wy*wy);
        if (wn > 0.01f) {
            float perp_x = -wy / wn;  // perpendicular to wind
            float perp_y =  wx / wn;
            // Alternate direction each time
            float sign = (step_count_ % 8 == 0) ? 1.0f : -1.0f;
            float cross_dist = std::max(2.0f, step_size_ * 2.0f);
            best_x = cx + sign * cross_dist * perp_x;
            best_y = cy + sign * cross_dist * perp_y;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV: cross-wind sweep ({:.2f},{:.2f}) perp=({:.2f},{:.2f})",
                     best_x, best_y, perp_x, perp_y);
            return;
        }
    }

    // SURGE-CAST: if wind > 0.3 and we have hits, move toward MAP
    if (ws > 0.3f && gas_hit_count_ > 3 && step_count_ > 3) {"""
code = code.replace(old_sdnbv, new_sdnbv)

with open(path, 'w') as f:
    f.write(code)

print("All 6 bugfixes applied successfully!")