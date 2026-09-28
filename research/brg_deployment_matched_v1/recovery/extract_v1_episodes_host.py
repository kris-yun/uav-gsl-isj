"""Extract only verified VGR event features from immutable host log packages."""
from __future__ import annotations

import hashlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
from collections import defaultdict

from sample_time_contract import verify_distinct_vgr_samples

ROOT = Path(__file__).resolve().parent
OUT = Path(r'C:\Users\50176\Desktop\vm数据\BRG_V1_EPISODES_20260928')
ZSTD = Path(r'D:\Anaconda\Library\bin\zstd.exe')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_episode_members(path: Path) -> tuple[bytes, bytes, dict[str, bytes]]:
    proc = subprocess.Popen([str(ZSTD), '-dc', str(path)], stdout=subprocess.PIPE)
    assert proc.stdout is not None
    npz = meta = None
    raw = {}
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
            else:
                for name in ('measurement_blocks.csv', 'measurement_samples.csv',
                             'sensor_trace.csv'):
                    if member.name.endswith('_raw/' + name):
                        raw[name] = archive.extractfile(member).read()
    # tarfile stops at end-of-archive blocks, while zstd may still be writing
    # the compressed stream. Drain the pipe so decompressor exit status is real.
    for _ in iter(lambda: proc.stdout.read(1024 * 1024), b''):
        pass
    proc.stdout.close()
    if proc.wait() or npz is None or meta is None or len(raw) != 3:
        raise RuntimeError('incomplete compressed VGR episode')
    return npz, meta, raw


def verify_publications(raw: dict[str, bytes], event_count: int) -> dict:
    def csv_rows(name):
        return list(csv.DictReader(io.StringIO(raw[name].decode('utf-8'))))
    blocks = csv_rows('measurement_blocks.csv')
    samples = csv_rows('measurement_samples.csv')
    trace = csv_rows('sensor_trace.csv')
    if len(blocks) != event_count:
        raise RuntimeError('measurement block count differs from encoded events')
    groups = defaultdict(list)
    for row in samples:
        groups[int(row['measurement_cycle_id'])].append(row)
    collisions = 0
    max_lag = 0.
    for n, block in enumerate(blocks, 1):
        if int(block['measurement_cycle_id']) != n:
            raise RuntimeError('noncontiguous measurement cycle in archive')
        match = verify_distinct_vgr_samples(groups[n], trace,
                    float(block['sim_time_start']), float(block['sim_time_end']),
                    (float(block['pose_x']), float(block['pose_y'])))
        collisions += match['clock_collision_count']
        max_lag = max(max_lag, match['max_clock_lag_s'])
    return {'distinct_vgr_publications_verified': True,
            'pmfs_callback_clock_collisions': collisions,
            'max_pmfs_to_vgr_clock_lag_s': max_lag}


def main() -> None:
    import numpy as np
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = []
    receipt_paths = []
    for folder in ('native_collection_receipts', 'coverage_collection_receipts',
                   'self_collection_receipts'):
        receipt_paths.extend((ROOT / folder).glob('*.json'))
    for receipt_path in sorted(receipt_paths):
        receipt = json.loads(receipt_path.read_text())
        path = Path(receipt['host_package'])
        if sha(path.read_bytes()) != receipt['archive_sha256']:
            raise RuntimeError('VGR package checksum drift')
        npz_data, meta_data, raw = read_episode_members(path)
        meta = json.loads(meta_data)
        if (meta['case_id'] != receipt['case_id'] or
                meta['features_sha256'] != sha(npz_data) or
                meta['split'] not in ('train', 'dev') or
                meta['policy'] not in ('native_pmfs', 'native', 'coverage',
                                       'candidate_gru', 'brg', 'brg_ungated')):
            raise RuntimeError('episode identity/feature checksum mismatch')
        policy = 'native_pmfs' if meta['policy'] == 'native' else meta['policy']
        publication_integrity = verify_publications(raw, meta['events'])
        with np.load(io.BytesIO(npz_data)) as arr:
            if (arr['obs'].shape[1] != 6 or arr['cues'].shape[-1] != 6 or
                    arr['obs'].shape[0] != arr['cues'].shape[0] or
                    arr['cues'].shape[1] != meta['candidate_count'] or
                    not np.isfinite(arr['obs']).all() or
                    not np.isfinite(arr['cues']).all()):
                raise RuntimeError('invalid frozen event feature shape')
        stem = f'{receipt["ordinal"]:03d}_{receipt["case_id"]}_{policy}'
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
                          'split': meta['split'], 'policy': policy,
                          'recorded_policy': meta['policy'],
                          'episode_path': str(output), 'episode_sha256': sha(npz_data),
                          'metadata_path': str(metadata_path), 'events': meta['events'],
                          'candidate_count': meta['candidate_count'],
                          'package_sha256': receipt['archive_sha256'],
                          **publication_integrity})
    result = {'status': 'VGR_OPEN_EPISODES_EXTRACTED', 'count': len(inventory),
              'train': sum(x['split'] == 'train' for x in inventory),
              'dev': sum(x['split'] == 'dev' for x in inventory),
              'episodes': inventory}
    manifest = OUT / 'OPEN_EPISODE_INVENTORY.json'
    manifest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'count', 'train', 'dev')}))


if __name__ == '__main__':
    main()
