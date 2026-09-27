#!/usr/bin/env bash
set -Ee -o pipefail
printf 'GEOMETRY_TABLE_CANDIDATES\n'
find /home/zyc -maxdepth 6 -type f \( -iname '*source*bank*.tsv' -o -iname '*house03*geometry*.tsv' -o -iname '*house03*source*.tsv' -o -iname 'E1*json' -o -name 'E1_HOUSE_PROBE_CONTRACTS.tsv' \) 2>/dev/null | head -n 70
printf 'CANONICAL_H03_GEOMETRY\n'
find /home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4 -maxdepth 5 -type f \( -name 'pruned_meta.json' -o -name 'pruned_occupancy.bin' -o -name '*launch*.py' -o -name '*config*.yaml' \) 2>/dev/null | grep H03 | head -n 35
printf 'H03_WIND_CONFIG_ASSETS\n'
find /mnt/hgfs/workspace/GADEN_files/scenarios/House03 -maxdepth 5 -type f \( -name '1-2,5_fast_*.csv' -o -name '*.yaml' -o -name 'OccupancyGrid3D.csv' \) 2>/dev/null | head -n 35
printf 'E1_GEOMETRY_DIRECTORIES\n'
find /home/zyc -maxdepth 4 -type d \( -name '*e1*' -o -name '*benchmark*' -o -name '*geometry*' \) 2>/dev/null | head -n 40
