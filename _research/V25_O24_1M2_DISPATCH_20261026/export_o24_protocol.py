#!/usr/bin/env python3
"""Read-only O24 qualification/export. Standard library, Python >=3.9.

This program does not change the freeze, build a binary, start ROS, repair an
asset, or invent a missing parameter. All output goes to a new outside directory.
"""
import argparse
import csv
import hashlib
import json
import math
import pathlib
import sys
from datetime import datetime, timezone

IDENTITY = 'PMFS-O24-PORT-GMRF-PAPERSTOP1M2-SCREEN12-20261024'
AUTHOR = 'a8d5a764b7cbfc1d5d1887aebfe890e2c75d7533'
LOCAL = '631145657461c41840f6844f118de57d1e747ea4'
ELF = 'e63fadfdb5b4b20ea6936f38c3a1d5edf0d1e9e236ed8d78a4846b009aefed78'
LOCK_HASHES = {
    'e376f7a02be97b40332f8c7d98c9abcfa08c89e7c957c319f89e73722e65293e': 'original Windows CRLF, 2967 bytes',
    '68e4cda7038b2c9f28db00c012bd4d55c60a344e4cb711779504b458607553f0': 'verified Git LF blob ee086dfe21c82e6b76a8bea65f74cd5ca516b9ad, 2883 bytes',
}
ROLES = ['A2_R01_REFERENCE','B2_R01','B2_R02','B2_R03','B2_R04','B2_R05','A2_R02','A2_R03','C3_R01','C3_R02','D4_R01','E3_R01']
LEGAL = ['A2_R01_REFERENCE','A2_R02','A2_R03','C3_R01','C3_R02','D4_R01','E3_R01']
DEFAULT_ROOT = 'D:/ZYC/A-gas/workspace/FROZEN_O24_1M2_SCREEN12_20261024'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))


def write_new(path, value):
    with pathlib.Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def validate_lock(lock, cases):
    require(lock['freeze_identity'] == IDENTITY, 'Wrong O24 experiment identity')
    require(lock['source_commit'] == LOCAL and lock['public_author_snapshot'] == AUTHOR, 'Code ancestry mismatch')
    require(lock['ELF_sha256'] == ELF and lock['source_file_count'] == 128, 'Binary/source identity mismatch')
    s = lock['normal_stop']
    require(s['value'] == 1.0 and s['unit'] == 'm2' and s['comparison'] == 'strictly less than', 'Not strict variance < 1 m2')
    c = lock['baseline_core']
    require(c['sourceDiscriminationPower'] == .2 and c['useWindGroundTruth'] is False and c['USE_GADEN'] is False, 'D/information/build permission mismatch')
    t = lock['time_protocol']
    require(t['BasicSim_speed'] == 1.0 and t['use_sim_time'] is True and t['gas_world_looping'] is False, 'Clock/loop identity mismatch')
    require(t['maxSearchTime'] == 1e9 and t['fixed_300_or_600_normal_stop'] is False, 'Normal stop must not be replaced by a short time cap')
    require(lock['roles'] == ROLES and lock['legal_source_roles'] == LEGAL, 'Frozen role list changed')
    require([r['role'] for r in cases] == ROLES, 'Case order changed')
    for row in cases:
        p = row['GSL_parameters']
        require(p['convergence_thr'] == 1.0 and p['sourceDiscriminationPower'] == .2, row['role'] + ': threshold/D mismatch')
        require(p['useWindGroundTruth'] is False and p['use_sim_time'] is True and p['maxSearchTime'] == 1e9, row['role'] + ': permission/clock mismatch')
        require(p['noiseSTDev'] == c['noiseSTDev_by_case'][row['case']], row['role'] + ': noise mismatch')
        require(row['native_ELF_sha256'] == ELF, row['role'] + ': ELF mismatch')
        require((row['source_domain'] == 'LEGAL') == (row['role'] in LEGAL), row['role'] + ': source-domain class mismatch')


def check_full_freeze(root, live_elf=None):
    """Strict original byte hashes, including original line endings. No repair."""
    manifest = load_json(root / 'FREEZE_MANIFEST_SHA256.json')
    declared = {r['path'] for r in manifest['files']}
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
              if p.is_file() and p.name != 'FREEZE_MANIFEST_SHA256.json' and '__pycache__' not in p.parts}
    require(declared == actual, 'Freeze file inventory mismatch: missing=' + str(sorted(declared-actual)[:15]) + '; unexpected=' + str(sorted(actual-declared)[:15]))
    for row in manifest['files']:
        p = (root / row['path']).resolve()
        require(root == p.parent or root in p.parents, 'Unsafe manifest path')
        require(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'], 'Original byte hash mismatch: ' + row['path'])
    source = load_json(root / 'FROZEN_SOURCE_IDENTITY_128.json')['files']
    require(len(source) == 128, 'Source inventory is not 128 files')
    for row in source:
        p = root / 'source_snapshot' / row['path']
        b = p.read_bytes()
        require(hashlib.sha256(b).hexdigest() == row['sha256'], 'Source hash mismatch: ' + row['path'])
        require(hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == row['frozen_commit_blob'], 'Source Git blob mismatch: ' + row['path'])
    require(digest(root / 'binaries/gsl_actionserver_node') == ELF, 'Frozen ELF mismatch')
    if live_elf:
        require(digest(live_elf) == ELF, 'Live ELF mismatch')
    cases = load_json(root / 'FROZEN_CASES.json')
    for row in cases:
        gate = load_json(root / row['configuration_prefix'] / 'runtime/BASELINE_PARAMETER_GATE.json')
        require(gate['checked'] == row['GSL_parameters'], 'Captured ROS parameter mismatch: ' + row['role'])
    return {'status': 'PASS_ORIGINAL_FREEZE_BYTES', 'files_checked': len(declared), 'source_files_checked': 128,
            'live_binary_checked': bool(live_elf), 'new_ROS_runs': 0}


def archive_inventory(cases, archive_root=None):
    rows = []
    for row in cases:
        a = row['full_original_archive']
        original = a.get('archive')
        p = pathlib.Path(original.replace('\\', '/')) if original else None
        if archive_root and original:
            p = pathlib.Path(archive_root) / pathlib.PureWindowsPath(original).name
        valid = bool(p and p.is_file() and digest(p) == a.get('archive_sha256'))
        if row['role'] == 'B2_R04':
            action = 'RETAIN_TECHNICAL_ABORT_NO_REPLACEMENT'
        elif valid:
            action = 'VERIFY_AND_EXPORT_EXISTING_TRACE_NO_NEW_GOAL'
        else:
            action = 'LOCATE_OR_RESTORE_EXACT_ARCHIVE_BEFORE_CONSIDERING_NEW_RUN'
        rows.append({'role': row['role'], 'source_domain': row['source_domain'], 'archive': str(p) if p else None,
                     'expected_sha256': a.get('archive_sha256'), 'archive_verified': valid,
                     'recommended_action': action, 'new_goal_authorized_by_this_tool': False})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline-root', default=DEFAULT_ROOT)
    ap.add_argument('--out-root', required=True, help='New directory outside the immutable freeze')
    ap.add_argument('--metadata-only', action='store_true', help='Inspect the observed Git metadata; never qualifies local execution')
    ap.add_argument('--live-elf', help='Optional Linux/VM binary path, SHA checked before launch elsewhere')
    ap.add_argument('--archive-root', help='Existing full_runs directory; filenames/hashes remain frozen')
    args = ap.parse_args()
    root, out = pathlib.Path(args.baseline_root).resolve(), pathlib.Path(args.out_root).resolve()
    require(root not in out.parents and out != root, 'Output must be outside the immutable freeze')
    require(not out.exists(), 'Output already exists; choose a new receipt directory')
    lock_path = root / 'BASELINE_LOCK.json'
    lock_hash = digest(lock_path)
    require(lock_hash in LOCK_HASHES, 'Unknown lock bytes; do not silently normalize or edit the freeze')
    lock, cases = load_json(lock_path), load_json(root / 'FROZEN_CASES.json')
    validate_lock(lock, cases)
    published = load_json(pathlib.Path(__file__).with_name('O24_BASELINE_PROTOCOL_LOCK.json'))
    require(lock == published['actual_baseline_lock'], 'Local lock differs from the audited snapshot')
    require(cases == published['frozen_cases'], 'Local complete case parameters differ from audited snapshot')
    if args.metadata_only:
        integrity = {'status': 'METADATA_ONLY_NOT_RUNTIME_QUALIFICATION', 'new_ROS_runs': 0}
    else:
        integrity = check_full_freeze(root, args.live_elf)
    archive_rows = archive_inventory(cases, args.archive_root)
    result = dict(published)
    result['local_verification'] = {'UTC': datetime.now(timezone.utc).isoformat(), 'baseline_root': str(root),
        'observed_lock_sha256': lock_hash, 'encoding_identity': LOCK_HASHES[lock_hash], 'integrity': integrity}
    # Physical playback assets, live domain ownership, actual timing and clocks need
    # Codex's VM preflight. A file hash guard cannot certify them or launch ROS.
    result['execution_ready'] = False
    result['remaining_runtime_gates'] = ['exact physical-world/time-map hashes', 'live ELF/process/domain ownership',
        'captured actual ROS parameter equality', 'native sensor and clock rate preflight', 'new output path isolation']
    out.mkdir(parents=True, exist_ok=False)
    write_new(out / 'O24_BASELINE_PROTOCOL_LOCK.local.json', result)
    write_new(out / 'ROLE_REUSE_PLAN.json', {'frozen_roles': ROLES, 'roles': archive_rows, 'run_policy': 'REUSE_FIRST_NO_SILENT_REPEATS'})
    write_new(out / 'LOCAL_QUALIFICATION_RECEIPT.json', result['local_verification'])
    print(json.dumps({'status': integrity['status'], 'out_root': str(out), 'execution_ready': False,
                      'archives_verified': sum(x['archive_verified'] for x in archive_rows), 'new_ROS_runs': 0}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'REJECT_WITHOUT_MODIFYING_FREEZE', 'error': str(error), 'new_ROS_runs': 0}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
