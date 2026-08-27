#!/usr/bin/env bash
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$HERE"

python3 -m py_compile \
  v3_math.py \
  v3_adequacy.py \
  v3_bernoulli_adequacy.py \
  ctt_bank_io.py \
  materialize_h02_reconstructed_ctt_tensor.py \
  qualify_h02_reconstructed_analysis_contract.py \
  discover_h02_observation_event_support.py \
  verify_h02_reconstructed_bank_v1.py \
  selftest_v3_math.py \
  selftest_v3_adequacy.py \
  selftest_v3_bernoulli_adequacy.py \
  observation_quotient_gate.py \
  local_tangent_information.py \
  local_pair_audit_v3.py \
  observation_adequacy.py \
  block_dynamic_marker.py \
  qualify_bridge_causal_contract.py \
  qualify_observation_support_contract.py \
  freeze_h02_reconstructed_context_manifest.py \
  h02_reconstructed_challenge_verdict.py \
  v12_response_bank_tangent_audit.py \
  "$ROOT/closed_loop/cg_pc_ctt/v3_quotient_rank_posterior.py" \
  "$ROOT/closed_loop/cg_pc_ctt/selftest_v3_quotient_posterior.py"

python3 selftest_v3_math.py
python3 selftest_v3_adequacy.py
python3 selftest_v3_bernoulli_adequacy.py
python3 "$ROOT/closed_loop/cg_pc_ctt/selftest_v3_quotient_posterior.py"

echo "CG_PC_CTT_V3_STATIC_AND_MATH_SELFTEST PASS"
