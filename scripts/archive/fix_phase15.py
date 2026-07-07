import sys

filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    lines = f.readlines()

# Lines 598-638 (0-indexed: 597-637) need replacement
# Verify content
assert "Phase 1.5" in lines[597], f"Line 598: {lines[597]}"
assert "SBD: Sequential" in lines[638] or "SBD: Sequential" in lines[639], f"Line 639: {lines[638]}"

new_block = """    // -- Phase 1.5: Upwind plume-tracking with overshoot detection (steps 7-16) --
    // FIX V6: Enable concentration gradient detection + step limit
    // Key insight: if concentration DROPS while going upwind, we have passed the source
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
        
        // Check if best hit is nearby
        float bh_dx = best_hit_x_ - cx, bh_dy = best_hit_y_ - cy;
        float bh_dist = std::sqrt(bh_dx*bh_dx + bh_dy*bh_dy);
        
        if (overshoot) {
            // Passed the source! Navigate back toward best-hit position
            if (bh_dist > 0.5f) {
                float nav_step = std::min(1.0f, bh_dist * 0.5f);
                best_x = cx + nav_step * bh_dx / bh_dist;
                best_y = cy + nav_step * bh_dy / bh_dist;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1.5: OVERSHOOT! returning ({:.2f},{:.2f}) c={:.3f} d={:.2f}",
                         best_x, best_y, best_hit_conc_, bh_dist);
            } else {
                GSL_INFO("SDNBV-P1.5: OVERSHOOT near best-hit, switch to Phase 2");
            }
            return;
        } else if (bh_dist < 2.0f && best_hit_conc_ > 0.05f) {
            // Near high-concentration area, navigate toward best hit
            float nav_step = std::min(0.8f, bh_dist * 0.6f);
            best_x = cx + nav_step * bh_dx / bh_dist;
            best_y = cy + nav_step * bh_dy / bh_dist;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV-P1.5: best-hit ({:.2f},{:.2f}) c={:.3f} d={:.2f}",
                     best_x, best_y, best_hit_conc_, bh_dist);
            return;
        } else {
            // Normal upwind tracking
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
    }
"""

# Replace lines 598-638 (0-indexed 597-637 inclusive = 41 lines)
new_lines = lines[:597] + [new_block + "\n"] + lines[638:]
with open(filepath, "w") as f:
    f.writelines(new_lines)
print("PATCH SUCCESS: replaced lines 598-638 with overshoot detection")
