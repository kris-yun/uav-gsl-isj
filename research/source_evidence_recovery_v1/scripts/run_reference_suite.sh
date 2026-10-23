#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_root"
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export PYTHONPATH="$task_root/src${PYTHONPATH:+:$PYTHONPATH}"
run_dir="${1:-runs/reference_v1}"
mkdir -p "$run_dir"
python -m gsl_recovery doctor --out "$run_dir/environment.json"
python -m pytest -q --junitxml="$run_dir/tests.xml"
python -m gsl_recovery native-replay --root examples/native_b4 --out "$run_dir/native_b4"
python -m gsl_recovery generate-controlled --out "$run_dir/data" --episodes 64 --length 10 --seed 11
python -m gsl_recovery audit-data --manifest "$run_dir/data/manifest.json" --training --out "$run_dir/data_qualification.json"
python -m gsl_recovery train --manifest "$run_dir/data/manifest.json" --variant Bprime --out "$run_dir/model" --maxiter 200
python -m gsl_recovery train-diagnosis --manifest "$run_dir/data/manifest.json" --model "$run_dir/model/model.npz" --out "$run_dir/diagnosis" --maxiter 300
python -m gsl_recovery.m2_diagnosis.benchmark --manifest "$run_dir/data/manifest.json" --model "$run_dir/model/model.npz" --diagnosis "$run_dir/diagnosis/diagnosis.npz" --out "$run_dir/diagnosis_budget"
python -m gsl_recovery evaluate --manifest "$run_dir/data/manifest.json" --model "$run_dir/model/model.npz" --out "$run_dir/offline"
python -m gsl_recovery demo --model "$run_dir/model/model.npz" --diagnosis "$run_dir/diagnosis/diagnosis.npz" --out "$run_dir/active" --rounds 3 --draws 128
python -m gsl_recovery matrix --manifest "$run_dir/data/manifest.json" --config configs/controlled_matrix.yaml --out "$run_dir/matrix"
