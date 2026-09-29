#!/usr/bin/env python3
"""Package frozen R0 inputs, code, and both deterministic scoring passes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[3]
E = REPO/'evidence/ocb_r2/mechanism_census_r0'
OUT = Path('D:/ZYC/A-gas/_staging/OCB_R2_MECHANISM_CENSUS_R0_REVIEW_20260930.zip')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    scientific = sorted(p for p in E.rglob('*') if p.is_file())
    protocol = [REPO/'research/ocb_r2/OCB_R2_SOURCE_INFORMATION_MECHANISM_CENSUS_R0.md',
                REPO/'evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv',
                REPO/'evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv']
    code = sorted(p for p in (REPO/'research/ocb_r2/mechanism_census_r0').glob('*') if p.is_file())
    selected = sorted(set(scientific+protocol+code))
    assert len(selected) > 90
    result = json.loads((E/'R0_MECHANISM_SUMMARY.json').read_text())
    assert result['decision'] == 'OCB_R2_MECH_CROSS_TIME_STABLE'
    repeat = json.loads((E/'R0_DETERMINISTIC_REPEAT.json').read_text())
    assert repeat['byte_identical'] and repeat['scoring_passes'] == 2
    sums = {}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in selected:
            name = str(path.relative_to(REPO)).replace('\\', '/')
            data = path.read_bytes()
            sums[name] = sha(data)
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        payload = ''.join(f'{digest}  {name}\n' for name, digest in sorted(sums.items())).encode()
        info = zipfile.ZipInfo('SHA256SUMS', date_time=(2026, 9, 30, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, payload)
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None
        for name, digest in sums.items():
            assert sha(z.read(name)) == digest
    print(json.dumps(dict(package=str(OUT), bytes=OUT.stat().st_size,
                          sha256=sha(OUT.read_bytes()), included_files=len(selected)), sort_keys=True))


if __name__ == '__main__':
    main()
