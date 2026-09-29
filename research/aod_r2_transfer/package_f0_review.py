#!/usr/bin/env python3
"""Verify deterministic F0 repeat and package independent review inputs/results."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[2]
F0 = REPO/'evidence/ocb_r2/aod_r2_f0'
OUT = Path('D:/ZYC/A-gas/_staging/AOD_R2_F0_NO_SIGNAL_REVIEW_20260929.zip')
REPEAT = F0/'AOD_R2_F0_DETERMINISTIC_REPEAT.json'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    first, second = F0/'score_pass1', F0/'score_pass2'
    names = ['AOD_R2_F0_RESULT.json', 'TARGET_RESULTS.tsv', 'GROUP_RESULTS.tsv',
             'CONTEXT_RESULTS.tsv', 'HOUSE_RESULTS.tsv']
    checks = {name: sha(first/name) for name in names}
    assert all(sha(second/name) == checks[name] for name in names)
    result = json.loads((first/'AOD_R2_F0_RESULT.json').read_text())
    assert result['decision'] == 'AOD_R2_F0_NO_SIGNAL'
    REPEAT.write_text(json.dumps(dict(byte_identical=True, files_sha256=checks,
                                      scoring_passes=2, decision=result['decision']),
                                 indent=2, sort_keys=True)+'\n')
    selected = []
    selected.extend(sorted(p for p in (REPO/'research/aod_r2_transfer').glob('*') if p.is_file()))
    selected.append(REPO/'research/amplitude_operator_decoupling_v0/amplitude_readout.py')
    selected.append(REPO/'research/marked_encounter_pmfs_d0/protocol/E1_HOUSE_PROBE_CONTRACTS.tsv')
    selected.extend(sorted(p for p in F0.rglob('*') if p.is_file()))
    native = REPO/'_staging/AOD_R2_F0_FROZEN_SNAPSHOTS.tar'
    assert sha(native) == json.loads((F0/'AOD_R2_F0_STAGED_SNAPSHOTS.json').read_text())['staged_tar_sha256']
    selected.append(native)
    assert len(selected) == len(set(selected))
    sums = {str(p.relative_to(REPO)).replace('\\', '/'): sha(p) for p in selected}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in selected:
            name = str(path.relative_to(REPO)).replace('\\', '/')
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        payload = ''.join(f'{digest}  {name}\n' for name, digest in sorted(sums.items()))
        info = zipfile.ZipInfo('SHA256SUMS', date_time=(2026, 9, 29, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, payload.encode())
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None and len(z.namelist()) == len(selected)+1
    print(json.dumps(dict(package=str(OUT), bytes=OUT.stat().st_size,
                          sha256=sha(OUT), included_files=len(selected),
                          deterministic_repeat=True), sort_keys=True))


if __name__ == '__main__':
    main()
