path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/WranfSupervisor.cpp"
with open(path) as f:
    content = f.read()

# Add ESSA retrigger mechanism after the ESSA feedback block
# Find: "if (essa.found_gas_during_spiral && essa.best_spiral_gas > 0.1)"
old_feedback = """    // FEEDBACK: ESSA spiral findings update GRACE memory
    if (essa.found_gas_during_spiral && essa.best_spiral_gas > 0.1) {
        GasMem fb{essa.best_spiral_x, essa.best_spiral_y, essa.best_spiral_gas, 0.8, input.time_sec};
        grace_memory_.push_back(fb);
    }"""

new_feedback = """    // FEEDBACK: ESSA spiral findings update GRACE memory
    if (essa.found_gas_during_spiral && essa.best_spiral_gas > 0.1) {
        GasMem fb{essa.best_spiral_x, essa.best_spiral_y, essa.best_spiral_gas, 0.8, input.time_sec};
        grace_memory_.push_back(fb);
    }

    // ESSA RETRIGGER: if ESSA is done but new high-concentration gas detected,
    // allow ESSA to fire again from updated GRACE centroid
    if (essa_done_ && senpai.gas_detected && input.gas_concentration > 0.5
        && grace.has_memory && grace.confidence > cfg_.essa_trigger_min_confidence) {
        static double last_retrigger_gas = 0;
        if (input.gas_concentration > last_retrigger_gas * 1.2 || input.gas_concentration > 2.0) {
            essa_done_ = false;
            last_retrigger_gas = input.gas_concentration;
            GSL_INFO("[WRANF-RETRIGGER] gas={:.3f} at ({:.2f},{:.2f}), allowing new ESSA cycle",
                     input.gas_concentration, input.pose_x, input.pose_y);
        }
    }"""

if old_feedback in content:
    content = content.replace(old_feedback, new_feedback)
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Added ESSA retrigger mechanism")
else:
    print("ERROR: Pattern not found")
