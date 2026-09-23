#!/usr/bin/env bash
set -Eeuo pipefail

# Reproducible remote wrapper for the preregistered one-source cost gate.
# This creates no PMFS or ROS live-loop process; it invokes the standalone
# GADEN filament simulator and stores outputs under OUT_ROOT.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARK="${BENCHMARK:-${SCRIPT_DIR}/../../evidence/causal_compositional_plume_world_model_v1/benchmark_gaden_intervention_generation.sh}"

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/c0_5_cost_benchmark_20260923}"
export OUT_ROOT

export BINARY="${BUILD_ROOT}/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
export OCCUPANCY="${CANONICAL_ROOT}/House02/OccupancyGrid3D.csv"
export WIND_DIR="${CANONICAL_ROOT}/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
export SOURCE_X="-2.242730141"
export SOURCE_Y="-2.200880051"
export SOURCE_Z="0.20"
export SEED="2026092301"

[[ -x "${BINARY}" ]] || { echo "missing generator binary: ${BINARY}" >&2; exit 2; }
[[ -f "${OCCUPANCY}" ]] || { echo "missing occupancy: ${OCCUPANCY}" >&2; exit 2; }
[[ -f "${WIND_DIR}/wind_iteration_0" ]] || { echo "missing wind field: ${WIND_DIR}" >&2; exit 2; }
[[ ! -e "${OUT_ROOT}" ]] || { echo "refuse overwrite: ${OUT_ROOT}" >&2; exit 3; }

set +u
source /opt/ros/humble/setup.bash
source "${BUILD_ROOT}/install/setup.bash"
set -u
export LD_LIBRARY_PATH="${BUILD_ROOT}/build/gaden_common/third_party/gaden_core/third_party/libbsc:${BUILD_ROOT}/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

exec bash "${BENCHMARK}"
