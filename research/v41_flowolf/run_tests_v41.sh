#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python -m pytest tests/test_v41.py -q
python demo_v41.py --steps 20 --seed 9001 --out V41_SYNTHETIC_20.json