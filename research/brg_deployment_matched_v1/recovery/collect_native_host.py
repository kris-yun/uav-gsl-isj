"""Archive-verified host orchestration for frozen Native OPEN VGR histories."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
NATIVE_ARCHIVE = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_OPEN_CONTINUOUS_20260928')
VGR_ARCHIVE = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_VGR_NATIVE_20260928')
RECEIPTS = ROOT / 'native_collection_receipts'
VM = 'zyc@192.168.111.128'
KEY = Path.home() / '.ssh' / 'id_ed25519_vm'
ACTIVE = '/home/zyc/brg_v1_active_case_20260928'
VM_CODE = '/home/zyc/brg_v1_recovery_20260928'
ZSTD = Path(r'D:\Anaconda\Library\bin\zstd.exe')


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def command(argv: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed: {result.stderr[-1500:]} {result.stdout[-800:]}')
    return result


def ssh(shell_text: str) -> str:
    return command(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
                    '-i', str(KEY), VM, shell_text]).stdout.strip()


def remote_json(shell_text: str) -> dict:
    # ROS children may print diagnostics before the final JSON receipt.
    stdout = ssh(shell_text)
    return json.loads(stdout.splitlines()[-1])


def verify_tar(path: Path, case: dict) -> None:
    command([str(ZSTD), '-t', str(path)])
    proc = subprocess.Popen([str(ZSTD), '-dc', str(path)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    listing = subprocess.run(['tar', '-tf', '-'], stdin=proc.stdout, capture_output=True, text=True)
    proc.stdout.close()
    if proc.wait() or listing.returncode:
        raise RuntimeError('VGR archive tar/zstd verification failed')
    names = listing.stdout.splitlines()
    required = ('_episode.npz', '_episode.json', '_raw/measurement_samples.csv',
                '_raw/measurement_events.csv', '_raw/measurement_blocks.csv',
                '_raw/beliefs.jsonl', '_raw/sim_pose_trace.csv')
    if not all(any(name.endswith(suffix) for name in names) for suffix in required):
        raise RuntimeError(f'VGR archive missing required event/log member for {case["case_id"]}')


def one(ordinal: int) -> dict:
    files = list((ROOT / 'v1_cases').glob(f'{ordinal:03d}_*.json'))
    if len(files) != 1:
        raise RuntimeError('frozen case file missing or ambiguous')
    case = json.loads(files[0].read_text())
    if case['ordinal'] != ordinal or case['split'] not in ('train', 'dev'):
        raise RuntimeError('case not eligible for training/development collection')
    run_id = case['case_id']
    if not re.fullmatch(r'[A-Za-z0-9_,.\-]+', run_id):
        raise RuntimeError('unsafe frozen run ID')
    original = NATIVE_ARCHIVE / (run_id + '.tar.zst')
    original_receipt = list((ROOT / 'receipts').glob(f'{ordinal:03d}_{run_id}.json'))
    if len(original_receipt) != 1 or not original.is_file():
        raise RuntimeError('verified native archive missing')
    if sha(original) != json.loads(original_receipt[0].read_text())['archive_sha256']:
        raise RuntimeError('native source archive drift')
    stem = f'native_{ordinal:03d}_{run_id}'
    package = VGR_ARCHIVE / (stem + '.tar.zst')
    receipt_path = RECEIPTS / f'{ordinal:03d}_{run_id}.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if sha(package) != receipt['archive_sha256']:
            raise RuntimeError('saved VGR archive drift')
        return receipt
    if package.exists():
        raise RuntimeError('unreceipted VGR package exists; inspect before continuing')
    remote_active = f'{ACTIVE}/{run_id}'
    if subprocess.run(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                       f'test -d {shlex.quote(remote_active)}/realization'],
                      capture_output=True).returncode != 0:
        remote_tar = f'{ACTIVE}/{run_id}.tar.zst'
        command(['scp', '-q', '-i', str(KEY), str(original), f'{VM}:{remote_tar}'])
        vm_sha = ssh(f'sha256sum {shlex.quote(remote_tar)}').split()[0]
        if vm_sha != sha(original):
            raise RuntimeError('VM copied native archive SHA mismatch')
        ssh(f'mkdir -p {shlex.quote(ACTIVE)} && tar -I zstd -C {shlex.quote(ACTIVE)} -xf {shlex.quote(remote_tar)} && rm -f -- {shlex.quote(remote_tar)}')
    if ssh(f'test -d {shlex.quote(remote_active)}/realization && echo READY') != 'READY':
        raise RuntimeError('native realization restore incomplete')
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
              f'python3 {VM_CODE}/collect_native_vm.py {action} {ordinal}')
    result = remote_json(f'bash -lc {shlex.quote(source)}')
    if result['status'] != 'VGR_NATIVE_COLLECTION_PACKAGE_READY' or result['ordinal'] != ordinal:
        raise RuntimeError('VM collection receipt mismatch')
    command(['scp', '-q', '-i', str(KEY), f'{VM}:{result["archive"]}', str(package)])
    actual = sha(package)
    if package.stat().st_size != result['archive_bytes'] or actual != result['archive_sha256']:
        raise RuntimeError('host package byte/SHA mismatch; VM data preserved')
    verify_tar(package, case)
    receipt = {**result, 'host_package': str(package),
               'native_archive_sha256': sha(original),
               'case_binding_sha256': sha(files[0]), 'science_use': 'training/development only'}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    cleaned = remote_json(f'python3 {VM_CODE}/collect_native_vm.py cleanup {ordinal} {actual}')
    if cleaned['status'] != 'VERIFIED_NATIVE_WORK_COPY_REMOVED':
        raise RuntimeError('VM cleanup did not confirm exact target')
    print(f'[{ordinal}/72] {case["split"]} {result["event_count"]} events, '
          f'{result["wall_time_s"]:.1f}s, package {package.stat().st_size/1e6:.1f}MB', flush=True)
    return receipt


def adopt_existing_13() -> dict:
    """Preserve the already validated 300 s Native pilot without rerunning it."""
    ordinal = 13
    case_file = next((ROOT / 'v1_cases').glob('013_*.json'))
    case = json.loads(case_file.read_text())
    receipt_path = RECEIPTS / f'013_{case["case_id"]}.json'
    package = VGR_ARCHIVE / f'native_013_{case["case_id"]}.tar.zst'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if sha(package) != receipt['archive_sha256']:
            raise RuntimeError('adopted first-pilot package drift')
        return receipt
    if package.exists():
        raise RuntimeError('unreceipted first-pilot package exists')
    vm_logs = '/home/zyc/brg_v1_logs_20260928'
    remote_package = f'/home/zyc/brg_v1_collection_packages_20260928/{package.name}'
    base = 'train013_native_v1valid'
    names = [base + '.json', base + '_raw', base + '_episode.npz', base + '_episode.json']
    shell = ('mkdir -p /home/zyc/brg_v1_collection_packages_20260928 && '
             f'tar -C {shlex.quote(vm_logs)} -cf - ' + ' '.join(shlex.quote(n) for n in names) +
             f' | zstd -T1 -1 -o {shlex.quote(remote_package)} && '
             f'sha256sum {shlex.quote(remote_package)}')
    remote_sha = ssh(shell).splitlines()[-1].split()[0]
    command(['scp', '-q', '-i', str(KEY), f'{VM}:{remote_package}', str(package)])
    if sha(package) != remote_sha:
        raise RuntimeError('adopted first-pilot host/VM SHA mismatch')
    verify_tar(package, case)
    receipt = {'status': 'VGR_NATIVE_COLLECTION_PACKAGE_READY', 'ordinal': 13,
               'case_id': case['case_id'], 'split': case['split'], 'host_package': str(package),
               'archive_bytes': package.stat().st_size, 'archive_sha256': remote_sha,
               'case_binding_sha256': sha(case_file), 'event_count': 53,
               'scientific_result': False, 'adopted_valid_300s_pilot': True}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    # Cleanup is limited to the exact first pilot after archive verification.
    cleanup = f'''python3 - <<'PY'
from pathlib import Path
import hashlib,shutil
a=Path({remote_package!r}); assert hashlib.sha256(a.read_bytes()).hexdigest()=={remote_sha!r}
logs=Path({vm_logs!r})
for name in {names!r}:
 p=logs/name; assert p.parent==logs
 if p.is_dir(): shutil.rmtree(p)
 elif p.exists(): p.unlink()
active=Path({(ACTIVE + '/' + case['case_id'])!r})
assert active.parent==Path({ACTIVE!r})
shutil.rmtree(active)
a.unlink()
print('VERIFIED_FIRST_PILOT_WORK_COPY_REMOVED')
PY'''
    if ssh(cleanup).splitlines()[-1] != 'VERIFIED_FIRST_PILOT_WORK_COPY_REMOVED':
        raise RuntimeError('adopted first-pilot VM cleanup failed')
    print(f'[13/72] adopted valid Native pilot, 53 events, package {package.stat().st_size/1e6:.1f}MB', flush=True)
    return receipt


def main() -> None:
    if not KEY.is_file() or not ZSTD.is_file():
        raise RuntimeError('VM key or zstd missing')
    VGR_ARCHIVE.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(exist_ok=True)
    if shutil.disk_usage(VGR_ARCHIVE).free < 10_000_000_000:
        raise RuntimeError('host archival volume has less than 10GB free')
    if len(sys.argv) > 1 and sys.argv[1] == 'adopt13':
        adopt_existing_13()
        return
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
