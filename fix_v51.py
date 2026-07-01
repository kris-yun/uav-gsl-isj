path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

# Fix Phase 1: reduce step size from 2.0 to 1.2, add better direction logic
old_p1 = """    // -- Phase 1: Coarse exploration (steps 1-15) --
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
    }"""

new_p1 = """    // -- Phase 1: Coarse exploration (steps 1-12) --
    if (step_count_ <= 12) {
        float coarse_step = 1.2f;  // V5.1: reduced from 2.0 to avoid stuck
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
        // If we have gas hits, navigate toward best hit area
        if (best_hit_conc_ > 0.01f) {
            float dx = best_hit_x_ - cx, dy = best_hit_y_ - cy;
            float d = std::sqrt(dx*dx + dy*dy);
            if (d > 0.3f) {
                best_x = cx + std::min(coarse_step, d * 0.6f) * dx / d;
                best_y = cy + std::min(coarse_step, d * 0.6f) * dy / d;
                clipToMapBounds(best_x, best_y);
                GSL_INFO("SDNBV-P1: best-hit nav ({:.2f},{:.2f}) d={:.2f} c={:.3f}",
                         best_x, best_y, d, best_hit_conc_);
                return;
            }
        }
        // Downwind + slight cross-wind exploration
        if (ws > 0.05f) {
            float wn = std::sqrt(wx*wx + wy*wy);
            float down_x = wx / wn, down_y = wy / wn;
            float perp_x = -down_y, perp_y = down_x;
            float cross_offset = std::uniform_real_distribution<float>(-0.3f, 0.3f)(rng_);
            best_x = cx + coarse_step * down_x + cross_offset * perp_x;
            best_y = cy + coarse_step * down_y + cross_offset * perp_y;
        } else {
            float angle = step_count_ * 2.39996323f;
            float radius = std::min(0.8f + 0.2f * step_count_, 3.0f);
            best_x = -0.9f + radius * std::cos(angle);
            best_y = 0.15f + radius * std::sin(angle);
        }
        clipToMapBounds(best_x, best_y);
        GSL_INFO("SDNBV-P1: coarse explore ({:.2f},{:.2f}) step={}", best_x, best_y, step_count_);
        return;
    }"""

code = code.replace(old_p1, new_p1)

# Fix Phase 2: also reduce cross-wind step and improve best-hit nav
old_p2_cross = """    // Cross-wind sweep every 5 steps (less frequent in Phase 2)
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
    }"""

new_p2_cross = """    // Cross-wind sweep every 6 steps (less frequent in Phase 2)
    if (step_count_ % 6 == 0 && ws > 0.1f) {
        float wn = std::sqrt(wx*wx + wy*wy);
        if (wn > 0.01f) {
            float perp_x = -wy / wn;
            float perp_y =  wx / wn;
            float sign = (step_count_ % 12 == 0) ? 1.0f : -1.0f;
            float cross_dist = std::min(fine_step * 1.2f, 1.5f);
            best_x = cx + sign * cross_dist * perp_x;
            best_y = cy + sign * cross_dist * perp_y;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV-P2: cross-wind ({:.2f},{:.2f})", best_x, best_y);
            return;
        }
    }"""

code = code.replace(old_p2_cross, new_p2_cross)

# Fix Phase 2 best-hit nav: use 0.5f instead of 0.5f threshold (keep as is but reduce step)
old_bhnav = """    // Navigate toward best hit (concentration-guided)
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
    }"""

new_bhnav = """    // Navigate toward best hit (concentration-guided)
    if (best_hit_conc_ > 0.005f) {
        float dx = best_hit_x_ - cx, dy = best_hit_y_ - cy;
        float d = std::sqrt(dx*dx + dy*dy);
        if (d > 0.3f) {
            float nav_step = std::min(fine_step, d * 0.6f);
            best_x = cx + nav_step * dx / d;
            best_y = cy + nav_step * dy / d;
            clipToMapBounds(best_x, best_y);
            GSL_INFO("SDNBV-P2: best-hit nav ({:.2f},{:.2f}) d={:.2f} best_c={:.3f}",
                     best_x, best_y, d, best_hit_conc_);
            return;
        }
    }"""

code = code.replace(old_bhnav, new_bhnav)

with open(path, 'w') as f:
    f.write(code)

print("V5.1 fix applied: reduced Phase 1 step 2.0->1.2, added best-hit nav in P1, reduced cross-wind dist")