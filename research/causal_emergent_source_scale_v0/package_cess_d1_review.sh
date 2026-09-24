#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
DATA_ROOT="${DATA_ROOT:-/home/zyc/cess_d1_630x8_20260924}"
EVIDENCE="$ROOT/evidence/causal_emergent_source_scale_v0/d1"
RESEARCH="$ROOT/research/causal_emergent_source_scale_v0"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
PKG="${PKG:-/home/zyc/CESS_D1_REVIEW_20260924}"
ARCHIVE="${ARCHIVE:-/home/zyc/CESS_D1_REVIEW_20260924.tar.gz}"

[[ -f "$EVIDENCE/CESS_D1_RESULT.json" ]] || { echo "missing result" >&2; exit 2; }

rm -rf "$PKG"
mkdir -p "$PKG"/{repo,data}

cp "$RESEARCH/CESS_D1_PROTOCOL_FREEZE_20260924.md" "$PKG/repo/"
cp "$RESEARCH/build_connected_ward_hierarchy.py" "$PKG/repo/"
cp "$RESEARCH/analyze_cess_d1.py" "$PKG/repo/"
cp "$RESEARCH/test_cess_d1_weighting.py" "$PKG/repo/"
cp "$RESEARCH/run_cess_d1_vm.sh" "$PKG/repo/"
cp "$RESEARCH/package_cess_d1_review.sh" "$PKG/repo/"
cp "$GATE1A_ROOT/source_bank.tsv" "$PKG/repo/"
cp "$GATE1A_ROOT/gate1a_contract.json" "$PKG/repo/"
cp "$EVIDENCE"/CESS_D1_* "$PKG/repo/" 2>/dev/null || true

python3 - "$GATE1A_ROOT/source_bank.tsv" "$DATA_ROOT" "$PKG/data/pooled_all.npy" "$PKG/data/seed_matrix.tsv" <<'PY'
import sys,numpy as np,pandas as pd
from pathlib import Path
bank=pd.read_csv(sys.argv[1],sep="\t")
root=Path(sys.argv[2])
out=np.empty((630,8,10,30),dtype=np.float64)
rows=[]
for i,sid in enumerate(bank.source_id):
    for rep in range(1,9):
        seed=2026100000+8*i+rep
        f=root/sid/f"rep_{rep:02d}_seed_{seed}"/"pooled.npy"
        a=np.load(f,allow_pickle=False)
        assert a.shape==(10,30)
        out[i,rep-1]=a
        rows.append((i,sid,rep,seed))
np.save(sys.argv[3],out,allow_pickle=False)
pd.DataFrame(rows,columns=["source_index","source_id","replicate","rng_seed"]).to_csv(
    sys.argv[4],sep="\t",index=False)
print("consolidated",out.shape,out.nbytes)
PY

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
