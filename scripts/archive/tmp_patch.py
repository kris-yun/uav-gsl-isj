#!/usr/bin/env python3
"""Adaptive fix patch for OPGSL.cpp - addresses seed variance issue"""
import re

path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path, 'r') as f:
    code = f.read()

# ============================================================
# FIX 1: Adaptive Phase 1 length (6 -> dynamic 6-12)
# If no gas detected by step 6, extend Levy exploration
# ============================================================
old_p1 = """    // -- Phase 1: Coarse downwind exploration (steps 1-6) --
    if (step_count_ <= 6) {"""
new_p1 = """    // -- Phase 1: Adaptive coarse exploration (steps 1-6, extend to 12 if no gas) --
    // FIX: If no gas detected by step 6, extend exploration to avoid directional bias
    int phase1_end = 6;
    if (gas_hit_count_ == 0 && step_count_ <= 6) {
        phase1_end = 12;  // Extend: no gas yet, keep exploring
        if (step_count_ == 6)
            GSL_INFO("SDNBV-P1: EXTENDED to step 12 (no gas detected yet)");
    }
    if (step_count_ <= phase1_end) {"""
code = code.replace(old_p1, new_p1, 1)

# ============================================================
# FIX 2: FAST EXIT requires posterior convergence, not just proximity
# Add: posterior entropy check + MAP stability check
# ============================================================
old_fast = """    // V5.2: fast exit requires MAP also near robot (not just best_hit)
    float map_dist = std::sqrt((map_x-cx)*(map_x-cx) + (map_y-cy)*(map_y-cy));
    if (step_count_ >= 20 && best_hit_conc_ > 0.05f && near_best_hit && map_dist < 2.5f) {
        GSL_INFO("OPGSL-SDNBV FAST EXIT: best_c={:.3f} near_hit={} map_dist={:.2f} step={}",
                 best_hit_conc_, near_best_hit, map_dist, step_count_);
        convergence_reported_ = true; return GSLResult::Success;
    }"""
new_fast = """    // V5.2: fast exit requires MAP also near robot (not just best_hit)
    // FIX: Also require posterior entropy below threshold to prevent premature exit
    float map_dist = std::sqrt((map_x-cx)*(map_x-cx) + (map_y-cy)*(map_y-cy));
    auto fast_field = field_estimator_.computeField();
    bool posterior_converged = fast_field.field_entropy < convergence_entropy_threshold_ * 1.2f;
    if (step_count_ >= 20 && best_hit_conc_ > 0.05f && near_best_hit && map_dist < 2.5f && posterior_converged) {
        GSL_INFO("OPGSL-SDNBV FAST EXIT: best_c={:.3f} near_hit={} map_dist={:.2f} step={} entropy={:.3f}",
                 best_hit_conc_, near_best_hit, map_dist, step_count_, fast_field.field_entropy);
        convergence_reported_ = true; return GSLResult::Success;
    }
    // If fast exit conditions met but posterior not converged, log warning
    if (step_count_ >= 20 && best_hit_conc_ > 0.05f && near_best_hit && map_dist < 2.5f && !posterior_converged) {
        GSL_INFO("OPGSL-SDNBV FAST EXIT BLOCKED: posterior not converged entropy={:.3f} thresh={:.3f}",
                 fast_field.field_entropy, convergence_entropy_threshold_ * 1.2f);
    }"""
code = code.replace(old_fast, new_fast, 1)

# ============================================================
# FIX 3: Adaptive MAP/Gradient switching with MAP drift detection
# If MAP jumps > 2m in one step, suspect posterior lock and force gradient
# ============================================================
old_adapt = """        // Decision: MAP or Gradient?
        bool use_map = (H_ratio < 0.85f) && (min_eig > 0.3f);"""
new_adapt = """        // Decision: MAP or Gradient?
        // FIX: Add MAP drift detection - if MAP jumps too fast, posterior is unstable
        static float prev_map_x = cx, prev_map_y = cy;
        float map_dx = 0, map_dy = 0;
        { float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
          map_dx = std::abs(mx - prev_map_x); map_dy = std::abs(my - prev_map_y);
          prev_map_x = mx; prev_map_y = my; }
        bool map_drift = (map_dx > 2.0f || map_dy > 2.0f);  // MAP jumped > 2m = suspicious
        bool use_map = (H_ratio < 0.85f) && (min_eig > 0.3f) && !map_drift;
        if (map_drift) {
            GSL_INFO("SDNBV-ADAPT: MAP DRIFT detected dx={:.2f} dy={:.2f} -> forcing gradient", map_dx, map_dy);
        }"""
code = code.replace(old_adapt, new_adapt, 1)

# ============================================================
# FIX 4: Adaptive Phase 1.5 extension
# If still in upwind tracking at step 16 and gas detected, extend to step 20
# ============================================================
old_p15 = """    if (use_upwind_tracking_ && step_count_ >= 7 && step_count_ <= 16 && ws > 0.05f && gas_hit_count_ > 0) {"""
new_p15 = """    // FIX: Extend Phase 1.5 if still actively tracking gas
    int phase15_end = 16;
    if (step_count_ >= 14 && step_count_ <= 16 && latest_gas_ > 0.02f) {
        phase15_end = 20;  // Still detecting gas, keep upwind tracking
        if (step_count_ == 16)
            GSL_INFO("SDNBV-P1.5: EXTENDED to step 20 (still detecting gas c={:.3f})", latest_gas_);
    }
    if (use_upwind_tracking_ && step_count_ >= 7 && step_count_ <= phase15_end && ws > 0.05f && gas_hit_count_ > 0) {"""
code = code.replace(old_p15, new_p15, 1)

with open(path, 'w') as f:
    f.write(code)

# Verify changes
with open(path, 'r') as f:
    content = f.read()
checks = [
    ("Adaptive Phase 1", "phase1_end = 12" in content),
    ("FAST EXIT entropy check", "posterior_converged" in content),
    ("MAP drift detection", "map_drift" in content),
    ("Adaptive Phase 1.5", "phase15_end = 20" in content),
]
for name, ok in checks:
    print(("PASS" if ok else "FAIL") + ": " + name)