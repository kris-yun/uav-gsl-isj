#!/usr/bin/env python3
"""Fix OPGSL.cpp bugs: CP residual, CUSUM logic, convergence."""
import re, sys

path = "/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp"
with open(path) as f:
    code = f.read()

original = code

# BUG 1: CP residual - prev_mx should be cp_prev_mx_
code = code.replace(
    'float residual = std::sqrt((mx - cp_prev_mx_) * (mx - prev_mx) + (my - cp_prev_my_) * (my - cp_prev_my_));',
    'float residual = std::sqrt((mx - cp_prev_mx_) * (mx - cp_prev_mx_) + (my - cp_prev_my_) * (my - cp_prev_my_));'
)

# BUG 2: CUSUM logic is inverted. High CUSUM = posterior still changing = should NOT trigger.
# Change: trigger when CUSUM is LOW (posterior stable) instead of HIGH.
# Replace the CUSUM check with: posterior stable when CUSUM stays low for N steps
old_cusum = '''        // 3. Check convergence via CUSUM
        if (cusum_stat_ > cusum_threshold_) {
            GSL_INFO("SBD: CUSUM triggered (stat={:.3f} > {:.1f}), posterior stabilized",
                     cusum_stat_, cusum_threshold_);
            // Posterior stabilized - move to MAP
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            best_x = map_x;
            best_y = map_y;
            clipToMapBounds(best_x, best_y);
            return;
        }'''

new_cusum = '''        // 3. Check convergence: posterior STABLE when KL change stays low
        if (kl_change < 0.01f) {
            sbd_stable_count_++;
        } else {
            sbd_stable_count_ = 0;
        }
        if (sbd_stable_count_ >= 5) {
            GSL_INFO("SBD: Posterior STABLE (kl={:.6f} stable_count={} > 5), moving to MAP",
                     kl_change, sbd_stable_count_);
            float map_x, map_y, map_z;
            posterior3d_.getMAP(map_x, map_y, map_z);
            best_x = map_x;
            best_y = map_y;
            clipToMapBounds(best_x, best_y);
            return;
        }'''

code = code.replace(old_cusum, new_cusum)

# BUG 3: CUSUM stat accumulation direction - should decrease when stable
# The current formula: cusum_stat_ = max(0, cusum_stat_ + kl_change - cusum_drift_)
# This makes CUSUM increase when KL > drift. We want to track instability.
# Keep this but also add the stable_count logic above.

# Write fixed code
with open(path, 'w') as f:
    f.write(code)

# Count changes
changes = 0
if 'prev_mx)' not in code and 'prev_mx)' in original:
    changes += 1
if 'sbd_stable_count_' in code and 'sbd_stable_count_' not in original:
    changes += 1

print(f"Fixed {changes} bugs in OPGSL.cpp")
print("Bug 1: CP residual prev_mx -> cp_prev_mx_")
print("Bug 2: CUSUM convergence logic inverted -> stable_count based")