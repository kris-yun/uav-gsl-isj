#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
R="$ROOT/research/local_stochastic_confusability_v0"
E="$ROOT/evidence/local_stochastic_confusability_v0/crosswind_d0"
DATA="/home/zyc/lsc_crosswind_d0_128_runs_20260925"
GATE1A="/home/zyc/bigreen_gate1a_exact_20260924"
PANEL="/home/zyc/cess_d1r_reference_repo_20260925/evidence/causal_emergent_source_scale_v0/d1r/CESS_D1R_PANEL_168.tsv"
W0="/home/zyc/CESS_D1R_REFERENCE_REVIEW_20260925/data/reference_168x16x10x30.npy"
PKG="/home/zyc/LSC_CROSSWIND_D0_REVIEW_20260925"
ARCHIVE="/home/zyc/LSC_CROSSWIND_D0_REVIEW_20260925.tar.gz"
[[ -f "$E/LSC_CROSSWIND_D0_RESULT.json" ]] || { echo "missing result" >&2; exit 2; }
[[ "$(tail -n +2 "$E/LSC_CROSSWIND_D0_ARTIFACT_SHA256.tsv" | wc -l)" -eq 128 ]] || exit 3
rm -rf "$PKG"
mkdir -p "$PKG"/{repo,data,manifests}
cp "$ROOT/CODEX_LSC_CROSSWIND_D0_HANDOFF_20260925.md" "$PKG/repo/"
cp "$R/LSC_CROSSWIND_D0_PROTOCOL_20260925.md" "$PKG/repo/"
cp "$R/analyze_lsc_crosswind_d0.py" "$R/run_lsc_crosswind_d0_vm.sh" \
  "$R/package_lsc_crosswind_d0_review.sh" "$PKG/repo/"
cp "$ROOT/evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json" "$PKG/repo/"
cp "$GATE1A/gate1a_contract.json" "$GATE1A/source_bank.tsv" "$PANEL" "$PKG/repo/"
cp "$E"/LSC_CROSSWIND_D0_* "$PKG/repo/"
cp "$W0" "$PKG/data/reference_W0_168x16x10x30.npy"
cp "$E/LSC_CROSSWIND_D0_W1_8x8x10x30.npy" "$E/LSC_CROSSWIND_D0_W2_8x8x10x30.npy" "$PKG/data/"
while IFS=$'\t' read -r wi wind si sid rep seed csha psha; do
  [[ "$wi" == "wind_index" ]] && continue
  src="$DATA/$wind/$sid/rep_$(printf '%02d' "$rep")_seed_$seed"
  dst="$PKG/manifests/$wind/$sid/rep_$(printf '%02d' "$rep")_seed_$seed"
  mkdir -p "$dst"
  cp "$src/manifest.tsv" "$src/generation.log" "$src/extract.log" "$dst/"
done < "$E/LSC_CROSSWIND_D0_ARTIFACT_SHA256.tsv"
{
  echo "branch=$(git branch --show-current)"
  echo "head=$(git rev-parse HEAD)"
  echo "status:"
  git status --short
} > "$PKG/repo/package_git_state.txt"
(cd "$PKG"; find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt; sha256sum -c SHA256SUMS.txt --quiet)
rm -f "$ARCHIVE"
tar -C /home/zyc -czf "$ARCHIVE" "$(basename "$PKG")"
echo "archive=$ARCHIVE"
stat -c 'bytes=%s' "$ARCHIVE"
sha256sum "$ARCHIVE"
