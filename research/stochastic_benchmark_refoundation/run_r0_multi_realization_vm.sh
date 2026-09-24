#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED_BRANCH="research/stochastic-benchmark-refoundation-20260924"
[[ "$(git -C "$ROOT" branch --show-current)" == "$EXPECTED_BRANCH" ]] || {
  echo "wrong branch: $(git -C "$ROOT" branch --show-current)" >&2; exit 2;
}

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/r0_stochastic_benchmark_20260924}"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"

BINARY="$BUILD_ROOT/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
OCC="$CANONICAL_ROOT/House02/OccupancyGrid3D.csv"
W2="$CANONICAL_ROOT/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

EXPECTED_BINARY_SHA="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_OCC_SHA="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W2_ITER1_SHA="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
EXPECTED_EXTRACTOR_SHA="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"

RESEARCH="$ROOT/research/stochastic_benchmark_refoundation"
EVIDENCE="$ROOT/evidence/stochastic_benchmark_refoundation/r0"
PANEL="$RESEARCH/R0_SOURCE_PANEL_18.tsv"
SEEDS="$RESEARCH/R0_SEED_MATRIX_18x16.tsv"
CONTRACT="$GATE1A_ROOT/gate1a_contract.json"
SOURCE_BANK="$GATE1A_ROOT/source_bank.tsv"
PRED_ROOT="$GATE1A_ROOT/predictions"
ITERS=(100 150 200 250 300 350 400 450 500 550)

mkdir -p "$OUT_ROOT" "$EVIDENCE"

check_sha(){
  local p="$1" e="$2" n="$3"
  [[ -e "$p" ]] || { echo "missing $n: $p" >&2; exit 3; }
  local a; a="$(sha256sum "$p" | awk '{print $1}')"
  [[ "$a" == "$e" ]] || { echo "$n hash drift: $a expected $e" >&2; exit 4; }
}
check_sha "$BINARY" "$EXPECTED_BINARY_SHA" "binary"
check_sha "$OCC" "$EXPECTED_OCC_SHA" "occupancy"
check_sha "$W2/wind_iteration_1" "$EXPECTED_W2_ITER1_SHA" "W2 iteration1"
check_sha "$EXTRACTOR" "$EXPECTED_EXTRACTOR_SHA" "extractor"

for f in "$PANEL" "$SEEDS" "$CONTRACT" "$SOURCE_BANK"; do
  [[ -f "$f" ]] || { echo "missing frozen input: $f" >&2; exit 5; }
done
for s in 2026092401 2026092402; do
  n="$(find "$PRED_ROOT/seed_$s" -maxdepth 1 -type f -name 'pmfs_*.npy' | wc -l)"
  [[ "$n" -eq 630 ]] || { echo "legacy prediction count seed $s = $n" >&2; exit 6; }
done

# Reproduce panel selection and compare source IDs / coordinates / legacy metrics.
python3 "$RESEARCH/select_r0_panel.py"   --source-bank "$SOURCE_BANK"   --prediction-root "$PRED_ROOT"   --out "$OUT_ROOT/panel_reproduced.tsv"   > "$OUT_ROOT/panel_reproduction.log"

python3 - "$PANEL" "$OUT_ROOT/panel_reproduced.tsv" "$SOURCE_BANK" "$SEEDS" <<'PY'
import sys,pandas as pd,numpy as np
p=pd.read_csv(sys.argv[1],sep="\t")
r=pd.read_csv(sys.argv[2],sep="\t")
b=pd.read_csv(sys.argv[3],sep="\t")
s=pd.read_csv(sys.argv[4],sep="\t")
assert len(p)==18 and p.source_id.nunique()==18
assert len(r)==18
assert list(p.source_id)==list(r.source_id)
for c in ["x_m","y_m","z_m","legacy_cd_rel_l2","legacy_cd_mean_mass"]:
    assert np.allclose(p[c].astype(float),r[c].astype(float),rtol=1e-9,atol=1e-9),c
assert len(s)==288 and s.rng_seed.nunique()==288
assert s.rng_seed.min()==2026093001 and s.rng_seed.max()==2026093288
assert (s.groupby("source_id").size()==16).all()
assert set(s.source_id)==set(p.source_id)
for _,x in p.iterrows():
    q=b[b.source_id==x.source_id]
    assert len(q)==1
    q=q.iloc[0]
    assert abs(float(q.x_m)-float(x.x_m))<1e-8
    assert abs(float(q.y_m)-float(x.y_m))<1e-8
    assert abs(float(q.z_m)-float(x.z_m))<1e-8
print("R0 frozen panel + seed matrix verified")
PY

set +u
source /opt/ros/humble/setup.bash
source "$BUILD_ROOT/install/setup.bash"
set -u
export LD_LIBRARY_PATH="$BUILD_ROOT/build/gaden_common/third_party/gaden_core/third_party/libbsc:$BUILD_ROOT/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

inventory="$EVIDENCE/R0_ARTIFACT_SHA256.tsv"
printf "panel_index\tsource_id\treplicate\trng_seed\tconcentration_sha256\tpooled_sha256\n" > "$inventory"

tail -n +2 "$SEEDS" | while IFS=$'\t' read -r panel_idx source_id rep seed; do
  row="$(awk -F'\t' -v id="$source_id" 'NR>1 && $2==id {print $0}' "$PANEL")"
  [[ -n "$row" ]] || { echo "source not in panel: $source_id" >&2; exit 7; }
  sx="$(echo "$row" | awk -F'\t' '{print $3}')"
  sy="$(echo "$row" | awk -F'\t' '{print $4}')"
  sz="$(echo "$row" | awk -F'\t' '{print $5}')"

  work="$OUT_ROOT/$source_id/rep_$(printf '%02d' "$rep")_seed_$seed"
  real="$work/realization"
  spatial="$work/spatial"
  pooled="$work/pooled.npy"
  mkdir -p "$work"

  valid=0
  if [[ -f "$spatial/concentration.npy" && -f "$pooled" && -f "$work/manifest.tsv" ]]; then
    if python3 - "$spatial/concentration.npy" "$pooled" <<'PY' >/dev/null 2>&1
import sys,numpy as np
c=np.load(sys.argv[1],allow_pickle=False)
p=np.load(sys.argv[2],allow_pickle=False)
assert c.shape==(10,83,119) and p.shape==(10,30)
assert np.isfinite(c).all() and np.isfinite(p).all()
assert (c>=0).all() and (p>=0).all()
PY
    then valid=1; fi
  fi

  if [[ "$valid" -eq 0 ]]; then
    rm -rf "$real" "$spatial" "$pooled"
    mkdir -p "$real" "$spatial"
    ln -s "$OCC" "$real/OccupancyGrid3D.csv"

    echo "RUN panel=$panel_idx source=$source_id rep=$rep seed=$seed xyz=$sx,$sy,$sz"
    env GADEN_RNG_SEED="$seed" "$BINARY" --ros-args       -p verbose:=false       -p wait_preprocessing:=false       -p sim_time:=300.0       -p time_step:=0.1       -p num_filaments_sec:=7       -p variable_rate:=true       -p filament_stop_steps:=0       -p ppm_filament_center:=10.0       -p filament_initial_std:=10.0       -p filament_growth_gamma:=15.0       -p filament_noise_std:=0.01       -p gas_type:=10       -p temperature:=298.0       -p pressure:=1.0       -p concentration_unit_choice:=1       -p occupancy3D_data:="$OCC"       -p fixed_frame:=map       -p wind_data:="$W2"       -p wind_time_step:=1.0       -p allow_looping:=true       -p loop_from_step:=1       -p loop_to_step:=10       -p source_position_x:="$sx"       -p source_position_y:="$sy"       -p source_position_z:="$sz"       -p save_results:=1       -p results_time_step:=0.5       -p results_min_time:=0.0       -p writeConcentrations:=false       -p results_location:="$real"       >"$work/generation.log" 2>&1

    grep -q 'Filament simulator finished correctly!' "$work/generation.log" || {
      echo "GADEN completion marker missing: $source_id rep $rep" >&2; exit 20;
    }
    n="$(find "$real" -maxdepth 1 -type f -name 'iteration_*' | wc -l)"
    [[ "$n" -eq 566 ]] || { echo "frame count $n for $source_id rep $rep" >&2; exit 21; }

    [[ -e "$real/OccupancyGrid3D.csv" ]] || ln -s "$OCC" "$real/OccupancyGrid3D.csv"

    "$EXTRACTOR"       "$real" "$real"       "$spatial/concentration.npy" "$spatial/metadata.json"       "-5.39273" "-7.45088" "0.1" "1" "0.20" "83" "119" "${ITERS[@]}"       >"$work/extract.log" 2>&1

    python3 "$RESEARCH/pool_r0_cube.py"       --cube "$spatial/concentration.npy"       --contract "$CONTRACT"       --out "$pooled"       >"$work/pool.log"

    cat > "$work/manifest.tsv" <<EOF
panel_index	$panel_idx
source_id	$source_id
source_xyz_m	$sx,$sy,$sz
replicate	$rep
rng_seed	$seed
house	House02
wind_id	W2
wind_name	3,5-1_slow
binary_sha256	$EXPECTED_BINARY_SHA
occupancy_sha256	$EXPECTED_OCC_SHA
w2_iteration1_sha256	$EXPECTED_W2_ITER1_SHA
extractor_sha256	$EXPECTED_EXTRACTOR_SHA
EOF
    rm -rf "$real"
  else
    echo "SKIP valid panel=$panel_idx source=$source_id rep=$rep seed=$seed"
  fi

  csha="$(sha256sum "$spatial/concentration.npy" | awk '{print $1}')"
  psha="$(sha256sum "$pooled" | awk '{print $1}')"
  printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$panel_idx" "$source_id" "$rep" "$seed" "$csha" "$psha" >> "$inventory"
done

[[ "$(tail -n +2 "$inventory" | wc -l)" -eq 288 ]] || {
  echo "artifact inventory incomplete" >&2; exit 22;
}

set +e
python3 "$RESEARCH/analyze_r0_stability.py"   --panel "$PANEL"   --seed-matrix "$SEEDS"   --data-root "$OUT_ROOT"   --out-dir "$EVIDENCE"   | tee "$EVIDENCE/R0_ANALYSIS_RUN.log"
rc=${PIPESTATUS[0]}
set -e

{
  echo "branch=$(git -C "$ROOT" branch --show-current)"
  echo "head=$(git -C "$ROOT" rev-parse HEAD)"
  echo "analysis_exit_code=$rc"
  echo "status:"
  git -C "$ROOT" status --short
} > "$EVIDENCE/R0_GIT_STATE.txt"

sha256sum   "$PANEL"   "$SEEDS"   "$RESEARCH/select_r0_panel.py"   "$RESEARCH/pool_r0_cube.py"   "$RESEARCH/analyze_r0_stability.py"   "$ROOT/research/stochastic_benchmark_refoundation/run_r0_multi_realization_vm.sh"   "$SOURCE_BANK"   "$CONTRACT"   "$EVIDENCE/R0_RESULT.json"   > "$EVIDENCE/R0_FROZEN_SHA256.txt"

cat "$EVIDENCE/R0_RESULT.json"
exit "$rc"
