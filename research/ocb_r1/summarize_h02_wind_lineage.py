#!/usr/bin/env python3
"""Prepare read-only House02 lineage tables and a future staging manifest."""

import csv
from pathlib import Path, PurePosixPath

ROOT = Path('evidence/ocb_r1/h02_wind_asset_lineage')
A = PurePosixPath('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/wind_simulations')
B = PurePosixPath('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02/wind_simulations')
GAS_A = PurePosixPath('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/gas_simulations')
GAS_B = PurePosixPath('/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02/gas_simulations')


def read(name):
    with (ROOT / name).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def write(name, columns, rows):
    with (ROOT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    a = {r['relative_path']: r for r in read('A_FILES.tsv')}
    b = {r['relative_path']: r for r in read('B_FILES.tsv')}
    historical = read('HISTORICAL_WIND_MATCH.tsv')
    assert len(a) == 113 and len(b) == 176 and len(historical) == 44
    assert all(r['B_matches_historical'] == 'True' for r in historical)
    assert all(r['outer_historical_sha256'] == r['historical_sha256'] for r in historical)
    assert sum(r['A_matches_historical'] == 'True' for r in historical) == 28

    third = []
    for wind, gas, xyz in (
        ('3,5-1_fast', '10', '0.00_-1.00_0.20'),
        ('3,5-1_slow', '10', '0.00_-1.00_0.20'),
        ('4,5-3_fast', '13', '1.00_-2.30_-0.10'),
        ('4,5-3_slow', '13', '1.00_-2.30_-0.10'),
    ):
        subset = [r for r in historical if r['wind'] == wind]
        observed_a = [r for r in subset if r['A_matches_historical'] != 'N/A']
        folder = f'FilamentSimulation_gasType_{gas}_sourcePosition_{xyz}'
        for root, label in ((GAS_B, 'nested'), (GAS_A, 'outer')):
            third.append(dict(path=str(root / wind / folder / 'wind'),
                              relationship=f'{label} historical GADEN saved wind sequence, binary encoding',
                              file_count=11,
                              matching_A=f'{sum(r["A_matches_historical"] == "True" for r in observed_a)}/{len(observed_a)} complete states available in A',
                              matching_B='11/11 exact component-payload SHA256',
                              notes='Contains wind_iteration_0..10; not a same-format CFD text copy; original gas-run output includes full U/V/W wind fields.'))
    write('THIRD_COPY_CANDIDATES.tsv',
          ('path', 'relationship', 'file_count', 'matching_A', 'matching_B', 'notes'), third)

    staging = []
    for relative, b_item in sorted(b.items()):
        a_item = a.get(relative)
        if a_item and a_item['sha256'] == b_item['sha256']:
            selected = A / relative
            reason = 'A identical to B; preserve original launch-tree byte content'
        else:
            selected = B / relative
            reason = 'B historical-run-matched full asset; A absent or truncated'
        staging.append(dict(relative_path=relative, planned_staging_path='RECONSTRUCTED_H02_WIND_STAGING/' + relative,
                            source_path=str(selected), source_tree='A' if selected.is_relative_to(A) else 'B',
                            sha256=b_item['sha256'], reason=reason))
    assert len(staging) == 176 and sum(r['source_tree'] == 'A' for r in staging) == 112
    assert sum(r['source_tree'] == 'B' for r in staging) == 64
    write('RECONSTRUCTED_H02_WIND_STAGING_PLAN.tsv',
          ('relative_path', 'planned_staging_path', 'source_path', 'source_tree', 'sha256', 'reason'), staging)
    print('third candidates:', len(third), 'future staging entries:', len(staging))


if __name__ == '__main__':
    main()
