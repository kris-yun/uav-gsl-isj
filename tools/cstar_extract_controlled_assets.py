"""Extract the precommitted kinematic route interventions, never select by gas.

Truth/raw simulator fields stay in evaluator-only outputs. Production needs no
raw-query executable or bank. No learner is loaded by this program.
"""
import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import select
import subprocess
import sys
import time

from cstar_freeze_controlled_routes import ROOT, ENV, DT, STARTS, Grid, sha, dump

ROUTES = ROOT / 'evidence/cstar_controlled_routes_20260907'
PROV = ROOT / 'evidence/cstar_raw_provenance_20260906/CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json'
SPLIT = ROOT / 'experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json'
ENV_AUDIT = ENV / 'CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json'
FREEZE_COMMIT = 'd3fa825a2da06a308af6bb6398d5f5a43e5b701a'
HELPER_SHA = '6797c938875c4d13021de56d214fefb6af4291ae4de3da9bb223e08127b4c333'


def load_archived(name):
    path = ENV / 'source_snapshot' / (name+'.py')
    spec = importlib.util.spec_from_file_location('controlled_'+name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SensorModel = load_archived('sensor_model').SensorModel
Timebase = load_archived('sim_timebase').DeterministicTimebase


def new_sensor():
    frozen = json.loads((ENV / 'probes_v1/H01/sensor_manifest.json').read_text())['sensor']
    sensor = SensorModel(seed=12, **frozen['config'])
    assert sensor.manifest() == frozen
    return sensor


def route_points(row):
    path = ROUTES / row['path']
    assert sha(path) == row['sha256'], ('ROUTE_HASH', path)
    with path.open() as f:
        return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True)+'\n')


def iteration(step):
    return Timebase(DT, step=step).replay_iteration(1999, 12, 'seeded_time_replay')


class Query:
    def __init__(self, helper, record, out):
        self.path = Path(record['resolved_realization_path'])
        self.hashes = {}
        self.log = (out / 'raw_query.stderr.log').open('x')
        self.proc = subprocess.Popen([str(helper), str(self.path.parents[2]), str(self.path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log, text=True, bufsize=1)

    def query(self, step, point):
        it = iteration(step)
        path = self.path / f'iteration_{it}'
        if it not in self.hashes:
            self.hashes[it] = sha(path)
        self.proc.stdin.write(f"{it} {point['x']:.17g} {point['y']:.17g} {point['z']:.17g}\n")
        self.proc.stdin.flush()
        if not select.select([self.proc.stdout], [], [], 30)[0]:
            raise RuntimeError('RAW_QUERY_TIMEOUT')
        line = self.proc.stdout.readline()
        parts = line.split()
        if len(parts) != 6 or parts[0] != 'OK':
            raise RuntimeError(f'RAW_QUERY_BAD_RESPONSE:{line!r}')
        gas, u, v, w = map(float, parts[1:5])
        assert all(math.isfinite(v) for v in (gas, u, v, w)) and gas >= 0
        return {'t_sim_s': round(step*DT, 9), 'stamp_ns': step*200000000,
            'step': step, 'iteration': it, 'pose_xy': [point['x'], point['y']], 'z': point['z'],
            'true_gas_ppm': gas, 'wind_uv': [u, v], 'wind_w': w, 'wind_index': int(parts[5])}

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc.wait(timeout=3)
        self.log.close()


def observed(raw, sensor):
    return {'stamp_ns': raw['stamp_ns'], 't_sim_s': raw['t_sim_s'],
            'pose_xy': raw['pose_xy'], 'wind_uv': raw['wind_uv'],
            'gas_ppm': sensor.process(raw['true_gas_ppm'], DT)}


def parity(helper, records, out):
    # Reuse archived measured ROS frames, not another environment launch.
    result = {}
    for house in STARTS:
        baseline = json.loads((ENV / f'probes_v1/{house}/run_status.json').read_text())
        record = next(r for r in records if r['resolved_realization_path'] == baseline['realization'])
        target = out / 'adapter_parity' / house
        target.mkdir(parents=True)
        query, sensor = Query(helper, record, target), new_sensor()
        raw_frames, differences = [], []
        frames = [json.loads(s) for s in (ENV / f'probes_v1/{house}/aligned_input_frames.jsonl').read_text().splitlines()]
        try:
            for f in frames:
                if f['stamp_ns'] == 0:
                    continue
                step = f['stamp_ns']//200000000
                raw = query.query(step, {'x': f['pose_xy'][0], 'y': f['pose_xy'][1], 'z': 0.3})
                obs = observed(raw, sensor)
                raw_frames.append(raw)
                differences.append(max(abs(obs['gas_ppm']-f['gas_ppm']),
                    *(abs(obs['wind_uv'][i]-f['wind_uv'][i]) for i in (0, 1))))
        finally:
            query.close()
        write_jsonl(target / 'raw_frames.jsonl', raw_frames)
        result[house] = {'frames': len(differences), 'max_abs_gas_wind_error': max(differences),
                         'pass': len(differences) == 8 and max(differences) < 1e-6}
    dump(out / 'QUERY_ADAPTER_PARITY.json', result)
    assert all(r['pass'] for r in result.values()), ('ADAPTER_PARITY_FAILED', result)
    print('CSTAR_RAW_QUERY_TO_ARCHIVED_ROS_PARITY=PASS', flush=True)


def extract_one(helper, record, design, out):
    rid, house = record['realization_id'], record['house']
    target = out / 'realizations' / rid
    target.mkdir(parents=True, exist_ok=False)
    points = route_points(design['history'])
    routes = [{**r, 'points': route_points(r)} for r in design['routes']]
    query, sensor = Query(helper, record, target), new_sensor()
    history, raw_history, branches = [], [], []
    started = time.monotonic()
    try:
        for step in range(1, len(points)):
            raw = query.query(step, points[step])
            raw_history.append(raw)
            history.append(observed(raw, sensor))
            for branch in branches:
                index = step-branch['decision_step']
                if 0 < index < len(branch['points']):
                    future_raw = query.query(step, branch['points'][index])
                    branch['raw'].append(future_raw)
                    branch['outcome'].append(observed(future_raw, branch['sensor']))
            for route in routes:
                if step == round(route['decision_time_s']/DT):
                    branches.append({**route, 'decision_step': step, 'sensor': copy.deepcopy(sensor),
                                     'raw': [], 'outcome': []})
        write_jsonl(target / 'measured_history.jsonl', history)
        write_jsonl(target / 'evaluator_raw_history.jsonl', raw_history)
        for branch in branches:
            name = Path(branch['path']).stem
            assert len(branch['outcome']) == 20
            write_jsonl(target / (name+'_outcome.jsonl'), branch['outcome'])
            write_jsonl(target / (name+'_evaluator_raw.jsonl'), branch['raw'])
        dump(target / 'RAW_ITERATION_SHA256.json', query.hashes)
        summary = {'realization_id': rid, 'house': house, 'history_frames': len(history),
            'route_cases': len(branches), 'future_frames': sum(len(b['outcome']) for b in branches),
            'query_pose_minus_command_pose_max_m': 0.0,
            'deviation_scope': 'offline query at exact frozen coordinates, not measured flight tracking',
            'wall_seconds': time.monotonic()-started, 'pass': True}
        dump(target / 'EXTRACTION_STATUS.json', summary)
        print(json.dumps(summary), flush=True)
    finally:
        query.close()


def manifests(out, design, split, provenance, git_sha):
    entries = {r['realization_id']: r for r in provenance['normalized_entries']}
    for held, fold in split['outer_folds'].items():
        data = {'contract': 'CSTAR_CONTROLLED_CAUSAL_ASSET_V1', 'created_git_sha': git_sha,
            'asset_root': '..', 'outer_fold': held, 'splits': ['train', 'heldout'],
            'environment_alignment_audit_path': '../../../cstar_environment_20260906/CSTAR_ENVIRONMENT_ALIGNMENT_AUDIT_V1.json',
            'environment_alignment_audit_sha256': sha(ENV_AUDIT),
            'raw_realization_provenance_audit_path': '../../../cstar_raw_provenance_20260906/CSTAR_RAW_REALIZATION_PROVENANCE_AUDIT_V1.json',
            'raw_realization_provenance_audit_sha256': sha(PROV),
            'frozen_realization_split_path': '../../../../experiments/ctpi_cstar/CSTAR_RAW_REALIZATION_SPLITS_FROZEN_20260906.json',
            'frozen_realization_split_sha256': sha(SPLIT),
            'route_freeze_path': '../../../cstar_controlled_routes_20260907/ROUTE_FREEZE.json',
            'route_freeze_sha256': sha(ROUTES / 'ROUTE_FREEZE.json'), 'route_freeze_git_sha': FREEZE_COMMIT,
            'model_input_fields': ['stamp_ns', 'pose_xy', 'gas_ppm', 'wind_uv', 'candidate_geometry', 'planned_route'],
            'evaluator_only_fields': ['source_xyz_m', 'source_id', 'house', 'realization_id', 'true_gas_ppm',
                                      'future_gas', 'future_wind', 'sensor_delay_queue'],
            'forbidden_model_inputs': ['true_gas_ppm', 'sensor_delay_queue'], 'm1_episodes': [], 'm2_route_cases': []}
        # Paths are relative to manifests/, while trace paths are relative to asset_root.
        for k in ['environment_alignment_audit_path', 'raw_realization_provenance_audit_path',
                  'frozen_realization_split_path', 'route_freeze_path']:
            data[k] = data[k].replace('../../../', '../../', 1)
        for record in split['records']:
            rid, house = record['realization_id'], record['house']
            e = entries[rid]
            role = 'heldout' if rid in fold['heldout_realization_ids'] else 'train'
            physical = e['physical_claims']
            base = {'episode_id': rid, 'realization_id': rid, 'split': role, 'house': house,
                'source_id': hashlib.sha256(json.dumps([house, physical['source_xyz_m']]).encode()).hexdigest()[:20],
                'source_xyz_m': physical['source_xyz_m'], 'geometry_identity': e['geometry_identity'],
                'transport_intervention_id': physical['transport_fingerprint'],
                'release_intervention_id': physical['release_fingerprint'],
                'sensor_intervention_id': sha(ENV / 'probes_v1/H01/sensor_manifest.json')}
            rel = f'realizations/{rid}/measured_history.jsonl'
            candidate = ENV / f'maps_v1/{house}/candidate.csv'
            data['m1_episodes'].append({**base, 'history_trace_path': rel, 'history_trace_sha256': sha(out / rel),
                'history_start_s': 0.2, 'history_end_s': 60.0,
                'candidate_domain_path': f'../cstar_environment_20260906/maps_v1/{house}/candidate.csv',
                'candidate_domain_sha256': sha(candidate), 'candidate_domain_truth_independent': True,
                'sensor_state_kind': 'absent', 'history_semantics': 'causal_prefixes',
                'prefix_times_s': design['m1_prefix_times_s'], 'runtime_feature_schema_version': 'CSTAR_MEASURED_HISTORY_V1'})
            for r in design['houses'][house]['routes']:
                name = Path(r['path']).stem
                outcome = f'realizations/{rid}/{name}_outcome.jsonl'
                data['m2_route_cases'].append({**base, 'decision_id': rid+'_'+name,
                    'decision_time_s': r['decision_time_s'], 'route_kind': 'controlled_open_loop_route',
                    'route_locked_time_s': 0.0, 'route_locked_before_outcome': True,
                    'future_policy_dependent_path_used': False,
                    'planned_route_path': '../cstar_controlled_routes_20260907/'+r['path'],
                    'planned_route_sha256': r['sha256'], 'outcome_trace_path': outcome,
                    'outcome_trace_sha256': sha(out / outcome), 'outcome_realization_id': rid,
                    'execution_deviation_reported': True, 'execution_deviation_max_m': 0.0,
                    'execution_kind': 'offline fixed-coordinate query; not real flight tracking'})
        dump(out / 'manifests' / (held+'.json'), data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--helper', type=Path, required=True)
    args = ap.parse_args()
    assert sha(args.helper) == HELPER_SHA, 'RAW_HELPER_IDENTITY'
    # A committed route lock is mandatory, not a Boolean supplied after extraction.
    subprocess.run(['git', 'merge-base', '--is-ancestor', FREEZE_COMMIT, 'HEAD'], cwd=ROOT, check=True)
    for path in [ROUTES / 'ROUTE_FREEZE.json', *ROUTES.glob('*/*.csv')]:
        rel = path.relative_to(ROOT).as_posix()
        frozen_bytes = subprocess.check_output(['git', 'show', FREEZE_COMMIT+':'+rel], cwd=ROOT)
        assert frozen_bytes == path.read_bytes(), ('COMMITTED_ROUTE_MISMATCH', rel)
    design = json.loads((ROUTES / 'ROUTE_FREEZE.json').read_text())
    split, provenance = json.loads(SPLIT.read_text()), json.loads(PROV.read_text())
    assert provenance['pass'] and provenance['frozen_split_manifest_sha256'] == sha(SPLIT)
    assert set(provenance['raw_realizations_eligible_for_future_truth_blind_route_extraction']) == {r['realization_id'] for r in split['records']}
    assert json.loads(ENV_AUDIT.read_text())['pass']
    for h in design['houses']:
        grid = Grid(h)
        assert grid.meta['geometry_identity'] == design['houses'][h]['geometry_identity']
        for r in [design['houses'][h]['history'], *design['houses'][h]['routes']]:
            grid.audit([(p['x'], p['y']) for p in route_points(r)])
    args.out.mkdir(parents=True, exist_ok=False)
    git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dump(args.out / 'EXTRACTION_START.json', {'git_sha': git_sha, 'route_freeze_git_sha': FREEZE_COMMIT,
        'route_freeze_sha256': sha(ROUTES / 'ROUTE_FREEZE.json'), 'helper_sha256': sha(args.helper),
        'started_utc': datetime.now(timezone.utc).isoformat(), 'new_seeds': False, 'scientific_models_loaded': False})
    parity(args.helper, split['records'], args.out)
    for record in split['records']:
        extract_one(args.helper, record, design['houses'][record['house']], args.out)
    manifests(args.out, design, split, provenance, git_sha)
    dump(args.out / 'EXTRACTION_COMPLETE.json', {'pass': True, 'realizations': 12,
        'm1_history_frames': 3600, 'm1_preregistered_prefixes': 180, 'm2_controlled_route_cases': 252,
        'm2_future_frames': 5040, 'scientific_gate_evaluated': False, 'asset_audit_pending': True})
    print('CSTAR_CONTROLLED_EXTRACTION_COMPLETE_PENDING_AUDIT', flush=True)


if __name__ == '__main__':
    main()
