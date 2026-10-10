"""Independent scalar M3 claim audit; no simulation or evidence mutation."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import csv,json,math,hashlib
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
M3=BASE/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010'
M1=BASE/'outputs/PMFS_B4_M1_SOURCE_REPRESENTATION_20261010'
def js(p):return json.loads(p.read_text(encoding='utf8'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf8',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(a,b):assert math.isclose(float(a),float(b),rel_tol=5e-12,abs_tol=2e-12),(a,b)
def choice(a,b,big=True):
    if abs(a-b)<=1e-12:return 'TIE'
    return 'C7' if (a>b if big else a<b) else 'K2'
ops=['PID_NATIVE','CENTER_COLUMN','CENTER_SENSOR_BAND','PID_CELL_TRUNCATED','PID_NO_GROWTH_KERNEL']
scores_saved=rows(M3/'operator_contrast/OPERATOR_SCORE_COMPARISON.csv');score_lookup={(r['operator'],r['task_id']):r for r in scores_saved}
assert len(score_lookup)==25
all_scores={}
for op in ops:
    data=js(M3/'operator_contrast'/f'ANONYMOUS_INPUT_{op}.json');saved=js(M3/'operator_contrast'/f'SCORES_{op}.json')
    p={cid:[(a+b+.5)/3 for a,b in zip(*reps)] for cid,reps in data['reference_events'].items()}
    assert saved['candidate_reference_probabilities']==p
    all_scores[op]={}
    for task,y in data['observation_events'].items():
        vals={cid:(math.fsum(math.log(q) if z else math.log1p(-q) for z,q in zip(y,v)),math.fsum((z-q)**2 for z,q in zip(y,v))/50) for cid,v in p.items()}
        row=score_lookup[op,task]
        for cid in ('C7','K2'):
            near(row[cid+'_log'],vals[cid][0]);near(row[cid+'_Brier'],vals[cid][1]);near(saved['tasks'][task][cid]['log_sum'],vals[cid][0]);near(saved['tasks'][task][cid]['brier_mean'],vals[cid][1])
        assert row['log_selected']==choice(vals['C7'][0],vals['K2'][0])
        assert row['Brier_selected']==choice(vals['C7'][1],vals['K2'][1],False)
        all_scores[op][task]=dict(C7_log_minus_K2=vals['C7'][0]-vals['K2'][0],K2_Brier_minus_C7=vals['K2'][1]-vals['C7'][1],selected_log=row['log_selected'],selected_Brier=row['Brier_selected'])
inp=rows(M1/'snapshot/input.csv');pobs=[1-1/(1+math.exp(float(r['logOdds']))) for r in inp];conf=[float(r['confidence']) for r in inp];free=[i for i,r in enumerate(inp) if r['occupancy']=='1'];assert len(free)==447
field=rows(M3/'projected_center_field/CENTER_FIELD_PER_CELL.csv');assert len(field)==12240
fl={(r['candidate_id'],r['variant'],r['stage'],int(r['cell_index'])):float(r['frequency']) for r in field};assert len(fl)==len(field)
field_saved=rows(M3/'projected_center_field/CENTER_FIELD_SOURCE_SCORES.csv');field_scores={}
for row in field_saved:
    cid,v,stage=row['candidate_id'],row['variant'],row['stage']
    total=math.fsum(math.log(1-.4*conf[i]*abs(pobs[i]-fl[cid,v,stage,i])) for i in free)
    near(total,row['native_style_log_similarity']);near(math.exp(total),row['native_style_similarity'])
    field_scores[cid,v,stage]=total
dense_margin={v+'/'+s:field_scores['C7',v,s]-field_scores['K2',v,s] for v in ('MASKED','ALL_XY') for s in ('UNBLURRED','NATIVE_STYLE_BLURRED')}
for pair in js(M3/'projected_center_field/CENTER_FIELD_RESULT.json')['pairs']:near(pair['C7_minus_K2_log_similarity'],dense_margin[pair['variant']+'/'+pair['stage']])
factorial=rows(M3/'boundary_point_experiment/PAIRWISE_FACTORIAL_EFFECTS.csv')
for r in factorial:
    near(float(r['wrong_score'])/float(r['true_score']),r['wrong_over_true_score']);near(math.log(float(r['wrong_score']))-math.log(float(r['true_score'])),r['wrong_minus_true_logscore']);assert r['selection']=='K2'
height=rows(M3/'height_intervention/HEIGHT_PAIRED_COMPARISONS.csv')
for r in height:
    near(float(r['wrong_score'])/float(r['true_score']),r['wrong_over_true_score']);near(math.log(float(r['wrong_score']))-math.log(float(r['true_score'])),r['wrong_minus_true_logscore']);assert r['choice']=='K2'
geometry=rows(M3/'projected_center_field/PROJECTED_GEOMETRY_OCCURRENCES.csv')
for r in geometry:near(float(r['projected_nonfree_occurrences'])/float(r['particle_snapshot_occurrences']),r['projected_nonfree_fraction'])
result=dict(status='PASS_INDEPENDENT_SCALAR_CLAIM_AUDIT_CURRENT_FOUR_STAGES',new_calls_from_this_review=0,operator_task_rows_checked=25,operator_original=all_scores['CENTER_COLUMN']['O0'],dense_field_margins_C7_minus_K2=dense_margin,factorial_all_eight_pairs='K2',height_all_six_pairs='K2',geometry_rows_checked=8,scopes=['operator_contrast','projected_center_field','boundary_point_experiment','height_intervention','own frozen proxy audit'],domain_support_new_call_results='NOT_REVIEWED_PENDING_PARENT',script_risks=['ALL_XY retains extra numerator support while normalizing with the old blurred navigation-free denominator and clipping; descriptive frozen readout control, not self-consistent gas-domain correction','Projected nonfree particle-snapshot fraction is an occupancy count, not causal percentage','Operator variants re-use already inspected M2 heldout tasks and compare proxy predictions to unchanged actual PID observations; exploratory not independent fresh test','Height SOURCE_PLANE true branches execute native maximum warmup and 3500 release points; candidate initial RNG matched but not event-keyed equal draw/path budget'],verified_input_sha256={str(p.relative_to(M3)).replace('\\','/'):sha(p) for p in [M3/'operator_contrast/OPERATOR_SCORE_COMPARISON.csv',M3/'operator_contrast/OPERATOR_RESULT.json',M3/'projected_center_field/CENTER_FIELD_SOURCE_SCORES.csv',M3/'projected_center_field/CENTER_FIELD_RESULT.json',M3/'boundary_point_experiment/PAIRWISE_FACTORIAL_EFFECTS.csv',M3/'height_intervention/HEIGHT_PAIRED_COMPARISONS.csv']})
(HERE/'M3_CLAIM_AUDIT_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:result[k] for k in ['status','operator_original','dense_field_margins_C7_minus_K2','factorial_all_eight_pairs','height_all_six_pairs','domain_support_new_call_results']},ensure_ascii=False,indent=2))
