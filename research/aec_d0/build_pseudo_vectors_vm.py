#!/usr/bin/env python3
"""Replay only D1 truth-source PMFS members and project archived H03 members."""
import csv
import hashlib
import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
H03 = Path('/home/zyc/aod_house03_f1_full624_20260927')
OUT = Path('/home/zyc/aec_d0_20260929')
ROUTES = Path('/home/zyc/aec_d0_routes.json')
cv2.setNumThreads(1)
os.environ['OMP_NUM_THREADS'] = '1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_csv(path, delimiter=','):
    return list(csv.DictReader(Path(path).open(), delimiter=delimiter))


def route_weights(meta, xy):
    width, height = int(meta['width']), int(meta['height'])
    d, ox, oy = (float(meta[k]) for k in ('resolution', 'origin_x', 'origin_y'))
    left = ox + np.arange(width) * d
    bottom = oy + np.arange(height) * d
    w = []
    for x, y in xy:
        wx = np.maximum(0., np.minimum(left + d, x + .1) - np.maximum(left, x - .1))
        wy = np.maximum(0., np.minimum(bottom + d, y + .1) - np.maximum(bottom, y - .1))
        row = np.outer(wy, wx).ravel() / .04
        assert abs(row.sum() - 1.) <= 1e-7
        w.append(row)
    return np.asarray(w)


def inventory(path):
    result = {}
    for line in Path(path).open():
        item = json.loads(line)
        if 'environment' in item:
            key = (int(item['environment']), int(item['source']), int(item['state']), int(item['seed']))
        else:
            key = (0, int(item['source']), int(item['state']), int(item['seed']))
        result[key] = item['hashes']
    return result


def generate_h01_h02(routes, vectors, manifest):
    all_groups = defaultdict(list)
    for ri, route in enumerate(routes):
        all_groups[(int(route['env']), route['source_id'])].append((ri, route))
    inv_h01 = inventory(ROOT/'h01_native_rebuild/forward_hash_inventory.jsonl')
    inv_h02 = inventory(ROOT/'full_support/forward_hash_inventory.jsonl')
    binary = ROOT/'full_support/full_support_forward'
    manifest['binary_sha256'] = sha(binary)
    tmp = OUT/'temporary'
    tmp.mkdir(parents=True, exist_ok=True)
    source_rows = []
    for (env, source_id), group in sorted(all_groups.items()):
        base = ROOT/'h01_native_rebuild' if env == 0 else ROOT/'full_support'
        inputs = base/('inputs' if env == 0 else f'inputs/env_{env}')
        sources = read_csv(inputs/'sources.csv')
        index = next(i for i, row in enumerate(sources) if row['source_id'] == source_id)
        with np.load(ROOT/f'legal_support_v2/env_{env}_bank.npz', allow_pickle=False) as bank:
            ids = [str(x) for x in bank['source_ids']]
            assert source_id in ids
            rawu_mean = bank['rawu'][ids.index(source_id)]
            meta = json.loads(bank['metadata'].item())
        weights = [(ri, route_weights(meta, route['xy'])) for ri, route in group]
        projected = {ri: {kind: [] for kind in ('u', 'rawu')} for ri, _ in group}
        rawu_sum = np.zeros_like(rawu_mean, dtype=np.float64)
        source_hashes = []
        for state in range(11):
            for seed in range(1, 9):
                prefix = tmp/f'env_{env}_source_{index}_state_{state}_seed_{seed}'
                command = [str(binary), str(inputs), str(index), str(state), str(seed), str(prefix)]
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                expected = (inv_h01 if env == 0 else inv_h02)[(env,index,state,seed)]
                maps = {}
                digest = {}
                for kind in ('p', 'u', 'rawp', 'rawu'):
                    path = Path(str(prefix)+'.'+kind+'.f32')
                    digest[kind] = sha(path)
                    assert digest[kind] == expected[kind], (env,source_id,state,seed,kind)
                    if kind in ('u','rawu'):
                        maps[kind] = np.fromfile(path, '<f4').astype(np.float64)
                    path.unlink()
                rawu_sum += maps['rawu']
                for ri, w in weights:
                    for kind in ('u','rawu'):
                        projected[ri][kind].append(w @ maps[kind])
                source_hashes.append(dict(state=state, seed=seed, hashes=digest))
        rawu_avg = rawu_sum / 88
        error = np.linalg.norm(rawu_avg-rawu_mean)/max(np.linalg.norm(rawu_mean),1e-12)
        assert error <= 1e-10, (env,source_id,error)
        for ri, _ in group:
            for kind in ('u','rawu'):
                value = np.asarray(projected[ri][kind], dtype=np.float64)
                assert value.shape == (88,len(routes[ri]['xy']))
                vectors[f'route_{ri}_{kind}'] = value
        source_rows.append(dict(env=env, source_id=source_id, source_index=index,
                                run_count=88, rawu_bank_mean_rel_l2=error,
                                input_files_sha256={p.name:sha(p) for p in sorted(inputs.iterdir()) if p.is_file()},
                                runs=source_hashes))
        print('PSEUDO_SOURCE_COMPLETE',env,source_id,flush=True)
    manifest['h01_h02_sources'] = source_rows


def project_h03(vectors, manifest):
    support = read_csv(H03/'templates/CANDIDATE_SUPPORT.csv')
    truth = read_csv(H03/'protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv','\t')
    assert len(support) == 624 and len(truth) == 12
    w = np.load(H03/'templates/footprint_W.npy', allow_pickle=False)
    path_rank = {path: [int(r['probe_rank'])-1 for r in read_csv(
        H03/f'protocol/frozen/HOUSE03_PATH_{path}_10.tsv','\t')] for path in ('A','B')}
    rows = []
    for si, source in enumerate(truth):
        cid = next(i for i, r in enumerate(support) if r['source_id'] == source['source_id'])
        assert cid == int(support[cid]['source_index'])
        values = {path:{kind:[] for kind in ('u','rawu')} for path in ('A','B')}
        hashes = []
        for state in range(11):
            for rep in range(8):
                prefix = H03/f'candidate_forward/source_{cid}/state_{state}_replica_{rep}'
                done = json.loads(Path(str(prefix)+'.done.json').read_text())
                rec = dict(state=state, replica=rep, hashes={})
                for kind in ('u','rawu'):
                    path = Path(str(prefix)+'.'+kind+'.f32')
                    digest = sha(path)
                    assert digest == done['hashes'][kind]
                    rec['hashes'][kind] = digest
                    map_values = np.fromfile(path,'<f4').astype(np.float64)
                    projected30 = w @ map_values
                    for name in ('A','B'):
                        values[name][kind].append(projected30[path_rank[name]])
                hashes.append(rec)
        for path in ('A','B'):
            for kind in ('u','rawu'):
                value = np.asarray(values[path][kind], dtype=np.float64)
                assert value.shape == (88,10)
                vectors[f'h03_source_{si}_path_{path}_{kind}'] = value
        rows.append(dict(source_index=si,source_id=source['source_id'],runs=hashes))
        print('PSEUDO_H03_SOURCE_COMPLETE',si,source['source_id'],flush=True)
    manifest['h03_sources'] = rows
    manifest['h03_footprint_sha256'] = sha(H03/'templates/footprint_W.npy')


def main():
    if OUT.exists():
        # The first launch may stop before any forward output if ROS shared
        # libraries are absent from LD_LIBRARY_PATH. Resume only that exact
        # empty scratch state; never overwrite a scientific output.
        assert {p.name for p in OUT.iterdir()} == {'temporary'}
        assert not list((OUT/'temporary').iterdir())
    else:
        OUT.mkdir()
    routes = json.loads(ROUTES.read_text())
    assert len(routes) == 49
    manifest = dict(protocol='AEC-D0 simulator-only competence',
                    route_sha256=sha(ROUTES),new_gaden_runs=0,new_vgr_runs=0,
                    h01_h02_pmfs_runs=13*88,h03_pmfs_runs=0,
                    target_concentrations_read=False)
    vectors = {}
    generate_h01_h02(routes,vectors,manifest)
    project_h03(vectors,manifest)
    np.savez_compressed(OUT/'PSEUDO_VECTORS.npz', **vectors)
    manifest['pseudo_vectors_sha256'] = sha(OUT/'PSEUDO_VECTORS.npz')
    (OUT/'SIMULATOR_ONLY_FREEZE.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('AEC_SIMULATOR_ONLY_ASSETS_COMPLETE',manifest['pseudo_vectors_sha256'],flush=True)


if __name__=='__main__':
    main()
