path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# Fix 1: Remove gas threshold gate on posterior update - always update
old_update = """    // Update 3D posterior with current observation
    if (latest_gas_ > 0.001f) {
        posterior3d_.update(cx, cy, current_altitude_, latest_gas_, wx, wy, ws);
    }"""
new_update = """    // V5.2: ALWAYS update posterior (even low gas = negative evidence)
    posterior3d_.update(cx, cy, current_altitude_, std::max(latest_gas_, 0.0001f), wx, wy, ws);"""
code = code.replace(old_update, new_update)

# Fix 2: FAST EXIT must also check MAP distance to robot
old_fast = """    // V5: fast exit if high concentration and near source area
    if (step_count_ >= 20 && best_hit_conc_ > 0.5f && near_best_hit) {
        GSL_INFO("OPGSL-SDNBV FAST EXIT: best_c={:.3f} near_hit={} step={}", best_hit_conc_, near_best_hit, step_count_);
        return GSLResult::Success;
    }"""
new_fast = """    // V5.2: fast exit requires MAP also near robot (not just best_hit)
    float map_dist = std::sqrt((map_x-cx)*(map_x-cx) + (map_y-cy)*(map_y-cy));
    if (step_count_ >= 20 && best_hit_conc_ > 0.5f && near_best_hit && map_dist < 2.0f) {
        GSL_INFO("OPGSL-SDNBV FAST EXIT: best_c={:.3f} near_hit={} map_dist={:.2f} step={}",
                 best_hit_conc_, near_best_hit, map_dist, step_count_);
        return GSLResult::Success;
    }"""
code = code.replace(old_fast, new_fast)

# Fix 3: Also tighten convergence - require MAP near robot
old_converge = """    // Path A: near MAP + low entropy + stable z
    // Path B: near best hit + high concentration + low entropy
    bool converged = (near_map && entropy_low && z_ok) || (near_best_hit && high_conc && entropy_low);"""
new_converge = """    // V5.2: all paths require MAP reasonably close to robot
    bool map_reasonable = dist_to_peak < 3.0f;
    bool converged = map_reasonable && ((near_map && entropy_low && z_ok) || (near_best_hit && high_conc && entropy_low));"""
code = code.replace(old_converge, new_converge)

with open(path, 'w') as f:
    f.write(code)
print("V5.2 fixes applied: always-update posterior, MAP-distance gated convergence")