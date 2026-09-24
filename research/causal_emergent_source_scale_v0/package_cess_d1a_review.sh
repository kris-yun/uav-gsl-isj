#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
DATA_ROOT="${DATA_ROOT:-/home/zyc/cess_d1a_168x16_20260925}"
E="$ROOT/evidence/causal_emergent_source_scale_v0/d1a"
R="$ROOT/research/causal_emergent_source_scale_v0"
GATE1A_ROOT="${GATE1A_ROOT:-/home/zyc/bigreen_gate1a_exact_20260924}"
PKG="${PKG:-/home/zyc/CESS_D1A_REVIEW_20260925}"
ARCHIVE="${ARCHIVE:-/home/zyc/CESS_D1A_REVIEW_20260925.tar.gz}"
[[ -f "$E/CESS_D1A_RESULT.json" ]] || { echo "missing result" >&2; exit 2; }
rm -rf "$PKG"; mkdir -p "$PKG"/{repo,data}
cp "$R/CESS_D1A_PROTOCOL_FREEZE_20260925.md" "$PKG/repo/"
cp "$R/CESS_D1B_STRONG_DECODER_CONTROL_FREEZE_20260925.md" "$PKG/repo/"
cp "$R/analyze_cess_d1b_markov.py" "$PKG/repo/"
cp "$GATE1A_ROOT/source_bank.tsv" "$PKG/repo/"
cp "$GATE1A_ROOT/gate1a_contract.json" "$PKG/repo/"
cp "$R/build_cess_d1a_panel.py" "$R/build_cess_d1a_hierarchy.py" "$R/analyze_cess_d1a.py" "$R/run_cess_d1a_vm.sh" "$R/test_cess_d1a_weighting.py" "$R/test_cess_d1a_hierarchy.py" "$PKG/repo/"
cp "$ROOT/CODEX_CESS_D1A_HANDOFF_20260925.md" "$PKG/repo/" 2>/dev/null || true
cp "$ROOT/01_idea/CESS_MAINLINE_FREEZE_V1_20260925.md" "$PKG/repo/" 2>/dev/null || true
cp "$ROOT/evidence/causal_emergent_source_scale_v0/CESS_D0_INTERVENTION_WEIGHTING_CORRECTION_20260925.md" "$PKG/repo/" 2>/dev/null || true
cp "$E"/CESS_D1A_* "$PKG/repo/" 2>/dev/null || true

python3 - "$E/CESS_D1A_PANEL_168.tsv" "$DATA_ROOT" "$PKG/data/pooled_168x16x10x30.npy" <<'PY'
import sys,pandas as pd,numpy as np
p=pd.read_csv(sys.argv[1],sep="\t"); root=sys.argv[2]
out=[]
for i,r in p.iterrows():
    a=[]
    for rep in range(1,17):
        seed=2026105000+16*i+rep
        f=f"{root}/{r.source_id}/rep_{rep:02d}_seed_{seed}/pooled.npy"
        x=np.load(f,allow_pickle=False)
        assert x.shape==(10,30)
        a.append(x)
    out.append(np.stack(a))
z=np.stack(out)
assert z.shape==(168,16,10,30)
np.save(sys.argv[3],z,allow_pickle=False)
print(z.shape)
PY

{
 echo "branch=$(git -C "$ROOT" branch --show-current)"
 echo "head=$(git -C "$ROOT" rev-parse HEAD)"
 echo "status:"; git -C "$ROOT" status --short
} > "$PKG/repo/package_git_state.txt"

(cd "$PKG"; find . -type f ! -name SHA256SUMS.txt -print0|sort -z|xargs -0 sha256sum > SHA256SUMS.txt; sha256sum -c SHA256SUMS.txt >/dev/null)
rm -f "$ARCHIVE"; tar -C "$(dirname "$PKG")" -czf "$ARCHIVE" "$(basename "$PKG")"
echo "archive=$ARCHIVE"; stat -c 'bytes=%s' "$ARCHIVE"; sha256sum "$ARCHIVE"
