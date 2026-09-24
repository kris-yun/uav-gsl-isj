#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED_BRANCH="research/realization-invariant-source-signature-v0"
[[ "$(git -C "$ROOT" branch --show-current)" == "$EXPECTED_BRANCH" ]] || {
  echo "wrong branch" >&2; exit 2;
}

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/mz_d3_s1_w2_20260924}"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"

BINARY="$BUILD_ROOT/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
OCC="$CANONICAL_ROOT/House02/OccupancyGrid3D.csv"
W2="$CANONICAL_ROOT/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

EXPECTED_BINARY_SHA="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_OCC_SHA="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W2_ITER1_SHA="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
EXPECTED_EXTRACTOR_SHA="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"

TRUTH_ID="pmfs_10_17"
SX="-2.242730141"
SY="-2.200880051"
SZ="0.20"
TARGET_SEEDS=(2026092301 2026092302)
TARGET_NAMES=(S1_W2_A S1_W2_B)
ITERS=(100 150 200 250 300 350 400 450 500 550)

RESEARCH="$ROOT/research/realization_invariant_source_signature_v0"
EVIDENCE="$ROOT/evidence/realization_invariant_source_signature_v0"
mkdir -p "$OUT_ROOT" "$EVIDENCE"

check_sha(){
  local p="$1" e="$2" n="$3"
  [[ -e "$p" ]] || { echo "missing $n: $p" >&2; exit 3; }
  local a; a="$(sha256sum "$p" | awk '{print $1}')"
  [[ "$a" == "$e" ]] || { echo "$n hash drift: $a" >&2; exit 4; }
}
check_sha "$BINARY" "$EXPECTED_BINARY_SHA" "binary"
check_sha "$OCC" "$EXPECTED_OCC_SHA" "occupancy"
check_sha "$W2/wind_iteration_1" "$EXPECTED_W2_ITER1_SHA" "W2 iteration1"
check_sha "$EXTRACTOR" "$EXPECTED_EXTRACTOR_SHA" "extractor"

[[ -f "$GATE1A_ROOT/source_bank.tsv" && -f "$GATE1A_ROOT/gate1a_contract.json" ]] || {
  echo "missing Gate1A contract/bank" >&2; exit 5;
}
for s in 2026092401 2026092402; do
  n="$(find "$GATE1A_ROOT/predictions/seed_$s" -maxdepth 1 -type f -name 'pmfs_*.npy' | wc -l)"
  [[ "$n" -eq 630 ]] || { echo "prediction count seed $s = $n" >&2; exit 6; }
done

python3 - "$GATE1A_ROOT/source_bank.tsv" <<'PY'
import sys,pandas as pd
p=sys.argv[1]
d=pd.read_csv(p,sep="\t")
r=d[d.source_id=="pmfs_10_17"]
assert len(r)==1
r=r.iloc[0]
assert abs(float(r.x_m)-(-2.242730141))<1e-5
assert abs(float(r.y_m)-(-2.200880051))<1e-5
assert abs(float(r.z_m)-0.20)<1e-8
print("S1 truth support verified:",r.source_id,r.x_m,r.y_m,r.z_m)
PY

set +u
source /opt/ros/humble/setup.bash
source "$BUILD_ROOT/install/setup.bash"
set -u
export LD_LIBRARY_PATH="$BUILD_ROOT/build/gaden_common/third_party/gaden_core/third_party/libbsc:$BUILD_ROOT/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

for idx in 0 1; do
  seed="${TARGET_SEEDS[$idx]}"
  name="${TARGET_NAMES[$idx]}"
  work="$OUT_ROOT/$name"
  real="$work/realization"
  spatial="$work/spatial"
  mkdir -p "$real" "$spatial"

  if [[ -f "$spatial/concentration.npy" ]]; then
    python3 - "$spatial/concentration.npy" <<'PY' >/dev/null
import sys,numpy as np
a=np.load(sys.argv[1],allow_pickle=False)
assert a.shape==(10,83,119)
assert np.isfinite(a).all() and (a>=0).all()
PY
    echo "SKIP valid $name"
    continue
  fi

  rm -rf "$real" "$spatial"
  mkdir -p "$real" "$spatial"
  ln -s "$OCC" "$real/OccupancyGrid3D.csv"

  env GADEN_RNG_SEED="$seed" "$BINARY" --ros-args     -p verbose:=false     -p wait_preprocessing:=false     -p sim_time:=300.0     -p time_step:=0.1     -p num_filaments_sec:=7     -p variable_rate:=true     -p filament_stop_steps:=0     -p ppm_filament_center:=10.0     -p filament_initial_std:=10.0     -p filament_growth_gamma:=15.0     -p filament_noise_std:=0.01     -p gas_type:=10     -p temperature:=298.0     -p pressure:=1.0     -p concentration_unit_choice:=1     -p occupancy3D_data:="$OCC"     -p fixed_frame:=map     -p wind_data:="$W2"     -p wind_time_step:=1.0     -p allow_looping:=true     -p loop_from_step:=1     -p loop_to_step:=10     -p source_position_x:="$SX"     -p source_position_y:="$SY"     -p source_position_z:="$SZ"     -p save_results:=1     -p results_time_step:=0.5     -p results_min_time:=0.0     -p writeConcentrations:=false     -p results_location:="$real"     >"$work/generation.log" 2>&1

  grep -q 'Filament simulator finished correctly!' "$work/generation.log" || {
    echo "$name GADEN completion marker missing" >&2; exit 20;
  }
  n="$(find "$real" -maxdepth 1 -type f -name 'iteration_*' | wc -l)"
  [[ "$n" -eq 566 ]] || { echo "$name frame count $n" >&2; exit 21; }

  [[ -e "$real/OccupancyGrid3D.csv" ]] || ln -s "$OCC" "$real/OccupancyGrid3D.csv"

  "$EXTRACTOR"     "$real" "$real"     "$spatial/concentration.npy" "$spatial/metadata.json"     "-5.39273" "-7.45088" "0.1" "1" "0.20" "83" "119" "${ITERS[@]}"     >"$work/extract.log" 2>&1

  python3 - "$spatial/concentration.npy" <<'PY'
import sys,numpy as np
a=np.load(sys.argv[1],allow_pickle=False)
assert a.shape==(10,83,119)
assert np.isfinite(a).all() and (a>=0).all()
print("target cube verified",sys.argv[1],float(a.sum()))
PY

  cat > "$work/manifest.tsv" <<EOF
target	$name
house	House02
source_id	$TRUTH_ID
source_xyz_m	$SX,$SY,$SZ
wind_id	W2
wind_name	3,5-1_slow
rng_seed	$seed
binary_sha256	$EXPECTED_BINARY_SHA
occupancy_sha256	$EXPECTED_OCC_SHA
w2_iteration1_sha256	$EXPECTED_W2_ITER1_SHA
extractor_sha256	$EXPECTED_EXTRACTOR_SHA
EOF

  rm -rf "$real"
done

RESULT="$EVIDENCE/D3_S1_W2_RESULT_20260924.json"
set +e
python3 "$RESEARCH/score_d3_second_source.py"   --contract "$GATE1A_ROOT/gate1a_contract.json"   --source-bank "$GATE1A_ROOT/source_bank.tsv"   --prediction-root "$GATE1A_ROOT/predictions"   --target-a "$OUT_ROOT/S1_W2_A/spatial/concentration.npy"   --target-b "$OUT_ROOT/S1_W2_B/spatial/concentration.npy"   --truth-source-id "$TRUTH_ID"   --out "$RESULT" | tee "$EVIDENCE/D3_S1_W2_RUN_20260924.log"
rc=${PIPESTATUS[0]}
set -e

{
  git -C "$ROOT" rev-parse HEAD
  sha256sum     "$RESEARCH/score_d3_second_source.py"     "$ROOT/research/realization_invariant_source_signature_v0/run_d3_s1_w2_vm.sh"     "$GATE1A_ROOT/source_bank.tsv"     "$GATE1A_ROOT/gate1a_contract.json"     "$OUT_ROOT/S1_W2_A/spatial/concentration.npy"     "$OUT_ROOT/S1_W2_B/spatial/concentration.npy"     "$RESULT"
} > "$EVIDENCE/D3_S1_W2_SHA256_20260924.txt"

cat "$RESULT"
exit "$rc"
