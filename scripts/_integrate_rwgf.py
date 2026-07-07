import re

# 1. Modify header file
hpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.hpp'
with open(hpp_path, 'r') as f:
    hpp = f.read()

# Add include
if 'RwgfSupervisor.hpp' not in hpp:
    hpp = hpp.replace(
        '#include <gsl_server/wranf/WranfSupervisor.hpp>',
        '#include <gsl_server/wranf/WranfSupervisor.hpp>\n#include <gsl_server/wranf/RwgfSupervisor.hpp>'
    )

# Add member variables after WRANF section
if 'rwgfSupervisor_' not in hpp:
    hpp = hpp.replace(
        '        int wranfStep_ = 0;',
        '        int wranfStep_ = 0;\n\n        // RWGF-UAV Supervisor\n        std::unique_ptr<uav_gsl_rwgf::RwgfSupervisor> rwgfSupervisor_;\n        int rwgfStep_ = 0;'
    )

with open(hpp_path, 'w') as f:
    f.write(hpp)
print('header modified')

# 2. Modify cpp file
cpp_path = '/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp'
with open(cpp_path, 'r') as f:
    cpp = f.read()

# Add initialization after WRANF block (find the GSL_INFO line for WRANF init)
if 'rwgfSupervisor_' not in cpp:
    rwgf_init = '''
        // RWGF-UAV Supervisor initialization
        {
            uav_gsl_rwgf::RwgfConfig rcfg;
            rcfg.enabled = pmfs->getParam<bool>("use_rwgf_supervisor", false);
            rcfg.cell_size = pmfs->getParam<double>("rwgf_cell_size", 0.3);
            rcfg.x_min = pmfs->getParam<double>("wranf_x_min", -7.6);
            rcfg.x_max = pmfs->getParam<double>("wranf_x_max", 1.2);
            rcfg.y_min = pmfs->getParam<double>("wranf_y_min", -7.9);
            rcfg.y_max = pmfs->getParam<double>("wranf_y_max", 3.5);
            rcfg.target_z = pmfs->getParam<double>("flight_height", 1.0);
            rcfg.cone_base_angle_deg = pmfs->getParam<double>("rwgf_cone_base_angle", 30.0);
            rcfg.cone_ref_wind_speed = pmfs->getParam<double>("rwgf_cone_ref_wind", 0.10);
            rcfg.cone_max_angle_deg = pmfs->getParam<double>("rwgf_cone_max_angle", 160.0);
            rcfg.hit_boost = pmfs->getParam<double>("rwgf_hit_boost", 0.15);
            rcfg.miss_decay = pmfs->getParam<double>("rwgf_miss_decay", 0.995);
            rcfg.wind_speed_threshold = pmfs->getParam<double>("rwgf_wind_threshold", 0.02);
            rcfg.nav_threshold = pmfs->getParam<double>("rwgf_nav_threshold", 0.3);
            rcfg.nav_step_size = pmfs->getParam<double>("rwgf_nav_step_size", 2.0);
            rcfg.blur_sigma = pmfs->getParam<double>("rwgf_blur_sigma", 1.0);
            rcfg.log_file = pmfs->getParam<std::string>("rwgf_log_file", "/tmp/rwgf_supervisor_log.csv");
            rwgfSupervisor_.reset(new uav_gsl_rwgf::RwgfSupervisor(rcfg));
            GSL_INFO("[RWGF] INITIALIZED enabled={} cone_base={} max_angle={} hit_boost={} nav_thr={}",
                     rcfg.enabled, rcfg.cone_base_angle_deg, rcfg.cone_max_angle_deg,
                     rcfg.hit_boost, rcfg.nav_threshold);
        }
'''
    # Find insertion point: after the WRANF init GSL_INFO line
    marker = 'GSL_INFO("[WRANF] INITIALIZED'
    idx = cpp.find(marker)
    if idx >= 0:
        # Find end of that line
        eol = cpp.find('\n', idx)
        # Find the closing brace of the WRANF block
        brace_count = 0
        block_start = cpp.rfind('{', 0, idx)
        # Actually, find the end of the WRANF initialization block
        # Look for the closing brace after the GSL_INFO
        search_start = eol
        # Find the next line that starts with just spaces and }
        next_section = cpp.find('\n        }', search_start)
        if next_section >= 0:
            insert_at = next_section + len('\n        }')
            cpp = cpp[:insert_at] + '\n' + rwgf_init + cpp[insert_at:]
            print('RWGF init added after WRANF block')
        else:
            print('WARNING: could not find WRANF block end')
    else:
        print('WARNING: could not find WRANF init marker')

    # Add RWGF processing after WRANF processing in chooseGoal
    rwgf_process = '''
        // RWGF-UAV Supervisor: independent source likelihood estimation
        if (rwgfSupervisor_ && rwgfSupervisor_->config().enabled) {
            uav_gsl_rwgf::RwgfSupervisor::Input rin;
            rin.step = rwgfStep_++;
            rin.time_sec = pmfs->node->now().seconds();
            rin.pose_x = pmfs->currentRobotPose.pose.pose.position.x;
            rin.pose_y = pmfs->currentRobotPose.pose.pose.position.y;
            rin.pose_z = pmfs->currentRobotPose.pose.pose.position.z;
            rin.backend_target_x = goal.pose.pose.position.x;
            rin.backend_target_y = goal.pose.pose.position.y;
            rin.backend_target_z = goal.pose.pose.position.z;
            rin.gas_concentration = pmfs->last_concentration;
            rin.wind_x = pmfs->last_windSpeed * std::cos(pmfs->last_windDirection);
            rin.wind_y = pmfs->last_windSpeed * std::sin(pmfs->last_windDirection);
            rin.pmfs_declared_convergence = false;
            rin.has_gt = true;
            rin.gt_source_x = pmfs->getParam<double>("ground_truth_x", 0);
            rin.gt_source_y = pmfs->getParam<double>("ground_truth_y", 0);

            uav_gsl_rwgf::RwgfOutput rout = rwgfSupervisor_->process(rin);

            if (rout.override_backend) {
                goal.pose.pose.position.x = rout.target_x;
                goal.pose.pose.position.y = rout.target_y;
                goal.pose.pose.position.z = rout.target_z;
                double r_angle = std::atan2(rout.target_y - rin.pose_y, rout.target_x - rin.pose_x);
                goal.pose.pose.orientation = Utils::createQuaternionMsgFromYaw(angles::normalize_angle(r_angle));
                GSL_INFO("[RWGF] OVERRIDE peak=({:.2f},{:.2f}) peak_val={:.4f} peak_err={:.2f} rel={:.2f} cone={:.0f} reason={}",
                         rout.peak_x, rout.peak_y, rout.peak_likelihood, rout.peak_error,
                         rout.wind_reliability, rout.cone_half_angle_deg, rout.reason);
            } else {
                GSL_INFO("[RWGF] PASS peak=({:.2f},{:.2f}) val={:.4f} err={:.2f} rel={:.2f} reason={}",
                         rout.peak_x, rout.peak_y, rout.peak_likelihood, rout.peak_error,
                         rout.wind_reliability, rout.reason);
            }
        }
'''
    # Insert after WRANF processing, before SAP
    sap_marker = '// SAP: Simulated Annealing Perturbation'
    sap_idx = cpp.find(sap_marker)
    if sap_idx >= 0:
        cpp = cpp[:sap_idx] + rwgf_process + '\n        ' + cpp[sap_idx:]
        print('RWGF processing added before SAP')
    else:
        print('WARNING: could not find SAP marker')

with open(cpp_path, 'w') as f:
    f.write(cpp)
print('cpp modified')
