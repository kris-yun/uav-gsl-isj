#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
DATA_ROOT="${DATA_ROOT:-/home/zyc/r0_stochastic_benchmark_20260924}"
EVIDENCE="$ROOT/evidence/stochastic_benchmark_refoundation/r0"
RESEARCH="$ROOT/research/stochastic_benchmark_refoundation"
PKG="${PKG:-/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924}"
ARCHIVE="${ARCHIVE:-/home/zyc/R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz}"

[[ -f "$EVIDENCE/R0_RESULT.json" ]] || { echo "missing R0 result" >&2; exit 2; }

rm -rf "$PKG"
mkdir -p "$PKG"/{repo,compact_data}

cp "$ROOT/research/stochastic_benchmark_refoundation/R0_PROTOCOL_FREEZE_20260924.md" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/R0_SOURCE_PANEL_18.tsv" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/R0_SEED_MATRIX_18x16.tsv" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/select_r0_panel.py" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/pool_r0_cube.py" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/analyze_r0_stability.py" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/run_r0_multi_realization_vm.sh" "$PKG/repo/"
cp "$ROOT/research/stochastic_benchmark_refoundation/package_r0_review.sh" "$PKG/repo/"

cp "$EVIDENCE"/R0_*.json "$PKG/repo/" 2>/dev/null || true
cp "$EVIDENCE"/R0_*.tsv "$PKG/repo/" 2>/dev/null || true
cp "$EVIDENCE"/R0_*.txt "$PKG/repo/" 2>/dev/null || true
cp "$EVIDENCE"/R0_*.log "$PKG/repo/" 2>/dev/null || true
cp "$EVIDENCE"/R0_GIT_STATE.txt "$PKG/repo/" 2>/dev/null || true

# Include every compact 10x30 pooled realization and its run manifest.
while IFS=$'\t' read -r panel_idx source_id rep seed; do
  [[ "$panel_idx" == "panel_index" ]] && continue
  src="$DATA_ROOT/$source_id/rep_$(printf '%02d' "$rep")_seed_$seed"
  dst="$PKG/compact_data/$source_id/rep_$(printf '%02d' "$rep")_seed_$seed"
  mkdir -p "$dst"
  cp "$src/pooled.npy" "$dst/"
  cp "$src/manifest.tsv" "$dst/"
done < "$RESEARCH/R0_SEED_MATRIX_18x16.tsv"

{
  echo "branch=$(git -C "$ROOT" branch --show-current)"
  echo "head=$(git -C "$ROOT" rev-parse HEAD)"
  echo "status:"
  git -C "$ROOT" status --short
} > "$PKG/repo/package_git_state.txt"

(
  cd "$PKG"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
  sha256sum -c SHA256SUMS.txt >/dev/null
)

rm -f "$ARCHIVE"
tar -C "$(dirname "$PKG")" -czf "$ARCHIVE" "$(basename "$PKG")"
echo "archive=$ARCHIVE"
stat -c 'bytes=%s' "$ARCHIVE"
sha256sum "$ARCHIVE"
