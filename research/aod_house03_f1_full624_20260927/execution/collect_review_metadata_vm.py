#!/usr/bin/env python3
"""Collect only metadata after the signed timebase HOLD; never open gas files."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

R = Path('/home/zyc/aod_house03_f1_full624_20260927')
TARGET = Path('/home/zyc/ros2_ws/aod_house03_f1_full624_targets_20260927')


def main():
    audit = json.loads((R / 'TIMEBASE_AUDIT.json').read_text())
    assert audit['decision'] == 'AOD_F1_HOLD_TIMEBASE'
    dest = R / 'review_metadata'
    dest.mkdir(exist_ok=False)
    inventory = {}
    for folder, names in [
        ('source_0_replica_0', ['RESULT_TIME_MAP.tsv', 'RELEASE_TIME_METADATA.tsv',
                              'RUN_CONFIGURATION.json', 'generation.log']),
        ('source_0_replica_0_loader_attempt_1', ['RUN_CONFIGURATION.json', 'generation.log'])]:
        out = dest / folder
        out.mkdir()
        for name in names:
            original = TARGET / folder / name
            copied = out / name
            shutil.copyfile(original, copied)
            inventory[str(copied.relative_to(dest))] = hashlib.sha256(copied.read_bytes()).hexdigest()
    usage = shutil.disk_usage(R)
    allocated = int(subprocess.check_output(['du', '-s', '-B1', str(R / 'candidate_forward')], text=True).split()[0])
    mem = {line.split(':', 1)[0]: int(line.split()[1]) * 1024
           for line in Path('/proc/meminfo').read_text().splitlines() if len(line.split()) == 3}
    runs = [p for p in TARGET.iterdir() if p.is_dir() and (p / 'realization').is_dir()]
    assert [p.name for p in runs] == ['source_0_replica_0']
    capacity = dict(vm_cpu_count=os.cpu_count(), vm_available_disk_bytes=usage.free,
                    vm_available_memory_bytes=mem['MemAvailable'],
                    candidate_forward_allocated_bytes=allocated,
                    candidate_forward_rows=54912, approved_gaden_runs=96,
                    actual_generated_plumes=len(runs), remaining_95_not_started=True,
                    old_data_deleted=False, candidate_bank_preserved=True,
                    concentration_values_read=False, inventory=inventory)
    (R / 'FINAL_CAPACITY_AND_METADATA_AUDIT.json').write_text(json.dumps(capacity, indent=2) + '\n')
    print(json.dumps(capacity, indent=2))


if __name__ == '__main__':
    main()
