#!/usr/bin/env python3
"""Run only the 3,168 pre-frozen PMFS neighborhood rows; no GADEN access."""
from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np


ROOT = Path('/home/zyc/aod_r2_f0')
TOOLS = ROOT / 'tools'
OUT = ROOT / 'forward'
RUNLIST = TOOLS / 'AOD_R2_F0_FORWARD_RUNLIST.tsv'
PREFORWARD = TOOLS / 'AOD_R2_F0_PRE_FORWARD_INPUTS.json'
BIN = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927/full_support/full_support_forward')
EXPECTED_PRE = 'bc11862f012979a65d0a81c4113f068ac778a8e47b9557905bef31c24b6d3d5a'
EXPECTED_RUNLIST = 'ecce280ed07b23e88dd8a0c5e414e8d3f4af62eb627164bf3be7d57887be7740'
KINDS = ('p', 'u', 'rawp', 'rawu')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def row_path(row):
    return OUT / row['context'] / row['source_id'] / f"state_{int(row['wind_state']):02d}_key_{int(row['pmfs_transport_key']):02d}"


def main():
    assert sha(PREFORWARD) == EXPECTED_PRE and sha(RUNLIST) == EXPECTED_RUNLIST
    pre = json.loads(PREFORWARD.read_text())
    assert pre['decision'] == 'AOD_R2_F0_FORWARD_INPUTS_FROZEN'
    assert sha(BIN) == pre['model_binary_sha256']
    with RUNLIST.open(newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    assert len(rows) == pre['selected_forward_rows'] == 3168
    for context, info in pre['contexts'].items():
        folder = ROOT / 'inputs' / context
        for name, digest in info['files'].items():
            assert sha(folder / name) == digest
    expected_bytes = sum(4 * 4 * int(json.loads((ROOT/'inputs'/r['context']/'meta.json').read_text())['width']) *
                         int(json.loads((ROOT/'inputs'/r['context']/'meta.json').read_text())['height']) for r in rows)
    assert shutil.disk_usage(ROOT).free >= expected_bytes + 512*1024**2
    os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    OUT.mkdir(exist_ok=True)
    start = time.monotonic()
    save_json(OUT/'EXECUTION_START.json', dict(rows=len(rows), binary_sha256=sha(BIN),
                                               pre_forward_sha256=EXPECTED_PRE, expected_map_bytes=expected_bytes,
                                               free_before_bytes=shutil.disk_usage(ROOT).free, workers=8,
                                               target_concentration_read=False, new_gaden=0))

    def run(row):
        prefix = row_path(row)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        done = Path(str(prefix)+'.done.json')
        if done.exists():
            record = json.loads(done.read_text())
            assert all(sha(str(prefix)+f'.{k}.f32') == record['sha256'][k] for k in KINDS)
            return record
        assert not any(Path(str(prefix)+f'.{k}.f32').exists() for k in KINDS), f'partial row: {prefix}'
        cmd = [str(BIN), str(ROOT/'inputs'/row['context']), row['full_legal_index'],
               row['wind_state'], row['pmfs_transport_key'], str(prefix)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert result.returncode == 0, (cmd, result.stdout)
        meta = json.loads((ROOT/'inputs'/row['context']/'meta.json').read_text())
        n = int(meta['width']) * int(meta['height'])
        outputs = {}
        for kind in KINDS:
            path = Path(str(prefix)+f'.{kind}.f32')
            a = np.fromfile(path, '<f4')
            assert a.shape == (n,) and np.isfinite(a).all() and (a >= 0).all()
            outputs[kind] = sha(path)
        record = dict(context=row['context'], source_id=row['source_id'],
                      full_legal_index=int(row['full_legal_index']), state=int(row['wind_state']),
                      key=int(row['pmfs_transport_key']), sha256=outputs)
        save_json(done, record)
        return record

    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for count, record in enumerate(pool.map(run, rows), 1):
            records.append(record)
            if count % 176 == 0:
                print(f'F0_FORWARD {count}/{len(rows)} elapsed_s={time.monotonic()-start:.1f}', flush=True)
    assert len(records) == 3168
    inventory = OUT/'AOD_R2_F0_FORWARD_HASH_INVENTORY.jsonl'
    with inventory.open('w') as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True)+'\n')
    bank_hashes = {}
    for context in sorted(pre['contexts']):
        selected = sorted({(r['source_id'], int(r['full_legal_index'])) for r in rows if r['context'] == context},
                          key=lambda pair: pair[1])
        mean_u, mean_rawu = [], []
        for sid, index in selected:
            matching = [r for r in rows if r['context'] == context and r['source_id'] == sid]
            assert len(matching) == 88
            mean_u.append(np.stack([np.fromfile(str(row_path(r))+'.u.f32', '<f4').astype(np.float64)
                                    for r in matching]).mean(axis=0))
            mean_rawu.append(np.stack([np.fromfile(str(row_path(r))+'.rawu.f32', '<f4').astype(np.float64)
                                       for r in matching]).mean(axis=0))
        path = OUT/f'{context}_NEIGHBORHOOD_BANK.npz'
        np.savez_compressed(path, source_ids=np.array([sid for sid, _ in selected]),
                            full_legal_indices=np.array([index for _, index in selected]),
                            u=np.stack(mean_u), rawu=np.stack(mean_rawu))
        bank_hashes[context] = sha(path)
    save_json(OUT/'AOD_R2_F0_FORWARD_COMPLETE.json',
              dict(decision='AOD_R2_F0_LOCAL_PMFS_BANK_COMPLETE', rows=len(records),
                   selected_candidates=sum(v['selected_candidate_count'] for v in pre['contexts'].values()),
                   inventory_sha256=sha(inventory), bank_sha256=bank_hashes,
                   pre_forward_sha256=EXPECTED_PRE, elapsed_seconds=time.monotonic()-start,
                   target_concentration_read=False, new_gaden=0))
    print('AOD_R2_F0_LOCAL_PMFS_BANK_COMPLETE', time.monotonic()-start, flush=True)


if __name__ == '__main__':
    main()
