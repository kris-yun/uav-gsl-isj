#!/usr/bin/env python3
"""Patch V5b: Upwind when gas detected, posterior when no gas"""
f = '/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/OPGSL/OPGSL.cpp'
with open(f, 'r') as fh:
    code = fh.read()

# The current condition triggers for all steps >= 7 with wind.
# Better: only go upwind when gas was recently detected.
# Replace the condition to check for recent gas hits.
old_cond = "if (use_upwind_tracking_ && step_count_ >= 7 && ws > 0.05f) {"
new_cond = "if (use_upwind_tracking_ && step_count_ >= 7 && ws > 0.05f && gas_hit_count_ > 0) {"
if old_cond in code:
    code = code.replace(old_cond, new_cond)
    print("Added gas_hit_count_ > 0 check to upwind tracking")
else:
    print("Condition not found, checking current state...")
    idx = code.find("use_upwind_tracking_ && step_count_ >= 7")
    if idx >= 0:
        print("Found at pos", idx, repr(code[idx:idx+100]))

with open(f, 'w') as fh:
    fh.write(code)
print("PATCH V5b APPLIED")