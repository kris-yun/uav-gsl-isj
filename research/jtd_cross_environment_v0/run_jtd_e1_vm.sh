#!/usr/bin/env bash
set -Ee -o pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$(git -C "$ROOT" branch --show-current)" == "research/jtd-cross-environment-v0" ]] || { echo "wrong JTD branch" >&2; exit 2; }
git -C "$ROOT" diff --quiet && git -C "$ROOT" diff --cached --quiet || { echo "tracked source modified" >&2; exit 2; }
python3 -m py_compile "$ROOT/research/jtd_cross_environment_v0/run_jtd_e1_vm.py"
set +u
source /opt/ros/humble/setup.bash
source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
set -u
export LD_LIBRARY_PATH="/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
python3 "$ROOT/research/jtd_cross_environment_v0/run_jtd_e1_vm.py" acquire
