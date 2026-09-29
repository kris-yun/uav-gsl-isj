#!/usr/bin/env python3
"""Read-only source/wind/occupancy audit, including sealed House03 inputs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import struct

TOOLS = Path('/home/zyc/ocb_r2_s1_tools')
MASTER = TOOLS / 'OCB_R2_MASTER_MANIFEST_96.tsv'
CATALOG = TOOLS / 'ORIGINAL_CONFIG_CATALOG.tsv'
OUT = TOOLS / 'static_asset_audit'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    with MASTER.open(newline='') as f:
        master = list(csv.DictReader(f, delimiter='\t'))
    with CATALOG.open(newline='') as f:
        catalog = {int(x['config_index']): x for x in csv.DictReader(f, delimiter='\t')}
    assert len(master) == 96 and len(catalog) == 12
    OUT.mkdir(exist_ok=True)
    entries, h03_rows = [], []
    for idx in range(12):
        rows = [x for x in master if int(x['config_index']) == idx]
        assert len(rows) == 8
        meta = rows[0]
        old = catalog[idx]
        for key, mk in [('house', 'house'), ('source_id', 'source_id'), ('wind_config', 'wind_id'),
                        ('gas_type', 'gas_type')]:
            assert old[key] == meta[mk]
        assert [int(x['master_seed']) for x in rows] == [2026900000 + 100*idx + r for r in range(1,9)]
        assert meta['original_launch_sha256'] == old['launch_sha256']
        launch = Path(old['launch_path'])
        occupancy = Path(meta['occupancy'])
        assert launch.is_file() and occupancy.is_file()
        assert sha(launch) == old['launch_sha256']
        assert old['occupancy'] == str(occupancy)
        prefix = meta['wind_asset']
        hashes, cells = [], None
        for state in range(11):
            axis_sizes = []
            for axis in 'UVW':
                path = Path(f'{prefix}_{state}.csv_{axis}')
                assert path.is_file(), f'missing {path}'
                size = path.stat().st_size
                assert (size-4) % 8 == 0 and size > 4
                with path.open('rb') as fh:
                    assert struct.unpack('<I', fh.read(4))[0] == 999
                axis_sizes.append((size-4)//8)
                hashes.append({'state': state, 'axis': axis, 'path': str(path), 'size_bytes': size, 'sha256': sha(path)})
            assert len(set(axis_sizes)) == 1
            if cells is None:
                cells = axis_sizes[0]
            assert cells == axis_sizes[0]
        bundle_hash = hashlib.sha256(''.join(x['sha256'] for x in hashes).encode()).hexdigest()
        entry = {'config_index': idx, 'house': meta['house'], 'source_id': meta['source_id'],
                 'wind_id': meta['wind_id'], 'source_xyz': [meta[x] for x in ('source_x','source_y','source_z')],
                 'gas_type': meta['gas_type'], 'occupancy_path': str(occupancy),
                 'occupancy_sha256': sha(occupancy), 'wind_prefix': prefix,
                 'wind_bundle_sha256': bundle_hash, 'wind_state_count': 11,
                 'wind_cells_per_state': cells, 'wind_files': hashes,
                 'launch_path': str(launch), 'launch_sha256': sha(launch),
                 'master_seeds': [int(x['master_seed']) for x in rows],
                 'output_template': f'/home/zyc/ocb_r2_future/ocb_r2_cfg{idx:02d}_r{{replicate:02d}}',
                 'status': 'SEALED_NOT_RUN' if idx >= 8 else 'INPUTS_READY_NOT_RUN'}
        entries.append(entry)
        if idx >= 8:
            h03_rows.append({key: entry[key] for key in ('config_index','house','source_id','wind_id','gas_type','occupancy_path','occupancy_sha256','wind_prefix','wind_bundle_sha256','wind_state_count','wind_cells_per_state','launch_path','launch_sha256','output_template','status')}
                            | {'source_xyz': ','.join(entry['source_xyz']), 'master_seed_count': len(entry['master_seeds'])})
    (OUT / 'S1_STATIC_ASSET_AUDIT.json').write_text(json.dumps(entries, indent=2) + '\n')
    with (OUT / 'H03_SEALED_STATIC_READINESS.tsv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(h03_rows[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(h03_rows)
    print(json.dumps({'configs': len(entries), 'h03_sealed_configs': len(h03_rows),
                      'houses': {house: sum(x['house']==house for x in entries) for house in ('House01','House02','House03')}}))


if __name__ == '__main__':
    main()
