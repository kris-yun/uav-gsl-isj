"""Host-side frozen OPEN VGR coverage collection with per-case archival QC."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

from collect_native_host import ROOT, NATIVE_ARCHIVE, KEY, VM, ACTIVE, VM_CODE, ZSTD
from collect_native_host import sha, command, ssh, remote_json, verify_tar

ARCHIVE = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_VGR_COVERAGE_20260928')
RECEIPTS = ROOT / 'coverage_collection_receipts'


def one(ordinal: int) -> dict:
    files = list((ROOT / 'v1_cases').glob(f'{ordinal:03d}_*.json'))
    if len(files) != 1:
        raise RuntimeError('frozen case file missing or ambiguous')
    case = json.loads(files[0].read_text())
    if case['ordinal'] != ordinal or case['split'] not in ('train', 'dev'):
        raise RuntimeError('case outside frozen OPEN train/dev coverage budget')
    run_id = case['case_id']
    if not re.fullmatch(r'[A-Za-z0-9_,.\-]+', run_id):
        raise RuntimeError('unsafe frozen run ID')
    native_asset = NATIVE_ARCHIVE / (run_id + '.tar.zst')
    native_receipt = list((ROOT / 'receipts').glob(f'{ordinal:03d}_{run_id}.json'))
    if len(native_receipt) != 1 or sha(native_asset) != json.loads(native_receipt[0].read_text())['archive_sha256']:
        raise RuntimeError('verified original native plume unavailable')
    stem = f'coverage_{ordinal:03d}_{run_id}'
    package = ARCHIVE / (stem + '.tar.zst')
    receipt_path = RECEIPTS / f'{ordinal:03d}_{run_id}.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if sha(package) != receipt['archive_sha256']:
            raise RuntimeError('coverage archive checksum drift')
        return receipt
    if package.exists():
        raise RuntimeError('unreceipted coverage archive exists')
    active = f'{ACTIVE}/{run_id}'
    present = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                              f'test -d {shlex.quote(active)}/realization'],
                             capture_output=True).returncode == 0
    if not present:
        remote_tar = f'{ACTIVE}/{run_id}.tar.zst'
        command(['scp', '-q', '-i', str(KEY), str(native_asset), f'{VM}:{remote_tar}'])
        if ssh(f'sha256sum {shlex.quote(remote_tar)}').split()[0] != sha(native_asset):
            raise RuntimeError('copied native plume SHA mismatch')
        ssh(f'tar -I zstd -C {shlex.quote(ACTIVE)} -xf {shlex.quote(remote_tar)} && rm -f -- {shlex.quote(remote_tar)}')
    remote_out = f'/home/zyc/brg_v1_logs_20260928/{stem}.json'
    completed_prior = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                                      f'test -f {shlex.quote(remote_out)}'],
                                     capture_output=True).returncode == 0
    action = 'resume-encode' if completed_prior else 'collect'
    source = ('source /opt/ros/humble/setup.bash && '
              'source /home/zyc/ros2_ws/install/setup.bash && '
              'source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash && '
              'source /home/zyc/ros2_ws/brg_closedloop_20260927/install/setup.bash && '
              'export LD_LIBRARY_PATH=/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH && '
              f'python3 {VM_CODE}/collect_coverage_vm.py {action} {ordinal}')
    result = remote_json(f'bash -lc {shlex.quote(source)}')
    if result['status'] != 'VGR_COVERAGE_COLLECTION_PACKAGE_READY' or result['ordinal'] != ordinal:
        raise RuntimeError('coverage VM receipt mismatch')
    command(['scp', '-q', '-i', str(KEY), f'{VM}:{result["archive"]}', str(package)])
    actual = sha(package)
    if actual != result['archive_sha256'] or package.stat().st_size != result['archive_bytes']:
        raise RuntimeError('host/VM coverage archive SHA or byte mismatch')
    verify_tar(package, case)
    receipt = {**result, 'host_package': str(package),
               'native_archive_sha256': sha(native_asset),
               'case_binding_sha256': sha(files[0]),
               'coverage_profile': 'frozen source-blind 300s legal-cell graph route',
               'science_use': 'training/development only'}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    cleaned = remote_json(f'python3 {VM_CODE}/collect_coverage_vm.py cleanup {ordinal} {actual}')
    if cleaned['status'] != 'VERIFIED_COVERAGE_WORK_COPY_REMOVED':
        raise RuntimeError('VM coverage cleanup not confirmed')
    print(f'[{ordinal}/72] coverage {case["split"]} {result["event_count"]} events, '
          f'{result["wall_time_s"]:.1f}s, {package.stat().st_size/1e6:.1f}MB', flush=True)
    return receipt


def main() -> None:
    if not KEY.is_file() or not ZSTD.is_file():
        raise RuntimeError('VM key or zstd missing')
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(exist_ok=True)
    if shutil.disk_usage(ARCHIVE).free < 10_000_000_000:
        raise RuntimeError('host archival volume has less than 10GB free')
    begin = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 72
    if not 1 <= begin <= end <= 72:
        raise RuntimeError('range outside frozen 72 cases')
    for ordinal in range(begin, end + 1):
        case = json.loads(next((ROOT / 'v1_cases').glob(f'{ordinal:03d}_*.json')).read_text())
        if case['split'] in ('train', 'dev'):
            one(ordinal)


if __name__ == '__main__':
    main()
