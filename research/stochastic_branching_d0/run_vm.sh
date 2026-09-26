#!/usr/bin/env bash
set -Eeuo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
task=/home/zyc/stochastic_branching_d0_20260926
cd "$task"
test -f freeze_commit.txt
test ! -e result
test ! -e repeat
python3 protocol/analyze_branching_d0.py --data-root /home/zyc/r0_stochastic_benchmark_20260924 --seed-matrix contracts/R0_SEED_MATRIX_18x16.tsv --out-dir result > analysis.log 2>&1
python3 protocol/analyze_branching_d0.py --data-root /home/zyc/r0_stochastic_benchmark_20260924 --seed-matrix contracts/R0_SEED_MATRIX_18x16.tsv --out-dir repeat > repeat.log 2>&1
python3 execution/finalize.py
