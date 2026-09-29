#!/usr/bin/env python3
"""Independently recheck all staged House02 wind states against historical runs."""

import csv
import hashlib
from pathlib import Path

BASE = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02')
STAGE = Path('/home/zyc/ocb_r1_assets/h02_wind_reconstructed')
OUT = Path('/home/zyc/ocb_r1_assets/RECONSTRUCTED_H02_WIND_STATE_MATCH.tsv')
PLAN = Path('/home/zyc/RECONSTRUCTED_H02_WIND_STAGING_PLAN.tsv')
CONFIGS = (
    ('3,5-1_fast', '10', '0.00_-1.00_0.20'),
    ('3,5-1_slow', '10', '0.00_-1.00_0.20'),
    ('4,5-3_fast', '13', '1.00_-2.30_-0.10'),
    ('4,5-3_slow', '13', '1.00_-2.30_-0.10'),
)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def staged_state_sha(wind, index):
    h = hashlib.sha256()
    for axis in 'UVW':
        with (STAGE / wind / f'{wind}_{index}.csv_{axis}').open('rb') as stream:
            assert len(stream.read(4)) == 4
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
    return h.hexdigest()


def main():
    with PLAN.open(encoding='utf-8', newline='') as stream:
        plan = list(csv.DictReader(stream, delimiter='\t'))
    if len(plan) != 176:
        raise RuntimeError('Staging plan count changed')
    expected = {r['relative_path'] for r in plan}
    actual = {str(p.relative_to(STAGE)).replace('\\', '/') for p in STAGE.rglob('*') if p.is_file()}
    if expected != actual:
        raise RuntimeError('Staging tree differs from frozen plan')
    for row in plan:
        if sha(STAGE / row['relative_path']) != row['sha256']:
            raise RuntimeError(f"Staged file hash mismatch: {row['relative_path']}")
    match_count = 0
    with OUT.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(('wind', 'state', 'staging_payload_sha256',
                         'historical_saved_wind_sha256', 'match'))
        for wind, gas, xyz in CONFIGS:
            folder = f'FilamentSimulation_gasType_{gas}_sourcePosition_{xyz}'
            for index in range(11):
                old = BASE / 'gas_simulations' / wind / folder / 'wind' / f'wind_iteration_{index}'
                a, b = staged_state_sha(wind, index), sha(old)
                passed = a == b
                writer.writerow((wind, index, a, b, 'PASS' if passed else 'FAIL'))
                match_count += passed
    if match_count != 44:
        raise RuntimeError(f'Only {match_count}/44 wind states matched')
    print(f'{len(plan)}/176 staged files and {match_count}/44 wind states matched')


if __name__ == '__main__':
    main()
