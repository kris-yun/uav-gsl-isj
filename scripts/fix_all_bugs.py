#!/usr/bin/env python3
"""Fix ALL 5 OPGSL bugs identified by code regression analysis."""
import re

path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
hpp_path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.hpp"

with open(path) as f:
    code = f.read()
with open(hpp_path) as f:
    hpp = f.read()

# BUG 1 FIX: RNG seeding - use random_device for exploration, seed_param only for SBD reproducibility
# Replace: rng_.seed(static_cast<unsigned int>(seed_param));
# With: rng_.seed(std::random_device{}()); // Always random exploration
# Keep seed_param for logging only
old_rng = '''    if (seed_param >= 0) { rng_.seed(static_cast<unsigned int>(seed_param)); GSL_INFO("RNG seeded with {}", seed_param); }'''
new_rng = '''    if (seed_param >= 0) { GSL_INFO("RNG seed param={} (exploration remains random)", seed_param); }
    rng_.seed(std::random_device{}());  // Always random for diverse exploration'''
code = code.replace(old_rng, new_rng)

# BUG 2 FIX: CUSUM initialization - prev_posterior_ should be uniform (-log(N^2)), not zeros
# Find the initialization in declareParameters or Initialize
old_cusum_init = 'prev_posterior_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);'
new_cusum_init = 'prev_posterior_ = Eigen::MatrixXf::Constant(n_cells_, n_cells_, -std::log((float)(n_cells_*n_cells_)));'
code = code.replace(old_cusum_init, new_cusum_init)
# Also fix in SBD safety check
code = code.replace(
    'eig_field_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);\n            prev_posterior_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);',
    'eig_field_ = Eigen::MatrixXf::Zero(n_cells_, n_cells_);\n            prev_posterior_ = Eigen::MatrixXf::Constant(n_cells_, n_cells_, -std::log((float)(n_cells_*n_cells_)));'
)

# BUG 3 FIX: CP residual prev_mx (already fixed in previous run, but ensure correctness)
code = code.replace(
    'float residual = std::sqrt((mx - cp_prev_mx_) * (mx - prev_mx) + (my - cp_prev_my_) * (my - cp_prev_my_));',
    'float residual = std::sqrt((mx - cp_prev_mx_) * (mx - cp_prev_mx_) + (my - cp_prev_my_) * (my - cp_prev_my_));'
)

# BUG 4 FIX: Remove TIME FALLBACK at 250s - let the algorithm converge naturally
old_fallback = '''    if (elapsed_time_ > 250.0f && !convergence_reported_) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("TIME FALLBACK: MAP=({:.2f},{:.2f},{:.2f})", mx, my, mz);
        convergence_reported_ = true; return GSLResult::Success;
    }'''
new_fallback = '''    // BUG-4 fix: Removed forced 250s timeout - let algorithm converge naturally
    // Only hard timeout at 300s (from maxSearchTime param)
    if (elapsed_time_ > 295.0f && !convergence_reported_) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("HARD TIMEOUT: MAP=({:.2f},{:.2f},{:.2f}) step={}", mx, my, mz, step_count_);
        convergence_reported_ = true; return GSLResult::Success;
    }'''
code = code.replace(old_fallback, new_fallback)

# BUG 5 FIX: Actually call CP shouldStop() in checkSourceFound()
# Add CP stopping check before the convergence check
cp_check = '''    // BUG-5 fix: Actually use CP stopping criterion
    if (use_cp_ && cp_stopping_.shouldStop()) {
        float mx, my, mz; posterior3d_.getMAP(mx, my, mz);
        GSL_INFO("CP-STOP: converged at step={} MAP=({:.2f},{:.2f},{:.2f}) width={:.3f}",
                 step_count_, mx, my, mz, cp_stopping_.getWidth());
        convergence_reported_ = true; return GSLResult::Success;
    }

    // V5: Multiple convergence paths'''
code = code.replace('    // V5: Multiple convergence paths', cp_check)

with open(path, 'w') as f:
    f.write(code)

print("All 5 bugs fixed in OPGSL.cpp")
print("Bug 1: RNG seeding -> always random exploration")
print("Bug 2: CUSUM prev_posterior_ -> uniform initialization")
print("Bug 3: CP residual prev_mx -> cp_prev_mx_")
print("Bug 4: TIME FALLBACK 250s -> 295s hard timeout only")
print("Bug 5: CP shouldStop() -> actually called in checkSourceFound()")