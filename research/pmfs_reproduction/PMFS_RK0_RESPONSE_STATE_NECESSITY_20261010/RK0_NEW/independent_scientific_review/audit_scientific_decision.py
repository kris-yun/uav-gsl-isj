"""Read-only arithmetic QA of frozen RK0 tables, never learns a new kernel."""
import sys
sys.dont_write_bytecode = True
import argparse, csv, hashlib, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package', type=Path, default=ROOT/'outputs/PMFS_RK0_RESPONSE_STATE_NECESSITY_20261010')
parser.add_argument('--out', type=Path, help='Optional new output JSON path; defaults to read-only stdout.')
args = parser.parse_args()
P = args.package
OUT = args.out

def load(name):
    return json.loads((P / name).read_text(encoding='utf-8'))

def rows(name):
    with (P / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def close(a, b):
    assert abs(float(a)-float(b)) < 1e-12, (a, b)

truth = {'O0': 'C7', 'H101': 'C7', 'H102': 'K2', 'H103': 'C7', 'H104': 'K2'}
inputs = {m: load(f'SOURCE_BLIND_INPUT_{m}.json') for m in ['U', 'S', 'R', 'F']}
assert all(inputs[m]['observation_events'] == inputs['F']['observation_events'] for m in inputs)
assert inputs['R']['reference_events'] == inputs['U']['reference_events']
prob = {m: {s: [(a+b+.5)/3 for a, b in zip(*v)] for s, v in j['reference_events'].items()}
        for m, j in inputs.items()}
sc = {}
for m, j in inputs.items():
    sc[m] = {}
    for t, y in j['observation_events'].items():
        assert len(y) == 50 and set(y) <= {0, 1}
        scores = {}
        for s, pp in prob[m].items():
            scores[s] = {
                'log_sum': math.fsum(v*math.log(q)+(1-v)*math.log1p(-q) for v, q in zip(y, pp)),
                'brier_mean': math.fsum((q-v)**2 for v, q in zip(y, pp))/50}
        g = truth[t]; w = 'C7' if g == 'K2' else 'K2'
        sc[m][t] = dict(scores=scores,
            truth_mean_log=scores[g]['log_sum']/50,
            truth_Brier=scores[g]['brier_mean'],
            wrong_mean_log=scores[w]['log_sum']/50,
            wrong_Brier=scores[w]['brier_mean'],
            truth_directed_mean_log_margin=(scores[g]['log_sum']-scores[w]['log_sum'])/50,
            truth_directed_Brier_contrast=scores[w]['brier_mean']-scores[g]['brier_mean'])
    stored = load(f'SOURCE_BLIND_SCORES_{m}.json')
    for t, own in sc[m].items():
        for s, v in own['scores'].items():
            for k, val in v.items():
                close(val, stored['tasks'][t][s][k])

prediction = {m: rows(f'PREDICTIONS_{m}.csv') for m in ['U', 'S', 'R']}
metrics = {m: {x['bank']: x for x in rows(f'RECEIVER_METRICS_{m}.csv')} for m in prediction}
receiver = {}
for m, rr in prediction.items():
    receiver[m] = {}
    for b in ['C7_2', 'C7_3', 'K2_2', 'K2_3']:
        z = [r for r in rr if r['bank'] == b and r['membership_branch'] == '0']
        assert len(z) == 50
        certified = [r for r in z if r['prediction_event'] != 'AMBIGUOUS']
        complete = [r for r in z if int(r['uncovered_particles']) == 0]
        errors = sum(int(r['prediction_event']) != int(r['native_F_event']) for r in certified)
        a = dict(full_point_count=len(complete), certified_events=len(certified),
            event_error_lower=errors, event_error_upper=errors+50-len(certified),
            missing_particle_exposures=sum(int(r['uncovered_particles']) for r in z),
            total_particle_exposures=sum(int(r['particle_count']) for r in z))
        stored = metrics[m][b]
        for k, col in [('full_point_count','fully_covered_blocks'), ('certified_events','certified_events'),
                       ('event_error_lower','total_event_error_lower'), ('event_error_upper','total_event_error_upper'),
                       ('missing_particle_exposures','uncovered_particle_exposures'), ('total_particle_exposures','total_particle_exposures')]:
            assert a[k] == int(stored[col]), (m, b, k)
        for r in z:
            lo = float(r['prediction_lower_ppm']); hi = float(r['prediction_upper_ppm'])
            assert 0 <= lo <= hi
            assert (r['point_prediction_ppm'] == 'UNSUPPORTED') == (int(r['uncovered_particles']) > 0)
            event = '1' if lo > 0.10000000149011612 else '0' if hi <= 0.10000000149011612 else 'AMBIGUOUS'
            assert event == r['prediction_event']
        receiver[m][b] = a
    receiver[m]['all_200'] = {k: sum(v[k] for v in receiver[m].values()) for k in next(iter(receiver[m].values()))}

pair = []
for a in rows('PAIRED_U_S_HELDOUT_RESULTS.csv'):
    t = a['task']; b = a['bank']
    dl = sc['S'][t]['truth_directed_mean_log_margin'] - sc['U'][t]['truth_directed_mean_log_margin']
    db = sc['S'][t]['truth_directed_Brier_contrast'] - sc['U'][t]['truth_directed_Brier_contrast']
    close(dl, a['delta_mean_log_margin']); close(db, a['delta_Brier_contrast'])
    u = {int(r['block_id']): r for r in prediction['U'] if r['bank']==b and r['membership_branch']=='0'}
    s = {int(r['block_id']): r for r in prediction['S'] if r['bank']==b and r['membership_branch']=='0'}
    common = [i for i in u if int(u[i]['uncovered_particles']) == int(s[i]['uncovered_particles']) == 0]
    assert len(common) == int(a['common_complete_support_blocks'])
    if common:
        mu = math.fsum(float(u[i]['point_squared_error']) for i in common)/len(common)
        ms = math.fsum(float(s[i]['point_squared_error']) for i in common)/len(common)
        close(mu,a['U_MSE_common_support']); close(ms,a['S_MSE_common_support'])
    else: mu=ms=None
    pair.append(dict(task=t,bank=b,delta_mean_log_margin=dl,delta_Brier_contrast=db,
        common_full_point_count=len(common),U_common_MSE=mu,S_common_MSE=ms,
        S_correct_source_mean_log_gain=sc['S'][t]['truth_mean_log']-sc['U'][t]['truth_mean_log'],
        S_correct_source_Brier_improvement=sc['U'][t]['truth_Brier']-sc['S'][t]['truth_Brier']))

contract_hash = sha(P/'frozen_contract.json')
assert contract_hash == (P/'PRE_RUN_CONTRACT_SHA256.txt').read_text().split()[0]
assert contract_hash == load('EXECUTION_LEDGER.json')['contract_SHA256']
for n,h in load('BLIND_SCORES_PRE_ANALYSIS_SHA256.json').items():
    assert sha(P/n)==h,n

names = ['frozen_contract.json','PRE_RUN_CONTRACT_SHA256.txt','RK0_RESULT.json','EXECUTION_LEDGER.json',
         'PAIRED_U_S_HELDOUT_RESULTS.csv','PAIRED_R_S_HELDOUT_RESULTS.csv','ALL_SOURCE_TASK_RESULTS.csv',
         'REFERENCE_ONLY_STATE_BOUNDARIES.json','MODEL_COMPLEXITY_AND_ZERO_DENOMINATORS.json']
names += [f'{prefix}_{m}.{ext}' for m in inputs for prefix,ext in [('SOURCE_BLIND_INPUT','json'),('SOURCE_BLIND_SCORES','json')]]
names += [f'{prefix}_{m}.csv' for m in prediction for prefix in ['PREDICTIONS','RECEIVER_METRICS']]
qa = dict(status='PASS_READONLY_FROZEN_ARITHMETIC_AND_CLAIM_SCOPE_AUDIT',new_kernel_fits=0,new_physical_calls=0,
          contract_SHA256=contract_hash,U_R_reference_events_exactly_equal=True,
          source_scoring_from_frozen_inputs=sc,reference_event_counts={m:{s:[sum(x) for x in v] for s,v in j['reference_events'].items()} for m,j in inputs.items()},
          receiver_metrics_recomputed_from_frozen_predictions=receiver,paired_U_S_checks=pair,
          input_SHA256={n:sha(P/n) for n in names},
          scientific_scope='Oracle count response compression diagnostic; no CSCG necessity, independent confirmation or new localization gain established.')
if OUT is not None:
    assert not OUT.exists(), 'refuse to overwrite prior independent QA'
    OUT.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':qa['status'],'saved_QA':str(OUT) if OUT else None,
                  'receiver_summary':{m:z['all_200'] for m,z in receiver.items()}},ensure_ascii=False,indent=2))
