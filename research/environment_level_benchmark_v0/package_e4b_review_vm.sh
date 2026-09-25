#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
E="$ROOT/evidence/environment_level_benchmark_v0/e4b"
STAGE="/home/zyc/E4B_H02_FACTORIAL_CORNER_REVIEW_20260925"
OUT="/home/zyc/E4B_H02_FACTORIAL_CORNER_REVIEW_20260925.tar.gz"
[[ -f "$E/E4B_RESULT.json" && -f "$E/E4B_SHA256SUMS.txt" ]] || { echo "E4B evidence missing" >&2; exit 2; }
[[ ! -e "$STAGE" && ! -e "$OUT" ]] || { echo "review output already exists" >&2; exit 3; }
(cd "$E" && sha256sum -c E4B_SHA256SUMS.txt >/dev/null)
mkdir -p "$STAGE/evidence" "$STAGE/repo" "$STAGE/predata" "$STAGE/w3_raw_cubes"
cp -a "$E" "$STAGE/evidence/e4b"
for file in \
  research/environment_level_benchmark_v0/E4A_FAILURE_POSTMORTEM_20260925.md \
  research/environment_level_benchmark_v0/E4B_H02_FACTORIAL_CORNER_GATE_20260925.md \
  research/environment_level_benchmark_v0/CODEX_E4B_EXECUTION_PROMPT_20260925.md \
  research/environment_level_benchmark_v0/E4B_PRE_RUN_IMPLEMENTATION_NOTE_20260925.md \
  research/environment_level_benchmark_v0/acquire_e4b_w3_vm.py \
  research/environment_level_benchmark_v0/e4b_factorial_gate.py \
  research/environment_level_benchmark_v0/run_e4b_w3_vm.sh \
  research/environment_level_benchmark_v0/package_e4b_review_vm.sh \
  evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv \
  evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv; do
  mkdir -p "$STAGE/repo/$(dirname "$file")"
  cp "$ROOT/$file" "$STAGE/repo/$file"
done
cp "$ROOT/evidence/environment_level_benchmark_v0/e2/E2_OPEN_DISCOVERY_10x30.npy" "$STAGE/predata/"
cp "$ROOT/evidence/environment_level_benchmark_v0/e4a/E4A_H02_W1_6x4x10x30.npy" "$STAGE/predata/"
python3 - "$E/E4B_W3_RUN_MANIFEST.tsv" "$STAGE/w3_raw_cubes" <<'PY'
import csv,hashlib,shutil,sys
from pathlib import Path
rows=list(csv.DictReader(open(sys.argv[1],newline=''),delimiter='\t'))
assert len(rows)==24
out=Path(sys.argv[2])
for r in rows:
 p=Path(r['cube_path'])
 assert '/E4B_H02_W3_24_RUNS_20260925/' in str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['cube_sha256']
 q=out/r['source_id']/f"r{r['replicate_index']}_seed{r['requested_seed']}.npy"
 q.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(p,q)
PY
(cd "$STAGE" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
(cd "$STAGE" && sha256sum -c SHA256SUMS.txt >/dev/null)
tar -czf "$OUT" -C "$STAGE" .
printf 'archive=%s\nbytes=%s\nsha256=%s\n' "$OUT" "$(stat -c %s "$OUT")" "$(sha256sum "$OUT" | cut -d' ' -f1)"
