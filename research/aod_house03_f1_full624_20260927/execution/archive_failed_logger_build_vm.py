#!/usr/bin/env python3
"""Preserve the failed new logger build; no source or gas data are removed."""
import json
from pathlib import Path

root = Path('/home/zyc/aod_house03_f1_full624_20260927').resolve()
source = root / 'timebase_logger'
target = root / 'timebase_logger_compile_attempt_1'
assert source.resolve().parent == target.resolve().parent == root
assert source.is_dir() and not target.exists()
assert not Path('/home/zyc/ros2_ws/aod_house03_f1_full624_targets_20260927').exists()
source.rename(target)
for name in ['timebase_build.log', 'timebase_launch.log']:
    p = root / name
    if p.exists():
        assert not (target / name).exists()
        p.rename(target / name)
(root / 'INFRA_LOGGER_REPAIR.json').write_text(json.dumps(dict(
    failed_build_preserved=str(target), original_failure='unresolved bsc_init/bsc_compress',
    repair='link the existing historical libbsc.so; seeded core unchanged',
    fresh_gaden_runs_at_repair=0, concentration_values_read=False), indent=2) + '\n')
