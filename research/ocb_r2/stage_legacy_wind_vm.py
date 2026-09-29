#!/usr/bin/env python3
"""Convert approved 999-header split double wind files to native GADEN v3.

This is only a storage-layout conversion: each (U,V,W) double tuple is cast
to the float vector representation consumed by the frozen current simulator.
Original staged files are read-only and never modified.
"""
from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

SOURCE = Path('/home/zyc/ocb_r1_assets/h02_wind_reconstructed/3,5-1_slow')
DEST = Path('/home/zyc/ocb_r2_seeded_gaden/wind_compat')
STEM = '3,5-1_slow'
EXPECTED_CELLS = 256802


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(path: Path) -> array:
    raw = path.read_bytes()
    assert len(raw) == 4 + 8 * EXPECTED_CELLS
    assert struct.unpack_from('<I', raw, 0)[0] == 999
    values = array('d')
    values.frombytes(raw[4:])
    if sys.byteorder != 'little':
        values.byteswap()
    assert len(values) == EXPECTED_CELLS
    assert all(math.isfinite(v) and abs(v) <= 1e4 for v in values)
    return values


def main():
    assert not DEST.exists(), f'refusing to overwrite {DEST}'
    DEST.mkdir()
    inventory = []
    for index in range(11):
        inputs = [SOURCE / f'{STEM}_{index}.csv_{axis}' for axis in 'UVW']
        axes = [decode(path) for path in inputs]
        vec = array('f')
        for xyz in zip(*axes):
            vec.extend(xyz)
        if sys.byteorder != 'little':
            vec.byteswap()
        dest = DEST / f'{STEM}_{index}.csv_gaden'
        with dest.open('xb') as fh:
            fh.write(struct.pack('<ii', 3, 0))
            vec.tofile(fh)
        assert dest.stat().st_size == 8 + 12 * EXPECTED_CELLS
        inventory.append({'index': index, 'input_paths': [str(p) for p in inputs],
                          'input_sha256': [sha(p) for p in inputs],
                          'output_path': str(dest), 'output_sha256': sha(dest),
                          'cells': EXPECTED_CELLS})
    (DEST / 'WIND_LAYOUT_CONVERSION_MANIFEST.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(json.dumps({'states': len(inventory), 'cells_per_state': EXPECTED_CELLS,
                      'manifest_sha256': sha(DEST / 'WIND_LAYOUT_CONVERSION_MANIFEST.json')}))


if __name__ == '__main__':
    main()
