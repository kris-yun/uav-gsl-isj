"""Evaluate frozen three-arm outputs. Requires an approved gate amendment file."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--audit',type=Path,required=True)
p.add_argument('--outputs',type=Path,required=True)
p.add_argument('--amendment',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
amendment=json.loads(a.amendment.read_text())
assert amendment['three_arm_control_authorized'] is True
assert amendment['rank_gate'] in ('strict_improvement','noninferiority')
assert amendment['scientific_execution_authorized'] is True
audit=json.loads(a.audit.read_text())
def rows(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))
cases=[]
for case in audit['cases']:
    t=case['terminal'];par=case['resolved_parameters']
    i=math.floor((float(par['ground_truth_x'])-float(t['origin_x']))/float(t['cell_size']))
    j=math.floor((float(par['ground_truth_y'])-float(t['origin_y']))/float(t['cell_size']))
    leaves=case['active_candidates']
    covers=lambda leaf,x,y:int(leaf['origin_i'])<=x<int(leaf['origin_i'])+int(leaf['size_i']) and int(leaf['origin_j'])<=y<int(leaf['origin_j'])+int(leaf['size_j'])
    owner=[leaf['candidate_id'] for leaf in leaves if covers(leaf,i,j)]
    assert len(owner)==1
    truth=owner[0]
    snapshot=a.audit.parent/'frozen_inputs'/case['case']/'context_bank'/f"source_update_{int(t['source_update_id']):04d}"
    free=[r for r in rows(snapshot/'measured_hit_probability.csv') if r['occupancy']=='Free']
    cell_owners={int(r['cell_index']):next(leaf['candidate_id'] for leaf in leaves if covers(leaf,int(r['grid_i']),int(r['grid_j']))) for r in free}
    record=dict(case=case['case'],truth_owner_leaf=truth,active_leaves=len(leaves),free_cells=len(free),arms={})
    for arm in ('native','oracle2d','oracle3d'):
        scores={r['candidate_id']:float(r['log_score']) for r in rows(a.outputs/case['case']/arm/'candidate_log_scores.csv')}
        assert set(scores)=={leaf['candidate_id'] for leaf in leaves}
        assert all(not math.isnan(v) and v!=math.inf for v in scores.values())
        target=scores[truth];wrong=[v for cid,v in scores.items() if cid!=truth]
        assert math.isfinite(target) and any(math.isfinite(v) for v in wrong), 'margin undefined'
        better=sum(v>target for v in wrong);tied=sum(v==target for v in wrong)
        peak=max(scores.values());weights={idx:math.exp(scores[cid]-peak) for idx,cid in cell_owners.items()}
        total=sum(weights.values());posterior={idx:w/total for idx,w in weights.items()}
        margin=target-max(wrong)
        free_values=[scores[cid] for cid in cell_owners.values()]
        cell_midrank=1+sum(v>target for v in free_values)+0.5*(sum(v==target for v in free_values)-1)
        map_cells=[r for r in free if scores[cell_owners[int(r['cell_index'])]]==peak]
        xy=(float(map_cells[0]['x']),float(map_cells[0]['y'])) if len(map_cells)==1 else None
        arm_record=dict(truth_leaf_midrank=1+better+tied/2,truth_leaf_pessimistic_rank=1+better+tied,
                        equal_score_other_leaves=tied,unique_top1=int(better==0 and tied==0),
                        recall_at5=int(1+better+tied<=5),truth_log_score=target,source_margin=margin,
                        free_cell_midrank=cell_midrank,source_map_entropy_nats=-sum(v*math.log(v) for v in posterior.values() if v>0),
                        unique_map_xy=xy,map_tied_cell_count=len(map_cells))
        record['arms'][arm]=arm_record
        out=a.out/case['case']/arm;out.mkdir(parents=True,exist_ok=False)
        with (out/'sourceProbability.csv').open('w',newline='') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(['cell_index','grid_i','grid_j','x','y','leaf_id','source_probability'])
            for r in free:
                idx=int(r['cell_index']);w.writerow([idx,r['grid_i'],r['grid_j'],r['x'],r['y'],cell_owners[idx],format(posterior[idx],'.17g')])
    record['delta_margin_3d_vs_oracle2d']=record['arms']['oracle3d']['source_margin']-record['arms']['oracle2d']['source_margin']
    record['delta_margin_3d_vs_native']=record['arms']['oracle3d']['source_margin']-record['arms']['native']['source_margin']
    cases.append(record)
delta=[c['delta_margin_3d_vs_oracle2d'] for c in cases]
med2=statistics.median(c['arms']['oracle2d']['truth_leaf_midrank'] for c in cases)
med3=statistics.median(c['arms']['oracle3d']['truth_leaf_midrank'] for c in cases)
margin_pass=sum(v>0 for v in delta)>=3 and statistics.median(delta)>0
rank_pass=med3<med2 if amendment['rank_gate']=='strict_improvement' else med3<=med2
decision='PMFS3D_R1_ORACLE_RANKING_PASS' if margin_pass and rank_pass else ('PMFS3D_R1_MARGIN_ONLY_PROMISING' if margin_pass else 'PMFS3D_R1_NO_RANKING_GAIN')
result=dict(decision=decision,primary_comparison='oracle3d minus oracle2d',rank_gate=amendment['rank_gate'],
            positive_margin_cases=sum(v>0 for v in delta),median_delta_margin=statistics.median(delta),
            median_rank_oracle2d=med2,median_rank_oracle3d=med3,margin_gate_pass=margin_pass,rank_gate_pass=rank_pass,
            amendment_sha256=hashlib.sha256(a.amendment.read_bytes()).hexdigest(),cases=cases,
            interpretation='four historical offline cases, known source height, state0 CFD, leaf hypotheses; not held-out main innovation confirmation')
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'R1_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
print(json.dumps({key:result[key] for key in ('decision','positive_margin_cases','median_delta_margin','median_rank_oracle2d','median_rank_oracle3d')}))
