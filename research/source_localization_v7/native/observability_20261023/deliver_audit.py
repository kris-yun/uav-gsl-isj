"""Package this completed bounded audit; never query or generate physical data."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[2]
DELIVERY = Path('D:/ZYC/A-gas/_deliverables')
NAME = 'V7_SOURCE_PAIR_OBSERVABILITY_AUDIT_20261023'
PARENT = '061ecf5ddea0a59dcf932b5038ad646b7af454a4'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8', newline='\n')


def package():
    DELIVERY.mkdir(parents=True, exist_ok=True)
    destination = DELIVERY / (NAME + '.zip')
    if destination.exists():
        raise FileExistsError(destination)
    excluded_dirs = {'.venv', 'local_assets', '__pycache__', '.pytest_cache', '.git'}
    files = []
    for base, dirs, names in os.walk(PROJECT):
        dirs[:] = sorted(d for d in dirs if d not in excluded_dirs)
        for name in sorted(names):
            p = Path(base) / name
            rel = p.relative_to(PROJECT)
            if p.suffix in ('.obj', '.lib', '.exp'):
                continue
            if len(rel.parts) == 1 and (name.endswith('.log') or name == 'install-native-v7.log'):
                continue
            files.append(p)
    entries = {p.relative_to(PROJECT).as_posix(): sha(p) for p in files}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=PROJECT, text=True).strip()
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=PROJECT, text=True).strip()
    receipt = {
        'git_commit': commit, 'branch': branch, 'parent_commit': PARENT,
        'payloads': len(entries), 'new_physical_worlds': 0, 'new_ROS': 0,
        'M1_threshold_changed': False, 'new_M1_M2_M3_fit': 0,
        'sealed_data_opened': False, 'original_raw_gas_archives_included': False,
        'derived_TRAIN_and_selected_DEV_arrays_included': True,
        'prior_negative_V7_results_preserved': True,
        'next_proposal_is_not_execution_authorization': True,
        'native_query_dll': 'previously compiled read-only component; source and parity receipts included'
    }
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for p in files:
            archive.write(p, NAME + '/' + p.relative_to(PROJECT).as_posix())
        archive.writestr(NAME + '/MANIFEST_SHA256.json', json.dumps(entries, indent=2))
        archive.writestr(NAME + '/DELIVERY_RECEIPT.json', json.dumps(receipt, indent=2))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for relative, digest in entries.items():
            assert hashlib.sha256(archive.read(NAME + '/' + relative)).hexdigest() == digest
    receipt.update(zip_path=str(destination), zip_bytes=destination.stat().st_size,
                   zip_sha256=sha(destination), payload_sha_verification='PASS')
    write(DELIVERY / (NAME + '.receipt.json'), receipt)
    (DELIVERY / (NAME + '.sha256')).write_text(
        receipt['zip_sha256'] + '  ' + destination.name + '\n', encoding='ascii')
    (DELIVERY / (NAME + '_中文裁决.md')).write_bytes(
        (PROJECT / 'SOURCE_PAIR_OBSERVABILITY_AUDIT.md').read_bytes())
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


def verify():
    archive_path = DELIVERY / (NAME + '.zip')
    qa_root = DELIVERY / ('_qa_' + NAME)
    if qa_root.exists():
        raise FileExistsError(qa_root)
    qa_root.mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        for info in archive.infolist():
            resolved = (qa_root / info.filename).resolve()
            assert resolved.is_relative_to(qa_root.resolve())
        archive.extractall(qa_root)
    extracted = qa_root / NAME
    entries = json.loads((extracted / 'MANIFEST_SHA256.json').read_text())
    for relative, digest in entries.items():
        assert sha(extracted / relative) == digest, relative
    command = [sys.executable, str(extracted / 'native/observability_20261023/verify_audit.py')]
    proc = subprocess.run(command, cwd=extracted, text=True, capture_output=True)
    (qa_root / 'fresh_verify.log').write_text(proc.stdout + proc.stderr, encoding='utf-8')
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads((extracted / 'results/source_pair_observability_20261023/INDEPENDENT_QA.json').read_text())
    assert result['scalar_known_profile_checks'] == 624
    assert result['selected_DEV_scalar_scores_recomputed'] == 92
    write(DELIVERY / (NAME + '.fresh_qa.json'), {
        'status': 'PASS', 'zip_sha256': sha(archive_path), 'payload_hashes_checked': len(entries),
        'command': command, 'exit_code': proc.returncode, 'raw_gas_files_required': False,
        'TRAIN_scalar_checks': 624, 'DEV_score_checks': 92,
        'log_path': str(qa_root / 'fresh_verify.log')
    })
    print('FRESH_EXTRACT_QA_PASS', len(entries), proc.stdout.strip())


if __name__ == '__main__':
    if sys.argv[1:] == ['package']:
        package()
    elif sys.argv[1:] == ['verify']:
        verify()
    else:
        raise SystemExit('usage: deliver_audit.py package|verify')
