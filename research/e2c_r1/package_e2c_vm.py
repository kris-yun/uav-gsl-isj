#!/usr/bin/env python3
"""Package E2C provenance and OPEN data; never package sealed values."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-dir', type=Path, required=True)
    parser.add_argument('--code-dir', type=Path, required=True)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((args.data_dir / 'E2C_QC_SUMMARY.json').read_text(encoding='utf-8'))
    if report['decision'] != 'E2C_R1_BENCHMARK_COMPLETE_SEALED' or report['total_runs'] != 192:
        raise RuntimeError('benchmark QC incomplete')
    freeze_names = [
        'TIMEBASE_MAP.csv', 'TIMEBASE_PROVENANCE.json',
        'SOURCE_PANEL_8x3.tsv', 'SOURCE_PANEL_SELECTION_AUDIT.json',
        'PRIOR_EXPOSURE_AUDIT.json',
        'PRIOR_SOURCE_EXPOSURE_UNION.tsv', 'PRIOR_SOURCE_EXPOSURE_PROVENANCE.tsv',
        'PRIOR_SOURCE_EXPOSURE_AUDIT.json', 'PRIOR_SOURCE_EXPOSURE_BRANCH_AUDIT.json',
        'PRIOR_SOURCE_EXPOSURE_BRANCH_REFS.tsv',
        'CONFIRMATION_SOURCE_UNSEEN_AUDIT.tsv', 'SEED_MANIFEST_144.tsv',
        'SPLIT_MANIFEST.tsv', 'PRE_RUN_ASSET_SHA256.tsv', 'PRE_RUN_FREEZE.json',
    ]
    data_names = [
        'E2C_RUN_MANIFEST.tsv', 'E2C_ALL192_HASH_MANIFEST.tsv',
        'E2C_QC_SUMMARY.json', 'E2C_OPEN_DISCOVERY_2H_6S_8R_10x30.npy',
    ]
    files = [(args.freeze_dir / name, 'freeze/' + name) for name in freeze_names]
    code_names = [
        'E2C_R1_PREREG_20260929.md', 'E2C_R1_PRE_RUN_FREEZE_20260929.md',
        'E2C_R1_CONFIRMATION_REDESIGN_DECISION_20260929.md',
        'E2C_R1_144_PRE_RUN_FREEZE_20260929.md',
        'E2C_R1_TIMEBASE_RESULT_20260929.md', 'audit_e2_timebase.py',
        'select_e2c_sources_vm.py', 'prepare_e2c_freeze.py',
        'select_e2c_unexposed_sources_vm.py', 'build_prior_source_exposure_union.py',
        'audit_all_branch_source_metadata.py',
        'run_e2c_vm.py', 'finalize_e2c_vm.py', 'package_e2c_vm.py',
    ]
    files.extend((args.code_dir / name, 'code/' + name) for name in code_names)
    files.extend((args.data_dir / name, 'result/' + name) for name in data_names)
    for path, _ in files:
        if not path.is_file():
            raise RuntimeError(f'missing package file: {path}')
    if sha(args.data_dir / 'E2C_OPEN_DISCOVERY_2H_6S_8R_10x30.npy') != report['open_array_sha256']:
        raise RuntimeError('OPEN array hash mismatch')
    if sha(args.data_dir / 'E2C_ALL192_HASH_MANIFEST.tsv') != report['all192_manifest_sha256']:
        raise RuntimeError('all192 manifest hash mismatch')
    checksums = ''.join(f'{sha(path)}  {name}\n' for path, name in files).encode('utf-8')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise RuntimeError('refuse to overwrite existing review package')
    with tarfile.open(args.output, 'w:gz') as archive:
        for path, name in files:
            archive.add(path, arcname=name, recursive=False)
        info = tarfile.TarInfo('SHA256SUMS')
        info.size = len(checksums)
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(checksums))
    print(json.dumps({'package': str(args.output), 'bytes': args.output.stat().st_size,
                      'sha256': sha(args.output), 'file_count': len(files),
                      'sealed_scientific_values_included': False}, sort_keys=True))


if __name__ == '__main__':
    main()
