#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED_BRANCH="research/causal-emergent-source-scale-v0"
[[ "$(git -C "$ROOT" branch --show-current)" == "$EXPECTED_BRANCH" ]] || { echo "wrong branch" >&2; exit 2; }

BUILD_ROOT="${BUILD_ROOT:-/home/zyc/hcmc_gaden_seed_build_20260922}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
OUT_ROOT="${OUT_ROOT:-/home/zyc/cess_d1a_168x16_20260925}"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"

BINARY="$BUILD_ROOT/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
OCC="$CANONICAL_ROOT/House02/OccupancyGrid3D.csv"
W2="$CANONICAL_ROOT/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"

EXPECTED_BINARY_SHA="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_OCC_SHA="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W2_ITER1_SHA="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"
EXPECTED_EXTRACTOR_SHA="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"
EXPECTED_BANK_SHA="0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb"
EXPECTED_CONTRACT_SHA="68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334"

RESEARCH="$ROOT/research/causal_emergent_source_scale_v0"
EVIDENCE="$ROOT/evidence/causal_emergent_source_scale_v0/d1a"
SOURCE_BANK="$GATE1A_ROOT/source_bank.tsv"
CONTRACT="$GATE1A_ROOT/gate1a_contract.json"
PANEL="$EVIDENCE/CESS_D1A_PANEL_168.tsv"
HIER="$EVIDENCE/CESS_D1A_HIERARCHY.json"
MERGES="$EVIDENCE/CESS_D1A_HIERARCHY_MERGES.tsv"
ITERS=(100 150 200 250 300 350 400 450 500 550)
mkdir -p "$OUT_ROOT" "$EVIDENCE"

check_sha(){
  local p="$1" e="$2" n="$3"
  [[ -e "$p" ]] || { echo "missing $n: $p" >&2; exit 3; }
  local a; a="$(sha256sum "$p" | awk '{print $1}')"
  [[ "$a" == "$e" ]] || { echo "$n hash drift: $a expected $e" >&2; exit 4; }
}
check_sha "$BINARY" "$EXPECTED_BINARY_SHA" binary
check_sha "$OCC" "$EXPECTED_OCC_SHA" occupancy
check_sha "$W2/wind_iteration_1" "$EXPECTED_W2_ITER1_SHA" w2_iter1
check_sha "$EXTRACTOR" "$EXPECTED_EXTRACTOR_SHA" extractor
check_sha "$SOURCE_BANK" "$EXPECTED_BANK_SHA" source_bank
check_sha "$CONTRACT" "$EXPECTED_CONTRACT_SHA" gate1a_contract

# Fail fast before any GADEN generation if the frozen analysis/hierarchy
# implementation has drifted.
python3 "$RESEARCH/test_cess_d1a_weighting.py"
python3 "$RESEARCH/test_cess_d1a_hierarchy.py"

python3 "$RESEARCH/build_cess_d1a_panel.py" --source-bank "$SOURCE_BANK" --out "$PANEL"
python3 "$RESEARCH/build_cess_d1a_hierarchy.py" --panel "$PANEL" --out-json "$HIER" --merge-log "$MERGES"

python3 - "$PANEL" <<'PY'
import sys,pandas as pd
p=pd.read_csv(sys.argv[1],sep="\t")
assert len(p)==168 and p.source_id.nunique()==168
assert p.pmfs_i.min()==1 and p.pmfs_i.max()==24
assert p.pmfs_j.min()==12 and p.pmfs_j.max()==18
assert len(set(zip(p.pmfs_i,p.pmfs_j)))==168
print("D1A panel verified",len(p))
PY

set +u
source /opt/ros/humble/setup.bash
source "$BUILD_ROOT/install/setup.bash"
set -u
export LD_LIBRARY_PATH="$BUILD_ROOT/build/gaden_common/third_party/gaden_core/third_party/libbsc:$BUILD_ROOT/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

inventory="$EVIDENCE/CESS_D1A_ARTIFACT_SHA256.tsv"
printf "panel_index\tsource_id\treplicate\trng_seed\tconcentration_sha256\tpooled_sha256\n" > "$inventory"

python3 - "$PANEL" <<'PY' > "$OUT_ROOT/source_rows.tsv"
import sys,pandas as pd
p=pd.read_csv(sys.argv[1],sep="\t")
for _,r in p.iterrows():
    print(int(r.panel_index),r.source_id,repr(float(r.x_m)),repr(float(r.y_m)),repr(float(r.z_m)),sep="\t")
PY

while IFS=$'\t' read -r panel_index source_id sx sy sz; do
  for rep in $(seq 1 16); do
    seed=$((2026105000 + 16*panel_index + rep))
    work="$OUT_ROOT/$source_id/rep_$(printf '%02d' "$rep")_seed_$seed"
    real="$work/realization"; spatial="$work/spatial"; pooled="$work/pooled.npy"
    mkdir -p "$work"
    valid=0
    if [[ -f "$spatial/concentration.npy" && -f "$pooled" && -f "$work/manifest.tsv" ]]; then
      if python3 - "$spatial/concentration.npy" "$pooled" <<'PY' >/dev/null 2>&1
import sys,numpy as np
c=np.load(sys.argv[1],allow_pickle=False); p=np.load(sys.argv[2],allow_pickle=False)
assert c.shape==(10,83,119) and p.shape==(10,30)
assert np.isfinite(c).all() and np.isfinite(p).all() and (c>=0).all() and (p>=0).all()
PY
      then valid=1; fi
    fi

    if [[ "$valid" -eq 0 ]]; then
      rm -rf "$real" "$spatial" "$pooled"
      mkdir -p "$real" "$spatial"; ln -s "$OCC" "$real/OccupancyGrid3D.csv"
      echo "RUN panel=$panel_index source=$source_id rep=$rep seed=$seed"
      env GADEN_RNG_SEED="$seed" "$BINARY" --ros-args         -p verbose:=false -p wait_preprocessing:=false         -p sim_time:=300.0 -p time_step:=0.1         -p num_filaments_sec:=7 -p variable_rate:=true -p filament_stop_steps:=0         -p ppm_filament_center:=10.0 -p filament_initial_std:=10.0         -p filament_growth_gamma:=15.0 -p filament_noise_std:=0.01         -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0         -p concentration_unit_choice:=1 -p occupancy3D_data:="$OCC"         -p fixed_frame:=map -p wind_data:="$W2" -p wind_time_step:=1.0         -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10         -p source_position_x:="$sx" -p source_position_y:="$sy" -p source_position_z:="$sz"         -p save_results:=1 -p results_time_step:=0.5 -p results_min_time:=0.0         -p writeConcentrations:=false -p results_location:="$real"         >"$work/generation.log" 2>&1

      grep -q 'Filament simulator finished correctly!' "$work/generation.log" || { echo "GADEN failed $source_id rep $rep" >&2; exit 20; }
      n="$(find "$real" -maxdepth 1 -type f -name 'iteration_*' | wc -l)"
      [[ "$n" -eq 566 ]] || { echo "bad frame count $n $source_id rep $rep" >&2; exit 21; }
      [[ -e "$real/OccupancyGrid3D.csv" ]] || ln -s "$OCC" "$real/OccupancyGrid3D.csv"

      "$EXTRACTOR" "$real" "$real" "$spatial/concentration.npy" "$spatial/metadata.json"         "-5.39273" "-7.45088" "0.1" "1" "0.20" "83" "119" "${ITERS[@]}"         >"$work/extract.log" 2>&1

      python3 - "$spatial/concentration.npy" "$CONTRACT" "$pooled" <<'PY'
import sys,json,numpy as np
cube=np.load(sys.argv[1],allow_pickle=False); c=json.load(open(sys.argv[2]))
assert cube.shape==(10,83,119)
v=[]
for p in c["probe_points"]:
    x0,x1=int(p["native_x0"]),int(p["native_x1_exclusive"])
    y0,y1=int(p["native_y0"]),int(p["native_y1_exclusive"])
    v.append(cube[:,x0:x1,y0:y1].mean(axis=(1,2)))
a=np.stack(v,axis=1).astype(np.float64)
assert a.shape==(10,30) and np.isfinite(a).all() and (a>=0).all()
np.save(sys.argv[3],a,allow_pickle=False)
PY

      cat > "$work/manifest.tsv" <<EOF
panel_index	$panel_index
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
source_bank_sha256	$EXPECTED_BANK_SHA
EOF
      rm -rf "$real"
    else
      echo "SKIP valid panel=$panel_index $source_id rep=$rep seed=$seed"
    fi
    csha="$(sha256sum "$spatial/concentration.npy"|awk '{print $1}')"
    psha="$(sha256sum "$pooled"|awk '{print $1}')"
    printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$panel_index" "$source_id" "$rep" "$seed" "$csha" "$psha" >> "$inventory"
  done
done < "$OUT_ROOT/source_rows.tsv"

[[ "$(tail -n +2 "$inventory"|wc -l)" -eq 2688 ]] || { echo "inventory incomplete" >&2; exit 22; }

set +e
python3 "$RESEARCH/analyze_cess_d1a.py" --panel "$PANEL" --hierarchy-json "$HIER"   --data-root "$OUT_ROOT" --out-dir "$EVIDENCE" | tee "$EVIDENCE/CESS_D1A_ANALYSIS_RUN.log"
rc=${PIPESTATUS[0]}
set -e

{
 echo "branch=$(git -C "$ROOT" branch --show-current)"
 echo "head=$(git -C "$ROOT" rev-parse HEAD)"
 echo "analysis_exit_code=$rc"
 echo "status:"; git -C "$ROOT" status --short
} > "$EVIDENCE/CESS_D1A_GIT_STATE.txt"

sha256sum "$RESEARCH/CESS_D1A_PROTOCOL_FREEZE_20260925.md"  "$RESEARCH/build_cess_d1a_panel.py" "$RESEARCH/build_cess_d1a_hierarchy.py"  "$RESEARCH/analyze_cess_d1a.py" "$RESEARCH/test_cess_d1a_weighting.py" "$RESEARCH/test_cess_d1a_hierarchy.py" \
  "$ROOT/research/causal_emergent_source_scale_v0/run_cess_d1a_vm.sh"  "$SOURCE_BANK" "$CONTRACT" "$PANEL" "$HIER" "$EVIDENCE/CESS_D1A_RESULT.json"  > "$EVIDENCE/CESS_D1A_FROZEN_SHA256.txt"

cat "$EVIDENCE/CESS_D1A_RESULT.json"
exit "$rc"
