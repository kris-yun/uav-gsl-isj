#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -Ee -o pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export LD_LIBRARY_PATH=/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}
python3 /home/zyc/aod_house03_f1_full624_20260927/execution/prepare_amended_extraction_vm.py
python3 /home/zyc/aod_house03_f1_full624_20260927/execution/resume_amended_f1_vm.py extract
