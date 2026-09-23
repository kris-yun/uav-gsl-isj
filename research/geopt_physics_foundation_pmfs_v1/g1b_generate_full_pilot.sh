#!/usr/bin/env bash
# Frozen G1-B expansion launcher. Run only after the compact proof commit.
set -Ee -o pipefail
source /opt/ros/humble/setup.bash
export LD_LIBRARY_PATH=/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_common/lib:${LD_LIBRARY_PATH:-}

SAMPLER=/tmp/m6_g1b_compact_sampler_20260923
OCC=/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv
WIND=/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind
GRID=/mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923_grid.csv
SOURCE_TABLE=/mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923_sources.csv
OUT=/mnt/hgfs/workspace/M6_G1_STAGE1_PILOT_20260923/full

test -x "$SAMPLER"
test -s "$OCC"; test -s "$GRID"; test -s "$SOURCE_TABLE"
rm -rf "$OUT"; mkdir -p "$OUT"

count=0
while IFS=, read -r split order grid_i grid_j x y z_rule clearance; do
    [[ "$split" == "split" ]] && continue
    # Strip a possible CR from a Windows-transferred CSV.
    clearance=${clearance//$'\r'/}
    source_id="${split}${order}"
    test "$z_rule" = "INHERIT_FIXED_SOURCE_PLANE_FROM_PROTOCOL"
    for seed in 2026092311 2026092312; do
        d="$OUT/$source_id/seed$seed"
        mkdir -p "$d"
        env GADEN_RNG_SEED="$seed" /usr/bin/time -v "$SAMPLER" "$OCC" "$WIND" "$GRID" "$x" "$y" 0.20 "$seed" "$source_id" "$split" "$d" >"$d/stdout.log" 2>"$d/stderr.log"
        sha256sum "$d"/* >"$d/SHA256SUMS.txt"
        test -s "$d/hit_samples_u8.bin"
        count=$((count+1))
    done
done < "$SOURCE_TABLE"

test "$count" -eq 24
find "$OUT" -mindepth 2 -maxdepth 2 -type f -name metadata.json | sort > "$OUT/METADATA_PATHS.txt"
sha256sum "$OUT/METADATA_PATHS.txt" "$GRID" "$SOURCE_TABLE" > "$OUT/MANIFEST_INPUT_HASHES.txt"
echo "G1B_FULL_GENERATION_OK cases=$count out=$OUT"
