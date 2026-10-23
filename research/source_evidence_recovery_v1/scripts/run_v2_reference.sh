#!/usr/bin/env bash
set -euo pipefail
# CPU engineering reproducibility, not the native physical/scientific contract.
GSL_V2_RUN="${1:-runs/v2_reference_01}"
if [ -e "$GSL_V2_RUN" ]; then
  echo "Refuse to overwrite an existing evidence directory: $GSL_V2_RUN" >&2
  exit 2
fi
mkdir -p "$GSL_V2_RUN/receipts"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
python -m gsl_recovery.v2_cli doctor --out "$GSL_V2_RUN/receipts/environment.json"
python -m pytest -q --junitxml="$GSL_V2_RUN/receipts/tests.xml"
python -m gsl_recovery.v2_cli prepare-engineering --out "$GSL_V2_RUN/data" --seed 31
python -m gsl_recovery.v2_cli train-teacher --manifest "$GSL_V2_RUN/data/manifest.json" --bank "$GSL_V2_RUN/data/bank" --out "$GSL_V2_RUN/teacher" --epochs 8 --seed 23 --device cpu --wall-seconds 175
python - "$GSL_V2_RUN/teacher/training_receipt.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))['status'] == 'COMPLETE', 'Teacher training incomplete'
PY
python -m gsl_recovery.v2_cli build-targets --manifest "$GSL_V2_RUN/data/manifest.json" --teacher "$GSL_V2_RUN/teacher/model" --out "$GSL_V2_RUN/targets" --count 32 --seed 23 --order 8
python scripts/run_v2_engineering_matrix.py --manifest "$GSL_V2_RUN/data/manifest.json" --targets "$GSL_V2_RUN/targets" --out "$GSL_V2_RUN/matrix" --epochs 8
python -m gsl_recovery.v2_cli demo --model "$GSL_V2_RUN/matrix/projected_evidence/model" --out "$GSL_V2_RUN/active" --rounds 3 --draws 512 --eig-draws 16 --variant Bprime --m2 Bprime
echo "Engineering run complete. Inspect all results; scientific success is not inferred."
