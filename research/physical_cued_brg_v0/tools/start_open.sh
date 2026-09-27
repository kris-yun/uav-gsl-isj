#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MARKED_REVIEW:?Set MARKED_REVIEW to the existing MARKED_ENCOUNTER_PMFS_D0_REVIEW_20260927.zip}"
python tools/import_open.py --marked-zip "$MARKED_REVIEW" --out data/open
python -m unittest discover -s tests -v
# Same data split, optimization budget and seed; no model-architecture search.
for v in brg gru ungated; do
  width=32; if [ "$v" = "gru" ]; then width=35; fi
  python tools/train.py --data data/open --out "trained/$v" --variant "$v" --hidden "$width" --epochs 30 --routes 8 --batch 48 --threads 2
 done
printf '\nNext: use integration/apply_humble_patch.py --dry-run on a NEW worktree.\n'
