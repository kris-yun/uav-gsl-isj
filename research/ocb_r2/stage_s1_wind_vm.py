#!/usr/bin/env python3
"""Layout-convert frozen H01/H02 split wind assets without changing values."""
from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

TOOLS = Path('/home/zyc/ocb_r2_s1_tools')
ROOT = Path('/home/zyc/ocb_r2_seeded_gaden/wind_compat_s1')
AUDIT = TOOLS / 'static_asset_audit/S1_STATIC_ASSET_AUDIT.json'
CONFIG = TOOLS / 'OCB_R2_S1_FROZEN_CONFIGS.json'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def decode(path: Path, cells: int) -> array:
    raw = path.read_bytes()
    assert len(raw) == 4 + 8*cells
    assert struct.unpack_from('<I', raw, 0)[0] == 999
    values = array('d')
    values.frombytes(raw[4:])
    if sys.byteorder != 'little':
        values.byteswap()
    assert len(values) == cells
    assert all(math.isfinite(v) and abs(v) <= 1e4 for v in values)
    return values


def main():
    audit = {int(x['config_index']): x for x in json.loads(AUDIT.read_text())}
    configs = json.loads(CONFIG.read_text())
    assert len(configs) == 8
    ROOT.mkdir(exist_ok=True)
    summary = []
    for cfg in range(8):
        entry = audit[cfg]
        run_id = f'ocb_r2_cfg{cfg:02d}_r01'
        params = configs[run_id]['parameters']
        if cfg == 5:
            # Reuse the already qualified bytes/path for the identical wind.
            path = Path('/home/zyc/ocb_r2_seeded_gaden/wind_compat/WIND_LAYOUT_CONVERSION_MANIFEST.json')
            assert path.is_file()
            original = json.loads(path.read_text())
            assert len(original) == 11
            for state in original:
                for p, digest in zip(state['input_paths'], state['input_sha256']):
                    assert sha(Path(p)) == digest
                assert sha(Path(state['output_path'])) == state['output_sha256']
            assert params['wind_data'] == '/home/zyc/ocb_r2_seeded_gaden/wind_compat/3,5-1_slow'
            summary.append({'config_index': cfg, 'conversion_manifest': str(path), 'sha256': sha(path), 'reused_qualified': True})
            continue
        dest = ROOT / f'cfg{cfg:02d}'
        assert not dest.exists(), f'refusing overwrite: {dest}'
        dest.mkdir()
        cells = int(entry['wind_cells_per_state'])
        prefix = entry['wind_prefix']
        runtime_prefix = params['wind_data']
        assert runtime_prefix == str(dest / entry['wind_id'])
        by_key = {(int(x['state']), x['axis']): x for x in entry['wind_files']}
        inventory = []
        for state in range(11):
            inputs = [Path(f'{prefix}_{state}.csv_{axis}') for axis in 'UVW']
            for axis, path in zip('UVW', inputs):
                assert sha(path) == by_key[state, axis]['sha256']
            axes = [decode(path, cells) for path in inputs]
            vec = array('f')
            for xyz in zip(*axes):
                vec.extend(xyz)
            if sys.byteorder != 'little':
                vec.byteswap()
            output = Path(f'{runtime_prefix}_{state}.csv_gaden')
            with output.open('xb') as f:
                f.write(struct.pack('<ii', 3, 0))
                vec.tofile(f)
            assert output.stat().st_size == 8 + 12*cells
            inventory.append({'state': state, 'input_paths': list(map(str, inputs)),
                              'input_sha256': [by_key[state, axis]['sha256'] for axis in 'UVW'],
                              'output_path': str(output), 'output_sha256': sha(output), 'cells': cells})
        manifest = dest / 'WIND_LAYOUT_CONVERSION_MANIFEST.json'
        manifest.write_text(json.dumps(inventory, indent=2) + '\n')
        summary.append({'config_index': cfg, 'conversion_manifest': str(manifest), 'sha256': sha(manifest), 'reused_qualified': False})
    out = TOOLS / 'static_asset_audit/S1_WIND_LAYOUT_CONVERSION_SUMMARY.json'
    out.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'configs': len(summary), 'new_conversions': 7, 'reused_qualified': 1, 'summary_sha256': sha(out)}))


if __name__ == '__main__':
    main()
