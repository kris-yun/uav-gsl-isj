"""Execute the frozen eight-case, four-arm VGR development evaluation."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

from collect_native_host import ROOT, NATIVE_ARCHIVE, KEY, VM, ACTIVE, VM_CODE, ZSTD
from collect_native_host import sha, command, ssh, remote_json

ARCHIVE = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_EVAL32_20260928')
RECEIPTS = ROOT / 'eval_collection_receipts'
MODELS = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_MODELS_20260928')
ARMS = ('native_pmfs', 'candidate_gru', 'brg', 'brg_ungated')


def preflight() -> dict:
    freeze_path = ROOT / 'V1_EVAL8_FROZEN_MANIFEST.json'
    freeze = json.loads(freeze_path.read_text())
    if (freeze['status'] != 'BRG_V1_8_CASE_4_ARM_EVALUATION_FROZEN' or
            freeze['expected_run_count'] != 32):
        raise RuntimeError('eight-case 32-run evaluation manifest missing')
    vm_freeze = f'{VM_CODE}/V1_EVAL8_FROZEN_MANIFEST.json'
    if ssh(f'sha256sum {shlex.quote(vm_freeze)}').split()[0] != sha(freeze_path):
        raise RuntimeError('VM eight-case eval manifest drift')
    final = MODELS / 'FINAL_CHECKPOINT_FREEZE.json'
    frozen_models = json.loads(final.read_text())
    if frozen_models['status'] != 'BRG_V1_FINAL_MODELS_FROZEN_BEFORE_EVAL':
        raise RuntimeError('final weights not frozen')
    remote = '/home/zyc/brg_v1_models_20260928/FINAL_CHECKPOINT_FREEZE.json'
    if ssh(f'sha256sum {remote}').split()[0] != sha(final):
        raise RuntimeError('host/VM final model manifest drift')
    for arm in ARMS[1:]:
        item = frozen_models['arms'][arm]
        host_path = MODELS / f'final_{arm}_best.pt'
        if sha(host_path) != item['sha256'] or ssh(f'sha256sum {shlex.quote(item["path"])}').split()[0] != item['sha256']:
            raise RuntimeError(f'final {arm} checkpoint SHA drift')
    return freeze


def verify_eval_package(path: Path, ordinal: int, arm: str) -> None:
    command([str(ZSTD), '-t', str(path)])
    proc = subprocess.Popen([str(ZSTD), '-dc', str(path)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    listing = subprocess.run(['tar', '-tf', '-'], stdin=proc.stdout, capture_output=True, text=True)
    proc.stdout.close()
    if proc.wait() or listing.returncode:
        raise RuntimeError('eval compressed archive integrity failure')
    names = listing.stdout.splitlines()
    stem = f'eval_{arm}_{ordinal:03d}_'
    required = ('.json', '_raw/gaden_player.log')
    if not all(any(name.startswith(stem) and name.endswith(s) for name in names)
               for s in required):
        raise RuntimeError('eval archive missing required member')


def one(case: dict, arm: str) -> dict:
    ordinal, run_id = case['ordinal'], case['case_id']
    if arm not in ARMS or not re.fullmatch(r'[A-Za-z0-9_,.\-]+', run_id):
        raise RuntimeError('unsafe eval arm/case identity')
    native_asset = NATIVE_ARCHIVE / (run_id + '.tar.zst')
    native_receipt = list((ROOT / 'receipts').glob(f'{ordinal:03d}_{run_id}.json'))
    if len(native_receipt) != 1 or sha(native_asset) != json.loads(native_receipt[0].read_text())['archive_sha256']:
        raise RuntimeError('frozen eval plume archive missing')
    stem = f'eval_{arm}_{ordinal:03d}_{run_id}'
    package = ARCHIVE / (stem + '.tar.zst')
    receipt_path = RECEIPTS / (stem + '.json')
    if receipt_path.exists():
        saved = json.loads(receipt_path.read_text())
        if sha(package) != saved['archive_sha256']:
            raise RuntimeError('saved eval archive drift')
        return saved
    if package.exists():
        raise RuntimeError('unreceipted eval archive exists')
    active = f'{ACTIVE}/{run_id}'
    present = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-i', str(KEY), VM,
                              f'test -d {shlex.quote(active)}/realization'],
                             capture_output=True).returncode == 0
    if not present:
        remote_tar = f'{ACTIVE}/{run_id}.tar.zst'
        command(['scp', '-q', '-i', str(KEY), str(native_asset), f'{VM}:{remote_tar}'])
        if ssh(f'sha256sum {shlex.quote(remote_tar)}').split()[0] != sha(native_asset):
            raise RuntimeError('VM eval plume restore SHA mismatch')
        ssh(f'tar -I zstd -C {shlex.quote(ACTIVE)} -xf {shlex.quote(remote_tar)} && rm -f -- {shlex.quote(remote_tar)}')
    source = ('source /opt/ros/humble/setup.bash && '
              'source /home/zyc/ros2_ws/install/setup.bash && '
              'source /home/zyc/hcmc_gaden_seed_build_20260922/install/setup.bash && '
              'source /home/zyc/ros2_ws/brg_closedloop_20260927/install/setup.bash && '
              'export LD_LIBRARY_PATH=/home/zyc/hcmc_gaden_seed_build_20260922/build/gaden_common/third_party/gaden_core/third_party/libbsc:$LD_LIBRARY_PATH && '
              f'python3 {VM_CODE}/evaluate_v1_vm.py evaluate {ordinal} {arm}')
    result = remote_json(f'bash -lc {shlex.quote(source)}')
    if (result['status'] != 'BRG_V1_EVAL_RUN_PACKAGED' or
            result['ordinal'] != ordinal or result['arm'] != arm):
        raise RuntimeError('evaluation VM receipt mismatch')
    command(['scp', '-q', '-i', str(KEY), f'{VM}:{result["archive"]}', str(package)])
    actual = sha(package)
    if actual != result['archive_sha256'] or package.stat().st_size != result['archive_bytes']:
        raise RuntimeError('host/VM evaluation archive SHA or byte mismatch')
    verify_eval_package(package, ordinal, arm)
    receipt = {**result, 'host_package': str(package),
               'native_archive_sha256': sha(native_asset),
               'frozen_case_file_sha256': case['case_file_sha256']}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    cleaned = remote_json(f'python3 {VM_CODE}/evaluate_v1_vm.py cleanup {ordinal} {arm} {actual}')
    if cleaned['status'] != 'VERIFIED_EVAL_WORK_COPY_REMOVED':
        raise RuntimeError('VM eval cleanup not confirmed')
    print(f'[eval {ordinal} {arm}] geometric={result["geometric_success"]} '
          f'error={result["final_source_error_m"]} status={result["status_detail"]}', flush=True)
    return receipt


def main() -> None:
    freeze = preflight()
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(exist_ok=True)
    if shutil.disk_usage(ARCHIVE).free < 10_000_000_000:
        raise RuntimeError('host eval archive volume has less than 10GB free')
    stage = sys.argv[1] if len(sys.argv) > 1 else 'full'
    key = {'p0': 'stage_p0_ordinals', 'p1': 'stage_p1_cumulative_ordinals',
           'full': 'stage_full_ordinals'}.get(stage)
    if key is None:
        raise RuntimeError('stage must be p0, p1, or full')
    selected = set(freeze[key])
    for case in freeze['cases']:
        if case['ordinal'] in selected:
            for arm in ARMS:
                one(case, arm)


if __name__ == '__main__':
    main()
