#!/usr/bin/env bash
set -Ee -o pipefail
printf 'E1_FROZEN_GEOMETRY_MANIFEST\n'
cat /home/zyc/E1_CROSS_HOUSE_CONTRACT_REVIEW_20260925_FINAL/evidence/e1/E1_GEOMETRY_PROVENANCE.md
printf 'E1_GEOMETRY_FILE_NAMES\n'
find /home/zyc/E1_CROSS_HOUSE_CONTRACT_REVIEW_20260925_FINAL/inputs/geometry -maxdepth 3 -type f | sort
printf 'SOURCE_BANK_HEADER_SAMPLES\n'
for p in /home/zyc/bigreen_gate1a_exact_20260924/source_bank.tsv /home/zyc/PASI_D0_S3_W2_REVIEW_20260924/frozen_inputs/source_bank.tsv /home/zyc/CESS_D1R_REFERENCE_REVIEW_20260925/repo/source_bank.tsv; do
  printf '%s\n' "$p"
  sed -n '1,3p' "$p"
done
printf 'FROZEN_RUNTIME_CONFIGURATION_NAMES\n'
find /home/zyc/rmfe_v2_runtime_causal_20260814_a2_002 -maxdepth 5 -type f \( -name '*.yaml' -o -name '*launch*.py' -o -name '*args*.txt' -o -name '*settings*.json' -o -name '*config*.json' \) | sort
printf 'NAVIGATION_PARAMETERS_SOURCE_NAMES\n'
find /home/zyc/ros2_ws/src /home/zyc/native_pmfs_recovery_v1/src -maxdepth 8 -type f \( -name '*.yaml' -o -name '*.py' \) 2>/dev/null | grep -E 'nav|House03|house03|navigation|simulation|GSL' | sed -n '1,55p'
printf 'FROZEN_NAVIGATION_METADATA\n'
cat /home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H03_seed0/off/geometry_export/pruned_meta.json
