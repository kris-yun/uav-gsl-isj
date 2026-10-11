"""Standalone SAVED-ONLY RK2 numerical verification.

This checker needs only the new RK2 experiment directory. It imports no
prototype code and invokes no optimizer, phi/LOS, simulator or native process.
It checks frozen source/prepared-input/model/prediction SHA, saved-matrix KKT,
score algebra, compression/cost summaries, capacity and the registered A gate.
It DOES NOT recheck the 642 external parent assets, reconstruct X/prior from
196 reference caches, execute original information-isolation tests, rerun exact
physical readouts, validate unobserved data, or independently benchmark speed.
Use verify_rk2.py with the frozen RK1 parent for those lineage matrix checks.
All outputs must be written outside the immutable experiment directory.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np


def load(p):
    return json.loads(p.read_text(encoding='utf-8'))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def csvread(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def near(a, b, atol=3e-12, rtol=2e-10):
    assert math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol), (a, b)


def asbool(s):
    return s in (True, 'True', 'true', '1', 1)


def mean(v):
    return math.fsum(map(float, v)) / len(v)


def physical_key_features(f):
    xy = (f[:, :2] - np.asarray([-7.55, -7.88], dtype=np.float32)) / np.float32(.25)
    cell = np.floor(xy).astype(np.int32)
    features = np.column_stack((xy - cell, f[:, 2], f[:, 3])).astype(np.float64)
    return cell, features


def assign(features, spec):
    if spec['kind'] == 'U':
        return np.zeros(len(features), dtype=np.int32)
    if spec['kind'] == 'S':
        return 2 * (features[:, 2] >= spec['z_cut']).astype(np.int32) + (features[:, 3] >= spec['sigma_cut']).astype(np.int32)
    assert spec['kind'] == 'L'
    out = np.empty(len(features), dtype=np.int32)
    def visit(tree, indexes):
        if type(tree) is int:
            out[indexes] = tree
            return
        left = features[indexes, tree['feature']] < float(tree['cut'])
        visit(tree['left'], indexes[left])
        visit(tree['right'], indexes[~left])
    visit(spec['tree'], np.arange(len(features)))
    return out


def node_count(tree):
    return 0 if type(tree) is int else 1 + node_count(tree['left']) + node_count(tree['right'])


def leaf_ids(tree):
    return [tree] if type(tree) is int else leaf_ids(tree['left']) + leaf_ids(tree['right'])


def owning_object_size(x, seen=None):
    if seen is None:
        seen = set()
    if id(x) in seen:
        return 0
    seen.add(id(x))
    result = sys.getsizeof(x)
    if isinstance(x, dict):
        result += sum(owning_object_size(k, seen) + owning_object_size(v, seen) for k, v in x.items())
    elif isinstance(x, (list, tuple)):
        result += sum(owning_object_size(v, seen) for v in x)
    return result


def capacity(keys, spec):
    states = len(keys)
    nodes = node_count(spec['tree']) if spec['kind'] == 'L' else (2 if spec['kind'] == 'S' else 0)
    route_bytes = nodes * 32 if spec['kind'] == 'L' else (32 if spec['kind'] == 'S' else 0)
    runtime = dict(spec=json.loads(json.dumps(spec)), keys=np.array(keys, dtype=np.int32, copy=True),
                   h=np.zeros((states, 10), dtype=np.float64))
    return dict(active_states=states, decoder_coefficients=states * 10, routing_nodes=nodes,
                routing_bytes=route_bytes, canonical_key_bytes=states * 12,
                canonical_decoder_bytes=states * 80, canonical_total_bytes=states * 92 + route_bytes,
                routing_spec_UTF8_bytes=len(json.dumps(spec, sort_keys=True).encode('utf-8')),
                actual_minimal_runtime_object_bytes=owning_object_size(runtime))


def verified_forecast(forecast, observation, model):
    required = {'candidate_ids', 'source_xyz', 'reference_response_ppm', 'receiver_plan_id'}
    with np.load(forecast, allow_pickle=False) as z:
        assert set(z.files) == required
        ids = list(map(str, z['candidate_ids']))
        source_xyz = z['source_xyz'].copy()
        response = np.asarray(z['reference_response_ppm'], dtype=np.float32)
        plan = str(z['receiver_plan_id'].item())
    obs = load(observation)
    assert set(obs) == {'observation_id', 'observed_ppm', 'receiver_plan_id'}
    assert obs['receiver_plan_id'] == plan
    observed = np.asarray(obs['observed_ppm'], dtype=np.float32)
    assert observed.shape == (50,) and response.shape == (2, 2, 50)
    assert np.isfinite(observed).all() and np.isfinite(response).all()
    assert (observed >= 0).all() and (response >= 0).all()
    events = response > np.float32(.1)
    y = observed > np.float32(.1)
    # Each realization is thresholded first. Mean concentration is never thresholded.
    probability = (events.sum(axis=1).astype(np.float64) + .5) / 3.
    rows = []
    for c, cid in enumerate(ids):
        logs = [math.log(float(p)) if hit else math.log1p(-float(p)) for p, hit in zip(probability[c], y)]
        brier = [(int(hit) - float(p)) ** 2 for p, hit in zip(probability[c], y)]
        rows.append(dict(candidate_id=cid, physical_source_xyz=list(map(float, source_xyz[c])),
                         reference_realizations=2, reference_events=events[c].astype(np.int8).tolist(),
                         observed_events=y.astype(np.int8).tolist(), probability_by_block=probability[c].tolist(),
                         mean_Bernoulli_log_score=mean(logs), mean_Brier=mean(brier)))
    maximum = max(r['mean_Bernoulli_log_score'] for r in rows)
    unnormalized = [math.exp(r['mean_Bernoulli_log_score'] - maximum) for r in rows]
    normalizer = math.fsum(unnormalized)
    for r, v in zip(rows, unnormalized):
        r['source_probability'] = v / normalizer
    top = sorted(r['candidate_id'] for r in rows if abs(r['mean_Bernoulli_log_score'] - maximum) <= 1e-15)
    return dict(model_id=model, observation_id=obs['observation_id'], receiver_plan_id=plan,
                top1_candidate_ids=top, candidates=rows), response


def verify(root):
    root = Path(root).resolve(strict=True)
    files_before = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}
    contract = load(root / 'contract.json')
    assert digest(root / 'contract.json') == (root / 'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
    source_count = 0
    for name, expected in contract['source_SHA256'].items():
        assert digest(root / 'source' / name) == expected, name
        source_count += 1
    for name, expected in contract['prepared_input_SHA256'].items():
        assert digest(root / name) == expected, name
    for name, expected in load(root / 'PRE_REFERENCE_PREDICTION_MODEL_SHA256.json').items():
        assert digest(root / 'models' / name) == expected
    for name, expected in load(root / 'CANDIDATE_FORECAST_SHA256_BEFORE_OBSERVATIONS.json').items():
        assert digest(root / 'candidate_forecasts' / name) == expected
    frozen = load(root / 'PRE_TRUTH_EVALUATION_SHA256.json')
    for name, expected in frozen.items():
        assert digest(root / name) == expected, name
    assert 'SOURCE_TASK_PREDICTIONS_BLIND.json' in frozen

    layout = load(root / 'INPUT_LAYOUT.json')
    queries = [q for r in layout['reference_banks'] for q in r['queries']]
    assert len(queries) == 200
    target = np.asarray([q['native_ppm'] for q in queries], dtype=np.float64)
    poses = np.asarray([q['pose_id'] for q in queries], dtype=np.int32)
    info = load(root / 'FINAL_MODEL_RULES_AND_TRAIN_FITS.json')
    final_capacity = load(root / 'FINAL_CAPACITY_AND_STORAGE.json')
    fit_table = []
    cap_table = []
    model_data = {}
    for name in ('U_query', 'S_query', 'L'):
        with np.load(root / 'models' / (name + '.npz'), allow_pickle=False) as z:
            assert set(z.files) == {'keys', 'decoder', 'prior', 'train_counts', 'train_native_ppm', 'train_pose_ids', 'routing_spec'}
            keys = z['keys'].copy(); h = z['decoder'].copy(); prior = z['prior'].copy(); counts = z['train_counts'].copy()
            spec = json.loads(str(z['routing_spec'].item()))
            np.testing.assert_array_equal(z['train_native_ppm'], target)
            np.testing.assert_array_equal(z['train_pose_ids'], poses)
        assert counts.shape == (200, len(keys)) and h.shape == prior.shape == (len(keys), 10)
        assert np.isfinite(counts).all() and np.isfinite(h).all() and np.isfinite(prior).all()
        assert (counts >= 0).all() and (h >= 0).all() and (prior >= 0).all()
        assert np.all(counts == np.floor(counts))
        assert spec == info[name]['spec']
        with np.load(root / 'runtime_models' / (name + '.npz'), allow_pickle=False) as z:
            assert set(z.files) == {'keys', 'decoder', 'routing_spec'}
            np.testing.assert_array_equal(z['keys'], keys)
            np.testing.assert_array_equal(z['decoder'], h)
            assert json.loads(str(z['routing_spec'].item())) == spec
        per_pose_mse = []
        for p in range(10):
            A = counts[poses == p]; b = target[poses == p]
            assert len(b) == 20
            scale = np.sqrt(np.mean(A ** 2, axis=0)); scale[scale == 0] = 1.
            Z = A / scale; beta = h[:, p] * scale; beta0 = prior[:, p] * scale
            e = Z @ beta - b
            lam = float(contract['ridge_lambda']); assert lam == .01
            objective = float(np.mean(e ** 2) + lam * np.dot(beta - beta0, beta - beta0))
            g = 2 * (Z.T @ e / 20 + lam * (beta - beta0))
            projected = np.where(beta > 1e-10, np.abs(g), np.maximum(0., -g))
            kkt = float(projected.max(initial=0.))
            bound = float(contract['KKT_relative_tolerance']) * (1 + float(np.abs(Z.T @ b / 20).max(initial=0.)) + lam * float(np.abs(beta0).max(initial=0.)))
            assert kkt <= bound, (name, p, kkt, bound)
            mse = float(np.mean(e ** 2)); per_pose_mse.append(mse)
            log = info[name]['fit_logs'][p]
            assert int(log['pose_id']) == p and int(log['query_rows']) == 20
            near(objective, log['objective']); near(mse, log['train_MSE'])
            near(kkt, log['KKT_projected_gradient_max'], atol=3e-13)
            near(bound, log['KKT_threshold'])
            assert log['KKT_pass'] and log['dual_polish_cap'] == 32
            assert 0 <= log['identical_objective_dual_polish_steps'] <= 32
            fit_table.append(dict(method=name, pose_id=p, query_rows=20, train_MSE=mse,
                                  objective=objective, KKT_projected_gradient_max=kkt, KKT_threshold=bound))
        near(mean(per_pose_mse), info[name]['train_MSE'])
        cap = capacity(keys, spec)
        for key, value in cap.items():
            assert value == final_capacity[name][key], (name, key, value, final_capacity[name][key])
        assert int(np.count_nonzero(h)) == final_capacity[name]['decoder_nonzero_coefficients']
        assert keys.nbytes == final_capacity[name]['actual_key_array_nbytes']
        assert h.nbytes == final_capacity[name]['actual_decoder_array_nbytes']
        assert (root / 'runtime_models' / (name + '.npz')).stat().st_size == final_capacity[name]['actual_runtime_NPZ_file_bytes']
        model_data[name] = (keys, h, prior, counts, spec)
        cap_table.append(dict(method=name, **cap,
                              actual_runtime_NPZ_file_bytes=final_capacity[name]['actual_runtime_NPZ_file_bytes']))
    assert len(leaf_ids(model_data['L'][4]['tree'])) <= 4
    assert node_count(model_data['L'][4]['tree']) <= 3
    for k in ('active_states', 'canonical_total_bytes', 'actual_minimal_runtime_object_bytes', 'actual_runtime_NPZ_file_bytes'):
        assert final_capacity['L'][k] <= final_capacity['S_query'][k], k

    # Existing fit metadata is checked without solving an optimization problem.
    proposals = load(root / 'TRAIN_TREE_PROPOSAL_LOG.json')
    assert len(proposals) <= 72
    ids = [r['proposal_id'] for r in proposals]
    assert ids == list(range(1, len(ids) + 1))
    stages = sorted({r['stage'] for r in proposals})
    progress = [json.loads(line) for line in (root / 'PROGRESS_EVENTS.jsonl').read_text(encoding='utf-8').splitlines()]
    accepted = [v for v in progress if v['phase'] == 'TREE_SPLIT_ACCEPTED']
    for a in accepted:
        fitted = [r for r in proposals if r['stage'] == a['stage'] and r['status'] == 'FITTED_TRAIN_ONLY']
        best = min(fitted, key=lambda r: (r['train_MSE'], r['leaf'], r['feature'], r['cut']))
        assert best['proposal_id'] == a['proposal_id']
        near(best['train_MSE'], a['train_MSE'])
    for p in proposals:
        assert 1 <= p['stage'] <= 3 and 0 <= p['feature'] < 4
        if p['status'] == 'FITTED_TRAIN_ONLY':
            assert p['fit_KKT_all_pass'] and len(p['fit_logs']) == 10
            for log in p['fit_logs']:
                assert log['KKT_projected_gradient_max'] <= log['KKT_threshold']
            near(mean([r['train_MSE'] for r in p['fit_logs']]), p['train_MSE'])
            for k in ('active_states', 'canonical_total_bytes', 'actual_minimal_runtime_object_bytes'):
                assert p[k] <= final_capacity['S_query'][k]

    forecasts = {}
    score_rows = []
    blind = load(root / 'SOURCE_TASK_PREDICTIONS_BLIND.json')
    assert len(blind) == 16
    blind_lookup = {(r['model_id'], r['observation_id']): r['result'] for r in blind}
    for name in ('F', 'U_query', 'S_query', 'L'):
        for opath in sorted((root / 'observable_inputs').glob('O*.json')):
            result, response = verified_forecast(root / 'candidate_forecasts' / (name + '.npz'), opath, name)
            forecasts[name] = response
            saved = blind_lookup[(name, result['observation_id'])]
            assert saved['top1_candidate_ids'] == result['top1_candidate_ids']
            assert saved['receiver_plan_id'] == result['receiver_plan_id']
            assert saved['temperature'] == 1 and saved['smoothing_alpha'] == saved['smoothing_beta'] == .5
            assert saved['blocks'] == 50
            for r, s in zip(result['candidates'], saved['candidates']):
                assert r['candidate_id'] == s['candidate_id']
                assert r['reference_events'] == s['reference_events'] and r['observed_events'] == s['observed_events']
                np.testing.assert_array_equal(r['probability_by_block'], s['probability_by_block'])
                for k in ('mean_Bernoulli_log_score', 'mean_Brier', 'source_probability'):
                    near(r[k], s[k], atol=3e-15)
            score_rows.append(dict(method=name, observation_id=result['observation_id'], recomputed=result))
    reference_readouts = csvread(root / 'CANDIDATE_REFERENCE_READOUTS.csv')
    assert len(reference_readouts) == 200
    ordered_refs = layout['reference_banks']
    candidate_ids = list(dict.fromkeys(r['candidate_hypothesis_id'] for r in ordered_refs))
    rid_membership = {}
    for c, cid in enumerate(candidate_ids):
        rr = [r for r in ordered_refs if r['candidate_hypothesis_id'] == cid]
        assert len(rr) == 2
        for j, r in enumerate(rr):
            rid_membership[r['opaque_id']] = (c, j)
    for row in reference_readouts:
        c, ri = rid_membership[row['reference_id']]
        block = int(row['block_id'])
        for name in forecasts:
            # Forecast NPZ is float64; independent infer uses mandated float32.
            near(float(np.float32(row[name + '_ppm'])), forecasts[name][c, ri, block], atol=0., rtol=0.)
        near(row['F_ppm'], row['native_CPP_ppm'], atol=3e-7, rtol=5e-6)

    # Reconnect the evaluation-only mapping after independently verifying scores.
    truth = load(root / 'evaluation_only' / 'truth_mapping_AFTER_prediction_freeze.json')
    saved_task = {(r['method'], r['observation_id']): r for r in csvread(root / 'SOURCE_TASK_METRICS_AFTER_FREEZE.csv')}
    task_table = []
    for rr in score_rows:
        name = rr['method']; oid = rr['observation_id']; r = rr['recomputed']
        cid = truth[oid]; byid = {c['candidate_id']: c for c in r['candidates']}
        true = byid[cid]; top = r['top1_candidate_ids']
        result = dict(method=name, observation_id=oid, source_NLL_nat=-math.log(true['source_probability']),
                      Top1_error=int(len(top) != 1 or cid not in top), Top1_tie_count=len(top),
                      true_source_probability=true['source_probability'], true_mean_Brier=true['mean_Brier'],
                      true_mean_Bernoulli_log_score=true['mean_Bernoulli_log_score'],
                      wrong_mean_Bernoulli_log_score=next(c['mean_Bernoulli_log_score'] for k,c in byid.items() if k != cid))
        s = saved_task[name, oid]
        assert s['correct_source_for_evaluation_only'] == cid
        for k, v in result.items():
            if k in ('method', 'observation_id'):
                assert s[k] == v
            else:
                near(v, s[k], atol=3e-15)
        task_table.append(result)

    compression = csvread(root / 'COMPRESSION_EVALUATION_READOUTS.csv')
    assert len(compression) == 600
    groups = defaultdict(list)
    for row in compression:
        error = float(row['predicted_ppm']) - float(row['exact_F_ppm'])
        near(error, row['error_ppm'])
        assert float(row['predicted_ppm']) >= 0 and math.isfinite(error)
        event_error = (np.float32(row['predicted_ppm']) > np.float32(.1)) != (np.float32(row['exact_F_ppm']) > np.float32(.1))
        assert event_error == asbool(row['event_error'])
        near(row['exact_F_ppm'], row['native_CPP_ppm'], atol=3e-7, rtol=5e-6)
        assert int(row['fallback_particles']) == int(row['phi_particle_tests'])
        assert int(row['fallback_particles']) <= int(row['particles'])
        groups[row['observation_id'], row['method']].append(row)
    saved_comp = {(r['observation_id'], r['method']): r for r in csvread(root / 'COMPRESSION_METRICS.csv')}
    comp_table = []
    for (oid, name), rr in sorted(groups.items()):
        assert len(rr) == 50 and sorted(int(r['block_id']) for r in rr) == list(range(50))
        e = [float(r['predicted_ppm']) - float(r['exact_F_ppm']) for r in rr]
        met = dict(observation_id=oid, method=name, MSE_ppm2=mean([v*v for v in e]),
                   mean_signed_error_ppm=mean(e), MAE_ppm=mean([abs(v) for v in e]),
                   event_errors=sum(asbool(r['event_error']) for r in rr),
                   fallback_particle_fraction=sum(int(r['fallback_particles']) for r in rr)/sum(int(r['particles']) for r in rr),
                   blocks_with_fallback=sum(int(r['fallback_particles']) > 0 for r in rr))
        for k, v in met.items():
            if k not in ('observation_id','method'):
                near(v, saved_comp[oid, name][k])
        assert asbool(saved_comp[oid,name]['all_50_queries_included']) and asbool(saved_comp[oid,name]['oracle_encoding_only'])
        comp_table.append(met)

    costs = csvread(root / 'ALL_READOUT_COSTS.csv')
    assert len(costs) == 1600
    cost_groups = defaultdict(list)
    for row in costs:
        assert float(row['total_readout_wall_s']) >= 0
        assert int(row['LOS_calls']) <= int(row['particle_tests'])
        assert 0 <= int(row['fallback_particles']) <= int(row['particle_tests'])
        cost_groups[row['role'], row['method']].append(row)
    saved_cost = {(r['role'], r['method']): r for r in csvread(root / 'READOUT_COST_SUMMARY.csv')}
    cost_table = []
    for (role, name), rr in sorted(cost_groups.items()):
        assert len(rr) == 200
        met = dict(role=role, method=name, queries=len(rr),
                   total_readout_wall_s=math.fsum(float(r['total_readout_wall_s']) for r in rr),
                   shared_parse_wall_s=math.fsum(float(r['read_wall_s']) for r in rr),
                   phi_particle_tests=sum(int(r['particle_tests']) for r in rr),
                   LOS_calls=sum(int(r['LOS_calls']) for r in rr),
                   fallback_particles=sum(int(r['fallback_particles']) for r in rr))
        for k, v in met.items():
            if k not in ('role','method'):
                near(v, saved_cost[role,name][k])
        cost_table.append(met)
    task_summary = {name: dict(equal_bank_source_NLL=mean([r['source_NLL_nat'] for r in task_table if r['method']==name]),
                              Top1_errors=sum(r['Top1_error'] for r in task_table if r['method']==name))
                    for name in forecasts}
    saved_result = load(root / 'RK2_RESULT.json')
    for name, r in task_summary.items():
        for key, value in r.items():
            near(value, saved_result['source_summary'][name][key])
    ordinary_gain = all(task_summary[n]['equal_bank_source_NLL'] - task_summary['L']['equal_bank_source_NLL'] > contract['task_score_tolerance']
                        and task_summary['L']['Top1_errors'] <= task_summary[n]['Top1_errors'] for n in ('U_query','S_query'))
    refcost = {r['method']:r for r in cost_table if r['role']=='candidate_reference'}
    latency = refcost['L']['total_readout_wall_s'] <= refcost['F']['total_readout_wall_s']
    storage = all(final_capacity['L'][k] <= final_capacity['S_query'][k] for k in ('canonical_total_bytes','actual_minimal_runtime_object_bytes','actual_runtime_NPZ_file_bytes'))
    assert ordinary_gain == saved_result['method_source_task_gain']
    assert latency == saved_result['latency_vs_local_python_F_pass']
    assert storage == saved_result['canonical_storage_budget_pass']
    expected_status = 'A_DEVELOPMENT_GATE_PASS_REQUEST_B_ONLY' if ordinary_gain and latency and storage else 'A_CURRENT_CONSTRUCTION_NOT_QUALIFIED_NO_EXPANSION'
    assert saved_result['status'] == expected_status
    phases = [p['phase'] for p in progress]
    assert phases.index('CANDIDATE_FORECASTS_FROZEN_ALL_SOURCES') < phases.index('INFERENCE_FROZEN_BEFORE_TRUTH_OR_COMPRESSION_TEST_STATES') < phases.index('COMPRESSION_EVALUATION_ONLY')
    files_after = {p.relative_to(root).as_posix(): digest(p) for p in root.rglob('*') if p.is_file()}
    assert files_before == files_after
    result = dict(status='PASS_SAVED_ONLY_RK2_NUMERICAL_RECOMPUTATION', source_hashes=source_count,
                  parent_input_hashes_checked=0, prepared_input_hashes=len(contract['prepared_input_SHA256']),
                  prediction_freeze_hashes=len(frozen), fitted_model_objective_checks=len(fit_table),
                  proposal_metadata_checked=len(proposals), candidate_reference_readouts=200,
                  independently_recomputed_source_results=16, compression_readouts=600, cost_readouts=1600,
                  external_reference_cache_files_checked=0,
                  training_count_matrices_reconstructed_from_parent=0,training_priors_reconstructed_from_parent=0,
                  input_lineage_scope='Saved X/prior and targets verified algebraically only. External 642 assets and 196-cache reconstruction require full verify_rk2.py plus frozen RK1 parent.',
                  source_summary=task_summary, reproduced_A_status=expected_status,
                  files_unchanged=len(files_before), model_imports=0, optimization_calls=0, phi_LOS_calls=0,
                  scope='SAVED-ONLY: new-package SHA and saved matrix optimality/score/metric/capacity recomputation. No external input lineage, reference-cache reconstruction, physical readout, information-isolation rerun, independent task confirmation, or wall-clock benchmark.')
    return result, dict(fit_KKT=fit_table, capacity=cap_table, source_task_metrics=task_table,
                        compression_metrics=comp_table, costs=cost_table)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    root = a.root.resolve(); out = a.out.resolve()
    assert root != out and root not in out.parents
    assert not out.exists(), 'Verification outputs require a fresh external directory'
    result,tables = verify(root)
    out.mkdir(parents=True)
    for name,rows in tables.items():
        with (out/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'SAVED_ONLY_RK2_REVIEW_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
