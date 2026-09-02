#!/usr/bin/env bash
set -Ee

# Frozen overlay order inherited from the predictive-bank generator.
source /opt/ros/humble/setup.bash
source /home/zyc/ros2_ws/install/setup.bash
set -uo pipefail

export OMP_NUM_THREADS=4
export OMP_DYNAMIC=FALSE
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONHASHSEED=0
export LD_LIBRARY_PATH="/opt/ros/humble/lib:/home/zyc/PF_DEI_V3_GADEN_BUILD/install/lib:/home/zyc/PF_DEI_V3_GADEN_BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"

exec python3 "$@"
