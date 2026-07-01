path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# ====== V5 OPTIMIZATION 1: Two-phase search in sdnbvStep ======
# Replace the entire sdnbvStep function with optimized version

old_sdnbv_start = """void OPGSL::sdnbvStep(float& best_x, float& best_y) {
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float wx = latest_wind_x_, wy = latest_wind_y_, ws = latest_wind_speed_;

    // Update 3D posterior with current observation
    if (latest_gas_ > 0.001f) {
        posterior3d_.update(cx, cy, current_altitude_, latest_gas_, wx, wy, ws);
    }

    // Bug1 fix: cross-wind exploration to break x-lock
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
    if (ws > 0.3f && gas_hit_count_ > 3 && step_count_ > 3) {
        float wn = std::sqrt(wx*wx + wy*wy);
        if (wn > 0.01f) {
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            // Bug5 fix: fuse posterior MAP with field estimator peak
            auto surge_field = field_estimator_.computeField();
            float fused_x = 0.6f * map_x + 0.4f * surge_field.peak_x;
            float fused_y = 0.6f * map_y + 0.4f * surge_field.peak_y;
            float to_map_x = fused_x - cx;
            float to_map_y = fused_y - cy;
            float to_map_d = std::sqrt(to_map_x*to_map_x + to_map_y*to_map_y);
            if (to_map_d > 0.3f) {
                best_x = cx + step_size_ * to_map_x / to_map_d;
                best_y = cy + step_size_ * to_map_y / to_map_d;
                GSL_INFO("SDNBV: surge-to-MAP ({:.2f},{:.2f}) d={:.2f}", best_x, best_y, to_map_d);
                clipToMapBounds(best_x, best_y);
                return;
            }
        }
    }

    // Get FIM eigenvalues to decide what to explore
    float eig_x, eig_y, eig_z;
    posterior3d_.getFIMEigenvalues(eig_x, eig_y, eig_z);
    float max_eig = std::max({eig_x, eig_y, eig_z});

    // NBV: select position that maximizes expected information gain
    if (use_sdnbv_ && step_count_ > 5) {
        auto nbv = posterior3d_.selectNBV(cx, cy, current_altitude_, wx, wy, ws);
        if (nbv.expected_info_gain > 0.001f) {
            best_x = nbv.x;
            best_y = nbv.y;
            GSL_INFO("SDNBV: NBV=({:.2f},{:.2f}) EIG={:.4f} FIM=({:.2f},{:.2f},{:.2f})",
                     best_x, best_y, nbv.expected_info_gain, eig_x, eig_y, eig_z);
            return;
        }
    }"""

new_sdnbv_start = """void OPGSL::sdnbvStep(float& best_x, float& best_y) {
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float wx = latest_wind_x_, wy = latest_wind_y_, ws = latest_wind_speed_;

    // Update 3D posterior with current observation
    if (latest_gas_ > 0.001f) {
        posterior3d_.update(cx, cy, current_altitude_, latest_gas_, wx, wy, ws);
    }

    // ====== V5: Two-phase search strategy ======
    // Phase 1 (steps 1-15): Coarse exploration with large steps
    // Phase 2 (steps 16+): Fine convergence with NBV + concentration guidance
    
    // -- Overshoot detection: if concentration peaked and dropped, reverse --
    bool overshoot_detected = false;
    if (obs_history_c_.size() >= 5) {
        int n = obs_history_c_.size();
        float peak_c = 0; int peak_idx = 0;
        for (int i = n-5; i < n; i++) {
            if (obs_history_c_[i] > peak_c) { peak_c = obs_history_c_[i]; peak_idx = i; }
        }
        // If peak was 2+ steps ago and current is <50% of peak -> overshoot
        if (peak_idx < n-2 && peak_c > 0.01f && latest_gas_ < peak_c * 0.5f) {
            overshoot_detected = true;
            // Navigate back toward peak position
            float px = obs_history_x_[peak_idx], py = obs_history_y_[peak_idx];
            float dx = px - cx, dy = py - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                float ret_step = std::min(1.5f, d * 0.6f);
                best_x = cx + ret_step * dx / d;
                best_y = cy + ret_step * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV: overshoot detected! returning to peak ({:.2f},{:.2f}) peak_c={:.3f}",
                         best_x, best_y, peak_c);
                return;
            }
        }
    }

    // -- Phase 1: Coarse exploration (steps 1-15) --
    if (step_count_ <= 15) {
        float coarse_step = 2.0f;  // Large steps for fast coverage
        // Cross-wind sweep every 3 steps to break x-lock
        if (step_count_ > 2 && step_count_ % 3 == 0 && ws > 0.1f) {
            float wn = std::sqrt(wx*wx + wy*wy);
            if (wn > 0.01f) {
                float perp_x = -wy / wn;
                float perp_y =  wx / wn;
                float sign = (step_count_ % 6 == 0) ? 1.0f : -1.0f;
                best_x = cx + sign * coarse_step * perp_x;
                best_y = cy + sign * coarse_step * perp_y;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1: cross-wind ({:.2f},{:.2f})", best_x, best_y);
                return;
            }
        }
        // Downwind + slight cross-wind exploration
        if (ws > 0.05f) {
            float wn = std::sqrt(wx*wx + wy*wy);
            float down_x = wx / wn, down_y = wy / wn;
            float perp_x = -down_y, perp_y = down_x;
            float cross_offset = std::uniform_real_distribution<float>(-0.5f, 0.5f)(rng_);
            best_x = cx + coarse_step * down_x + cross_offset * perp_x;
            best_y = cy + coarse_step * down_y + cross_offset * perp_y;
        } else {
            // No wind: spiral
            float angle = step_count_ * 2.39996323f;
            float radius = std::min(1.0f + 0.3f * step_count_, 4.0f);
            best_x = -0.9f + radius * std::cos(angle);
            best_y = 0.15f + radius * std::sin(angle);
        }
        clipToMapBounds(best_x, best_y);
        GSL_INFO("SDNBV-P1: coarse explore ({:.2f},{:.2f}) step={}", best_x, best_y, step_count_);
        return;
    }

    // -- Phase 2: Fine convergence (steps 16+) --
    // Adaptive step: high conc -> small step, low conc -> large step
    float fine_step;
    if (latest_gas_ > 0.1f) fine_step = 0.5f;
    else if (latest_gas_ > 0.01f) fine_step = 1.0f;
    else fine_step = 1.5f;

    // Cross-wind sweep every 5 steps (less frequent in Phase 2)
    if (step_count_ % 5 == 0 && ws > 0.1f) {
        float wn = std::sqrt(wx*wx + wy*wy);
        if (wn > 0.01f) {
            float perp_x = -wy / wn;
            float perp_y =  wx / wn;
            float sign = (step_count_ % 10 == 0) ? 1.0f : -1.0f;
            best_x = cx + sign * fine_step * 1.5f * perp_x;
            best_y = cy + sign * fine_step * 1.5f * perp_y;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV-P2: cross-wind ({:.2f},{:.2f})", best_x, best_y);
            return;
        }
    }

    // Navigate toward best hit (concentration-guided)
    if (best_hit_conc_ > 0.01f) {
        float dx = best_hit_x_ - cx, dy = best_hit_y_ - cy;
        float d = std::sqrt(dx*dx + dy*dy);
        if (d > 0.5f) {
            best_x = cx + std::min(fine_step, d * 0.7f) * dx / d;
            best_y = cy + std::min(fine_step, d * 0.7f) * dy / d;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV-P2: best-hit nav ({:.2f},{:.2f}) d={:.2f} best_c={:.3f}",
                     best_x, best_y, d, best_hit_conc_);
            return;
        }
    }

    // SURGE-CAST: if wind > 0.3 and we have hits, move toward fused target
    if (ws > 0.3f && gas_hit_count_ > 3) {
        float wn = std::sqrt(wx*wx + wy*wy);
        if (wn > 0.01f) {
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            auto surge_field = field_estimator_.computeField();
            float fused_x = 0.6f * map_x + 0.4f * surge_field.peak_x;
            float fused_y = 0.6f * map_y + 0.4f * surge_field.peak_y;
            float to_map_x = fused_x - cx;
            float to_map_y = fused_y - cy;
            float to_map_d = std::sqrt(to_map_x*to_map_x + to_map_y*to_map_y);
            if (to_map_d > 0.3f) {
                best_x = cx + fine_step * to_map_x / to_map_d;
                best_y = cy + fine_step * to_map_y / to_map_d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P2: surge ({:.2f},{:.2f}) d={:.2f}", best_x, best_y, to_map_d);
                return;
            }
        }
    }

    // NBV: select position with highest expected info gain
    float eig_x, eig_y, eig_z;
    posterior3d_.getFIMEigenvalues(eig_x, eig_y, eig_z);

    if (use_sdnbv_ && step_count_ > 15) {
        auto nbv = posterior3d_.selectNBV(cx, cy, current_altitude_, wx, wy, ws);
        if (nbv.expected_info_gain > 0.001f) {
            best_x = nbv.x;
            best_y = nbv.y;
            GSL_INFO("SDNBV-P2: NBV=({:.2f},{:.2f}) EIG={:.4f}", best_x, best_y, nbv.expected_info_gain);
            return;
        }
    }"""

code = code.replace(old_sdnbv_start, new_sdnbv_start)

# ====== V5 OPTIMIZATION 2: Better convergence ======
old_convergence = """GSLResult OPGSL::checkSourceFound() {
    if (elapsed_time_ < convergence_min_time_) return GSLResult::Running;
    if (gas_hit_count_ < convergence_min_bouts_) return GSLResult::Running;
    if (step_count_ < 30) return GSLResult::Running;

    auto field = field_estimator_.computeField();
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    // Use posterior MAP for convergence check
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    float dx = map_x - cx, dy = map_y - cy;
    float dist_to_peak = std::sqrt(dx*dx + dy*dy);
    float dz = std::abs(map_z - current_altitude_);
    bool near_peak = dist_to_peak < 2.0f;
    bool entropy_low = field.field_entropy < convergence_entropy_threshold_;
    bool z_stable = dz < 1.5f;

    if (near_peak && entropy_low && z_stable) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }

    if (stable_steps_count_ >= convergence_stable_steps_) {
        GSL_INFO("OPGSL-SDNBV CONVERGED: entropy={:.2f} dist={:.2f} z_dist={:.2f} hits={} step={}",
                 field.field_entropy, dist_to_peak, dz, gas_hit_count_, step_count_);
        return GSLResult::Success;
    }
    if (step_count_ >= 500) return GSLResult::Failure;
    return GSLResult::Running;
}"""

new_convergence = """GSLResult OPGSL::checkSourceFound() {
    // V5: Relaxed early constraints for faster convergence
    if (elapsed_time_ < 15.0f) return GSLResult::Running;
    if (gas_hit_count_ < 3) return GSLResult::Running;
    if (step_count_ < 15) return GSLResult::Running;

    auto field = field_estimator_.computeField();
    float cx = currentRobotPosition.x, cy = currentRobotPosition.y;
    float map_x, map_y, map_z;
    posterior3d_.getMAP(map_x, map_y, map_z);
    float dx = map_x - cx, dy = map_y - cy;
    float dist_to_peak = std::sqrt(dx*dx + dy*dy);
    float dz = std::abs(map_z - current_altitude_);

    // V5: Multiple convergence paths
    bool near_map = dist_to_peak < 1.5f;
    bool near_best_hit = std::sqrt((best_hit_x_-cx)*(best_hit_x_-cx) + (best_hit_y_-cy)*(best_hit_y_-cy)) < 1.0f;
    bool entropy_low = field.field_entropy < convergence_entropy_threshold_;
    bool z_ok = dz < 1.0f;
    bool high_conc = best_hit_conc_ > 0.3f;

    // Path A: near MAP + low entropy + stable z
    // Path B: near best hit + high concentration + low entropy
    bool converged = (near_map && entropy_low && z_ok) || (near_best_hit && high_conc && entropy_low);

    if (converged) {
        stable_steps_count_++;
    } else {
        stable_steps_count_ = 0;
    }

    // V5: fewer stable steps needed (3 vs 5)
    if (stable_steps_count_ >= 3) {
        GSL_INFO("OPGSL-SDNBV CONVERGED: entropy={:.2f} dist={:.2f} z_dist={:.2f} hits={} step={} best_c={:.3f}",
                 field.field_entropy, dist_to_peak, dz, gas_hit_count_, step_count_, best_hit_conc_);
        return GSLResult::Success;
    }
    // V5: fast exit if high concentration and near source area
    if (step_count_ >= 20 && best_hit_conc_ > 0.5f && near_best_hit) {
        GSL_INFO("OPGSL-SDNBV FAST EXIT: best_c={:.3f} near_hit={} step={}", best_hit_conc_, near_best_hit, step_count_);
        return GSLResult::Success;
    }
    if (step_count_ >= 300) return GSLResult::Failure;
    return GSLResult::Running;
}"""

code = code.replace(old_convergence, new_convergence)

with open(path, 'w') as f:
    f.write(code)

print("V5 optimization applied: two-phase search + overshoot detection + better convergence")