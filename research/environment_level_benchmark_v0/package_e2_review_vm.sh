#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
E="$ROOT/evidence/environment_level_benchmark_v0/e2"
DATA="/home/zyc/E2_CROSS_ENVIRONMENT_168_RUNS_20260925"
STAGE="/home/zyc/E2_CROSS_ENVIRONMENT_REVIEW_20260925"
OUT="/home/zyc/E2_CROSS_ENVIRONMENT_REVIEW_20260925.tar.gz"
[[ -f "$E/E2_QC_SUMMARY.json" && -f "$E/E2_SHA256SUMS.txt" ]] || { echo "E2 evidence missing" >&2; exit 2; }
[[ ! -e "$STAGE" && ! -e "$OUT" ]] || { echo "review output already exists" >&2; exit 3; }
(cd "$E" && sha256sum -c E2_SHA256SUMS.txt >/dev/null)
python3 - "$E/E2_QC_SUMMARY.json" <<'PY'
import json,sys
q=json.load(open(sys.argv[1]))
assert q['decision']=='E2_PASS_BENCHMARK_ACQUIRED_AND_SEALED'
assert q['completed_new_plume_runs']==168
assert q['full_concentration_cubes_retained']==168
PY
mkdir -p "$STAGE/evidence" "$STAGE/repo" "$STAGE/open_raw_cubes"
cp -a "$E" "$STAGE/evidence/e2"
for file in \
  research/environment_level_benchmark_v0/CODEX_E2_EXECUTION_PROMPT_20260925.md \
  research/environment_level_benchmark_v0/E2_MINIMAL_FILLIN_CHARTER_20260925.md \
  research/environment_level_benchmark_v0/acquire_e2_vm.py \
  research/environment_level_benchmark_v0/finalize_e2_vm.py \
  research/environment_level_benchmark_v0/run_e2_vm.sh \
  research/environment_level_benchmark_v0/package_e2_review_vm.sh \
  evidence/environment_level_benchmark_v0/e1/E1_HOUSE_PROBE_CONTRACTS.tsv \
  evidence/environment_level_benchmark_v0/e1/E1_HOUSE_SOURCE_PANELS.tsv \
  evidence/environment_level_benchmark_v0/e1/E1_RESULT.json; do
  mkdir -p "$STAGE/repo/$(dirname "$file")"
  cp "$ROOT/$file" "$STAGE/repo/$file"
done
python3 - "$E/E2_RUN_MANIFEST.tsv" "$STAGE/open_raw_cubes" <<'PY'
import csv,shutil,sys
from pathlib import Path
rows=list(csv.DictReader(open(sys.argv[1],newline=''),delimiter='\t'))
assert len(rows)==168
out=Path(sys.argv[2]); n=0
for r in rows:
 if r['role']!='OPEN_DISCOVERY': continue
 target=out/f"E{r['environment_index']}"/r['source_id']/f"r{r['replicate_index']}_seed{r['requested_seed']}.npy"
 target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(r['cube_path'],target)
 n+=1
assert n==72
PY
(cd "$STAGE" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
(cd "$STAGE" && sha256sum -c SHA256SUMS.txt >/dev/null)
tar -czf "$OUT" -C "$STAGE" .
printf 'archive=%s\nbytes=%s\nsha256=%s\n' "$OUT" "$(stat -c %s "$OUT")" "$(sha256sum "$OUT" | cut -d' ' -f1)"
