#!/usr/bin/env python3
"""Preserve a loader failure that occurred before the simulator main function."""
import json
from pathlib import Path

root = Path('/home/zyc/ros2_ws/aod_house03_f1_full624_targets_20260927').resolve()
source = root / 'source_0_replica_0'
target = root / 'source_0_replica_0_loader_attempt_1'
assert source.resolve().parent == target.resolve().parent == root
assert source.is_dir() and not target.exists()
assert not (source / 'realization').exists()
assert not (source / 'RESULT_TIME_MAP.tsv').exists()
assert 'error while loading shared libraries: libbsc.so' in (source / 'generation.log').read_text()
source.rename(target)
record = dict(preserved_directory=str(target), actual_plumes_generated=0,
              simulator_main_entered=False, target_values_read=False,
              reason='libbsc runtime search path; no simulator output existed')
Path('/home/zyc/aod_house03_f1_full624_20260927/INFRA_LOADER_REPAIR.json').write_text(
    json.dumps(record, indent=2) + '\n')
