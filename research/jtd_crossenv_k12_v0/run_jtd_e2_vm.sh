#!/usr/bin/env bash
set -Ee -o pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$(git -C "$ROOT" branch --show-current)" == "research/jtd-crossenv-k12-confirmation-v0" ]] || exit 2
git -C "$ROOT" diff --quiet && git -C "$ROOT" diff --cached --quiet || { echo "tracked source modified" >&2; exit 2; }
mode="${1:?pass reference or target}"
[[ "$mode" == reference || "$mode" == target ]] || exit 2
python3 -m py_compile "$ROOT/research/jtd_crossenv_k12_v0/run_jtd_e2_vm.py"
source /opt/ros/humble/setup.bash
source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
export LD_LIBRARY_PATH="/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
cd "$ROOT"
python3 research/jtd_crossenv_k12_v0/run_jtd_e2_vm.py "$mode"
