#!/usr/bin/env python3
"""Independent integrity check of every OCB-R2 qualification output file."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/zyc/ocb_r2_validation')
WIND = Path('/home/zyc/ocb_r2_seeded_gaden/wind_compat')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    conversion = json.loads((WIND / 'WIND_LAYOUT_CONVERSION_MANIFEST.json').read_text())
    assert len(conversion) == 11
    for state in conversion:
        for path, expected in zip(state['input_paths'], state['input_sha256']):
            assert sha(Path(path)) == expected
        assert sha(Path(state['output_path'])) == state['output_sha256']
    output_count = 0
    for arm in 'ABC':
        base = ROOT / f'RUN_{arm}'
        manifest = json.loads((base / 'RUN_MANIFEST.json').read_text())
        assert manifest['wind_layout_conversion_manifest_sha256'] == sha(WIND / 'WIND_LAYOUT_CONVERSION_MANIFEST.json')
        assert manifest['record_timeline_sha256'] == sha(base / 'RECORD_TIMELINE.tsv')
        with (base / 'OUTPUT_SHA256SUMS.tsv').open(newline='') as f:
            rows = list(csv.DictReader(f, delimiter='\t'))
        assert len(rows) == manifest['record_count'] == 1803
        assert set(x['name'] for x in rows) == set(f'iteration_{i}' for i in range(1803))
        for row in rows:
            path = base / row['name']
            assert path.stat().st_size == int(row['size_bytes'])
            assert sha(path) == row['sha256']
            output_count += 1
    report = {'verified_wind_input_files': 33, 'verified_converted_wind_files': 11,
              'verified_scientific_output_files': output_count,
              'all_checks_pass': True}
    (ROOT / 'INDEPENDENT_INTEGRITY_CHECK.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
