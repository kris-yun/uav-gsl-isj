#!/usr/bin/env python3
"""Repeat the frozen calculation, inventory assets, and make a compact review ZIP."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'evidence/tcma_d0'
ZIP = Path(r'D:\ZYC\A-gas\_staging\TCMA_D0_TARGET_CONDITIONED_ADEQUACY_REVIEW_20260929.zip')
OUTPUTS = [
    'TARGET_ADEQUACY.csv', 'SOURCE_ADEQUACY.csv', 'SIM_SELF_RESIDUALS.npz',
    'ADEQUACY_FREEZE.json', 'TCMA_D0_SOURCE_RESULTS.csv', 'TCMA_D0_RESULT.json',
]
FILES = [
    'research/tcma_d0/TCMA_D0_PREREG_20260929.md',
    'research/tcma_d0/CODEX_EXECUTE_ONLY.txt',
    'research/tcma_d0/compute_adequacy.py',
    'research/tcma_d0/evaluate_tcma_d0.py',
    'research/tcma_d0/finalize_tcma_d0.py',
    'research/tcma_d0/TCMA_D0_RESULT_20260929.md',
    'evidence/tcma_d0/TARGET_ADEQUACY.csv',
    'evidence/tcma_d0/SOURCE_ADEQUACY.csv',
    'evidence/tcma_d0/SIM_SELF_RESIDUALS.npz',
    'evidence/tcma_d0/ADEQUACY_FREEZE.json',
    'evidence/tcma_d0/TCMA_D0_SOURCE_RESULTS.csv',
    'evidence/tcma_d0/TCMA_D0_RESULT.json',
    'evidence/tcma_d0/DETERMINISTIC_REPEAT.json',
    'evidence/tcma_d0/ASSET_MANIFEST_SHA256.tsv',
    'evidence/aec_d0/PSEUDO_VECTORS.npz',
    'evidence/aec_d0/SIM_COMPETENCE_FREEZE.json',
    'evidence/aec_d0/ROUTE_POSITIONS_ONLY.json',
    'evidence/aec_d0/AEC_D0_SOURCE_RESULTS.csv',
    'evidence/aec_d0/AEC_D0_RESULT.json',
    'evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json',
    'evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json',
    'evidence/r1_centered_aod/assets/TARGET_PATHS_12x8x2x10.npy',
    'evidence/aod_house03_f1_full624_20260927/amended/TARGET_DATA_FREEZE.json',
    'research/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv',
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> bytes:
    return path.read_bytes()


def repeat():
    before = {n: sha(read(OUT / n)) for n in OUTPUTS}
    for script in ('compute_adequacy.py', 'evaluate_tcma_d0.py'):
        subprocess.run([sys.executable, str(ROOT / 'research/tcma_d0' / script)],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    after = {n: sha(read(OUT / n)) for n in OUTPUTS}
    assert before == after, {n: (before[n], after[n]) for n in OUTPUTS if before[n] != after[n]}
    (OUT / 'DETERMINISTIC_REPEAT.json').write_text(json.dumps({
        'byte_identical': True, 'file_count': len(OUTPUTS),
        'first_sha256': before, 'second_sha256': after,
        'repeated_scripts': ['compute_adequacy.py', 'evaluate_tcma_d0.py'],
    }, indent=2, sort_keys=True) + '\n')


def inventory():
    assert len(FILES) == len(set(FILES))
    content = {name: read(ROOT / name) for name in FILES if not name.endswith('ASSET_MANIFEST_SHA256.tsv')}
    lines = ['sha256\tbytes\tpath']
    for name, data in sorted(content.items()):
        lines.append(f'{sha(data)}\t{len(data)}\t{name}')
    manifest = ('\n'.join(lines) + '\n').encode()
    (OUT / 'ASSET_MANIFEST_SHA256.tsv').write_bytes(manifest)
    content['evidence/tcma_d0/ASSET_MANIFEST_SHA256.tsv'] = manifest
    return content


def package(content):
    decision = json.loads((OUT / 'TCMA_D0_RESULT.json').read_text())['decision']
    assert decision == 'TCMA_D0_NO_CROSS_HOUSE_TARGET_CONDITIONED_SIGNAL'
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert branch == 'research/tcma-d0-target-conditioned-adequacy-20260929'
    content['PACKAGE_META.json'] = (json.dumps({
        'branch': branch, 'commit': commit, 'decision': decision,
        'new_gaden_runs': 0, 'new_pmfs_forward_runs': 0, 'new_vgr_runs': 0,
        'purpose': 'Independent review of frozen TCMA source-level adequacy gate',
    }, indent=2, sort_keys=True) + '\n').encode()
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(content.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 29, 0, 0, 0))
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        for name, data in content.items():
            assert z.read(name) == data
    return {'path': str(ZIP), 'bytes': ZIP.stat().st_size,
            'sha256': sha(read(ZIP)), 'branch': branch, 'commit': commit,
            'decision': decision}


def main():
    repeat()
    print(json.dumps(package(inventory()), indent=2))


if __name__ == '__main__':
    main()
