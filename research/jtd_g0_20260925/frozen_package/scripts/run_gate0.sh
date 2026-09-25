#!/usr/bin/env bash
set -euo pipefail

echo "JTD-G0 wrapper template"
echo "Codex must replace <repo_runner> only after implementing the repo-local runner."
echo "Frozen config: config/jtd_g0_frozen.yaml"

# Example only:
# python <repo_runner> \
#   --config config/jtd_g0_frozen.yaml \
#   --evidence-root evidence/jtd_g0_20260925
#
# python scripts/validate_evidence.py evidence/jtd_g0_20260925
