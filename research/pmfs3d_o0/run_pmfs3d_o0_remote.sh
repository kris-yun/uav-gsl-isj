#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${ROOT:-$(git rev-parse --show-toplevel)}"
EXPECTED_BRANCH="research/pmfs3d-o0-mechanism-ready-20261001"
BRANCH="$(git -C "$ROOT" branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || { echo "wrong branch: $BRANCH" >&2; exit 2; }
git -C "$ROOT" diff --quiet || { echo "tracked worktree dirty" >&2; exit 2; }
git -C "$ROOT" diff --cached --quiet || { echo "index dirty" >&2; exit 2; }

OUT="$ROOT/evidence/pmfs3d_o0_projected2d_20261001"
WORK_ROOT="${WORK_ROOT:-/home/zyc/PMFS3D_O0_PROJECTED2D_20261001}"
CANONICAL_ROOT="${CANONICAL_ROOT:-/mnt/hgfs/workspace/GADEN_files/scenarios}"
BINARY="${BINARY:-/home/zyc/hcmc_gaden_seed_build_20260922/install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator}"
EXTRACTOR="${EXTRACTOR:-/home/zyc/rmfe_filament_extractor_omp}"
mkdir -p "$OUT"

python "$ROOT/research/pmfs3d_o0/project_wind_to_2d.py" --self-test | tee "$OUT/SELFTEST_WIND.log"
python "$ROOT/research/pmfs3d_o0/pmfs3d_o0_projected2d_gate.py" --self-test | tee "$OUT/SELFTEST_GATE.log"
python "$ROOT/research/pmfs3d_o0/audit_pmfs_2d_contract.py" --repo-root "$ROOT" --out "$OUT/PMFS_2D_CONTRACT.json" | tee "$OUT/PMFS_2D_CONTRACT.log"

python "$ROOT/research/pmfs3d_o0/pmfs3d_o0_projected2d_gate.py" \
  --repo-root "$ROOT" \
  --canonical-root "$CANONICAL_ROOT" \
  --binary "$BINARY" \
  --extractor "$EXTRACTOR" \
  --work-root "$WORK_ROOT" \
  --result-json "$OUT/O0_RESULT.json" \
  | tee "$OUT/O0_RUN.log"

sha256sum \
  "$ROOT/research/pmfs3d_o0/project_wind_to_2d.py" \
  "$ROOT/research/pmfs3d_o0/pmfs3d_o0_projected2d_gate.py" \
  "$ROOT/research/pmfs3d_o0/audit_pmfs_2d_contract.py" \
  "$OUT/PMFS_2D_CONTRACT.json" \
  "$OUT/O0_RESULT.json" > "$OUT/SHA256SUMS.txt"

cat "$OUT/O0_RESULT.json"
echo "PMFS3D_O0_DONE_STOP"
