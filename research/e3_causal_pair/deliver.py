"""Freeze receipts and package completed results. Never performs propagation."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from analyze import O, load, put

REPO = Path(__file__).resolve().parents[2]
DOWNLOADS = Path('C:/Users/50176/Downloads')


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def payload():
    return sorted(path for path in O.rglob('*') if path.is_file()
                  and '__pycache__' not in path.parts
                  and path.name != 'PAYLOAD_SHA256.json')


def prepare():
    assert load(O / 'PORTABLE_RECOMPUTATION_QA.json')['status'].startswith('PASS_')
    assert load(O / 'FINAL_FROZEN_O24_GUARD.json')['status'] == 'PASS'
    for path in Path(__file__).parent.iterdir():
        if path.is_file():
            shutil.copy2(path, O / 'code' / path.name)
    shutil.copy2(Path(__file__).parent / 'README.md', O / 'README_复算.md')
    receipt = dict(
        status='COMPUTATION_COMPLETE_INDEPENDENT_RECOMPUTATION_PASS',
        primary_verdict=load(O / 'SCIENTIFIC_VERDICT.json')['primary_attribution'],
        physical_worlds=4, queries=2416, new_point_candidate_forwards=4,
        original_queried_frames_archived=95, new_ROS=0, neural_training=0,
        preregistered_output_cap_bytes=128 * 1024 * 1024,
        known_execution_wall_s=load(O / 'event_control/RECEIPT.json')['combined_execution_wall_s'],
        first_failed_compiler_CPU='UNKNOWN_AS_DOCUMENTED',
        native_baseline_source_commit='631145657461c41840f6844f118de57d1e747ea4',
        native_baseline_ELF_sha256='e63fadfdb5b4b20ea6936f38c3a1d5edf0d1e9e236ed8d78a4846b009aefed78',
        parent_audit_commit='01b2a9507590b770503e138151ede211c0a08b82',
        portable_result_files_byte_identical=19,
        no_whole_domain_new_algorithm_improvement_claim=True,
        no_unique_warmup_cause_claim=True,
        payload_bytes_before_delivery_receipt=sum(path.stat().st_size for path in payload()))
    assert receipt['payload_bytes_before_delivery_receipt'] < 128 * 1024 * 1024
    put(O / 'FINAL_DELIVERY_RECEIPT.json', receipt)
    destination = Path(__file__).parent / 'evidence'
    destination.mkdir(exist_ok=True)
    names = ['SCIENTIFIC_VERDICT.json', 'PREREGISTERED_CAUSAL_CONTRACT.json',
             'INPUT_IDENTITIES.json', 'ANALYSIS_SUMMARY.json',
             'INDEPENDENT_QA.json', 'PORTABLE_RECOMPUTATION_QA.json',
             'FINAL_FROZEN_O24_GUARD.json', 'FINAL_DELIVERY_RECEIPT.json',
             'ORDINARY_RESPONSE_RELIABILITY_GATE.json', 'AGE_INFERENCE_QA.json',
             'ENGINEERING_FIRST_FAILURES.json', 'NEW_WORLD_IDENTITY_REGISTRY.json',
             '中文科学裁决报告.md', 'FOR_PRO_交接说明.md']
    names += [path.name for path in O.glob('*.csv')]
    for name in names:
        shutil.copy2(O / name, destination / name)
    print(json.dumps(dict(prepared_evidence=len(names), output=str(O)), ensure_ascii=False))


def archive():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO,
                                       encoding='utf8').strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin',
                                      'refs/heads/codex/o24-e3-causal-pair-20261025'],
                                     cwd=REPO, encoding='utf8').split()[0]
    assert revision == remote
    put(O / 'GITHUB_DELIVERY_RECEIPT.json',
        dict(commit=revision, branch='codex/o24-e3-causal-pair-20261025',
             remote_verified=True,
             url='https://github.com/kris-yun/uav-gsl-isj/commit/' + revision))
    files = payload()
    manifest = [dict(path=path.relative_to(O).as_posix(), bytes=path.stat().st_size,
                     sha256=sha(path)) for path in files]
    put(O / 'PAYLOAD_SHA256.json', manifest)
    files.append(O / 'PAYLOAD_SHA256.json')
    size = sum(path.stat().st_size for path in files)
    assert size < 128 * 1024 * 1024, size
    target = DOWNLOADS / 'O24_E3_CAUSAL_PAIR_EVIDENCE_20261025.zip'
    assert not target.exists(), 'Do not overwrite a delivered archive'
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as archive_file:
        for path in files:
            archive_file.write(path, 'E3_CAUSAL_PAIR_20261025/' + path.relative_to(O).as_posix())
    with zipfile.ZipFile(target) as archive_file:
        assert archive_file.testzip() is None
        for item in manifest:
            raw = archive_file.read('E3_CAUSAL_PAIR_20261025/' + item['path'])
            assert len(raw) == item['bytes']
            assert hashlib.sha256(raw).hexdigest() == item['sha256']
        assert len(archive_file.namelist()) == len(manifest) + 1
    digest = sha(target)
    target.with_suffix('.zip.sha256').write_text(digest + '  ' + target.name + '\n', encoding='ascii')
    final = dict(status='PASS_COMPLETE_ZIP_READBACK_AND_PAYLOAD_SHA256',
                 zip=str(target), zip_bytes=target.stat().st_size,
                 zip_sha256=digest, payload_files=len(manifest),
                 uncompressed_payload_bytes=size,
                 below_scientific_output_cap_128MiB=True,
                 commit=revision, github_remote_verified=True,
                 physical_forward_stage_already_complete=True,
                 packaging_additional_physical_calls=0)
    put(target.with_suffix('.zip.receipt.json'), final)
    shutil.copy2(O / '中文科学裁决报告.md',
                 DOWNLOADS / 'O24_E3_最小因果归因_中文报告_20261025.md')
    shutil.copy2(O / 'FOR_PRO_交接说明.md',
                 DOWNLOADS / 'O24_E3_给Pro交接说明_20261025.md')
    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    argument = argparse.ArgumentParser()
    argument.add_argument('mode', choices=['prepare', 'archive'])
    options = argument.parse_args()
    prepare() if options.mode == 'prepare' else archive()
