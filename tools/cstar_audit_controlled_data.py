"""Independent trace/sensor/branch audit, plus non-selective data diagnostics."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import copy
import numpy as np

from cstar_freeze_controlled_routes import ROOT, ENV, DT, Grid, sha, dump


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def independent_sensor(raw):
    # Deliberately not SensorModel.process or a branch-state copy. Recompute
    # from the complete causal input prefix, including the initial zero input.
    gas, stamp, state, result = [0.0], [0.0], 0.0, []
    for r in raw:
        t = r['t_sim_s']
        gas.append(r['true_gas_ppm'])
        stamp.append(t)
        delayed_time = t-0.4
        delayed = 0.0
        if delayed_time > 0:
            j = next(j for j in range(1, len(stamp)) if stamp[j] >= delayed_time-1e-12)
            w = (delayed_time-stamp[j-1])/(stamp[j]-stamp[j-1])
            delayed = gas[j-1]+w*(gas[j]-gas[j-1])
        alpha = math.exp(-0.2/1.2)
        state = alpha*state+(1-alpha)*delayed
        result.append(min(1e6, max(0.0, state)))
    return result


def compare(raw, observed, expected_points, offset_step=0, expected_sensor=None):
    assert len(raw) == len(observed) == len(expected_points)
    if expected_sensor is None:
        expected_sensor = independent_sensor(raw)
    max_error = 0.0
    for i, (r, obs, point, expected) in enumerate(zip(raw, observed, expected_points, expected_sensor), 1):
        assert set(obs) == {'stamp_ns', 't_sim_s', 'pose_xy', 'wind_uv', 'gas_ppm'}, 'MODEL_HISTORY_FIELD_LEAK'
        assert obs['stamp_ns'] == (i+offset_step)*200000000 == r['stamp_ns']
        assert obs['t_sim_s'] == r['t_sim_s'] == point['t_sim_s']
        assert r['pose_xy'] == obs['pose_xy'] == [point['x'], point['y']]
        assert r['z'] == point['z'] == 0.3
        assert obs['wind_uv'] == r['wind_uv']
        assert all(math.isfinite(x) for x in [obs['gas_ppm'], *obs['pose_xy'], *obs['wind_uv']])
        max_error = max(max_error, abs(obs['gas_ppm']-expected))
    assert max_error < 1e-10, ('SENSOR_REPLAY_CONTRADICTION', max_error)
    return max_error


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets', type=Path, required=True)
    ap.add_argument('--read-only', action='store_true')
    args = ap.parse_args()
    assets = args.assets.resolve()
    routes_root = ROOT / 'evidence/cstar_controlled_routes_20260907'
    design = json.loads((routes_root / 'ROUTE_FREEZE.json').read_text())
    frozen = json.loads((ROOT / 'experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json').read_text())
    from cstar_extract_controlled_assets import route_points
    report = {'contract': 'CSTAR_CONTROLLED_TRACE_AUDIT_V1', 'pass': False,
              'scientific_module_effectiveness_evaluated': False, 'per_realization': []}
    live = assets / 'live_H01_numeric_wind'
    live_status = json.loads((live / 'run_status.json').read_text())
    assert live_status['pass'] and live_status['probe_exit_code'] == 0
    live_frames = [f for f in rows(live / 'aligned_input_frames.jsonl') if f['stamp_ns'] > 0]
    physical_raw = rows(assets / 'adapter_parity/H01/raw_frames.jsonl')
    expected_gas = independent_sensor(physical_raw)
    assert len(live_frames) == len(physical_raw) == 8
    wind_error, gas_error = 0.0, 0.0
    for f, raw, gas in zip(live_frames, physical_raw, expected_gas):
        assert f['stamp_ns'] == raw['stamp_ns'] and f['pose_xy'] == raw['pose_xy']
        wind_error = max(wind_error, *(abs(a-b) for a,b in zip(f['wind_uv'],raw['wind_uv'])))
        gas_error = max(gas_error, abs(f['gas_ppm']-gas))
    assert wind_error < 1e-6 and gas_error < 1e-10
    build = json.loads((ROOT / 'tools/cstar_numeric_wind_query_build.json').read_text())
    correction = {'contract': 'CSTAR_NUMERIC_WIND_RUNTIME_CORRECTION_V1', 'pass': True,
        'supersedes': 'H01 historical lexical wind selection only; maps/splits/raw provenance unchanged',
        'corrected_helper_sha256': build['tools/cstar_numeric_wind_raw_query'],
        'corrected_helper_source_sha256': build['tools/cstar_numeric_wind_raw_query.cpp'],
        'runtime_git_sha': live_status['git_sha'], 'live_frames': 8,
        'max_abs_live_to_numeric_wind_error': wind_error, 'max_abs_live_gas_error': gas_error,
        'live_frame_sha256': sha(live / 'aligned_input_frames.jsonl'),
        'physical_raw_frame_sha256': sha(assets / 'adapter_parity/H01/raw_frames.jsonl'),
        'adapter_parity_sha256': sha(assets / 'QUERY_ADAPTER_PARITY.json'),
        'environment_audit_sha256': sha(ENV / 'CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json')}
    if args.read_only:
        stored = json.loads((assets / 'WIND_INDEX_CORRECTION_AUDIT.json').read_text())
        assert stored == correction, 'STORED_WIND_CORRECTION_MISMATCH'
    else:
        dump(assets / 'WIND_INDEX_CORRECTION_AUDIT.json', correction)
    for record in frozen['records']:
        rid, house = record['realization_id'], record['house']
        target = assets / 'realizations' / rid
        row = design['houses'][house]
        raw = rows(target / 'evaluator_raw_history.jsonl')
        history = rows(target / 'measured_history.jsonl')
        assert len(raw) == 300
        error = compare(raw, history, route_points(row['history'])[1:])
        outcomes, contrast, contexts = [], {}, {}
        for r in row['routes']:
            key = Path(r['path']).stem
            future_raw = rows(target / (key+'_evaluator_raw.jsonl'))
            future = rows(target / (key+'_outcome.jsonl'))
            n = round(r['decision_time_s']/DT)
            expected = independent_sensor(raw[:n]+future_raw)[n:]
            error = max(error, compare(future_raw, future, route_points(r)[1:], n, expected))
            assert len(future) == 20
            hit = next((i for i, f in enumerate(future) if f['gas_ppm'] > 0.1), 20)
            outcomes.append(hit)
            contrast.setdefault(n, []).append(hit)
            contexts.setdefault(n, []).append([f['gas_ppm'] for f in future])
        status = json.loads((target / 'EXTRACTION_STATUS.json').read_text())
        assert status['numeric_header_wind_max_error'] == 0 and status['pass']
        report['per_realization'].append({'realization_id': rid, 'house': house,
            'independent_sensor_max_error': error, 'prefixes_retained': 15,
            'measured_history_max_ppm': max(r['gas_ppm'] for r in history),
            'history_positive_frames': sum(r['gas_ppm'] > 0.1 for r in history),
            'route_hit_cases': sum(t < 20 for t in outcomes), 'route_no_hit_cases': sum(t == 20 for t in outcomes),
            'same_context_different_first_hit_groups': sum(len(set(v)) > 1 for v in contrast.values()),
            'same_context_different_gas_sequence_groups': sum(any(v != a[0] for v in a[1:]) for a in contexts.values())})
    report['core_float32_position_quantization_max_m'] = max(
        math.dist([r['x'],r['y'],r['z']], np.asarray([r['x'],r['y'],r['z']], dtype=np.float32).astype(float))
        for h in design['houses'].values() for plan in [h['history'], *h['routes']] for r in route_points(plan))

    validator = ROOT / 'experiments/ctpi_cstar/validate_controlled_assets.py'
    temporary_audits = tempfile.TemporaryDirectory()
    for house in ['H01', 'H02', 'H03']:
        manifest = assets / 'manifests' / (house+'.json')
        data = json.loads(manifest.read_text())
        data['wind_index_correction_audit_path'] = '../WIND_INDEX_CORRECTION_AUDIT.json'
        data['wind_index_correction_audit_sha256'] = sha(assets / 'WIND_INDEX_CORRECTION_AUDIT.json')
        if args.read_only:
            assert json.loads(manifest.read_text()) == data
        else:
            dump(manifest, data)
        output_root = Path(temporary_audits.name) if args.read_only else assets
        subprocess.run([sys.executable, '-B', str(validator), '--manifest', str(assets / 'manifests' / (house+'.json')),
                        '--output', str(output_root / ('ASSET_AUDIT_'+house+'.json'))], check=True)

    # Destructive fixtures mutate copies only. Each must be rejected by the
    # actual validator, not a source-code string check.
    base = json.loads((assets / 'manifests/H01.json').read_text())
    base['asset_root'] = str(assets)
    for key in ('environment_alignment_audit_path', 'raw_realization_provenance_audit_path',
                'frozen_realization_split_path', 'route_freeze_path', 'wind_index_correction_audit_path'):
        base[key] = str((assets / 'manifests' / base[key]).resolve())
    tests = []
    def mutation(name, edit, expected):
        obj = copy.deepcopy(base)
        edit(obj)
        with tempfile.TemporaryDirectory() as td:
            inp, out = Path(td) / 'manifest.json', Path(td) / 'audit.json'
            dump(inp, obj)
            proc = subprocess.run([sys.executable, str(validator), '--manifest', str(inp), '--output', str(out)],
                                  capture_output=True, text=True)
            assert proc.returncode != 0 and expected in proc.stderr and not out.exists(), (name, proc.stderr)
            tests.append({'test': name, 'rejected': True, 'code': expected})
    mutation('parent_role_override', lambda d: d['m1_episodes'][0].update(split='train'), 'CSTAR_ASSET_PARENT_FROZEN_ROLE')
    mutation('fabricated_transport', lambda d: d['m1_episodes'][0].update(transport_intervention_id='fake'), 'CSTAR_ASSET_PARENT_TRANSPORT_IDENTITY')
    mutation('cross_parent_outcome', lambda d: d['m2_route_cases'][0].update(outcome_realization_id=d['m1_episodes'][4]['realization_id']), 'CSTAR_ASSET_M2_OUTCOME_PARENT_MISMATCH')
    mutation('source_truth_model_input', lambda d: d['model_input_fields'].append('source_xyz_m'), 'CSTAR_ASSET_FORBIDDEN_MODEL_INPUTS')
    mutation('forged_route_lock', lambda d: d.update(route_freeze_git_sha='0'*40), 'CSTAR_ASSET_UNREGISTERED_ROUTE_FREEZE')
    mutation('wrong_provenance_hash', lambda d: d.update(raw_realization_provenance_audit_sha256='0'*64), 'CSTAR_ASSET_HASH_MISMATCH')
    mutation('missing_parent', lambda d: d['m1_episodes'].pop(), 'CSTAR_ASSET_M1_')
    mutation('retrospective_adaptive_route', lambda d: d['m2_route_cases'][0].update(future_policy_dependent_path_used=True), 'CSTAR_ASSET_M2_RETROSPECTIVE_ADAPTIVE_PATH')
    report.update({'pass': True, 'm1_prefix_count': 180, 'm2_route_case_count': 252,
                   'outer_fold_audits_pass': 3, 'destructive_tests': tests,
                   'verdict': 'CSTAR_CONTROLLED_DATA_QUALIFICATION=PASS_NOT_MODEL_UTILITY'})
    if not args.read_only:
        dump(assets / 'CONTROLLED_TRACE_AUDIT.json', report)
    temporary_audits.cleanup()
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
