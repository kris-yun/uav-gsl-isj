#!/usr/bin/env python3
"""Merge WRANF integration into original MovingStatePMFS.cpp"""
import re

# Read original
with open("/home/zyc/gsl_ws/src/GasSourceLocalization/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp") as f:
    orig = f.read()

# Read the modified version (with WRANF + HCE + FRG + ADC)
with open("/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp.before_restore") as f:
    modified = f.read()

# Extract WRANF initialization block (lines 47-89 from modified)
wranf_init = """        // WRANF Supervisor initialization (SENPAI + GRACE/WRM + ESSA)
        {
            uav_gsl_wranf::Config wcfg;
            wcfg.enabled = pmfs->getParam<bool>("use_wranf_supervisor", false);
            wcfg.target_z = pmfs->getParam<double>("flight_height", 1.0);

            wcfg.senpai_enabled = pmfs->getParam<bool>("wranf_senpai_enabled", true);
            wcfg.senpai_window = pmfs->getParam<int>("wranf_senpai_window", 20);
            wcfg.senpai_snr_threshold = pmfs->getParam<double>("wranf_senpai_snr_threshold", 2.0);
            wcfg.senpai_min_threshold = pmfs->getParam<double>("wranf_senpai_min_threshold", 0.01);
            wcfg.senpai_decay = pmfs->getParam<double>("wranf_senpai_decay", 0.95);

            wcfg.grace_enabled = pmfs->getParam<bool>("wranf_grace_enabled", true);
            wcfg.grace_max_points = pmfs->getParam<int>("wranf_grace_max_points", 50);
            wcfg.grace_concentration_weight = pmfs->getParam<double>("wranf_grace_conc_weight", 2.0);
            wcfg.grace_snr_weight_factor = pmfs->getParam<double>("wranf_grace_snr_factor", 1.5);
            wcfg.grace_recency_half_life = pmfs->getParam<double>("wranf_grace_half_life", 30.0);
            wcfg.grace_navigate_threshold = pmfs->getParam<double>("wranf_grace_nav_threshold", 0.5);
            wcfg.grace_step_size = pmfs->getParam<double>("wranf_grace_step_size", 2.0);

            wcfg.grace_use_wrm = pmfs->getParam<bool>("wranf_grace_use_wrm", false);
            wcfg.wrm_max_iterations = pmfs->getParam<int>("wranf_wrm_max_iterations", 20);
            wcfg.wrm_convergence_tol = pmfs->getParam<double>("wranf_wrm_convergence_tol", 0.001);

            wcfg.essa_enabled = pmfs->getParam<bool>("wranf_essa_enabled", true);
            wcfg.essa_max_steps = pmfs->getParam<int>("wranf_essa_max_steps", 15);
            wcfg.essa_start_radius = pmfs->getParam<double>("wranf_essa_start_radius", 0.8);
            wcfg.essa_radius_growth = pmfs->getParam<double>("wranf_essa_radius_growth", 0.2);
            wcfg.essa_wind_bias = pmfs->getParam<double>("wranf_essa_wind_bias", 0.6);
            wcfg.essa_trigger_dist = pmfs->getParam<double>("wranf_essa_trigger_dist", 2.5);
            wcfg.essa_trigger_min_confidence = pmfs->getParam<double>("wranf_essa_trigger_min_conf", 0.3);

            wcfg.override_cooldown = pmfs->getParam<double>("wranf_override_cooldown", 5.0);
            wcfg.override_step_size = pmfs->getParam<double>("wranf_override_step_size", 3.0);

            wcfg.x_min = pmfs->getParam<double>("wranf_x_min", -7.6);
            wcfg.x_max = pmfs->getParam<double>("wranf_x_max", 1.2);
            wcfg.y_min = pmfs->getParam<double>("wranf_y_min", -7.9);
            wcfg.y_max = pmfs->getParam<double>("wranf_y_max", 3.5);
            wcfg.log_file = pmfs->getParam<std::string>("wranf_log_file", "/tmp/wranf_supervisor_log.csv");
            wranfSupervisor_.reset(new uav_gsl_wranf::WranfSupervisor(wcfg));
            GSL_INFO("[WRANF] INITIALIZED enabled={} SENPAI={} GRACE={} WRM={} ESSA={}",
                     wcfg.enabled, wcfg.senpai_enabled, wcfg.grace_enabled,
                     wcfg.grace_use_wrm, wcfg.essa_enabled);
        }
"""

# WRANF update block (to insert before sendGoal)
wranf_update = """        // WRANF Supervisor: SENPAI -> GRACE/WRM -> ESSA pipeline
        if (wranfSupervisor_ && wranfSupervisor_->config().enabled) {
            uav_gsl_wranf::Input win;
            win.step = pmfs->iterationsCounter;
            win.time_sec = pmfs->node->now().seconds();
            win.pose_x = pmfs->currentRobotPose.pose.pose.position.x;
            win.pose_y = pmfs->currentRobotPose.pose.pose.position.y;
            win.pose_z = pmfs->currentRobotPose.pose.pose.position.z;
            win.backend_target_x = goal.pose.pose.position.x;
            win.backend_target_y = goal.pose.pose.position.y;
            win.backend_target_z = goal.pose.pose.position.z;
            win.gas_concentration = pmfs->last_concentration;
            win.wind_x = pmfs->last_windSpeed * std::cos(pmfs->last_windDirection);
            win.wind_y = pmfs->last_windSpeed * std::sin(pmfs->last_windDirection);
            win.server_variance = Utils::Variance(Grid2D<double>(pmfs->sourceProbability, pmfs->occupancy, pmfs->gridMetadata));
            win.server_iterations = pmfs->iterationsCounter;

            uav_gsl_wranf::Output wout = wranfSupervisor_->update(win);
            if (wout.override_backend) {
                goal.pose.pose.position.x = wout.target_x;
                goal.pose.pose.position.y = wout.target_y;
                goal.pose.pose.position.z = wout.target_z;
                double move_angle = std::atan2(wout.target_y - win.pose_y, wout.target_x - win.pose_x);
                goal.pose.pose.orientation = Utils::createQuaternionMsgFromYaw(angles::normalize_angle(move_angle));
                GSL_INFO("[WRANF] OVERRIDE target=({:.2f},{:.2f}) reason={} policy={}",
                         wout.target_x, wout.target_y, wout.reason, (int)wout.policy);
            }
        }

"""

# Include
include_line = '#include <gsl_server/wranf/WranfSupervisor.hpp>'

# Now do the merge on the original file
lines = orig.split('\n')
output = []

# Add include at top
for i, line in enumerate(lines):
    output.append(line)
    if '#include' in line and 'MovingStatePMFS' in line:
        output.append(include_line)

# Re-process to insert WRANF blocks
result = '\n'.join(output)

# Insert WRANF init after "void MovingStatePMFS::chooseGoalAndMove()" opening brace
# Find the function body start
# The original has: void MovingStatePMFS::chooseGoalAndMove() { ... sendGoal(goal); ... }
# We need to insert WRANF init at the beginning of the function body
# And WRANF update before each sendGoal

# Strategy: insert WRANF init right after the opening brace of chooseGoalAndMove
# Insert WRANF update before each sendGoal(goal)

result = result.replace(
    'void MovingStatePMFS::chooseGoalAndMove()\n    {',
    'void MovingStatePMFS::chooseGoalAndMove()\n    {\n' + wranf_init
)

# Insert WRANF update before every sendGoal(goal)
result = result.replace(
    '        sendGoal(goal);',
    wranf_update + '        sendGoal(goal);',
)

outpath = "/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp"
with open(outpath, 'w') as f:
    f.write(result)

# Verify
with open(outpath) as f:
    content = f.read()
    wranf_count = content.count('wranfSupervisor_')
    sendgoal_count = content.count('sendGoal(goal)')
    print(f"WRANF references: {wranf_count}")
    print(f"sendGoal calls: {sendgoal_count}")
    print(f"Total lines: {len(content.splitlines())}")
    # Check no HCE/FRG/ADC remnants
    for bad in ['hceRefinement', 'frg_recovery', 'adc_']:
        if bad in content:
            print(f"WARNING: found {bad}!")
        else:
            print(f"OK: no {bad}")
