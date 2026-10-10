#!/bin/bash
set -e
source /home/zyc/pmfs_e3_native_validation_20261009/RUN_SETUP.sh
/usr/bin/time -v /home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator --ros-args --params-file /home/zyc/pmfs_e3_native_validation_20261009/E3_generation_RESOLVED.yaml
