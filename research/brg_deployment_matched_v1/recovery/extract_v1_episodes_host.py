"""Extract only verified VGR event features from immutable host log packages."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
OUT = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_EPISODES_20260928')
ZSTD = Path(r'D:\Anaconda\Library\bin\zstd.exe')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_episode_members(path: Path) -> tuple[bytes, bytes]:
    proc = subprocess.Popen([str(ZSTD), '-dc', str(path)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    npz = meta = None
    with tarfile.open(fileobj=proc.stdout, mode='r|') as archive:
        for member in archive:
            if not member.isfile():
                continue
            if member.name.endswith('_episode.npz'):
                if npz is not None:
                    raise RuntimeError('multiple episode arrays in VGR package')
                npz = archive.extractfile(member).read()
            elif member.name.endswith('_episode.json'):
                if meta is not None:
                    raise RuntimeError('multiple episode metadata in VGR package')
                meta = archive.extractfile(member).read()
    proc.stdout.close()
    if proc.wait() or npz is None or meta is None:
        raise RuntimeError('incomplete compressed VGR episode')
    return npz, meta


def main() -> None:
    import numpy as np
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = []
    for receipt_path in sorted((ROOT / 'native_collection_receipts').glob('*.json')):
        receipt = json.loads(receipt_path.read_text())
        path = Path(receipt['host_package'])
        if sha(path.read_bytes()) != receipt['archive_sha256']:
            raise RuntimeError('VGR package checksum drift')
        npz_data, meta_data = read_episode_members(path)
        meta = json.loads(meta_data)
        if (meta['case_id'] != receipt['case_id'] or
                meta['features_sha256'] != sha(npz_data) or
                meta['split'] not in ('train', 'dev') or
                meta['policy'] not in ('native_pmfs', 'native')):
            raise RuntimeError('episode identity/feature checksum mismatch')
        with np.load(io.BytesIO(npz_data)) as arr:
            if (arr['obs'].shape[1] != 6 or arr['cues'].shape[-1] != 6 or
                    arr['obs'].shape[0] != arr['cues'].shape[0] or
                    arr['cues'].shape[1] != meta['candidate_count'] or
                    not np.isfinite(arr['obs']).all() or
                    not np.isfinite(arr['cues']).all()):
                raise RuntimeError('invalid frozen event feature shape')
        stem = f'{receipt["ordinal"]:03d}_{receipt["case_id"]}_native'
        output = OUT / (stem + '.npz')
        metadata_path = OUT / (stem + '.json')
        if output.exists() and output.read_bytes() != npz_data:
            raise RuntimeError('existing extracted episode drift')
        if metadata_path.exists() and metadata_path.read_bytes() != meta_data:
            raise RuntimeError('existing extracted metadata drift')
        output.write_bytes(npz_data)
        metadata_path.write_bytes(meta_data)
        inventory.append({'ordinal': receipt['ordinal'], 'case_id': meta['case_id'],
                          'source_group': meta['source_group'], 'plume_group': meta['plume_group'],
                          'split': meta['split'], 'policy': 'native_pmfs',
                          'recorded_policy': meta['policy'],
                          'episode_path': str(output), 'episode_sha256': sha(npz_data),
                          'metadata_path': str(metadata_path), 'events': meta['events'],
                          'candidate_count': meta['candidate_count'],
                          'package_sha256': receipt['archive_sha256']})
    result = {'status': 'VGR_NATIVE_EPISODES_EXTRACTED', 'count': len(inventory),
              'train': sum(x['split'] == 'train' for x in inventory),
              'dev': sum(x['split'] == 'dev' for x in inventory),
              'episodes': inventory}
    manifest = OUT / 'NATIVE_EPISODE_INVENTORY.json'
    manifest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'count', 'train', 'dev')}))


if __name__ == '__main__':
    main()
