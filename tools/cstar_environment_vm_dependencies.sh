#!/usr/bin/env bash
# Source only persistent ROS/message dependencies, never the broken global overlay.
set -e -o pipefail
source /opt/ros/humble/setup.bash
source /home/zyc/CTPI_ONLINE_CORE_V2_20260905/message_install/olfaction_msgs/share/olfaction_msgs/local_setup.bash
CSTAR_GADEN=/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_install
source "$CSTAR_GADEN/gaden_msgs/share/gaden_msgs/local_setup.bash"
export LD_LIBRARY_PATH="$CSTAR_GADEN/gaden_common/lib:$CSTAR_GADEN/gaden_msgs/lib:/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828/gaden_build/gaden_common/third_party/gaden_core/third_party/libbsc:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="/home/zyc/CTPI_G2_M12_SEED12_20260905/vgr_bridge_overlay_c8454d5:${PYTHONPATH:-}"
export ROS_LOCALHOST_ONLY=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
