#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

python3 -m py_compile \
  v3_math.py \
  v3_adequacy.py \
  selftest_v3_math.py \
  selftest_v3_adequacy.py \
  observation_quotient_gate.py \
  local_tangent_information.py \
  local_pair_audit_v3.py \
  observation_adequacy.py \
  block_dynamic_marker.py \
  qualify_bridge_causal_contract.py \
  qualify_observation_support_contract.py \
  freeze_h02_reconstructed_context_manifest.py \
  h02_reconstructed_challenge_verdict.py \
  v12_response_bank_tangent_audit.py

python3 selftest_v3_math.py
python3 selftest_v3_adequacy.py

echo "CG_PC_CTT_V3_STATIC_AND_MATH_SELFTEST PASS"
