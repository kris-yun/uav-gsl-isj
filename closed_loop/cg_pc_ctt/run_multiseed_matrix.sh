#!/usr/bin/env bash
set -Eeo pipefail

# Full confirmatory matrix: 3 Houses x 10 seeds x OFF/ON = 60 runs.
# Runs matched OFF then ON sequentially inside each (House,seed) pair.
# Multiple pairs may run in parallel on isolated ROS domains.
#
# Required external contract:
#   CASE_RUNNER=/absolute/path/to/run_cg_pc_ctt_case.sh
# The runner is invoked with environment HOUSE, SEED, ARM, RUN_ROOT,
# DOMAIN_ID, TIMEOUT_SEC and must create:
#   $RUN_ROOT/$HOUSE/seed$SEED/$ARM/case_result.json
# compatible with aggregate_multiseed.py.

CASE_RUNNER="${CASE_RUNNER:?set CASE_RUNNER to the frozen one-case runner}"
RUN_ROOT="${RUN_ROOT:-/dev/shm/cg_pc_ctt_multiseed_$(date -u +%Y%m%dT%H%M%SZ)}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
MAX_PARALLEL="${MAX_PARALLEL:-3}"
DOMAIN_BASE="${DOMAIN_BASE:-120}"
SEEDS_CSV="${SEEDS_CSV:-0,1,2,3,4,5,6,7,8,9}"
HOUSES_CSV="${HOUSES_CSV:-House01,House02,House03}"

if (( DOMAIN_BASE < 0 || DOMAIN_BASE + MAX_PARALLEL - 1 > 232 )); then
  echo "ROS domain range must remain within 0..232" >&2; exit 2
fi
if [[ ! -x "$CASE_RUNNER" ]]; then
  echo "CASE_RUNNER is not executable: $CASE_RUNNER" >&2; exit 2
fi

mkdir -p "$RUN_ROOT" "$RUN_ROOT/_batch"
IFS=',' read -r -a SEEDS <<< "$SEEDS_CSV"
IFS=',' read -r -a HOUSES <<< "$HOUSES_CSV"

pairs=()
for h in "${HOUSES[@]}"; do
  for s in "${SEEDS[@]}"; do pairs+=("$h:$s"); done
done

cat > "$RUN_ROOT/_batch/BATCH_MANIFEST.txt" <<EOF
contract=CG_PC_CTT_MULTI_SEED_CONFIRMATORY_V1
created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
case_runner=$CASE_RUNNER
case_runner_sha256=$(sha256sum "$CASE_RUNNER" | awk '{print $1}')
timeout_sec=$TIMEOUT_SEC
houses=$HOUSES_CSV
seeds=$SEEDS_CSV
max_parallel=$MAX_PARALLEL
domain_base=$DOMAIN_BASE
pair_order=OFF_then_ON
EOF

run_pair() {
  local pair="$1" domain="$2"
  local house="${pair%%:*}" seed="${pair##*:}"
  local pair_root="$RUN_ROOT/$house/seed$seed"
  mkdir -p "$pair_root"
  echo "[$(date -u +%FT%TZ)] START $house seed=$seed domain=$domain" | tee "$pair_root/pair.log"
  local arm rc
  for arm in off on; do
    mkdir -p "$pair_root/$arm"
    set +e
    HOUSE="$house" SEED="$seed" ARM="$arm" RUN_ROOT="$RUN_ROOT" \
      CASE_OUTPUT_DIR="$pair_root/$arm" DOMAIN_ID="$domain" TIMEOUT_SEC="$TIMEOUT_SEC" \
      bash "$CASE_RUNNER" >>"$pair_root/$arm/runner.log" 2>&1
    rc=$?
    set -e
    echo "$rc" > "$pair_root/$arm/runner.rc"
    if (( rc != 0 )); then
      echo "[$(date -u +%FT%TZ)] FAIL $house seed=$seed arm=$arm rc=$rc" | tee -a "$pair_root/pair.log"
      return "$rc"
    fi
    if [[ ! -f "$pair_root/$arm/case_result.json" ]]; then
      echo "missing case_result.json for $house seed=$seed arm=$arm" | tee -a "$pair_root/pair.log"
      return 90
    fi
  done
  echo "[$(date -u +%FT%TZ)] DONE $house seed=$seed" | tee -a "$pair_root/pair.log"
}

# Fixed waves avoid ROS-domain reuse while an older job is still alive.
idx=0
fail=0
while (( idx < ${#pairs[@]} )); do
  pids=()
  labels=()
  for ((slot=0; slot<MAX_PARALLEL && idx<${#pairs[@]}; slot++,idx++)); do
    pair="${pairs[$idx]}"; domain=$((DOMAIN_BASE+slot))
    ( run_pair "$pair" "$domain" ) &
    pids+=("$!"); labels+=("$pair")
  done
  for j in "${!pids[@]}"; do
    if ! wait "${pids[$j]}"; then
      echo "PAIR_FAILED ${labels[$j]}" | tee -a "$RUN_ROOT/_batch/failures.txt"
      fail=1
    fi
  done
done

AGGREGATOR="${AGGREGATOR:-$(cd "$(dirname "$0")" && pwd)/aggregate_multiseed.py}"
python3 "$AGGREGATOR" "$RUN_ROOT" --out "$RUN_ROOT/_batch/MULTISEED_VERDICT.json" | tee "$RUN_ROOT/_batch/MULTISEED_VERDICT.stdout.txt"

if (( fail != 0 )); then exit 91; fi
