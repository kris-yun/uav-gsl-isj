filepath = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(filepath) as f:
    lines = f.readlines()

# Find SBD block
sbd_start = None
func_end = None
for i, line in enumerate(lines):
    if "SBD: Sequential Bayesian Design" in line and sbd_start is None:
        sbd_start = i
    if sbd_start and i > sbd_start and "void OPGSL::computeEIGField" in line:
        func_end = i
        break

print(f"Replacing SBD block: lines {sbd_start+1} to {func_end} ({func_end - sbd_start} lines)")

new_phase2 = """    // ================================================================
    // Phase 2+ (steps 17+): Adaptive MAP/Gradient Switching
    // ================================================================
    // Auxiliary Innovation 1: Adaptive Phase Switching
    //
    // When posterior is confident (low entropy): use MAP navigation
    //   - MAP is theoretically optimal under the binary observation model
    //   - Posterior has converged, MAP is reliable
    //
    // When posterior is uncertain (high entropy): use concentration gradient
    //   - Gradient ascent is model-free and robust
    //   - Avoids MAP drift when posterior hasn't converged
    //
    // The switching threshold is calibrated from the binary observation model:
    //   - Entropy < H_threshold: posterior converged, use MAP
    //   - Entropy >= H_threshold: posterior uncertain, use gradient
    // ================================================================
    if (step_count_ >= 17) {
        // Compute posterior confidence metrics
        float H_current = posterior3d_.getEntropy();
        float H_max = std::log((float)(posterior3d_.nx_ * posterior3d_.ny_ * posterior3d_.nz_));
        float H_ratio = H_current / H_max;  // Normalized entropy in [0, 1]
        
        // FIM-based confidence check
        float eig_x, eig_y, eig_z;
        posterior3d_.getFIMEigenvalues(eig_x, eig_y, eig_z);
        float min_eig = std::min({eig_x, eig_y, eig_z});
        
        // Decision: MAP or Gradient?
        bool use_map = (H_ratio < 0.85f) && (min_eig > 0.3f);
        
        if (use_map) {
            // ===== MAP Navigation (posterior confident) =====
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            float dx = map_x - cx, dy = map_y - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float nav_step = std::min(1.0f, d * 0.6f);
                best_x = cx + nav_step * dx / d;
                best_y = cy + nav_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-ADAPT: MAP ({:.2f},{:.2f}) H_ratio={:.2f} min_eig={:.3f} d={:.2f}",
                         best_x, best_y, H_ratio, min_eig, d);
            } else {
                // Near MAP, stop
                GSL_INFO("SDNBV-ADAPT: near MAP ({:.2f},{:.2f}) d={:.2f}", map_x, map_y, d);
            }
            return;
        } else {
            // ===== Concentration Gradient Ascent (posterior uncertain) =====
            // Compute gradient from recent observations
            int hist_n = obs_history_c_.size();
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
            
            // Overshoot detection for gradient mode
            float peak_c = 0.0f;
            int peak_idx = -1;
            for (int i = 0; i < hist_n; i++) {
                if (obs_history_c_[i] > peak_c) {
                    peak_c = obs_history_c_[i];
                    peak_idx = i;
                }
            }
            bool grad_overshoot = (peak_c > 0.05f && latest_gas_ < peak_c * 0.3f && peak_idx >= 0);
            
            if (grad_overshoot && peak_idx >= 0) {
                // Overshoot! Navigate back toward peak
                float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
                float dx = px - cx, dy = py - cy;
                float d = std::sqrt(dx*dx + dy*dy);
                if (d > 0.3f) {
                    float nav_step = std::min(1.0f, d * 0.5f);
                    best_x = cx + nav_step * dx / d;
                    best_y = cy + nav_step * dy / d;
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV-ADAPT: GRAD OVERSHOOT -> peak ({:.2f},{:.2f}) peak={:.3f} now={:.3f}",
                             best_x, best_y, peak_c, latest_gas_);
                }
                return;
            }
            
            if (latest_gas_ > 0.01f && grad_mag > 0.001f) {
                // Gas detected: follow gradient
                float nav_step = std::min(1.0f, std::max(0.3f, 1.0f - latest_gas_));
                best_x = cx + nav_step * grad_x / grad_mag;
                best_y = cy + nav_step * grad_y / grad_mag;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-ADAPT: GRAD ({:.2f},{:.2f}) c={:.3f} grad_mag={:.4f} H_ratio={:.2f}",
                         best_x, best_y, latest_gas_, grad_mag, H_ratio);
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
                    GSL_INFO("SDNBV-ADAPT: best-hit ({:.2f},{:.2f}) c={:.3f} d={:.2f}",
                             best_x, best_y, best_hit_conc_, d);
                }
                return;
            } else {
                // No gas: go upwind
                if (ws > 0.05f) {
                    float wn = std::sqrt(wx*wx + wy*wy);
                    best_x = cx + 0.8f * (-wx / wn);
                    best_y = cy + 0.8f * (-wy / wn);
                    clipToMapBounds(best_x, best_y);
                    GSL_INFO("SDNBV-ADAPT: UPWIND ({:.2f},{:.2f}) ws={:.2f}",
                             best_x, best_y, ws);
                }
                return;
            }
        }
    }

"""

new_lines = lines[:sbd_start] + [new_phase2] + lines[func_end:]
with open(filepath, "w") as f:
    f.writelines(new_lines)
print(f"ADAPTIVE PHASE 2 SUCCESS: replaced {func_end - sbd_start} lines")
