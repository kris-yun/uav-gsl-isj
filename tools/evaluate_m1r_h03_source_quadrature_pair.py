#!/usr/bin/env python3
"""Frozen H03 seed12 development screen; truth is evaluator-only."""
from __future__ import annotations
import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path

TRUTH = (-0.45, 1.90)
SHARED = (
    'house', 'seed', 'algorithm_seed', 'sensor_seed', 'arm', 'pfdi_mode',
    'method', 'method_family', 'git_commit', 'algorithm_sha256',
    'vgr_bridge_source_root', 'vgr_bridge_contract_sha256', 'bank_summary_sha256',
    'cell_manifest_sha256', 'environment_preflight', 'geometry_manifest',
    'steps_source_update', 'max_warmup_iterations', 'min_warmup_iterations',
    'start_x', 'start_y', 'gas_backend', 'realization', 'config_id', 'timeout_sec',
    'realtime_factor', 'm1r_historical_rolling_persistence',
)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rows(p):
    with p.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def read_json(p):
    return json.loads(p.read_text(encoding='utf-8'))

def interpolate(trace, t):
    times = [x[0] for x in trace]
    if not times[0] <= t <= times[-1]:
        raise ValueError('NO_EXTRAPOLATION')
    j = bisect.bisect_right(times, t)
    if j == len(trace):
        return trace[-1][1]
    a, b = trace[j-1], trace[j]
    return a[1] + (b[1]-a[1]) * (t-a[0]) / (b[0]-a[0])

def integrate(trace, times):
    values = [interpolate(trace, t) for t in times]
    return math.fsum((b-a)*(x+y)/2 for a,b,x,y in
                     zip(times, times[1:], values, values[1:]))

def load_arm(root):
    manifest = read_json(root/'formal_runtime_manifest.json')
    status = read_json(root/'run_status.json')
    raw = rows(root/'source_estimate_trace.csv')
    values = {}
    for row in raw:
        if row['estimate_available'].lower() != 'true':
            continue
        if row['estimate_semantics'] != 'POSTERIOR_MAP':
            raise ValueError('WRONG_ESTIMATE_SEMANTICS')
        t = float(row['sim_time'])
        if 0 <= t <= 240:
            xy = (float(row['estimate_x']), float(row['estimate_y']))
            if not all(map(math.isfinite, (t, *xy))):
                raise ValueError('NONFINITE_TRACE')
            # Last row at an exactly duplicated timestamp is the final state.
            values[t] = math.dist(xy, TRUTH)
    trace = sorted(values.items())
    if len(trace) < 2:
        raise ValueError('INSUFFICIENT_SOURCE_TRACE')
    timing_path = root/'context_bank/source_update_timing.csv'
    timing = rows(timing_path)
    if not timing:
        raise ValueError('NO_COMPLETED_SOURCE_UPDATE')
    last = max(timing, key=lambda r: int(r['source_update_id']))
    uid = int(last['source_update_id'])
    pp = root/f'context_bank/source_update_{uid:04d}/source_posterior.csv'
    posterior = rows(pp)
    width = int(last['grid_width'])
    size, ox, oy = [float(last[k]) for k in ('cell_size','origin_x','origin_y')]
    ti, tj = math.floor((TRUTH[0]-ox)/size), math.floor((TRUTH[1]-oy)/size)
    true_cell = ti + tj*width
    actual = next(r for r in posterior if int(r['cell_index']) == true_cell)
    mass = float(actual['source_probability'])
    total = math.fsum(float(r['source_probability']) for r in posterior)
    if not math.isclose(total, 1, abs_tol=1e-7):
        raise ValueError(f'POSTERIOR_NORMALIZATION:{total}')
    files = ['formal_runtime_manifest.json','run_status.json','source_estimate_trace.csv',
             'context_bank/source_update_timing.csv', str(pp.relative_to(root))]
    bridge = read_json(root/'vgr_bridge_runtime_preflight.json')
    times = [t for t,_ in trace]
    summary = {
        'run_directory': str(root), 'manifest': manifest, 'status': status,
        'bridge_preflight': bridge,
        'first_source_trace_time_s': times[0], 'last_source_trace_time_s': times[-1],
        'source_trace_rows': len(trace), 'final_source_map_error_m': trace[-1][1],
        'individual_trace_auc_m_s': integrate(trace, times),
        'source_updates': len(timing),
        'source_update_wall_s': math.fsum(float(r['native_update_wall_s']) for r in timing),
        'legacy_counted_forward_calls': sum(int(r['native_forward_simulation_count']) for r in timing),
        'last_update': {'id':uid, 'sim_time_s':float(last['sim_time']),
                        'true_cell_mass':mass, 'posterior_sum':total,
                        'true_cell_rank_best':1+sum(float(r['source_probability']) > mass for r in posterior),
                        'cell_count':len(posterior)},
        'inputs':[{'path':name,'sha256':sha(root/name)} for name in files],
    }
    return summary, trace

def evaluate(baseline, fixed):
    a, ta = load_arm(baseline)
    b, tb = load_arm(fixed)
    checks = {f'shared_{key}': key in a['manifest'] and key in b['manifest'] and
              a['manifest'][key] == b['manifest'][key] for key in SHARED}
    for name, arm, enabled in [('baseline', a, False), ('fixed_source', b, True)]:
        m = arm['manifest']
        checks[name+'_configuration'] = (
            m['house']=='H03' and m['seed']==m['sensor_seed']==m['algorithm_seed']==12
            and m['pfdi_mode']=='cer_ratio_m1' and m['timeout_sec']==240
            and m['m1r_historical_rolling_persistence'] is True
            and m['m1r_source_quadrature_enabled'] is enabled
            and m['steps_source_update']==3 and m['max_warmup_iterations']==3
            and m['min_warmup_iterations']==1 and m['realtime_factor']==1)
        checks[name+'_terminal_status'] = arm['status']['status']=='time_budget_timeout'
        checks[name+'_source_trace_coverage'] = (arm['first_source_trace_time_s'] <= 10
                                                and arm['last_source_trace_time_s'] >= 230)
    checks['bridge_code_equal'] = all(a['bridge_preflight'].get(k)==b['bridge_preflight'].get(k)
                                      for k in ('contract_sha256','runner_sha256','method'))
    start, end = max(ta[0][0],tb[0][0]), min(ta[-1][0],tb[-1][0])
    if end <= start:
        raise ValueError('NO_COMMON_INTERVAL')
    times = sorted({start, end, *(t for t,_ in ta if start<t<end),
                    *(t for t,_ in tb if start<t<end)})
    aa, ab = integrate(ta,times), integrate(tb,times)
    endpoint_delta = b['final_source_map_error_m'] - a['final_source_map_error_m']
    auc_delta = ab-aa
    valid = all(checks.values())
    gain = endpoint_delta < -1e-6 and auc_delta < -1e-6
    return {
        'contract':'M1R_H03_SOURCE_QUADRATURE_SCREEN_V1_20260912',
        'evidence_class':'ONE_EXISTING_HOUSE_ONE_EXISTING_SEED_DEVELOPMENT_SCREEN',
        'truth_evaluator_only':list(TRUTH), 'checks':checks,
        'valid_paired_run':valid, 'utility_both_improved':gain,
        'verdict':('INVALID_PAIR' if not valid else
                   'DEVELOPMENT_UTILITY_PASS_PENDING_COMPONENT_VERIFICATION' if gain else
                   'NO_GO_NO_WEIGHT_TUNING_NO_HOUSE_SWEEP'),
        'baseline':a,'fixed_source':b,
        'comparison':{'endpoint_delta_m_fixed_minus_baseline':endpoint_delta,
                      'common_interval_s':[start,end], 'common_auc_baseline_m_s':aa,
                      'common_auc_fixed_m_s':ab,'common_auc_delta_m_s_fixed_minus_baseline':auc_delta,
                      'integration':'piecewise linear, union timestamps, no extrapolation or 0/240 padding'},
        'causal_effect_identified':False,'cross_house_validated':False,'novelty_validated':False,
        'limitations':['5 forward calls per leaf versus 1; no compute matching',
                      'location geometry, finite quadrature, source identity and context changes not separately isolated',
                      'same seed is not exact continuous-time trajectory replay',
                      'native true-cell posterior mass is diagnostic, not calibration'],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--fixed-source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = evaluate(args.baseline,args.fixed_source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':result['verdict'],**result['comparison']},ensure_ascii=False))

if __name__=='__main__':
    main()
