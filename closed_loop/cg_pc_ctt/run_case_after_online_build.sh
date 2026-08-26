#!/usr/bin/env bash
set -Eeo pipefail

# Adapter used as CASE_RUNNER by run_multiseed_matrix.sh after the actual
# CG-PC-CTT online binary/launch path is built.
#
# Required:
#   CGPC_ONLINE_RUNNER=/absolute/path/to/online_one_arm.sh
# The inner runner receives HOUSE,SEED,ARM,CASE_OUTPUT_DIR,DOMAIN_ID,TIMEOUT_SEC
# but receives NO source truth. It must write:
#   $CASE_OUTPUT_DIR/final_posterior.csv
# Optional:
#   $CASE_OUTPUT_DIR/first_release_s.txt
#
# This outer wrapper introduces truth only AFTER the online runner exits and
# calls the external evaluator. Truth therefore cannot leak into runtime.

: "${HOUSE:?}" "${SEED:?}" "${ARM:?}" "${CASE_OUTPUT_DIR:?}" "${DOMAIN_ID:?}"
CGPC_ONLINE_RUNNER="${CGPC_ONLINE_RUNNER:?set CGPC_ONLINE_RUNNER}"
TIMEOUT_SEC="${TIMEOUT_SEC:-300}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$CASE_OUTPUT_DIR"

if [[ ! -x "$CGPC_ONLINE_RUNNER" ]]; then echo "online runner not executable: $CGPC_ONLINE_RUNNER" >&2; exit 2; fi

# Run online arm without truth in its environment.
env -u SOURCE_X -u SOURCE_Y -u TRUTH_X -u TRUTH_Y \
  HOUSE="$HOUSE" SEED="$SEED" ARM="$ARM" CASE_OUTPUT_DIR="$CASE_OUTPUT_DIR" \
  DOMAIN_ID="$DOMAIN_ID" TIMEOUT_SEC="$TIMEOUT_SEC" \
  bash "$CGPC_ONLINE_RUNNER"

POST="$CASE_OUTPUT_DIR/final_posterior.csv"
[[ -f "$POST" ]] || { echo "missing $POST" >&2; exit 90; }

case "$HOUSE" in
  House01) TX=-0.40; TY=-2.90 ;;
  House02) TX=0.00; TY=-1.00 ;;
  House03) TX=-0.45; TY=1.90 ;;
  *) echo "unsupported HOUSE=$HOUSE" >&2; exit 2 ;;
esac
FIRST=""
if [[ -f "$CASE_OUTPUT_DIR/first_release_s.txt" ]]; then FIRST="$(cat "$CASE_OUTPUT_DIR/first_release_s.txt")"; fi
BIN_SHA=""
[[ -f "$CASE_OUTPUT_DIR/online_binary.sha256" ]] && BIN_SHA="$(cat "$CASE_OUTPUT_DIR/online_binary.sha256")"

ARGS=(--posterior-csv "$POST" --out "$CASE_OUTPUT_DIR/case_result.json" --house "$HOUSE" --seed "$SEED" --arm "$ARM" --truth-x "$TX" --truth-y "$TY")
[[ -n "$FIRST" ]] && ARGS+=(--first-release-s "$FIRST")
[[ -n "$BIN_SHA" ]] && ARGS+=(--binary-sha256 "$BIN_SHA")
python3 "$HERE/evaluate_case_posterior.py" "${ARGS[@]}"
