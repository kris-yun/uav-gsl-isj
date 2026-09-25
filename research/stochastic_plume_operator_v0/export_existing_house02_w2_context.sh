#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
OUT="${OUT:-/home/zyc/SPOI_CONTEXT_ASSETS_20260925}"
ARCHIVE="${ARCHIVE:-/home/zyc/SPOI_CONTEXT_ASSETS_20260925.tar.gz}"

OCC="$CANONICAL_ROOT/House02/OccupancyGrid3D.csv"
WIND="$CANONICAL_ROOT/House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind"
EXPECTED_OCC_SHA="9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
EXPECTED_W1_SHA="54d7bc338ea681611f66004a3230f29feffc495446814607141b0623ef1dd9a8"

[[ -f "$OCC" ]] || { echo "missing occupancy: $OCC" >&2; exit 2; }
[[ -d "$WIND" ]] || { echo "missing wind dir: $WIND" >&2; exit 3; }

occ_sha="$(sha256sum "$OCC" | awk '{print $1}')"
[[ "$occ_sha" == "$EXPECTED_OCC_SHA" ]] || { echo "occupancy hash drift: $occ_sha" >&2; exit 4; }
w1_sha="$(sha256sum "$WIND/wind_iteration_1" | awk '{print $1}')"
[[ "$w1_sha" == "$EXPECTED_W1_SHA" ]] || { echo "W2 iteration1 hash drift: $w1_sha" >&2; exit 5; }

rm -rf "$OUT"
mkdir -p "$OUT/raw_wind"
cp -p "$OCC" "$OUT/OccupancyGrid3D.csv"
for i in $(seq 0 10); do
  f="$WIND/wind_iteration_$i"
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 6; }
  cp -p "$f" "$OUT/raw_wind/"
done

{
  echo "branch=$(git -C "$ROOT" branch --show-current)"
  echo "head=$(git -C "$ROOT" rev-parse HEAD)"
  echo "canonical_root=$CANONICAL_ROOT"
  echo "occupancy_source=$OCC"
  echo "wind_source=$WIND"
} > "$OUT/provenance.txt"

{
  printf "path\tbytes\tsha256\n"
  printf "OccupancyGrid3D.csv\t%s\t%s\n" "$(stat -c %s "$OUT/OccupancyGrid3D.csv")" "$(sha256sum "$OUT/OccupancyGrid3D.csv"|awk '{print $1}')"
  for f in "$OUT"/raw_wind/wind_iteration_*; do
    printf "raw_wind/%s\t%s\t%s\n" "$(basename "$f")" "$(stat -c %s "$f")" "$(sha256sum "$f"|awk '{print $1}')"
  done
} > "$OUT/ASSET_SHA256.tsv"

{
  file "$OUT/OccupancyGrid3D.csv"
  for f in "$OUT"/raw_wind/wind_iteration_*; do file "$f"; done
  echo "=== occupancy head ==="
  head -n 5 "$OUT/OccupancyGrid3D.csv" || true
  for f in "$OUT"/raw_wind/wind_iteration_*; do
    echo "=== $(basename "$f") head ==="
    head -n 5 "$f" 2>/dev/null || true
  done
} > "$OUT/FORMAT_PROBE.txt"

(
  cd "$OUT"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
  sha256sum -c SHA256SUMS.txt >/dev/null
)

rm -f "$ARCHIVE"
tar -C "$(dirname "$OUT")" -czf "$ARCHIVE" "$(basename "$OUT")"
echo "archive=$ARCHIVE"
stat -c "bytes=%s" "$ARCHIVE"
sha256sum "$ARCHIVE"
