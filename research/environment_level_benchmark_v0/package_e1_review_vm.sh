#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(git rev-parse --show-toplevel)"
E="$ROOT/evidence/environment_level_benchmark_v0/e1"
STAGE="/home/zyc/E1_CROSS_HOUSE_CONTRACT_REVIEW_20260925_FINAL"
OUT="/home/zyc/E1_CROSS_HOUSE_CONTRACT_REVIEW_20260925_FINAL.tar.gz"
SCENARIOS="/mnt/hgfs/workspace/GADEN_files/scenarios"
EXPORT="/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4"

[[ -f "$E/E1_RESULT.json" && -f "$E/SHA256SUMS.txt" ]] || { echo "E1 evidence missing" >&2; exit 2; }
[[ ! -e "$STAGE" && ! -e "$OUT" ]] || { echo "review output already exists" >&2; exit 3; }
(cd "$E" && sha256sum -c SHA256SUMS.txt >/dev/null)

mkdir -p "$STAGE/repo" "$STAGE/evidence" "$STAGE/inputs/e0" "$STAGE/inputs/geometry" "$STAGE/inputs/legacy"
cp -a "$E" "$STAGE/evidence/e1"
for file in \
  research/environment_level_benchmark_v0/CODEX_E1_EXECUTION_PROMPT_20260925.md \
  research/environment_level_benchmark_v0/E1_CROSS_HOUSE_CONTRACT_CHARTER_20260925.md \
  research/environment_level_benchmark_v0/E1_IMPLEMENTATION_RULES_20260925.md \
  research/environment_level_benchmark_v0/build_e1_cross_house_contract_vm.py \
  research/environment_level_benchmark_v0/verify_e1_geometry_vm.py \
  research/environment_level_benchmark_v0/package_e1_review_vm.sh \
  research/causal_biorthogonal_green_v1/prepare_gate1a_bank.py \
  research/causal_biorthogonal_green_v1/extract_gate1a_probe_vector.py; do
  mkdir -p "$STAGE/repo/$(dirname "$file")"
  cp "$ROOT/$file" "$STAGE/repo/$file"
done
cp "$ROOT/evidence/environment_level_benchmark_v0/e0/E0_ENVIRONMENT_ASSET_INVENTORY.tsv" "$STAGE/inputs/e0/"
cp /home/zyc/bigreen_gate1a_exact_20260924/gate1a_contract.json "$STAGE/inputs/legacy/"

for house in House01 House02 House03; do
  case "$house" in
    House01) prefix=H01_air_seed ;;
    House02) prefix=H02_seed ;;
    House03) prefix=H03_seed ;;
  esac
  mkdir -p "$STAGE/inputs/geometry/$house"
  cp "$SCENARIOS/$house/OccupancyGrid3D.csv" "$STAGE/inputs/geometry/$house/"
  for seed in 0 1; do
    src="$EXPORT/${prefix}${seed}/off/geometry_export"
    cp "$src/pruned_occupancy.bin" "$STAGE/inputs/geometry/$house/pruned_seed${seed}.bin"
    if [[ "$seed" == 0 ]]; then
      cp "$src/pruned_meta.json" "$STAGE/inputs/geometry/$house/"
    fi
  done
done

(cd "$STAGE" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
(cd "$STAGE" && sha256sum -c SHA256SUMS.txt >/dev/null)
tar -czf "$OUT" -C "$STAGE" .
printf 'archive=%s\nbytes=%s\nsha256=%s\n' "$OUT" "$(stat -c %s "$OUT")" "$(sha256sum "$OUT" | cut -d' ' -f1)"
