with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp', 'r') as f:
    lines = f.readlines()

# Find the RWGF processing block and replace it
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '// RWGF-UAV Supervisor: independent source likelihood estimation' in line:
        start_idx = i
    if start_idx and 'RWGF' in line and 'reason)' in line:
        # Find the closing brace
        for j in range(i, min(i+5, len(lines))):
            if lines[j].strip() == '}':
                end_idx = j
                break
        break

if start_idx and end_idx:
    new_block = '''        // AOC (Adaptive Override Controller): detect PMFS failure and intervene
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

            uav_gsl_rwgf::RwgfOutput rout = rwgfSupervisor_->process(rin);

            if (rout.override_backend) {
                goal.pose.pose.position.x = rout.target_x;
                goal.pose.pose.position.y = rout.target_y;
                goal.pose.pose.position.z = rout.target_z;
                double r_angle = std::atan2(rout.target_y - rin.pose_y, rout.target_x - rin.pose_x);
                goal.pose.pose.orientation = Utils::createQuaternionMsgFromYaw(angles::normalize_angle(r_angle));
                GSL_INFO("[AOC] OVERRIDE hit_rate={:.2f} avg_conc={:.4f} trend={:.4f} n_hits={} reason={}",
                         rout.gas_hit_rate, rout.avg_concentration, rout.concentration_trend,
                         rout.n_gas_hits, rout.reason);
            } else {
                GSL_INFO("[AOC] PASS hit_rate={:.2f} avg_conc={:.4f} trend={:.4f} reason={}",
                         rout.gas_hit_rate, rout.avg_concentration, rout.concentration_trend,
                         rout.reason);
            }
        }
'''
    lines[start_idx:end_idx+1] = [new_block]
    
    with open('/home/zyc/ros2_ws/src/GSL/gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp', 'w') as f:
        f.writelines(lines)
    print(f'Replaced processing block lines {start_idx+1}-{end_idx+1}')
else:
    print(f'Block not found: start={start_idx}, end={end_idx}')
