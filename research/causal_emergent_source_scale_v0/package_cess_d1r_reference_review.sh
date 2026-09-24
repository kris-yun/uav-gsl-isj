#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
DATA_ROOT="${DATA_ROOT:-/home/zyc/cess_d1r_168x16_reference_20260925}"
E="$ROOT/evidence/causal_emergent_source_scale_v0/d1r"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
PKG="${PKG:-/home/zyc/CESS_D1R_REFERENCE_REVIEW_20260925}"
ARCHIVE="${ARCHIVE:-/home/zyc/CESS_D1R_REFERENCE_REVIEW_20260925.tar.gz}"
[[ -f "$E/CESS_D1R_REFERENCE_SUMMARY.json" ]] || exit 2
rm -rf "$PKG"; mkdir -p "$PKG"/{repo,data}
cp "$ROOT/research/causal_emergent_source_scale_v0/CESS_D1R_REFERENCE_PROTOCOL_20260925.md" "$PKG/repo/"
cp "$ROOT/research/causal_emergent_source_scale_v0/build_cess_d1a_panel.py" "$PKG/repo/"
cp "$ROOT/research/causal_emergent_source_scale_v0/run_cess_d1r_reference_vm.sh" "$PKG/repo/"
cp "$ROOT/CODEX_CESS_D1R_REFERENCE_HANDOFF_20260925.md" "$PKG/repo/" 2>/dev/null || true
cp "$ROOT/01_idea/CESS_POST_PRO_REVIEW_MAINLINE_REVISION_20260925.md" "$PKG/repo/" 2>/dev/null || true
cp "$GATE1A_ROOT/source_bank.tsv" "$PKG/repo/"
cp "$GATE1A_ROOT/gate1a_contract.json" "$PKG/repo/"
cp "$E"/CESS_D1R_* "$PKG/repo/" 2>/dev/null || true
python3 - "$E/CESS_D1R_PANEL_168.tsv" "$DATA_ROOT" "$PKG/data/reference_168x16x10x30.npy" <<'PY'
import sys,pandas as pd,numpy as np
p=pd.read_csv(sys.argv[1],sep="	"); root=sys.argv[2]; out=[]
for i,r in p.iterrows():
 a=[]
 for rep in range(1,17):
  seed=2026105000+16*i+rep
  a.append(np.load(f"{root}/{r.source_id}/rep_{rep:02d}_seed_{seed}/pooled.npy",allow_pickle=False))
 out.append(np.stack(a))
z=np.stack(out); assert z.shape==(168,16,10,30)
np.save(sys.argv[3],z,allow_pickle=False)
PY
{
 echo "branch=$(git -C "$ROOT" branch --show-current)"
 echo "head=$(git -C "$ROOT" rev-parse HEAD)"
 echo "status:"; git -C "$ROOT" status --short
} > "$PKG/repo/package_git_state.txt"

(cd "$PKG"; find . -type f ! -name SHA256SUMS.txt -print0|sort -z|xargs -0 sha256sum > SHA256SUMS.txt; sha256sum -c SHA256SUMS.txt >/dev/null)
rm -f "$ARCHIVE"; tar -C "$(dirname "$PKG")" -czf "$ARCHIVE" "$(basename "$PKG")"
echo "archive=$ARCHIVE"; stat -c 'bytes=%s' "$ARCHIVE"; sha256sum "$ARCHIVE"
