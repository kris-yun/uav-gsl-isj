#!/usr/bin/env python3
"""Full PMFS model support; no concentration targets or learned selection.

Reuse the audited native multiplicity observer and 11-state x 8-seed recipe.
Only lift the six-source executable input bound. Aggregate in float64 and
retain per-forward hashes, keeping temporary files inside this new run root.
"""
import concurrent.futures, csv, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

BASE = Path('/home/zyc/marked_encounter_pmfs_d0_20260927')
ROOT = Path('/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927')
sys.path.insert(0, str(ROOT))
from pmfs_brg.bank import TemplateBank

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    out = ROOT/'full_support'; out.mkdir(exist_ok=True)
    provenance = json.loads((BASE/'build_provenance.json').read_text())
    for p, h in provenance['historical_library_sha256'].items():
        assert sha(p) == h, p
    src = (BASE/'execution/marked_forward.cpp').read_text()
    needle = 'source<0||source>=6||state<0||state>=11||seed<1||seed>8'
    assert src.count(needle) == 1
    src = src.replace(needle, 'source<0||source>=static_cast<int>(csv(in/"sources.csv").size())||state<0||state>=11||seed<1||seed>8')
    cpp = out/'full_support_forward.cpp'; cpp.write_text(src)
    cmd = provenance['binaries'][1]['command'].copy()
    cmd = [str(cpp) if x == str(BASE/'execution/marked_forward.cpp') else x for x in cmd]
    cmd[cmd.index('-o')+1] = str(out/'full_support_forward')
    with (out/'build.log').open('w') as f:
        subprocess.run(cmd, cwd='/home/zyc/native_pmfs_recovery_v1/build/gsl_server', stdout=f, stderr=subprocess.STDOUT, check=True)
    envs = json.loads((BASE/'inputs/environment_manifest.json').read_text())
    datasets = []
    for e in envs:
        idx = e['environment_index']; folder = out/f'inputs/env_{idx}'; folder.mkdir(parents=True, exist_ok=True)
        for n in ['meta.json', 'meta.csv', 'occupancy.u8'] + [f'wind_{i}.csv' for i in range(11)]:
            shutil.copyfile(BASE/f'inputs/env_{idx}'/n, folder/n)
        meta = e['metadata']; cells = np.flatnonzero(np.fromfile(folder/'occupancy.u8', np.uint8) == 1)
        xy = np.stack((meta['origin_x']+(cells%meta['width']+.5)*meta['resolution'], meta['origin_y']+(cells//meta['width']+.5)*meta['resolution']), 1)
        ids = [f'pmfs_{i%meta["width"]}_{i//meta["width"]}' for i in cells]
        with (folder/'sources.csv').open('w', newline='') as f:
            w = csv.writer(f); w.writerow(['source_index', 'source_id', 'x', 'y', 'z', 'pair_id'])
            for s, (sid, (x, y)) in enumerate(zip(ids, xy)):
                w.writerow([s, sid, x, y, .2, ''])
        datasets.append((e, folder, cells, xy, ids))
    freeze = {'purpose': 'FULL_SUPPORT_OPEN_TRAINING_ALIGNMENT', 'gas_arrays_read': False, 'new_gaden_plumes': 0,
              'wind_states': list(range(11)), 'replica_seeds': list(range(1, 9)), 'workers': 8,
              'kernel_provenance_sha256': sha(BASE/'build_provenance.json'), 'binary_sha256': sha(out/'full_support_forward'),
              'input_files': {str(p.relative_to(out)): sha(p) for p in sorted((out/'inputs').rglob('*')) if p.is_file()},
              'candidate_counts': {str(e['environment_index']): len(cells) for e, _, cells, _, _ in datasets}}
    (out/'PRE_FORWARD_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True)+'\n')
    os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    start = time.monotonic(); tmp = out/'temporary'; tmp.mkdir(exist_ok=True)
    perrun = (out/'forward_hash_inventory.jsonl').open('a', buffering=1)
    # One source task owns all temporary files it removes; historical banks remain read-only.
    def run_source(t):
        ei, si = t; e, folder, cells, xy, ids = datasets[ei]
        dest = out/f'source_means/env_{ei}/{si}.npz'
        if dest.exists():
            with np.load(dest) as z:
                assert str(z['input_freeze']) == sha(out/'PRE_FORWARD_FREEZE.json')
            return t, None
        n = e['metadata']['width']*e['metadata']['height']
        pp = np.zeros(n); uu = np.zeros(n); hashes = []
        for k in range(11):
            for r in range(1, 9):
                prefix = tmp/f'env_{ei}_source_{si}_state_{k}_seed_{r}'
                command = [str(out/'full_support_forward'), str(folder), str(si), str(k), str(r), str(prefix)]
                proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                if proc.returncode:
                    raise RuntimeError((t, k, r, proc.returncode, proc.stdout))
                row = {'environment': ei, 'source': si, 'state': k, 'seed': r, 'hashes': {}}
                for kind in ['p', 'u', 'rawp', 'rawu']:
                    path = Path(str(prefix)+'.'+kind+'.f32')
                    assert path.resolve().is_relative_to(tmp.resolve())
                    b = path.read_bytes(); a = np.frombuffer(b, '<f4')
                    assert a.size == n and np.isfinite(a).all() and (a >= 0).all()
                    row['hashes'][kind] = hashlib.sha256(b).hexdigest()
                    if kind == 'p':
                        assert (a[cells] <= 1).all(); pp += a
                    if kind == 'rawu': uu += a
                    path.unlink()
                hashes.append(row)
        dest.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(dest, p=pp/88, rawu=uu/88, input_freeze=np.array(sha(out/'PRE_FORWARD_FREEZE.json')))
        return t, hashes
    tasks = [(i, s) for i, (_, _, cells, _, _) in enumerate(datasets) for s in range(len(cells))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for done, (task, rows) in enumerate(pool.map(run_source, tasks), 1):
            if rows:
                for row in rows: perrun.write(json.dumps(row, sort_keys=True)+'\n')
            if done % 8 == 0:
                print('FULL_BANK_SOURCES', done, '/', len(tasks), 'elapsed_s', round(time.monotonic()-start, 1), flush=True)
    perrun.close()
    final = []
    for i, (e, folder, cells, xy, ids) in enumerate(datasets):
        arrays = [np.load(out/f'source_means/env_{i}/{s}.npz') for s in range(len(cells))]
        pp = np.stack([a['p'] for a in arrays]); uu = np.stack([a['rawu'] for a in arrays])
        for a in arrays: a.close()
        meta = {**e['metadata'], 'environment_id': f'env_{i}_full_support', 'house': e['house'], 'wind': e['wind'],
                'height_m': .2, 'footprint_x_m': .2, 'footprint_y_m': .2, 'unit': 'area_averaged_cell_count_proxy'}
        bank = TemplateBank(meta, ids, xy, cells, pp, uu); path = out/f'env_{i}_bank.npz'; bank.save(path)
        final.append({'environment': i, 'sources': len(cells), 'bank_sha256': sha(path), 'bank_id': bank.fingerprint})
    (out/'BANK_COMPLETE.json').write_text(json.dumps({'banks': final, 'seconds': time.monotonic()-start,
        'forward_count': 88*len(tasks), 'freeze_sha256': sha(out/'PRE_FORWARD_FREEZE.json'),
        'inventory_sha256': sha(out/'forward_hash_inventory.jsonl')}, indent=2)+'\n')
    print('FULL_SUPPORT_MODEL_BANK_COMPLETE', final, flush=True)

if __name__ == '__main__': main()
