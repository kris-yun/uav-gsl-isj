#!/usr/bin/env python3
"""Patch V5: Always upwind when gas detected, posterior only for stopping"""
f = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(f, 'r') as fh:
    code = fh.read()

# Change decay back to 0.999 (V4's 0.99 was too aggressive)
old_decay = "    float decay = 0.99f;  // V4: stronger forgetting (half-life ~69 steps)"
new_decay = "    float decay = 0.999f;"
if old_decay in code:
    code = code.replace(old_decay, new_decay)
    print("Reverted decay to 0.999")

# Extend upwind tracking: remove step 7-16 limit
# Old: step_count_ >= 7 && step_count_ <= 16
# New: step_count_ >= 7 (no upper limit - always go upwind when gas detected)
old_cond = "if (use_upwind_tracking_ && step_count_ >= 7 && step_count_ <= 16 && ws > 0.05f) {"
new_cond = "if (use_upwind_tracking_ && step_count_ >= 7 && ws > 0.05f) {"
if old_cond in code:
    code = code.replace(old_cond, new_cond)
    print("Extended upwind tracking: removed step 16 upper limit")

with open(f, 'w') as fh:
    fh.write(code)
print("PATCH V5 APPLIED")