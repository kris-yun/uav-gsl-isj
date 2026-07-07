path = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/PMFS_utils.cpp"
with open(path) as f:
    content = f.read()

# 1. Remove SET gate block
old_set = """        // SET gate: require sufficient evidence before declaring convergence
        bool setPass = true;
        if (settings.movement.set_enabled)
        {
            double hit_ratio = (set_total_count > 0) ? (double)set_hit_count / set_total_count : 0.0;
            setPass = (set_total_count >= settings.movement.set_min_evidence_count &&
                       hit_ratio >= settings.movement.set_confidence_threshold &&
                       set_consecutive_hits >= settings.movement.set_consecutive_hits_required);
            if (!setPass)
                GSL_INFO("SET gate: blocking convergence (hits={}/{} ratio={:.2f} consec={})",
                         set_hit_count, set_total_count, hit_ratio, set_consecutive_hits);
        }

        if (variance < settings.declaration.threshold && megPass && wccPass && setPass)"""

new_check = """        if (variance < settings.declaration.threshold && megPass && wccPass)"""

if old_set in content:
    content = content.replace(old_set, new_check)
    print("OK: Removed SET gate")
else:
    print("WARN: SET gate pattern not found")

# 2. Remove PGPT-NAV delay block
old_pgpt = """        {
            // PGPT-NAV: Navigate to peak-gas position before declaring success
            // Forces UAV to physically visit the location with highest measured concentration
            if (!hceRefinementDone && hasPeakGas)
            {
                hceRefinedTarget.x = peakGasPosition.x;
                hceRefinedTarget.y = peakGasPosition.y;
                hceRefinedTarget.z = currentRobotPose.pose.pose.position.z;
                
                hceRefinementDone = true;
                hceRefinementActive = true;
                
                double pgptErr = sqrt(pow(resultLogging.sourcePositionGT.x - peakGasPosition.x, 2) +
                                     pow(resultLogging.sourcePositionGT.y - peakGasPosition.y, 2));
                GSL_INFO("[PGPT-NAV] Navigating to peak-gas ({:.2f},{:.2f}) err={:.3f}m before declaring",
                         peakGasPosition.x, peakGasPosition.y, pgptErr);
                
                return GSLResult::Running;
            }
            
            // If HCE refinement is done (or not applicable), declare success normally
            hceRefinementActive = false;
            saveResultsToFile(GSLResult::Success);
            return GSLResult::Success;
        }"""

new_declare = """        {
            saveResultsToFile(GSLResult::Success);
            return GSLResult::Success;
        }"""

if old_pgpt in content:
    content = content.replace(old_pgpt, new_declare)
    print("OK: Removed PGPT-NAV delay")
else:
    print("WARN: PGPT-NAV pattern not found")

with open(path, 'w') as f:
    f.write(content)

# Verify
with open(path) as f:
    c = f.read()
print(f"SET gate present: {'setPass' in c}")
print(f"PGPT-NAV present: {'PGPT-NAV' in c}")
print(f"Simple convergence: {'megPass && wccPass)' in c}")
