#!/usr/bin/env bash
set -Ee -o pipefail
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
source /home/zyc/pmfs_official_alignment_r5_20261009/ws/install/setup.bash
source /home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/setup.bash
set -u
export LD_LIBRARY_PATH=/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/install/gaden_common/lib:/home/zyc/pmfs_clean_c1_preparation_r6_20261009/ws/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}
export ROS_DOMAIN_ID=224 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
unset GADEN_RNG_SEED
task_p24=/home/zyc/ros2_ws/pmfs_official_repro_audit_20261016
export AMENT_PREFIX_PATH="${task_p24}/paper2024_overlay:${task_p24}/install_paper_pmfs_2024:${task_p24}/install_paper_gmrf_tfqualified_2024:${AMENT_PREFIX_PATH}"
export LD_LIBRARY_PATH="${task_p24}/install_paper_gmrf_tfqualified_2024/lib:${task_p24}/install_paper_pmfs_2024/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${task_p24}/install_paper_gmrf_tfqualified_2024/local/lib/python3.10/dist-packages:${task_p24}/install_paper_gmrf_tfqualified_2024/lib/python3.10/site-packages:${PYTHONPATH:-}"
exec python3 -B /mnt/hgfs/workspace/PMFS_O24_ROS_QUAL_20261018/cases/O24G_A2_R01/runtime_driver.py
