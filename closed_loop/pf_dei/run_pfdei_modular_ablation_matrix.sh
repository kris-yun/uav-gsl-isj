#!/usr/bin/env bash
set -Eeo pipefail
# Run only after PF-DEI FULL is frozen on the development seed set.
# The already-completed FULL results are reused; this runner executes only
# module-removal arms so 30 expensive full runs are not repeated.
# CASE_RUNNER must accept HOUSE, SEED, ARM, PFDEI_MODE, CASE_OUTPUT_DIR,
# DOMAIN_ID, TIMEOUT_SEC and write case_result.json whose arm equals PFDEI_MODE.
CASE_RUNNER="${CASE_RUNNER:?set CASE_RUNNER}"
FULL_RESULT_ROOT="${FULL_RESULT_ROOT:?set FULL_RESULT_ROOT to frozen development FULL results}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/pfdei_ablation_$(date -u +%Y%m%dT%H%M%SZ)}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
DOMAIN_BASE="${DOMAIN_BASE:-170}"
SEEDS_CSV="${SEEDS_CSV:-0,1,2,3,4,5,6,7,8,9}"
HOUSES_CSV="${HOUSES_CSV:-House01,House02,House03}"
MODES_CSV="${MODES_CSV:-pfdei_ablate_sensor,pfdei_ablate_temporal,pfdei_ablate_coherence,pfdei_ablate_nuisance}"
if (( DOMAIN_BASE<0 || DOMAIN_BASE+MAX_PARALLEL-1>232 )); then echo 'invalid ROS domain range' >&2; exit 2; fi
mkdir -p "$RUN_ROOT/_batch"
IFS=',' read -r -a HOUSES <<<"$HOUSES_CSV"; IFS=',' read -r -a SEEDS <<<"$SEEDS_CSV"; IFS=',' read -r -a MODES <<<"$MODES_CSV"

# Copy only result metadata from the immutable full matrix and relabel the arm
# as pfdei_full for paired ablation aggregation. Raw full-run artifacts remain
# in FULL_RESULT_ROOT and are not duplicated.
for h in "${HOUSES[@]}"; do
  for s in "${SEEDS[@]}"; do
    src="$FULL_RESULT_ROOT/$h/seed$s/pfdei_full/case_result.json"
    [[ -f "$src" ]] || src="$FULL_RESULT_ROOT/$h/seed$s/on/case_result.json"
    [[ -f "$src" ]] || { echo "missing frozen full result for $h seed$s" >&2; exit 3; }
    dst="$RUN_ROOT/$h/seed$s/pfdei_full/case_result.json"; mkdir -p "$(dirname "$dst")"
    python3 - "$src" "$dst" <<'PY'
import json,sys
src,dst=sys.argv[1:]
d=json.load(open(src)); d['arm']='pfdei_full'; d['reused_frozen_full_result']=True; d['original_result_path']=src
open(dst,'w').write(json.dumps(d,indent=2)+'\n')
PY
  done
done

work=(); for h in "${HOUSES[@]}"; do for s in "${SEEDS[@]}"; do for m in "${MODES[@]}"; do work+=("$h:$s:$m"); done; done; done
cat >"$RUN_ROOT/_batch/BATCH_MANIFEST.txt" <<EOF
contract=PF_DEI_MODULAR_ABLATION_V1
case_runner=$CASE_RUNNER
case_runner_sha256=$(sha256sum "$CASE_RUNNER"|awk '{print $1}')
full_result_root=$FULL_RESULT_ROOT
houses=$HOUSES_CSV
seeds=$SEEDS_CSV
modes=$MODES_CSV
note=frozen_full_reused_ablation_only_no_retuning
EOF
run_one(){ local item="$1" domain="$2"; IFS=: read -r h s m <<<"$item"; local out="$RUN_ROOT/$h/seed$s/$m"; mkdir -p "$out"; HOUSE="$h" SEED="$s" ARM="$m" PFDEI_MODE="$m" CASE_OUTPUT_DIR="$out" DOMAIN_ID="$domain" TIMEOUT_SEC="$TIMEOUT_SEC" bash "$CASE_RUNNER" >"$out/runner.log" 2>&1; test -f "$out/case_result.json"; }
idx=0; fail=0
while (( idx<${#work[@]} )); do pids=(); labels=(); for ((slot=0;slot<MAX_PARALLEL && idx<${#work[@]};slot++,idx++)); do item="${work[$idx]}"; (run_one "$item" $((DOMAIN_BASE+slot))) & pids+=("$!"); labels+=("$item"); done; for j in "${!pids[@]}"; do if ! wait "${pids[$j]}"; then echo "FAILED ${labels[$j]}"|tee -a "$RUN_ROOT/_batch/failures.txt"; fail=1; fi; done; done
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"; python3 "$SCRIPT_DIR/aggregate_pfdei_ablation.py" "$RUN_ROOT" --out "$RUN_ROOT/_batch/ABLATION_SUMMARY.json"
exit "$fail"
