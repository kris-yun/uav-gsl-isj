with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp', 'r') as f:
    lines = f.readlines()

# Find the RWGF init block and replace it
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '// RWGF-UAV Supervisor initialization' in line:
        start_idx = i
    if start_idx and 'GSL_INFO("[RWGF] INITIALIZED' in line:
        # Find the closing brace
        for j in range(i, min(i+5, len(lines))):
            if lines[j].strip() == '}':
                end_idx = j
                break
        break

if start_idx and end_idx:
    new_block = '''        // AOC (Adaptive Override Controller) initialization
        {
            uav_gsl_rwgf::RwgfConfig rcfg;
            rcfg.enabled = pmfs->getParam<bool>("use_rwgf_supervisor", false);
            rcfg.x_min = pmfs->getParam<double>("wranf_x_min", -7.6);
            rcfg.x_max = pmfs->getParam<double>("wranf_x_max", 1.2);
            rcfg.y_min = pmfs->getParam<double>("wranf_y_min", -7.9);
            rcfg.y_max = pmfs->getParam<double>("wranf_y_max", 3.5);
            rcfg.target_z = pmfs->getParam<double>("flight_height", 1.0);
            rcfg.convergence_check_window = pmfs->getParam<int>("aoc_check_window", 10);
            rcfg.gas_hit_rate_threshold = pmfs->getParam<double>("aoc_hit_rate_thr", 0.2);
            rcfg.concentration_trend_threshold = pmfs->getParam<double>("aoc_trend_thr", -0.01);
            rcfg.min_steps_before_override = pmfs->getParam<int>("aoc_min_steps", 5);
            rcfg.override_cooldown = pmfs->getParam<double>("aoc_cooldown", 5.0);
            rcfg.explore_step_size = pmfs->getParam<double>("aoc_explore_step", 3.0);
            rcfg.crosswind_explore_dist = pmfs->getParam<double>("aoc_crosswind_dist", 4.0);
            rcfg.log_file = pmfs->getParam<std::string>("rwgf_log_file", "/tmp/rwgf_supervisor_log.csv");
            rwgfSupervisor_.reset(new uav_gsl_rwgf::RwgfSupervisor(rcfg));
            GSL_INFO("[AOC] INITIALIZED enabled={} window={} hit_thr={} trend_thr={}",
                     rcfg.enabled, rcfg.convergence_check_window,
                     rcfg.gas_hit_rate_threshold, rcfg.concentration_trend_threshold);
        }
'''
    lines[start_idx:end_idx+1] = [new_block]
    
    with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp', 'w') as f:
        f.writelines(lines)
    print(f'Replaced lines {start_idx+1}-{end_idx+1}')
else:
    print(f'Block not found: start={start_idx}, end={end_idx}')
