#!/usr/bin/env python3
"""Read-only comparison of House02 source wind components with historical run snapshots."""

import csv
import hashlib
from pathlib import Path

BASE = Path('/mnt/hgfs/workspace/GADEN_files/scenarios/House02')
OUT = Path('/home/zyc/h02_wind_lineage_r1_audit')
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


def component_sha(directory, wind, index):
    files = [directory / wind / f'{wind}_{index}.csv_{axis}' for axis in 'UVW']
    if not all(path.is_file() for path in files):
        return ''
    h = hashlib.sha256()
    for path in files:
        with path.open('rb') as stream:
            header = stream.read(4)
            if len(header) != 4:
                raise ValueError(path)
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    with (OUT / 'HISTORICAL_WIND_MATCH.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(('wind', 'state', 'nested_historical_path', 'historical_sha256',
                         'outer_historical_sha256', 'B_components_sha256', 'A_components_sha256',
                         'B_matches_historical', 'A_matches_historical'))
        for wind, gas, xyz in CONFIGS:
            folder = f'FilamentSimulation_gasType_{gas}_sourcePosition_{xyz}'
            for index in range(11):
                suffix = Path('gas_simulations') / wind / folder / 'wind' / f'wind_iteration_{index}'
                original = BASE / 'House02' / suffix
                outer = BASE / suffix
                original_sha = sha(original)
                outer_sha = sha(outer) if outer.is_file() else ''
                bsha = component_sha(BASE / 'House02' / 'wind_simulations', wind, index)
                asha = component_sha(BASE / 'wind_simulations', wind, index)
                writer.writerow((wind, index, original, original_sha, outer_sha, bsha, asha,
                                 bsha == original_sha, asha == original_sha if asha else 'N/A'))
    with (OUT / 'CONFLICT_CSV_FORMAT.tsv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(('tree', 'state', 'path', 'size_bytes', 'row_count_including_header',
                         'malformed_width_rows', 'ends_with_newline'))
        for label, root in (('A', BASE / 'wind_simulations'),
                            ('B', BASE / 'House02' / 'wind_simulations')):
            for index in range(11):
                path = root / '4,5-3_fast' / f'4,5-3_fast_{index}.csv'
                if not path.is_file():
                    continue
                rows = bad = 0
                with path.open(newline='') as csv_file:
                    for row in csv.reader(csv_file):
                        rows += 1
                        bad += len(row) != 6
                with path.open('rb') as binary:
                    binary.seek(-1, 2)
                    newline = binary.read(1) == b'\n'
                writer.writerow((label, index, path, path.stat().st_size, rows, bad, newline))


if __name__ == '__main__':
    main()
