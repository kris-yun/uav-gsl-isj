#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
D3_ROOT="${D3_ROOT:-/home/zyc/mz_d3_s1_w2_20260924}"
PKG="${PKG:-/home/zyc/MZ_D3_S1_W2_REVIEW_20260924}"
ARCHIVE="${ARCHIVE:-/home/zyc/MZ_D3_S1_W2_REVIEW_20260924.tar.gz}"
EVIDENCE="$ROOT/evidence/realization_invariant_source_signature_v0"
RESEARCH="$ROOT/research/realization_invariant_source_signature_v0"

RESULT="$EVIDENCE/D3_S1_W2_RESULT_20260924.json"
[[ -f "$RESULT" ]] || { echo "missing result" >&2; exit 2; }

rm -rf "$PKG"
mkdir -p "$PKG"/{targets,frozen_inputs,repo}

cp "$RESULT" "$PKG/repo/"
cp "$EVIDENCE/D3_S1_W2_RUN_20260924.log" "$PKG/repo/" 2>/dev/null || true
cp "$EVIDENCE/D3_S1_W2_SHA256_20260924.txt" "$PKG/repo/" 2>/dev/null || true
cp "$RESEARCH/score_d3_second_source.py" "$PKG/repo/"
cp "$RESEARCH/run_d3_s1_w2_vm.sh" "$PKG/repo/"

cp "$GATE1A_ROOT/gate1a_contract.json" "$PKG/frozen_inputs/"
cp "$GATE1A_ROOT/source_bank.tsv" "$PKG/frozen_inputs/"

for t in S1_W2_A S1_W2_B; do
  mkdir -p "$PKG/targets/$t"
  cp "$D3_ROOT/$t/spatial/concentration.npy" "$PKG/targets/$t/"
  cp "$D3_ROOT/$t/spatial/metadata.json" "$PKG/targets/$t/" 2>/dev/null || true
  cp "$D3_ROOT/$t/manifest.tsv" "$PKG/targets/$t/"
  cp "$D3_ROOT/$t/generation.log" "$PKG/targets/$t/" 2>/dev/null || true
  cp "$D3_ROOT/$t/extract.log" "$PKG/targets/$t/" 2>/dev/null || true
done

{
  echo "branch=$(git -C "$ROOT" branch --show-current)"
  echo "head=$(git -C "$ROOT" rev-parse HEAD)"
  echo "status:"
  git -C "$ROOT" status --short
} > "$PKG/repo/git_state.txt"

(
  cd "$PKG"
  find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)
(
  cd "$PKG"
  sha256sum -c SHA256SUMS.txt >/dev/null
)

rm -f "$ARCHIVE"
tar -C "$(dirname "$PKG")" -czf "$ARCHIVE" "$(basename "$PKG")"
echo "archive=$ARCHIVE"
stat -c 'bytes=%s' "$ARCHIVE"
sha256sum "$ARCHIVE"
