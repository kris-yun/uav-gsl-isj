"""Read-only PHIC observation semantics and sensor-only repair diagnostics.

This is not a substitute predictor or a source-posterior reconstruction.
Synthetic traces establish loss of temporal information under aggregation;
the real export establishes what was actually recorded, not concentration.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

from m1_causal.counterfactual_likelihood import FopdtConfig, fopdt_response


SOURCE = 'ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def temporal_counterexample():
    sensor = FopdtConfig(tau_s=1.2, dead_time_s=.4)
    stamps = tuple((i + 1) * .2 for i in range(20))
    early = tuple(1. if i < 5 else 0. for i in range(20))
    late = tuple(1. if 12 <= i < 17 else 0. for i in range(20))
    a, b = (fopdt_response(stamps, x, sensor) for x in (early, late))
    assert sum(early) == sum(late)
    gap = max(abs(x - y) for x, y in zip(a, b))
    assert gap > 0
    return dict(label='synthetic concentration inputs, not measured PMFS concentrations',
                equal_aggregate=sum(early), early_output=a, late_output=b,
                max_sensor_difference=gap,
                conclusion='Aggregate alone does not determine the sensor sequence.')


def audit(repo, path, candidate):
    count = 0
    noninteger = out_of_range = 0
    values = []
    truth_records = {}
    member_ids = set()
    with path.open(encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            value = float(row['aggregate_raw_exposure'])
            n = int(row['iterations_to_record'])
            if not math.isfinite(value) or n <= 0:
                raise ValueError('invalid export')
            count += 1
            noninteger += value != round(value)
            out_of_range += not 0 <= value <= n
            values.append(value)
            if row['candidate_id'] == candidate:
                key = (float(row['sim_time_s']), row['cell_index'])
                truth_records.setdefault(key, []).append(value)
                member_ids.add(row['member_index'])
    if not truth_records:
        raise ValueError('missing evaluator region')
    allzero = all(v == 0 for group in truth_records.values() for v in group)
    sensor_test = None
    if allzero:
        stamps = tuple(sorted({k[0] for k in truth_records}))
        output = fopdt_response(stamps, (0.,) * len(stamps), FopdtConfig(1.2, .4))
        assert all(v == 0 for v in output)
        sensor_test = dict(max_response=max(output),
            condition='Feed ONLY the exported zero surrogate history, with zero initial state/input.',
            conclusion='Persistent sensor state and delay alone cannot create a source response from these inputs.',
            caveat='Unrecorded concentration/prehistory could differ; this is not a physical observability proof.')
    source_versions = []
    for revision in ('8d2e211', '429b19f', 'HEAD'):
        content = subprocess.check_output(['git', 'show', f'{revision}:{SOURCE}'], cwd=repo)
        source = content.decode('utf-8')
        source_versions.append(dict(revision=revision, source_sha256=hashlib.sha256(content).hexdigest(),
            copies_hit_count_to_exposure='*exposureMapBeforeNormalization = hitMap;' in source,
            increments_occupancy_once_per_step='if (updated[index] < t)' in source and 'hitMap[index]++;' in source,
            samples_source_region_per_filament='activeFilamentVec->back().position = source.getPoint();' in source,
            scope='source inspection only; not a binary/source binding'))
    return dict(contract='M1_PHIC_OBSERVATION_SEMANTICS_DIAGNOSTIC_V1',
                attribution_sha256=sha(path), rows=count, min_count=min(values), max_count=max(values),
                noninteger_rows=noninteger, outside_iteration_count_rows=out_of_range,
                quantity='filament-centre cell occupancy timestep count, not ppm',
                candidate_evaluator_only=candidate, member_ids=sorted(member_ids),
                sensor_only_zero_input_test=sensor_test,
                temporal_aggregation_counterexample=temporal_counterexample(),
                inspected_sources=source_versions,
                next_required_measurement='time-resolved candidate concentration along executed sensor poses, with units and prehistory',
                verdict='AGGREGATE_OCCUPANCY_IS_NOT_A_CONCENTRATION_PROVIDER',
                limits=['Does not isolate wind, source discretization, 2D/3D mismatch or field-estimation errors.',
                        'The exported candidate coordinate is a region representative, not every sampled source point.',
                        'No online algorithm changes or closed-loop utility claims.'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError('refuse to overwrite evidence')
    repo = Path(__file__).resolve().parents[2]
    result = audit(repo, args.input, args.candidate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('temporal_aggregation_counterexample', 'inspected_sources')}, indent=2))
