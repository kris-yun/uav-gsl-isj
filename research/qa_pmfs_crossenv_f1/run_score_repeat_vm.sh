#!/usr/bin/env bash
set -Eeuo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /home/zyc/qa_pmfs_crossenv_f1_20260926
test -f pre_target_freeze_commit.txt
test ! -e result
test ! -e repeat
python3 execution/score_fresh.py --out result > scoring.log 2>&1
python3 execution/score_fresh.py --out repeat > repeat.log 2>&1
python3 execution/package_review_vm.py
