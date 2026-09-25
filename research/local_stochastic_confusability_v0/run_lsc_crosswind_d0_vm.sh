#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
[[ "$(git branch --show-current)" == "research/lsc-crosswind-d0-v0" ]] || { echo "wrong branch" >&2; exit 2; }
git diff --quiet && git diff --cached --quiet || { echo "tracked source modified" >&2; exit 2; }

R="$ROOT/research/local_stochastic_confusability_v0"
E="$ROOT/evidence/local_stochastic_confusability_v0/crosswind_d0"
DATA="/home/zyc/lsc_crosswind_d0_128_runs_20260925"
CANONICAL="/mnt/hgfs/workspace/GADEN_files/scenarios"
GATE1A="/home/zyc/bigreen_gate1a_exact_20260924"
BUILD="/home/zyc/hcmc_gaden_seed_build_20260922"
BINARY="$BUILD/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
EXTRACTOR="/home/zyc/rmfe_filament_extractor_omp"
OCC="$CANONICAL/House02/OccupancyGrid3D.csv"
CONTRACT="$GATE1A/gate1a_contract.json"
SOURCE_BANK="$GATE1A/source_bank.tsv"
PANEL="/home/zyc/cess_d1r_reference_repo_20260925/evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv"
W0="/home/zyc/CESS_D1R_REFERENCE_REVIEW_20260925/data/reference_168x16x10x30.npy"
WINVENTORY="$ROOT/evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json"
ITERS=(100 150 200 250 300 350 400 450 500 550)

check_sha() {
  local got
  [[ -f "$1" ]] || { echo "missing: $1" >&2; exit 3; }
  got="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$got" == "$2" ]] || { echo "hash drift: $1 got=$got expected=$2" >&2; exit 4; }
}
check_sha "$BINARY" 4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1
check_sha "$EXTRACTOR" 206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91
check_sha "$OCC" 9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d
check_sha "$SOURCE_BANK" 0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb
check_sha "$CONTRACT" 68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334
check_sha "$PANEL" 5df11712dd0e7dbef6e454c8d146427407644b9f27245c447479185ab2129d8e
check_sha "$W0" b21a089cb015ace71a448db58bd7a2f1fee25e9a8431cbb56728f48ca39573d9
check_sha "$WINVENTORY" dec3b877783b606fc3bd1fceaa06acb32e6616b2cae2d2f2e2f7f52fc4ed71fb

mkdir -p "$DATA" "$E"
python3 - "$PANEL" "$W0" "$WINVENTORY" "$E" "$DATA" <<'PY'
import hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0,str(Path(sys.argv[4]).parents[2]/"research/local_stochastic_confusability_v0"))
import analyze_lsc_crosswind_d0 as a
panel=pd.read_csv(sys.argv[1],sep="\t")
assert len(panel)==168 and panel.source_id.nunique()==168
ids=a.SOURCE_IDS
p=panel.set_index("source_id").loc[ids].reset_index()
assert p.pmfs_i.tolist()==[9,10,11,12,9,10,11,12]
assert p.pmfs_j.tolist()==[15]*4+[16]*4
assert np.allclose(p.z_m.to_numpy(),0.20)
p.insert(0,"source_index",range(8))
e=Path(sys.argv[4]); d=Path(sys.argv[5])
p.to_csv(e/"LSC_CROSSWIND_D0_SOURCE_PANEL.tsv",sep="\t",index=False)
p[["source_index","source_id","x_m","y_m","z_m"]].to_csv(d/"source_rows.tsv",sep="\t",index=False,header=False)
w0=np.load(sys.argv[2],allow_pickle=False)
assert w0.shape==(168,16,10,30) and np.isfinite(w0).all() and (w0>=0).all()
x=a.subset_w0(w0,panel)[:,:8]
edges=a.edges_from_panel(p)
aa=a.one_direction(x,edges,np.arange(4),np.arange(4,8))
bb=a.one_direction(x,edges,np.arange(4,8),np.arange(4))
stable=float(spearmanr(aa["energy"],bb["energy"])[0])
assert abs(stable-0.697)<0.01 and abs(aa["rho_energy_error"]+0.369)<0.01 and abs(bb["rho_energy_error"]+0.557)<0.01
(e/"LSC_CROSSWIND_D0_W0_PREFLIGHT.json").write_text(json.dumps({
  "rho_split_energy":stable,"rho_A":aa["rho_energy_error"],"rho_B":bb["rho_energy_error"],
  "w0_sha256":hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest(),
  "source_panel_sha256":hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()},indent=2)+"\n")
inv=json.load(open(sys.argv[3]))["houses"]["House02"]["wind_configs"]
rows=[]; paths=[]
for wi,name in enumerate(("3,5-1_fast","4,5-3_slow")):
    w=inv[name]; path=Path(w["path"])
    assert len(w["iteration_records"])==11
    for r in w["iteration_records"]:
        f=path/r["name"]
        assert f.stat().st_size==r["size_bytes"],f
        assert hashlib.sha256(f.read_bytes()).hexdigest()==r["sha256"],f
        rows.append((wi,name,str(f),r["sha256"],r["size_bytes"]))
    paths.append((wi,name,str(path),w["iteration_records"][1]["sha256"]))
pd.DataFrame(rows,columns=["wind_index","wind","path","sha256","bytes"]).to_csv(e/"LSC_CROSSWIND_D0_WIND_HASHES.tsv",sep="\t",index=False)
pd.DataFrame(paths).to_csv(d/"wind_rows.tsv",sep="\t",index=False,header=False)
print("PREFLIGHT_PASS W0_anchor",stable,aa["rho_energy_error"],bb["rho_energy_error"])
PY

set +u
source /opt/ros/humble/setup.bash
source "$BUILD/install/setup.bash"
set -u
export LD_LIBRARY_PATH="$BUILD/build/gaden_common/third_party/gaden_core/third_party/libbsc:$BUILD/install/gaden_common/lib:${LD_LIBRARY_PATH:-}"

inventory="$E/LSC_CROSSWIND_D0_ARTIFACT_SHA256.tsv"
printf 'wind_index\twind\tsource_index\tsource_id\treplicate\trng_seed\tconcentration_sha256\tpooled_sha256\n' > "$inventory"

while IFS=$'\t' read -r wi wind windpath wind1sha; do
  while IFS=$'\t' read -r si source_id sx sy sz; do
    for rep in $(seq 1 8); do
      seed=$((2026110000 + 64*wi + 8*si + rep))
      work="$DATA/$wind/$source_id/rep_$(printf '%02d' "$rep")_seed_$seed"
      real="$work/realization"; spatial="$work/spatial"; pooled="$work/pooled.npy"
      mkdir -p "$work"
      valid=0
      if [[ -f "$spatial/concentration.npy" && -f "$pooled" && -f "$work/manifest.tsv" ]]; then
        if python3 - "$spatial/concentration.npy" "$pooled" "$work/manifest.tsv" \
          "$wi" "$wind" "$windpath" "$wind1sha" "$si" "$source_id" "$rep" "$seed" <<'PY' >/dev/null 2>&1
import sys,numpy as np
c=np.load(sys.argv[1],allow_pickle=False); p=np.load(sys.argv[2],allow_pickle=False)
assert c.shape==(10,83,119) and p.shape==(10,30)
assert np.isfinite(c).all() and np.isfinite(p).all() and (c>=0).all() and (p>=0).all()
d={}
for line in open(sys.argv[3]):
    k,v=line.rstrip("\n").split("\t",1); d[k]=v
keys=("wind_index","wind","wind_path","wind_iteration1_sha256","source_index","source_id","replicate","rng_seed")
for k,v in zip(keys,sys.argv[4:]): assert d.get(k)==v,(k,d.get(k),v)
assert d.get("house")=="House02"
assert d.get("binary_sha256")=="4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
assert d.get("occupancy_sha256")=="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
assert d.get("extractor_sha256")=="206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"
assert d.get("gate1a_contract_sha256")=="68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334"
PY
        then valid=1; fi
      fi
      if [[ "$valid" -eq 0 ]]; then
        rm -rf "$real" "$spatial" "$pooled"
        mkdir -p "$real" "$spatial"
        ln -s "$OCC" "$real/OccupancyGrid3D.csv"
        echo "RUN wind=$wind source=$source_id rep=$rep seed=$seed"
        env GADEN_RNG_SEED="$seed" "$BINARY" --ros-args \
          -p verbose:=false -p wait_preprocessing:=false \
          -p sim_time:=300.0 -p time_step:=0.1 \
          -p num_filaments_sec:=7 -p variable_rate:=true -p filament_stop_steps:=0 \
          -p ppm_filament_center:=10.0 -p filament_initial_std:=10.0 \
          -p filament_growth_gamma:=15.0 -p filament_noise_std:=0.01 \
          -p gas_type:=10 -p temperature:=298.0 -p pressure:=1.0 \
          -p concentration_unit_choice:=1 -p occupancy3D_data:="$OCC" \
          -p fixed_frame:=map -p wind_data:="$windpath" -p wind_time_step:=1.0 \
          -p allow_looping:=true -p loop_from_step:=1 -p loop_to_step:=10 \
          -p source_position_x:="$sx" -p source_position_y:="$sy" -p source_position_z:="$sz" \
          -p save_results:=1 -p results_time_step:=0.5 -p results_min_time:=0.0 \
          -p writeConcentrations:=false -p results_location:="$real" \
          >"$work/generation.log" 2>&1
        grep -q 'Filament simulator finished correctly!' "$work/generation.log" || exit 20
        [[ "$(find "$real" -maxdepth 1 -type f -name 'iteration_*' | wc -l)" -eq 566 ]] || exit 21
        [[ -e "$real/OccupancyGrid3D.csv" ]] || ln -s "$OCC" "$real/OccupancyGrid3D.csv"
        "$EXTRACTOR" "$real" "$real" "$spatial/concentration.npy" "$spatial/metadata.json" \
          "-5.39273" "-7.45088" "0.1" "1" "0.20" "83" "119" "${ITERS[@]}" \
          >"$work/extract.log" 2>&1
        python3 - "$spatial/concentration.npy" "$CONTRACT" "$pooled" <<'PY'
import sys,json,numpy as np
cube=np.load(sys.argv[1],allow_pickle=False); c=json.load(open(sys.argv[2]))
v=[]
for p in c["probe_points"]:
    x0,x1=int(p["native_x0"]),int(p["native_x1_exclusive"])
    y0,y1=int(p["native_y0"]),int(p["native_y1_exclusive"])
    v.append(cube[:,x0:x1,y0:y1].mean(axis=(1,2)))
a=np.stack(v,axis=1).astype(np.float64)
assert a.shape==(10,30) and np.isfinite(a).all() and (a>=0).all()
np.save(sys.argv[3],a,allow_pickle=False)
PY
        printf 'wind_index\t%s\nwind\t%s\nwind_path\t%s\nwind_iteration1_sha256\t%s\nsource_index\t%s\nsource_id\t%s\nsource_xyz_m\t%s,%s,%s\nreplicate\t%s\nrng_seed\t%s\nhouse\tHouse02\nbinary_sha256\t%s\noccupancy_sha256\t%s\nextractor_sha256\t%s\ngate1a_contract_sha256\t%s\n' \
          "$wi" "$wind" "$windpath" "$wind1sha" "$si" "$source_id" "$sx" "$sy" "$sz" "$rep" "$seed" \
          4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1 \
          9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d \
          206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91 \
          68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334 \
          > "$work/manifest.tsv"
        rm -rf "$real"
      fi
      csha="$(sha256sum "$spatial/concentration.npy" | awk '{print $1}')"
      psha="$(sha256sum "$pooled" | awk '{print $1}')"
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$wi" "$wind" "$si" "$source_id" "$rep" "$seed" "$csha" "$psha" >> "$inventory"
    done
  done < "$DATA/source_rows.tsv"
done < "$DATA/wind_rows.tsv"

python3 - "$inventory" "$DATA" "$E" "$PANEL" "$W0" "$R/analyze_lsc_crosswind_d0.py" <<'PY'
import sys,subprocess
from pathlib import Path
import numpy as np,pandas as pd
inv=pd.read_csv(sys.argv[1],sep="\t"); root=Path(sys.argv[2]); e=Path(sys.argv[3])
assert len(inv)==128 and inv.rng_seed.nunique()==128
assert inv.groupby(["wind_index","source_index"]).size().eq(8).all()
assert inv.rng_seed.min()==2026110001 and inv.rng_seed.max()==2026110128
for wi,name,label in ((0,"3,5-1_fast","W1"),(1,"4,5-3_slow","W2")):
    x=[]
    for sid in ("pmfs_9_15","pmfs_10_15","pmfs_11_15","pmfs_12_15",
                "pmfs_9_16","pmfs_10_16","pmfs_11_16","pmfs_12_16"):
        a=[]
        for rep in range(1,9):
            si=len(x); seed=2026110000+64*wi+8*si+rep
            a.append(np.load(root/name/sid/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy",allow_pickle=False))
        x.append(np.stack(a))
    z=np.stack(x)
    assert z.shape==(8,8,10,30) and np.isfinite(z).all() and (z>=0).all()
    np.save(e/f"LSC_CROSSWIND_D0_{label}_8x8x10x30.npy",z,allow_pickle=False)
cmd=["python3",sys.argv[6],"--w0",sys.argv[5],"--panel",sys.argv[4],
     "--w1",str(e/"LSC_CROSSWIND_D0_W1_8x8x10x30.npy"),
     "--w2",str(e/"LSC_CROSSWIND_D0_W2_8x8x10x30.npy"),
     "--out",str(e/"LSC_CROSSWIND_D0_RESULT.json")]
subprocess.run(cmd,check=True)
PY

python3 - "$E/LSC_CROSSWIND_D0_RESULT.json" "$E/LSC_CROSSWIND_D0_DECISION.md" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); w=d["winds"]; p=d["pooled"]; g=d["gates"]
lines=["# LSC Cross-Wind D0 integrity and decision","",
       f"Decision: `{g['decision']}`","",
       "Frozen W0 anchor reproduced before W1/W2 scoring.","",
       f"W0 split/A/B rho: {w['W0_D1R_anchor']['rho_split_energy']:.9f}, "
       f"{w['W0_D1R_anchor']['A']['rho_energy_error']:.9f}, "
       f"{w['W0_D1R_anchor']['B']['rho_energy_error']:.9f}.","",
       f"Pooled A/B rho: {p['A']['rho_energy_error']:.9f}, {p['B']['rho_energy_error']:.9f}.",
       f"Pooled split energy rho: {p['rho_split_energy']:.9f}.","",
       f"G1={g['G1']}, G2={g['G2']}, G3={g['G3']}, G4={g['G4']}.","",
       "This is a mechanism gate only; no closed-loop or cross-House claim.",""]
open(sys.argv[2],"w").write("\n".join(lines))
PY

sha256sum "$WINVENTORY" "$OCC" "$BINARY" "$EXTRACTOR" "$CONTRACT" "$SOURCE_BANK" "$PANEL" "$W0" \
  "$R/LSC_CROSSWIND_D0_PROTOCOL_20260925.md" "$R/analyze_lsc_crosswind_d0.py" "$R/run_lsc_crosswind_d0_vm.sh" \
  "$E/LSC_CROSSWIND_D0_W1_8x8x10x30.npy" "$E/LSC_CROSSWIND_D0_W2_8x8x10x30.npy" \
  "$E/LSC_CROSSWIND_D0_RESULT.json" > "$E/LSC_CROSSWIND_D0_FROZEN_SHA256.txt"
echo "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["gates"]["decision"])' "$E/LSC_CROSSWIND_D0_RESULT.json")"
