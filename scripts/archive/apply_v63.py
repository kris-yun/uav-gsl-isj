filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    lines = f.readlines()

# Find Phase 1.5 block
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "Phase 1.5: Upwind plume-tracking" in line and "overshoot" not in line:
        start_idx = i
    if start_idx and i > start_idx and "SBD: Sequential Bayesian Design" in line:
        end_idx = i
        break

print(f"Replacing Phase 1.5: lines {start_idx+1} to {end_idx}")

new_block = """    // -- Phase 1.5: Upwind plume-tracking with peak-based overshoot detection (steps 7-16) --
    // FIX V6.3: Use peak concentration tracking for overshoot detection
    // Peak-based: if current gas drops below 30% of peak seen during upwind, we passed source
    if (use_upwind_tracking_ && step_count_ >= 7 && step_count_ <= 16 && ws > 0.05f && gas_hit_count_ > 0) {
        // Find peak concentration from recent observations (last 8 readings)
        float peak_c = 0.0f;
        int peak_idx = -1;
        int hist_n = obs_history_c_.size();
        int lookback = std::min(8, hist_n);
        for (int i = hist_n - lookback; i < hist_n; i++) {
            if (obs_history_c_[i] > peak_c) {
                peak_c = obs_history_c_[i];
                peak_idx = i;
            }
        }
        
        // Overshoot: current gas dropped below 30% of recent peak, and peak was significant
        bool overshoot = (peak_c > 0.1f && latest_gas_ < peak_c * 0.3f && peak_idx >= 0);
        
        if (overshoot) {
            // Passed the source! Navigate back toward peak concentration position
            float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
            float dx = px - cx, dy = py - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.2f, d * 0.5f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1.5: OVERSHOOT! -> peak ({:.2f},{:.2f}) peak_c={:.3f} now={:.3f} d={:.2f}",
                         best_x, best_y, peak_c, latest_gas_, d);
            } else {
                GSL_INFO("SDNBV-P1.5: OVERSHOOT near peak ({:.2f},{:.2f}), switch Phase 2", px, py);
            }
            return;
        }
        
        // Normal upwind tracking
        float wn = std::sqrt(wx*wx + wy*wy);
        float upwind_x = -wx / wn;
        float upwind_y = -wy / wn;
        float nav_step = 0.8f;
        best_x = cx + nav_step * upwind_x;
        best_y = cy + nav_step * upwind_y;
        clipToMapBounds(best_x, best_y);
        GSL_INFO("SDNBV-P1.5: UPWIND ({:.2f},{:.2f}) ws={:.2f} c={:.3f} peak={:.3f}",
                 best_x, best_y, ws, latest_gas_, peak_c);
        return;
    }

"""

new_lines = lines[:start_idx] + [new_block] + lines[end_idx:]
with open(filepath, "w") as f:
    f.writelines(new_lines)
print("V6.3 Phase 1.5 patch applied")
