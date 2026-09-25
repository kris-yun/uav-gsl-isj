#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$(git -C "$ROOT" branch --show-current)" == "research/generalization-refoundation-v0" ]] || { echo "wrong branch" >&2; exit 2; }
git -C "$ROOT" diff --quiet && git -C "$ROOT" diff --cached --quiet || { echo "tracked source modified" >&2; exit 2; }
R="$ROOT/research/environment_level_benchmark_v0"
[[ -f "$ROOT/evidence/environment_level_benchmark_v0/e4b/E4B_PRE_RUN_LOCK.json" ]] || { echo "pre-run lock missing" >&2; exit 3; }
python3 -m py_compile "$R/acquire_e4b_w3_vm.py" "$R/e4b_factorial_gate.py"
set +u
source /opt/ros/humble/setup.bash
source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash
set -u
export LD_LIBRARY_PATH="/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"
python3 "$R/acquire_e4b_w3_vm.py"
python3 "$R/e4b_factorial_gate.py" score
