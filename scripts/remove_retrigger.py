path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/WranfSupervisor.cpp"
with open(path) as f:
    content = f.read()

# Remove retrigger mechanism
old_retrigger = """
    // ESSA RETRIGGER: if ESSA is done but new high-concentration gas detected,
    // allow ESSA to fire again from updated GRACE centroid
    if (essa_done_ && senpai.gas_detected && input.gas_concentration > 0.5
        && grace.has_memory && grace.confidence > cfg_.essa_trigger_min_confidence) {
        static double last_retrigger_gas = 0;
        if (input.gas_concentration > last_retrigger_gas * 1.2 || input.gas_concentration > 2.0) {
            essa_done_ = false;
            last_retrigger_gas = input.gas_concentration;
            // GSL_INFO not available in this namespace; retrigger logged via supervisor CSV
        }
    }"""

if old_retrigger in content:
    content = content.replace(old_retrigger, "")
    with open(path, 'w') as f:
        f.write(content)
    print("OK: Removed retrigger mechanism")
else:
    print("WARN: Retrigger not found")
