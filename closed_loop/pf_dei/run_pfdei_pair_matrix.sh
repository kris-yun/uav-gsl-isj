#!/usr/bin/env bash
set -Eeo pipefail

CASE_RUNNER="${CASE_RUNNER:?set CASE_RUNNER to the frozen PF-DEI one-case runner}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/pfdei_pairs_$(date -u +%Y%m%dT%H%M%SZ)}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
DOMAIN_BASE="${DOMAIN_BASE:-120}"
SEEDS_CSV="${SEEDS_CSV:-0,1,2,3,4,5,6,7,8,9}"
HOUSES_CSV="${HOUSES_CSV:-House01,House02,House03}"
PHASE="${PHASE:-development}"

if [[ "$PHASE" != "development" && "$PHASE" != "confirmatory" ]]; then
  echo "PHASE must be development or confirmatory" >&2
  exit 2
fi
if (( DOMAIN_BASE < 0 || DOMAIN_BASE + MAX_PARALLEL - 1 > 232 )); then
  echo "ROS domain range must remain within 0..232" >&2
  exit 2
fi
if [[ ! -x "$CASE_RUNNER" ]]; then
  echo "CASE_RUNNER is not executable: $CASE_RUNNER" >&2
  exit 2
fi

mkdir -p "$RUN_ROOT/_batch"
IFS=',' read -r -a SEEDS <<< "$SEEDS_CSV"
IFS=',' read -r -a HOUSES <<< "$HOUSES_CSV"
pairs=()
for h in "${HOUSES[@]}"; do
  for s in "${SEEDS[@]}"; do
    pairs+=("$h:$s")
  done
done

cat > "$RUN_ROOT/_batch/BATCH_MANIFEST.txt" <<MANIFEST
contract=PF_DEI_PAIRED_CLOSED_LOOP_V1
phase=$PHASE
created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
case_runner=$CASE_RUNNER
case_runner_sha256=$(sha256sum "$CASE_RUNNER" | awk '{print $1}')
timeout_sec=$TIMEOUT_SEC
houses=$HOUSES_CSV
seeds=$SEEDS_CSV
max_parallel=$MAX_PARALLEL
domain_base=$DOMAIN_BASE
pair_order=OFF_then_FULL
on_mode=pfdei_full
MANIFEST

run_pair() {
  local pair="$1"
  local domain="$2"
  local house="${pair%%:*}"
  local seed="${pair##*:}"
  local pair_root="$RUN_ROOT/$house/seed$seed"
  mkdir -p "$pair_root"
  local arm mode out rc
  for arm in off on; do
    if [[ "$arm" == "off" ]]; then mode="off"; else mode="pfdei_full"; fi
    out="$pair_root/$arm"
    mkdir -p "$out"
    set +e
    HOUSE="$house" SEED="$seed" ARM="$arm" PFDEI_MODE="$mode" \
      CASE_OUTPUT_DIR="$out" RUN_ROOT="$RUN_ROOT" DOMAIN_ID="$domain" \
      TIMEOUT_SEC="$TIMEOUT_SEC" bash "$CASE_RUNNER" >"$out/runner.log" 2>&1
    rc=$?
    set -e
    echo "$rc" > "$out/runner.rc"
    if (( rc != 0 )); then
      echo "FAILED $house seed=$seed arm=$arm rc=$rc" >&2
      return "$rc"
    fi
    if [[ ! -f "$out/case_result.json" ]]; then
      echo "missing case_result.json: $out" >&2
      return 90
    fi
  done
}

idx=0
fail=0
while (( idx < ${#pairs[@]} )); do
  pids=()
  labels=()
  for ((slot=0; slot<MAX_PARALLEL && idx<${#pairs[@]}; slot++, idx++)); do
    pair="${pairs[$idx]}"
    domain=$((DOMAIN_BASE + slot))
    ( run_pair "$pair" "$domain" ) &
    pids+=("$!")
    labels+=("$pair")
  done
  for j in "${!pids[@]}"; do
    if ! wait "${pids[$j]}"; then
      echo "PAIR_FAILED ${labels[$j]}" | tee -a "$RUN_ROOT/_batch/failures.txt"
      fail=1
    fi
  done
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/aggregate_pfdei_pairs.py" "$RUN_ROOT" \
  --houses "$HOUSES_CSV" --seeds "$SEEDS_CSV" --phase "$PHASE" \
  --out "$RUN_ROOT/_batch/PAIR_VERDICT.json" | tee "$RUN_ROOT/_batch/PAIR_VERDICT.stdout.txt"

if (( fail != 0 )); then exit 91; fi
