#!/usr/bin/env bash
set -euo pipefail

# Package ONLY the pre-frozen DASN raw-field subset from the existing D1R bank.
# No GADEN execution is allowed.

OUT_ROOT="${OUT_ROOT:-/home/zyc/cess_d1r_168x16_reference_20260925}"
DEST="${DEST:-/home/zyc/DASN_RAW_FIELD_SUBSET_8x16_20260925}"
ARCHIVE="${ARCHIVE:-/home/zyc/DASN_RAW_FIELD_SUBSET_8x16_20260925.tar.gz}"

sources=(
  "114:pmfs_17_14"
  "156:pmfs_23_14"
  "131:pmfs_19_17"
  "35:pmfs_6_12"
  "159:pmfs_23_17"
  "20:pmfs_3_18"
  "164:pmfs_24_15"
  "107:pmfs_16_14"
)

rm -rf "$DEST"
mkdir -p "$DEST/data"
printf "panel_index\tsource_id\treplicate\trng_seed\tconcentration_sha256\tpooled_sha256\n" > "$DEST/manifest.tsv"

count=0
for spec in "${sources[@]}"; do
  panel_index="${spec%%:*}"
  source_id="${spec#*:}"
  for rep in $(seq 1 16); do
    seed=$((2026105000 + 16*panel_index + rep))
    rep2=$(printf "%02d" "$rep")
    work="$OUT_ROOT/$source_id/rep_${rep2}_seed_$seed"
    cube="$work/spatial/concentration.npy"
    pooled="$work/pooled.npy"

    [[ -f "$cube" ]] || { echo "MISSING $cube" >&2; exit 20; }
    [[ -f "$pooled" ]] || { echo "MISSING $pooled" >&2; exit 21; }

    python3 - "$cube" "$pooled" <<'PY'
import numpy as np,sys
cube=np.load(sys.argv[1],allow_pickle=False)
pooled=np.load(sys.argv[2],allow_pickle=False)
assert cube.shape==(10,83,119), cube.shape
assert pooled.shape==(10,30), pooled.shape
assert np.isfinite(cube).all() and (cube>=0).all()
assert np.isfinite(pooled).all() and (pooled>=0).all()
PY

    d="$DEST/data/$source_id/rep_${rep2}_seed_$seed"
    mkdir -p "$d"
    cp --reflink=auto "$cube" "$d/concentration.npy" 2>/dev/null || cp "$cube" "$d/concentration.npy"
    cp --reflink=auto "$pooled" "$d/pooled.npy" 2>/dev/null || cp "$pooled" "$d/pooled.npy"

    csha=$(sha256sum "$cube" | awk '{print $1}')
    psha=$(sha256sum "$pooled" | awk '{print $1}')
    printf "%s\t%s\t%d\t%d\t%s\t%s\n" "$panel_index" "$source_id" "$rep" "$seed" "$csha" "$psha" >> "$DEST/manifest.tsv"
    count=$((count+1))
  done
done

[[ "$count" -eq 128 ]]

python3 - "$DEST" <<'PY'
from pathlib import Path
import numpy as np,sys
root=Path(sys.argv[1])
cubes=list(root.glob("data/*/rep_*/concentration.npy"))
pooled=list(root.glob("data/*/rep_*/pooled.npy"))
assert len(cubes)==128, len(cubes)
assert len(pooled)==128, len(pooled)
print("DASN_RAW_SUBSET_FILES_OK",len(cubes),len(pooled))
PY

(
  cd "$DEST"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)

tar -C "$(dirname "$DEST")" -czf "$ARCHIVE" "$(basename "$DEST")"
sha256sum "$ARCHIVE"
stat -c '%n %s bytes' "$ARCHIVE"
echo "DASN_RAW_FIELD_SUBSET_READY"
