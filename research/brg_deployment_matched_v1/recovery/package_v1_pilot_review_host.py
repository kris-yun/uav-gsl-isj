"""Package the completed three-case pilot, input episodes, weights, and raw VGR logs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from collect_native_host import ROOT, sha
from evaluate_v1_pilot_host import ARCHIVE, RECEIPTS, ARMS


DESKTOP_DATA = ARCHIVE.parent
MODELS = DESKTOP_DATA / 'BRG_V1_MODELS_20260928'
OUTPUT = DESKTOP_DATA / 'BRG_V1_THREE_CASE_PILOT_REVIEW_20260928.zip'


def main() -> None:
    if OUTPUT.exists():
        raise RuntimeError('refuse to overwrite existing pilot review package')
    freeze = json.loads((ROOT / 'PILOT_EVAL_FREEZE.json').read_text())
    if (freeze['status'] != 'BRG_V1_NATIVE_ONLY_THREE_CASE_PILOT_FROZEN' or
            [x['ordinal'] for x in freeze['cases']] != [9, 21, 65]):
        raise RuntimeError('pilot freeze drift')
    model_freeze = json.loads((MODELS / 'PILOT_CHECKPOINT_FREEZE.json').read_text())
    if (model_freeze['status'] != 'BRG_V1_NATIVE_PILOT_MODELS_FROZEN_BEFORE_EVAL' or
            model_freeze['evaluation_freeze_sha256'] != sha(ROOT / 'PILOT_EVAL_FREEZE.json')):
        raise RuntimeError('pilot checkpoint freeze drift')

    files: dict[str, Path] = {}
    for name in (
        'PILOT_EVAL_FREEZE.json', 'NATIVE_OPEN_EPISODE_INVENTORY_FROZEN.json',
        'V1_EVAL8_FROZEN_MANIFEST.json', 'train_v1_native_pilot.py',
        'freeze_v1_pilot_models_host.py', 'evaluate_v1_pilot_host.py',
        'evaluate_v1_pilot_vm.py', 'bind_v1_case_vm.py',
        'serve_v1_vm.py', 'sample_time_contract.py',
        'summarize_v1_pilot_host.py',
    ):
        files[f'contract_and_code/{name}'] = ROOT / name
    files['contract_and_code/model.py'] = ROOT / 'v0_reference' / 'model.py'
    for path in sorted((ROOT / 'quick_pilot_20260928').iterdir()):
        if path.is_file():
            files[f'original_quick_pilot_contract/{path.name}'] = path
    for case in freeze['cases']:
        ordinal, run_id = case['ordinal'], case['case_id']
        files[f'frozen_eval_cases/{ordinal:03d}_{run_id}.json'] = ROOT / case['case_file']
        native_receipt = ROOT / 'receipts' / f'{ordinal:03d}_{run_id}.json'
        files[f'frozen_eval_native_receipts/{native_receipt.name}'] = native_receipt
        for arm in ARMS:
            prefix = 'pilot' if arm == 'native_pmfs' else 'pilot_fix1'
            stem = f'{prefix}_{arm}_{ordinal:03d}_{run_id}'
            receipt_path = RECEIPTS / f'{stem}.json'
            archive = ARCHIVE / f'{stem}.tar.zst'
            receipt = json.loads(receipt_path.read_text())
            if sha(archive) != receipt['archive_sha256']:
                raise RuntimeError(f'pilot archive hash drift: {stem}')
            files[f'pilot_receipts/{receipt_path.name}'] = receipt_path
            files[f'pilot_raw_logs/{archive.name}'] = archive
            if ordinal == 9 and arm != 'native_pmfs':
                failed_stem = f'pilot_{arm}_{ordinal:03d}_{run_id}'
                failed_receipt = RECEIPTS / f'{failed_stem}.json'
                failed_archive = ARCHIVE / f'{failed_stem}.tar.zst'
                failed = json.loads(failed_receipt.read_text())
                if failed['status_detail'] != 'service_error' or sha(failed_archive) != failed['archive_sha256']:
                    raise RuntimeError('original infrastructure failure evidence changed')
                files[f'original_infrastructure_failure/{failed_receipt.name}'] = failed_receipt
                files[f'original_infrastructure_failure/{failed_archive.name}'] = failed_archive
    files['pilot_summary/BRG_V1_PILOT_3CASE_SUMMARY.json'] = ARCHIVE / 'summary' / 'BRG_V1_PILOT_3CASE_SUMMARY.json'
    files['pilot_summary/BRG_V1_PILOT_3CASE_RUNS.csv'] = ARCHIVE / 'summary' / 'BRG_V1_PILOT_3CASE_RUNS.csv'
    files['pilot_models/PILOT_CHECKPOINT_FREEZE.json'] = MODELS / 'PILOT_CHECKPOINT_FREEZE.json'
    for arm in ('candidate_gru', 'brg', 'brg_ungated'):
        files[f'pilot_models/pilot_{arm}_best.pt'] = MODELS / f'pilot_{arm}_best.pt'
        for name in ('summary.json', 'history.json', 'trainer_state.pt', 'last.pt'):
            files[f'pilot_models/{arm}/{name}'] = MODELS / 'native_pilot' / arm / name
    episodes = json.loads((ROOT / 'NATIVE_OPEN_EPISODE_INVENTORY_FROZEN.json').read_text())['episodes']
    if len(episodes) != 48:
        raise RuntimeError('pilot Native training inventory changed')
    for row in episodes:
        data_path = Path(row['episode_path'])
        meta_path = Path(row['metadata_path'])
        if sha(data_path) != row['episode_sha256']:
            raise RuntimeError(f'training episode hash drift: {data_path.name}')
        files[f'native_training_episodes/{data_path.name}'] = data_path
        files[f'native_training_episodes/{meta_path.name}'] = meta_path

    readme = (
        'BRG V1 Native-only initial three-case VGR development pilot, 2026-09-28.\n'
        'Three models trained fresh for ten epochs on 40 Native train episodes; '
        '8 Native dev episodes selected checkpoints by source-update NLL.\n'
        'Pilot cases are frozen original eval8 ordinals 009, 021, 065, each with '
        'Native, candidate-GRU, BRG, and ungated BRG.\n'
        'The 12 VGR runs are interactive development examples, not Gazebo and '
        'not a confirmatory significance test. The inspected cases become '
        'development evidence. No new GADEN plume, candidate forward, extra '
        'coverage, or self-rollout data were generated.\n'
        'The raw VGR log tar.zst files, training episodes, code, checkpoint '
        'hashes, source splits, and per-run results are included. The original '
        'full native plume archives are external and identified by their '
        'existing receipts; they are not duplicated in this review ZIP.\n'
    )
    inventory = []
    for name, path in sorted(files.items()):
        if not path.is_file():
            raise FileNotFoundError(path)
        inventory.append({'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path)})
    metadata = {'status': 'BRG_V1_NATIVE_ONLY_THREE_CASE_PILOT_REVIEW_PACKAGE',
                'pilot_eval_freeze_sha256': sha(ROOT / 'PILOT_EVAL_FREEZE.json'),
                'pilot_checkpoint_freeze_sha256': sha(MODELS / 'PILOT_CHECKPOINT_FREEZE.json'),
                'files': inventory}
    generated = {'README.txt': readme.encode('utf-8'),
                 'PACKAGE_INVENTORY.json': (json.dumps(metadata, indent=2) + '\n').encode('utf-8')}
    sums = [f'{row["sha256"]}  {row["path"]}' for row in inventory]
    sums.extend(f'{hashlib.sha256(data).hexdigest()}  {name}' for name, data in generated.items())
    generated['SHA256SUMS'] = ('\n'.join(sums) + '\n').encode('utf-8')
    with zipfile.ZipFile(OUTPUT, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as bundle:
        for name, data in generated.items():
            bundle.writestr(name, data)
        for name, path in sorted(files.items()):
            bundle.write(path, name)
    with zipfile.ZipFile(OUTPUT) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('pilot review ZIP CRC error')
        for line in bundle.read('SHA256SUMS').decode().splitlines():
            digest, name = line.split('  ', 1)
            if hashlib.sha256(bundle.read(name)).hexdigest() != digest:
                raise RuntimeError(f'pilot review member checksum drift: {name}')
    print(json.dumps({'status': metadata['status'], 'path': str(OUTPUT),
                      'bytes': OUTPUT.stat().st_size, 'sha256': sha(OUTPUT),
                      'member_count': len(files) + len(generated), 'internal_sha256': 'PASS'}))


if __name__ == '__main__':
    main()
