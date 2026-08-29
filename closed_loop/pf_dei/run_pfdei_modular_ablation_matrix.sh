#!/usr/bin/env bash
set -Eeo pipefail
# Run only after PF-DEI FULL is frozen on the development seed set.
# CASE_RUNNER must accept HOUSE, SEED, ARM, PFDEI_MODE, CASE_OUTPUT_DIR,
# DOMAIN_ID, TIMEOUT_SEC and write case_result.json whose arm equals PFDEI_MODE.
CASE_RUNNER="${CASE_RUNNER:?set CASE_RUNNER}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/pfdei_ablation_$(date -u +%Y%m%dT%H%M%SZ)}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
DOMAIN_BASE="${DOMAIN_BASE:-170}"
SEEDS_CSV="${SEEDS_CSV:-0,1,2,3,4,5,6,7,8,9}"
HOUSES_CSV="${HOUSES_CSV:-House01,House02,House03}"
MODES_CSV="${MODES_CSV:-pfdei_full,pfdei_ablate_sensor,pfdei_ablate_temporal,pfdei_ablate_coherence,pfdei_ablate_nuisance}"
if (( DOMAIN_BASE<0 || DOMAIN_BASE+MAX_PARALLEL-1>232 )); then echo 'invalid ROS domain range' >&2; exit 2; fi
mkdir -p "$RUN_ROOT/_batch"
IFS=',' read -r -a HOUSES <<<"$HOUSES_CSV"; IFS=',' read -r -a SEEDS <<<"$SEEDS_CSV"; IFS=',' read -r -a MODES <<<"$MODES_CSV"
work=(); for h in "${HOUSES[@]}"; do for s in "${SEEDS[@]}"; do for m in "${MODES[@]}"; do work+=("$h:$s:$m"); done; done; done
cat >"$RUN_ROOT/_batch/BATCH_MANIFEST.txt" <<EOF
contract=PF_DEI_MODULAR_ABLATION_V1
case_runner=$CASE_RUNNER
case_runner_sha256=$(sha256sum "$CASE_RUNNER"|awk '{print $1}')
houses=$HOUSES_CSV
seeds=$SEEDS_CSV
modes=$MODES_CSV
note=ablation_only_after_full_freeze_no_retuning
EOF
run_one(){ local item="$1" domain="$2"; IFS=: read -r h s m <<<"$item"; local out="$RUN_ROOT/$h/seed$s/$m"; mkdir -p "$out"; HOUSE="$h" SEED="$s" ARM="$m" PFDEI_MODE="$m" CASE_OUTPUT_DIR="$out" DOMAIN_ID="$domain" TIMEOUT_SEC="$TIMEOUT_SEC" bash "$CASE_RUNNER" >"$out/runner.log" 2>&1; test -f "$out/case_result.json"; }
idx=0; fail=0
while (( idx<${#work[@]} )); do pids=(); labels=(); for ((slot=0;slot<MAX_PARALLEL && idx<${#work[@]};slot++,idx++)); do item="${work[$idx]}"; (run_one "$item" $((DOMAIN_BASE+slot))) & pids+=("$!"); labels+=("$item"); done; for j in "${!pids[@]}"; do if ! wait "${pids[$j]}"; then echo "FAILED ${labels[$j]}"|tee -a "$RUN_ROOT/_batch/failures.txt"; fail=1; fi; done; done
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"; python3 "$SCRIPT_DIR/aggregate_pfdei_ablation.py" "$RUN_ROOT" --out "$RUN_ROOT/_batch/ABLATION_SUMMARY.json"
exit "$fail"
