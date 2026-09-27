#!/usr/bin/env bash
set -Ee -o pipefail
printf 'RMFE_CONFIGURATION_SCRIPT_PATHS\n'
find /home/zyc -maxdepth 3 -type f \( -name '*rmfe*.py' -o -name '*rmfe*.sh' -o -name '*basic*sim*.py' -o -name '*basic*sim*.cpp' -o -name '*house123*.sh' \) 2>/dev/null | sed -n '1,65p'
printf 'OFFICIAL_BASIC_SIMULATION_FILES\n'
find /home/zyc/native_pmfs_recovery_v1 /home/zyc/ros2_ws/src -maxdepth 9 -type f \( -name '*Basic*' -o -name '*basic_sim*' -o -name '*basicSim*' -o -name '*basic_simulation*' \) 2>/dev/null | sed -n '1,55p'
printf 'NAV_SPEED_SETTINGS\n'
grep -n -E 'max_vel_x|max_speed_xy|desired_linear_vel|robot_speed|speed|velocity|initial|start' /home/zyc/ros2_ws/src/GSL/Environment_config/PMFS/navigation_config/simulation_base.py /home/zyc/ros2_ws/src/GSL/Environment_config/PMFS/navigation_config/nav2_params.yaml /home/zyc/ros2_ws/src/GSL/Environment_config/PMFS/scenarios/D/basicSim/D1.yaml
printf 'FROZEN_RUN_CONFIGURATION_FILENAMES\n'
find /home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H03_seed0/off -maxdepth 2 -type f | grep -v -E 'gas|concentration|snapshot|result|trace|report|diagnostic|estimate|score|trajectory|log' | sed -n '1,60p'
