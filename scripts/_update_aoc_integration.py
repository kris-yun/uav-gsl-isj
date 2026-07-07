with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp', 'r') as f:
    content = f.read()

# Replace the RWGF init block with AOC config
old_init = '''        // RWGF-UAV Supervisor initialization
        {
            uav_gsl_rwgf::RwgfConfig rcfg;
            rcfg.enabled = pmfs->getParam<bool>("use_rwgf_supervisor", false);
            rcfg.cell_size = pmfs->getParam<double>("rwgf_cell_size", 0.3);
            rcfg.x_min = pmfs->getParam<double>("wranf_x_min", -7.6);
            rcfg.x_max = pmfs->getParam<double>("wranf_x_max", 1.2);
            rcfg.y_min = pmfs->getParam<double>("wranf_y_min", -7.9);
            rcfg.y_max = pmfs->getParam<double>("wranf_y_max", 3.5);
            rcfg.target_z = pmfs->getParam<double>("flight_height", 1.0);
            rcfg.cone_base_angle_deg = pmfs->getParam<double>("rwgf_cone_base_angle", 15.0);
            rcfg.cone_ref_wind_speed = pmfs->getParam<double>("rwgf_cone_ref_wind", 0.10);
            rcfg.cone_max_angle_deg = pmfs->getParam<double>("rwgf_cone_max_angle", 90.0);
            rcfg.hit_boost = pmfs->getParam<double>("rwgf_hit_boost", 0.5);
            rcfg.miss_decay = pmfs->getParam<double>("rwgf_miss_decay", 0.99);
            rcfg.wind_speed_threshold = pmfs->getParam<double>("rwgf_wind_threshold", 0.02);
            rcfg.nav_threshold = pmfs->getParam<double>("rwgf_nav_threshold", 0.001);
            rcfg.nav_step_size = pmfs->getParam<double>("rwgf_nav_step_size", 1.5);
            rcfg.blur_sigma = pmfs->getParam<double>("rwgf_blur_sigma", 0.5);
            rcfg.log_file = pmfs->getParam<std::string>("rwgf_log_file", "/tmp/rwgf_supervisor_log.csv");
            rwgfSupervisor_.reset(new uav_gsl_rwgf::RwgfSupervisor(rcfg));
            GSL_INFO("[RWGF] INITIALIZED enabled={} cone_base={} max_angle={} hit_boost={} nav_thr={}",
                     rcfg.enabled, rcfg.cone_base_angle_deg, rcfg.cone_max_angle_deg,
                     rcfg.hit_boost, rcfg.nav_threshold);
        }'''

new_init = '''        // AOC (Adaptive Override Controller) initialization
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
        }'''

content = content.replace(old_init, new_init)

with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp', 'w') as f:
    f.write(content)
print('AOC integration updated')
