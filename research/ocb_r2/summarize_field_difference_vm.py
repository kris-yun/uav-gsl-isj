#!/usr/bin/env python3
"""Summarize physical filament-field differences between S1 and S2."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import zlib

import numpy as np

ROOT = Path('/home/zyc/ocb_r2_validation')


def filaments(path: Path) -> np.ndarray:
    blob = path.read_bytes()
    assert blob[:13] == b'GADEN_RESULT\x00'
    assert blob[13] == 1, 'Only zlib format expected in this qualification'
    expected = struct.unpack_from('<Q', blob, 14)[0]
    raw = zlib.decompress(blob[22:])
    assert len(raw) == expected
    marker = raw.find(b'filaments')
    assert marker >= 8 and raw.find(b'filaments', marker + 1) < 0
    assert struct.unpack_from('<Q', raw, marker - 8)[0] == 9
    count = struct.unpack_from('<Q', raw, marker + 9)[0]
    start = marker + 17
    assert len(raw) - start == 16 * count
    return np.frombuffer(raw, dtype='<f4', count=4*count, offset=start).reshape(count, 4)


def main():
    counts_a, counts_b, centroid_distance = [], [], []
    for i in range(1803):
        aa = filaments(ROOT / 'RUN_A' / f'iteration_{i}')
        bb = filaments(ROOT / 'RUN_B' / f'iteration_{i}')
        counts_a.append(len(aa))
        counts_b.append(len(bb))
        if len(aa) and len(bb):
            ca = aa[:, :3].mean(axis=0, dtype=np.float64)
            cb = bb[:, :3].mean(axis=0, dtype=np.float64)
            centroid_distance.append(float(np.linalg.norm(ca-cb)))
    delta = np.abs(np.array(counts_a)-np.array(counts_b))
    result = {
        'record_count': 1803,
        'filament_count_A_mean': float(np.mean(counts_a)),
        'filament_count_B_mean': float(np.mean(counts_b)),
        'records_with_different_filament_count': int(np.count_nonzero(delta)),
        'filament_count_abs_difference_median': float(np.median(delta)),
        'filament_count_abs_difference_max': int(np.max(delta)),
        'centroid_distance_m_median': float(np.median(centroid_distance)),
        'centroid_distance_m_q95': float(np.quantile(centroid_distance, 0.95)),
        'centroid_distance_m_max': float(np.max(centroid_distance)),
        'centroid_records_compared': len(centroid_distance),
        'first_record_count_A_B': [counts_a[0], counts_b[0]],
        'last_record_count_A_B': [counts_a[-1], counts_b[-1]],
    }
    out = ROOT / 'FIELD_DIFFERENCE_SUMMARY.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
