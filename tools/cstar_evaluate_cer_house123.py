"""Frozen single-seed development evaluator for nested PMFS arms."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

TRUTH = {'H01': (-.4, -2.9), 'H02': (0., -1.), 'H03': (-.45, 1.9)}


def evaluate(path, truth):
    status_path = path / 'run_status.json'
    trace_path = path / 'source_estimate_trace.csv'
    status = json.loads(status_path.read_text())
    if status.get('status') != 'time_budget_timeout':
        raise ValueError(f'TERMINAL:{path}:{status}')
    with trace_path.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    values = [(float(r['sim_time']), math.hypot(float(r['estimate_x'])-truth[0],
                                                   float(r['estimate_y'])-truth[1])) for r in rows]
    values = [v for v in values if v[0] <= 240.0]
    if not values or values[-1][0] < 235.0:
        raise ValueError(f'HORIZON:{path}:{values[-1] if values else None}')
    auc = sum((b[0]-a[0])*(a[1]+b[1])/2 for a,b in zip(values, values[1:]))
    return {'final_error_m': values[-1][1], 'distance_auc_m_s': auc,
            'last_estimate_time_s': values[-1][0], 'trace_rows_to_240': len(values),
            'status_sha256': hashlib.sha256(status_path.read_bytes()).hexdigest(),
            'trace_sha256': hashlib.sha256(trace_path.read_bytes()).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-root', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--m1-arm', default='M1')
    ap.add_argument('--m1m2-arm', default='M1M2')
    ap.add_argument('--contract', default='CSTAR_CER_HOUSE123_SEED12_DEVELOPMENT_V1')
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    arms = ('A0', args.m1_arm, args.m1m2_arm)
    if len(set(arms)) != 3 or any(not arm.replace('_', '').isalnum() for arm in arms):
        raise ValueError('CSTAR_EVALUATOR_ARM_IDS')
    houses = {}
    for house, truth in TRUTH.items():
        houses[house] = {arm: evaluate(args.run_root/f'{house}_seed12_{arm}', truth) for arm in arms}
        a0, m1, both = (houses[house][arm] for arm in arms)
        houses[house]['contrasts'] = {
          'm1_final_improvement_m': a0['final_error_m']-m1['final_error_m'],
          'm1_auc_improvement_m_s': a0['distance_auc_m_s']-m1['distance_auc_m_s'],
          'm2_increment_final_improvement_m': m1['final_error_m']-both['final_error_m'],
          'm2_increment_auc_improvement_m_s': m1['distance_auc_m_s']-both['distance_auc_m_s']}
    def gate(prefix):
        final = [houses[h]['contrasts'][prefix+'_final_improvement_m'] for h in TRUTH]
        auc = [houses[h]['contrasts'][prefix+'_auc_improvement_m_s'] for h in TRUTH]
        return {'final_improved_houses': sum(x > 0 for x in final),
                'auc_improved_houses': sum(x > 0 for x in auc),
                'mean_final_improvement_m': sum(final)/3,
                'mean_auc_improvement_m_s': sum(auc)/3,
                'pass': sum(x > 0 for x in final) >= 2 and sum(x > 0 for x in auc) >= 2 and
                        sum(final) > 0 and sum(auc) > 0}
    gates = {'m1_vs_a0': gate('m1'), 'm2_increment_vs_m1': gate('m2_increment')}
    report = {'contract': args.contract, 'seed': 12, 'arms': list(arms),
              'houses': houses, 'gates': gates,
              'verdict': 'DEVELOPMENT_GO' if all(g['pass'] for g in gates.values()) else 'NO_GO_NO_MULTISEED',
              'limits': ['seed12 exposed development screen','not independent confirmation','not causal identifiability proof']}
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'gates': gates, 'verdict': report['verdict']}, indent=2))


if __name__ == '__main__':
    main()
