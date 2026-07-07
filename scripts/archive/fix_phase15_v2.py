filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    lines = f.readlines()

# Find the Phase 1.5 block start and end
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "Phase 1.5: Upwind plume-tracking with overshoot" in line:
        start_idx = i
    if start_idx and i > start_idx and "SBD: Sequential Bayesian Design" in line:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"ERROR: could not find block. start={start_idx} end={end_idx}")
    exit(1)

print(f"Replacing lines {start_idx+1} to {end_idx} ({end_idx - start_idx} lines)")

new_block = """    // -- Phase 1.5: Upwind plume-tracking with overshoot detection (steps 7-16) --
    // FIX V6.2: Always go upwind; on overshoot, navigate back toward posterior MAP
    // The best-hit position is DOWNWIND from source (where gas drifted to), so we must NOT
    // navigate toward it. Instead, go UPWIND to trace back to source.
    // Overshoot detection: if concentration drops while going upwind, we passed the source.
    if (use_upwind_tracking_ && step_count_ >= 7 && step_count_ <= 16 && ws > 0.05f && gas_hit_count_ > 0) {
        // Detect overshoot: check if recent concentrations are declining
        bool overshoot = false;
        if (obs_history_c_.size() >= 4) {
            int n = obs_history_c_.size();
            float recent_avg = (obs_history_c_[n-1] + obs_history_c_[n-2]) / 2.0f;
            float prev_avg = (obs_history_c_[n-3] + obs_history_c_[n-4]) / 2.0f;
            // If concentration dropped by >50% and below 0.05, we passed the source
            if (prev_avg > 0.03f && recent_avg < prev_avg * 0.5f && recent_avg < 0.05f) {
                overshoot = true;
            }
        }
        
        if (overshoot) {
            // Passed the source! Navigate back toward posterior MAP estimate
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            float dx = map_x - cx, dy = map_y - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.0f, d * 0.5f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1.5: OVERSHOOT! -> MAP ({:.2f},{:.2f}) d={:.2f}",
                         best_x, best_y, d);
            } else {
                GSL_INFO("SDNBV-P1.5: OVERSHOOT near MAP, switch to Phase 2");
            }
            return;
        }
        
        // Normal upwind tracking: go against wind to trace back to source
        float wn = std::sqrt(wx*wx + wy*wy);
        float upwind_x = -wx / wn;
        float upwind_y = -wy / wn;
        float nav_step = 0.8f;
        best_x = cx + nav_step * upwind_x;
        best_y = cy + nav_step * upwind_y;
        clipToMapBounds(best_x, best_y);
        GSL_INFO("SDNBV-P1.5: UPWIND ({:.2f},{:.2f}) ws={:.2f} c={:.3f}",
                 best_x, best_y, ws, latest_gas_);
        return;
    }

"""

new_lines = lines[:start_idx] + [new_block] + lines[end_idx:]
with open(filepath, "w") as f:
    f.writelines(new_lines)
print("PATCH V6.2 SUCCESS")
