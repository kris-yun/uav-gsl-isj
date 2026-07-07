filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    lines = f.readlines()

# Find boundaries
sbd_start = None
func_end = None
for i, line in enumerate(lines):
    if "SBD: Sequential Bayesian Design" in line and sbd_start is None:
        sbd_start = i
    if sbd_start and i > sbd_start and "void OPGSL::computeEIGField" in line:
        func_end = i
        break

print(f"Replacing lines {sbd_start+1} to {func_end} ({func_end - sbd_start} lines)")

new_phase3 = """    // ================================================================
    // Phase 3: Concentration Gradient Ascent (steps 17+)
    // ================================================================
    // Replaces SBD/EIG-max/CUSUM/Posterior STABLE with direct gradient ascent.
    // Rationale: Bayesian posterior assumes isotropic decay (Poisson model),
    // but real gas plumes are anisotropic (wind-driven). Direct gradient
    // ascent on sensor data avoids model mismatch.
    //
    // Convergence: In a Lipschitz-continuous concentration field, gradient
    // ascent converges to local maximum at O(1/sqrt(t)) rate.
    // ================================================================
    if (step_count_ >= 17) {
        // Track concentration gradient from recent observations
        int hist_n = obs_history_c_.size();
        
        // Compute gradient direction from last N observations
        float grad_x = 0.0f, grad_y = 0.0f;
        int grad_window = std::min(6, hist_n);
        if (grad_window >= 2) {
            for (int i = hist_n - grad_window; i < hist_n - 1; i++) {
                float dc = obs_history_c_[i+1] - obs_history_c_[i];
                float ddx = obs_history_x_[i+1] - obs_history_x_[i];
                float ddy = obs_history_y_[i+1] - obs_history_y_[i];
                float dd = std::sqrt(ddx*ddx + ddy*ddy);
                if (dd > 0.01f) {
                    grad_x += dc * ddx / dd;
                    grad_y += dc * ddy / dd;
                }
            }
        }
        float grad_mag = std::sqrt(grad_x*grad_x + grad_y*grad_y);
        
        // Find peak concentration and its position
        float peak_c = 0.0f;
        int peak_idx = -1;
        for (int i = 0; i < hist_n; i++) {
            if (obs_history_c_[i] > peak_c) {
                peak_c = obs_history_c_[i];
                peak_idx = i;
            }
        }
        
        // Overshoot detection: current gas dropped below 30% of peak
        bool phase3_overshoot = (peak_c > 0.05f && latest_gas_ < peak_c * 0.3f && peak_idx >= 0);
        
        if (phase3_overshoot && peak_idx >= 0) {
            // Overshoot! Navigate back toward peak position
            float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
            float dx = px - cx, dy = py - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.0f, d * 0.5f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P3: OVERSHOOT -> peak ({:.2f},{:.2f}) peak={:.3f} now={:.3f}",
                         best_x, best_y, peak_c, latest_gas_);
            } else {
                // Near peak, do gradient ascent from here
                if (grad_mag > 0.001f) {
                    best_x = cx + 0.5f * grad_x / grad_mag;
                    best_y = cy + 0.5f * grad_y / grad_mag;
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV-P3: GRAD near peak ({:.2f},{:.2f}) grad_mag={:.4f}",
                             best_x, best_y, grad_mag);
                }
            }
            return;
        }
        
        if (latest_gas_ > 0.01f && grad_mag > 0.001f) {
            // Gas detected: follow gradient
            float nav_step = std::min(1.0f, std::max(0.3f, 1.0f - latest_gas_));
            best_x = cx + nav_step * grad_x / grad_mag;
            best_y = cy + nav_step * grad_y / grad_mag;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV-P3: GRAD ({:.2f},{:.2f}) c={:.3f} grad_mag={:.4f}",
                     best_x, best_y, latest_gas_, grad_mag);
            return;
        } else if (best_hit_conc_ > 0.01f) {
            // No current gas but have past hit: navigate toward it
            float dx = best_hit_x_ - cx, dy = best_hit_y_ - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(0.8f, d * 0.5f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P3: best-hit ({:.2f},{:.2f}) c={:.3f} d={:.2f}",
                         best_x, best_y, best_hit_conc_, d);
            }
            return;
        } else {
            // No gas detected: go upwind
            if (ws > 0.05f) {
                float wn = std::sqrt(wx*wx + wy*wy);
                float upwind_x = -wx / wn;
                float upwind_y = -wy / wn;
                best_x = cx + 0.8f * upwind_x;
                best_y = cy + 0.8f * upwind_y;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P3: UPWIND ({:.2f},{:.2f}) ws={:.2f}",
                         best_x, best_y, ws);
            }
            return;
        }
    }

"""

new_lines = lines[:sbd_start] + [new_phase3] + lines[func_end:]
with open(filepath, "w") as f:
    f.writelines(new_lines)
print(f"RESTRUCTURE SUCCESS: replaced {func_end - sbd_start} lines with Phase 3 gradient ascent")
