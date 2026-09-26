#!/usr/bin/env python3
"""Truth evaluator frozen before opening truth. Higher scores; lower ranks."""
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path
def rows(p):
    with p.open(newline='') as f: return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('truth'); ap.add_argument('freeze_commit'); a=ap.parse_args()
    root=Path(a.root); truthpath=Path(a.truth)
    assert hashlib.sha256(truthpath.read_bytes()).hexdigest()=='07ee4081fab67441f4bba9cde64f1828b369b6dca20b9c660dec9a5d542e4311'
    truth=json.loads(truthpath.read_text()); cid=truth['arms']['C']['truth_candidate_id']
    tx=float(truth['source_x']); ty=float(truth['source_y'])
    geometry={r['candidate_id']:r for r in rows(root/'inputs/C_candidate_scores.csv')}
    sr=rows(root/'scores/candidate_scores_source_blind.csv'); pr=rows(root/'scores/permutation_scores_source_blind.csv')
    def evaluate(data,metric):
        ranked=sorted(data,key=lambda r:(-float(r[metric]),r['candidate_id']))
        pos=next(i for i,r in enumerate(ranked) if r['candidate_id']==cid)
        top=ranked[0]; g=geometry[top['candidate_id']]
        return {'truth_rank':pos+1,'truth_score':float(ranked[pos][metric]),'top1':top['candidate_id'],'top1_error_m':math.hypot(float(g['center_x'])-tx,float(g['center_y'])-ty),'top10':[r['candidate_id'] for r in ranked[:10]]}
    arms={arm:{m:evaluate([r for r in sr if r['arm']==arm],m) for m in ('Elog','Ebrier')} for arm in ('historical','P1','C1','P2')}
    permutations={str(i):{m:evaluate([r for r in pr if int(r['permutation'])==i],m) for m in ('Elog','Ebrier')} for i in range(200)}
    controls={}
    for m in ('Elog','Ebrier'):
        matched=arms['P2'][m]; ranks=[v[m]['truth_rank'] for v in permutations.values()]; scores=[v[m]['truth_score'] for v in permutations.values()]
        controls[m]={'strict_rank_better_fraction':sum(r>matched['truth_rank'] for r in ranks)/200,'rank_tie_fraction':sum(r==matched['truth_rank'] for r in ranks)/200,'strict_score_better_fraction':sum(s<matched['truth_score'] for s in scores)/200,'score_tie_fraction':sum(s==matched['truth_score'] for s in scores)/200,'permutation_median_rank':statistics.median(ranks),'unique_truth_ranks':len(set(ranks)),'unique_truth_scores':len(set(scores)),'rank_deltas':{arm:matched['truth_rank']-arms[arm][m]['truth_rank'] for arm in ('historical','P1','C1')}}
    both=lambda pred: all(pred(m) for m in ('Elog','Ebrier'))
    improves=both(lambda m:arms['P2'][m]['truth_rank']<min(arms['P1'][m]['truth_rank'],arms['C1'][m]['truth_rank']))
    tail=any(controls[m]['strict_rank_better_fraction']>=0.95 and controls[other]['permutation_median_rank']>=arms['P2'][other]['truth_rank'] for m,other in [('Elog','Ebrier'),('Ebrier','Elog')])
    dynamic=improves and tail
    height=both(lambda m:arms['P1'][m]['truth_rank']<arms['historical'][m]['truth_rank']) and not dynamic
    mixture=both(lambda m:max(arms['C1'][m]['truth_rank'],arms['P2'][m]['truth_rank'])<arms['P1'][m]['truth_rank']) and not dynamic
    decision='WIND_ALIGNMENT_D0_'+('DYNAMIC_SIGNAL' if dynamic else 'HEIGHT_BASELINE_DEFECT' if height else 'MIXTURE_ONLY' if mixture else 'NULL_OR_ADVERSE')
    result={'decision':decision,'freeze_commit':a.freeze_commit,'truth_sha256':hashlib.sha256(truthpath.read_bytes()).hexdigest(),'truth_candidate_id':cid,'source_xy':[tx,ty],'arms':arms,'permutation_controls':controls,'gates':{'P2_improves_both_P1_C1_both_scores':improves,'permutation95_and_other_nonadverse':tail,'dynamic':dynamic,'height':height,'mixture':mixture},'decision_priority':['dynamic','height','mixture','null'],'rank_ties':'sort descending score then ascending candidate_id','percentiles':'strict comparisons; ties reported separately'}
    out=root/'evaluation'; out.mkdir(exist_ok=False)
    (out/'D0_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (out/'permutation_truth_evaluation.json').write_text(json.dumps(permutations,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
