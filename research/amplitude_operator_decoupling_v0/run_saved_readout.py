"""Implementation-only OPEN replay. Never invokes a simulator or ROS executable."""
from pathlib import Path
import argparse, hashlib, json, os, platform, subprocess, sys, tempfile, time, zipfile
import numpy as np
import pandas as pd
from amplitude_readout import Arm, AmplitudeTemplates, frozen_operators, load_saved_mean_maps, ranking

HERE = Path(__file__).resolve().parent
EXPECTED = {
    'task': '1bb824cf3488379a4d973252e058160485e1c6a9c412dde73f6a45c18db2f0d8',
    'pro': '79c26ccb52de73cf198c679a6c27fa93a9485cfd24e5913dcf287ea2315e491c',
    'd0': '7a3e436900ab2696c2d7148215cd58b6632a017e447583f77c9c864b56f9c56c'}
HOUSES = ['House01', 'House02', 'House02']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_manifest(root):
    manifest = next(p for p in [root/'SHA256SUMS', root/'SHA256SUMS.txt'] if p.exists())
    n = 0
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        name = name.lstrip('* ').strip()
        if sha((root/name).read_bytes()) != digest:
            raise ValueError('Manifest mismatch: '+name)
        n += 1
    return n


def compare_csv(actual, expected):
    a, b = pd.read_csv(actual), pd.read_csv(expected)
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        raise ValueError('CSV schema mismatch: '+str(actual))
    errors = {}
    for c in a.columns:
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            av, bv = a[c].to_numpy(float), b[c].to_numpy(float)
            if not np.array_equal(np.isnan(av), np.isnan(bv)):
                raise ValueError('CSV NaN mismatch')
            diff = np.abs(av-bv)
            errors[c] = {'max_absolute': float(np.nanmax(diff)),
                         'max_relative_1plus': float(np.nanmax(diff/(1+np.abs(bv))))}
            if not np.allclose(av, bv, rtol=1e-12, atol=1e-12, equal_nan=True):
                raise ValueError(f'Numeric reproduction mismatch: {actual} {c}')
        elif not a[c].equals(b[c]):
            raise ValueError(f'Categorical reproduction mismatch: {actual} {c}')
    return dict(byte_identical=actual.read_bytes() == expected.read_bytes(), columns=errors)


def main():
    p = argparse.ArgumentParser()
    for key in EXPECTED:
        p.add_argument('--'+key+'-zip', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for key, expected in EXPECTED.items():
        path = getattr(args, key+'_zip')
        hashes[key] = dict(path=str(path.resolve()), sha256=sha(path.read_bytes()), bytes=path.stat().st_size)
        if hashes[key]['sha256'] != expected:
            raise ValueError('Frozen input ZIP mismatch: '+key)
    package_entries = {name: check_manifest(HERE/name) for name in ['protocol', 'pro_reference']}
    pro_checks = {}
    for f in sorted((HERE/'pro_reference/results').glob('*.csv')):
        produced = out.parent/'pro_reproduction'/f.name
        if produced.exists():
            pro_checks[f.name] = compare_csv(produced, f)
    if len(pro_checks) != 12:
        raise ValueError('Expected all 12 supplied Pro CSV reproductions')
    with tempfile.TemporaryDirectory(prefix='amplitude_saved_open_') as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(args.d0_zip) as z:
            # Manifest verification is read-only; extraction contains only this
            # already-OPEN bank. No external/House03/sealed assets are queried.
            count = 0
            for line in z.read('SHA256SUMS').decode().splitlines():
                if not line.strip():
                    continue
                digest, name = line.split(None, 1)
                name = name.lstrip('* ').strip()
                if sha(z.read(name)) != digest:
                    raise ValueError('D0 manifest mismatch: '+name)
                count += 1
            for name in z.namelist():
                needed = (name.startswith(('forward/env_', 'inputs/env_')) or name in (
                    'protocol/E1_HOUSE_PROBE_CONTRACTS.tsv',
                    'protocol/JTD_E2_FRESH_TARGET_10x30.npy',
                    'evaluation/CANDIDATE_SCORES_ALL.csv'))
                if needed and not name.endswith('/'):
                    dest = (root/name).resolve()
                    if not dest.is_relative_to(root.resolve()):
                        raise ValueError('Unsafe archive path')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(z.read(name))
        # The amplitude module never consumes p. Verify all saved occurrence
        # products remain byte-identical across every arm and the full replay.
        p_before = {str(f.relative_to(root)): sha(f.read_bytes())
                    for f in sorted((root/'forward').rglob('*.p.f32'))}
        if len(p_before) != 1584:
            raise ValueError('Incomplete occurrence inventory')
        pr = pd.read_csv(root/'protocol/E1_HOUSE_PROBE_CONTRACTS.tsv', sep='\t')
        targets = np.load(root/'protocol/JTD_E2_FRESH_TARGET_10x30.npy')
        if targets.shape != (3, 6, 4, 10, 30):
            raise ValueError('Frozen OPEN target shape mismatch')
        candidates, records, fields_rows, pair_rows, costs, matrices = [], [], [], [], [], {}
        prepared = {}
        for e, house in enumerate(HOUSES):
            start = time.perf_counter_ns()
            meta = json.loads((root/f'inputs/env_{e}/meta.json').read_text())
            pi = pd.read_csv(root/f'inputs/env_{e}/probes.csv')
            source_panel = pd.read_csv(root/f'inputs/env_{e}/sources.csv').sort_values('source_index')
            if list(source_panel.source_index) != list(range(6)) or any(
                    source_panel.iloc[s].pair_id != source_panel.iloc[s^1].pair_id for s in range(6)):
                raise ValueError('Frozen paired source order mismatch')
            ops, geometry = frozen_operators(meta, pr[pr.house == house], pi)
            geom_done = time.perf_counter_ns()
            maps = {kind: load_saved_mean_maps(root, e, kind, meta['width']*meta['height'])
                    for kind in ['u', 'rawu']}
            load_done = time.perf_counter_ns()
            prepared[e] = {}
            for name, op in ops.items():
                matrices[f'env_{e}_{name}'] = op.weights
            (out/f'env_{e}_geometry.json').write_text(json.dumps(geometry, indent=2)+'\n')
            for arm in Arm:
                t = time.perf_counter_ns()
                bank = AmplitudeTemplates.prepare(maps, ops, arm)
                build_ns = time.perf_counter_ns()-t
                prepared[e][arm] = bank
                for k in range(6):
                    for q in range(30):
                        fields_rows.append(dict(env=e, source=k, probe=q+1, arm=arm.value, value=float(bank.fields[k, q])))
                for k in range(0, 6, 2):
                    va, vb = bank.fields[k], bank.fields[k+1]
                    co = float(np.dot(va, vb)/np.linalg.norm(va)/np.linalg.norm(vb))
                    pair_rows.append(dict(env=e, pair=k//2, arm=arm.value, cosine=co, angular_gap=1-co))
                durations = []
                for s in range(6):
                    for j in range(4):
                        t = time.perf_counter_ns()
                        sse, gain = bank.score(targets[e, s, j])
                        durations.append(time.perf_counter_ns()-t)
                        rank, unique = ranking(sse, s)
                        records.append(dict(env=e, source=s, target=j, arm=arm.value, rank=rank,
                            unique_top1=unique, map_source=int(np.argmin(sse)), true_sse=float(sse[s]),
                            pair_delta_sse=float(sse[s^1]-sse[s])))
                        for k in range(6):
                            candidates.append(dict(env=e, source=s, target=j, candidate=k, arm=arm.value,
                                sse=float(sse[k]), scale=float(gain[k])))
                # Cost-only repeat on the same OPEN observations, no fitting.
                # Warmed 100 x 24 avoids reporting a single cold call as online latency.
                times = []
                for _ in range(100):
                    for y in targets[e].reshape(24, 10, 30):
                        t = time.perf_counter_ns(); bank.score(y); times.append(time.perf_counter_ns()-t)
                costs.append(dict(env=e, arm=arm.value, geometry_seconds=(geom_done-start)/1e9,
                    load_average_both_kinds_seconds=(load_done-geom_done)/1e9,
                    projection_template_seconds=build_ns/1e9,
                    online_score_median_us=float(np.median(times)/1e3),
                    online_score_q95_us=float(np.quantile(times, .95)/1e3),
                    first_pass_median_us=float(np.median(durations)/1e3), measured_calls=len(times),
                    template_bytes=bank.values.nbytes, field_bytes=bank.fields.nbytes,
                    shared_mean_map_bytes=sum(m.nbytes for m in maps.values()),
                    shared_operator_bytes=sum(op.weights.nbytes for op in ops.values())))
            if p_before != {str(f.relative_to(root)): sha(f.read_bytes())
                            for f in sorted((root/'forward').rglob('*.p.f32'))}:
                raise ValueError('Occurrence products changed')
        D = pd.DataFrame(records)
        summary = D.groupby(['env', 'arm']).agg(mean_rank=('rank', 'mean'), unique_top1=('unique_top1', 'mean'), n=('rank', 'count')).reset_index()
        tables = {'targets': D, 'candidates': pd.DataFrame(candidates), 'templates': pd.DataFrame(fields_rows),
                  'pairgeometry': pd.DataFrame(pair_rows), 'summary': summary}
        for name, table in tables.items():
            table.to_csv(out/f'posthoc_readout_factorial_{name}.csv', index=False)
        comparisons = {name: compare_csv(out/f'posthoc_readout_factorial_{name}.csv',
                         HERE/f'pro_reference/results/posthoc_readout_factorial_{name}.csv') for name in tables}
        projection_deviation = 0.
        archived_projection_bitwise = True
        with np.load(HERE/'pro_reference/results/geometric_projection_weights.npz') as old, np.load(out.parent/'pro_reproduction/geometric_projection_weights.npz') as replay:
            for e in range(3):
                mat = matrices[f'env_{e}_footprint']
                if not np.array_equal(mat, replay[str(e)]):
                    raise ValueError('Projection differs from supplied Pro code on this runtime')
                if not np.allclose(mat, old[str(e)], rtol=0., atol=1e-14):
                    raise ValueError('Projection matrix differs numerically from Pro archive')
                projection_deviation = max(projection_deviation, float(np.max(np.abs(mat-old[str(e)]))))
                archived_projection_bitwise &= np.array_equal(mat, old[str(e)])
        np.savez(out/'observation_operators.npz', **matrices)
        np.savez(out/'amplitude_templates.npz', **{
            f'env_{e}_{arm.value}': bank.values for e, banks in prepared.items() for arm, bank in banks.items()})
        # Independent second scoring traversal: compare every float byte and rank.
        for row in candidates:
            sse, gain = prepared[row['env']][Arm(row['arm'])].score(targets[row['env'], row['source'], row['target']])
            k = row['candidate']
            if float(sse[k]).hex() != row['sse'].hex() or float(gain[k]).hex() != row['scale'].hex():
                raise ValueError('Nondeterministic scoring repeat')
        rescue = []
        for (e, s), group in D.groupby(['env', 'source']):
            old = group[group.arm == 'u_nearest'].sort_values('target').unique_top1.to_numpy()
            new = group[group.arm == 'rawu_footprint'].sort_values('target').unique_top1.to_numpy()
            rescue.append(dict(env=int(e), source=int(s), rescued=int((new & ~old).sum()), harmed=int((old & ~new).sum())))
        pd.DataFrame(rescue).to_csv(out/'source_rescue_harm.csv', index=False)
        old = pd.read_csv(root/'evaluation/CANDIDATE_SCORES_ALL.csv').sort_values(['environment_index', 'source_index', 'target_index', 'candidate_index'])
        baseline = tables['candidates'].query("arm == 'u_nearest'").sort_values(['env', 'source', 'target', 'candidate'])
        baseline_error = float(np.max(np.abs(baseline.sse.to_numpy()-old.scaled_value_SSE.to_numpy())))
        (out/'native_occurrence_inventory.json').write_text(json.dumps(p_before, indent=2)+'\n')
        report = dict(scope='OPEN posthoc implementation reproduction; no scientific PASS/FAIL label',
            execution_git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=HERE, text=True).strip(),
            source_hashes={f.name: sha(f.read_bytes()) for f in HERE.glob('*.py')},
            historical_decision_unchanged='ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE',
            new_forward_runs=0, new_gaden_runs=0, training_runs=0, house03_or_sealed_data_read=False,
            inputs=hashes, package_manifest_entries=package_entries, d0_verified_entries=count,
            pro_full_reproduction=pro_checks, implementation_vs_pro=comparisons,
            projection_same_runtime_pro_bitwise_equal=True,
            projection_archive_bitwise_equal=bool(archived_projection_bitwise),
            projection_archive_max_absolute_deviation=projection_deviation,
            native_occurrence_files_unchanged=len(p_before),
            scoring_repeat_bitwise_equal=True, archived_B2_max_absolute_sse_deviation=baseline_error,
            rescued_targets=sum(r['rescued'] for r in rescue), harmed_targets=sum(r['harmed'] for r in rescue),
            rescued_source_units=sum(r['rescued'] > 0 for r in rescue),
            python=sys.version, numpy=np.__version__, pandas=pd.__version__, platform=platform.platform(),
            thread_environment={k: os.environ.get(k) for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'PYTHONNOUSERSITE', 'PYTHONUTF8']})
        (out/'IMPLEMENTATION_REPRODUCTION.json').write_text(json.dumps(report, indent=2)+'\n')
        pd.DataFrame(costs).to_csv(out/'compute_cost.csv', index=False)
        print(summary.to_string(index=False))
        print('OPEN reproduction complete; historical decision unchanged; STOP.')


if __name__ == '__main__':
    main()
