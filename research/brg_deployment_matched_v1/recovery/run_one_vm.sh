#!/usr/bin/env bash
set -Ee -o pipefail
set +u
source /opt/ros/humble/setup.bash
source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
set -u
export LD_LIBRARY_PATH="/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
python3 /home/zyc/brg_v1_recovery_20260928/acquire_continuous_vm.py "$@"
