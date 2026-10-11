"""Prepare opaque scoring inputs and hash them before invoking frozen scoring code."""
from common import *
import csv,hashlib,shutil
R=OUT/'native_reference_evidence/realizations'
score_source=W/'scoring_contract/score_source_blind.py'
shutil.copyfile(score_source,OUT/'score_source_blind.py')
tasks={'C7_2':'H101','K2_2':'H102','C7_3':'H103','K2_3':'H104'}
events={};bank_events=[]
for root in sorted(R.iterdir()):
    with (root/'QUERY_OUTPUT.csv').open(encoding='utf-8',newline='') as f:prediction=list(csv.DictReader(f))
    receptors={row['query_id']:row for row in prediction if row['query_id'].startswith('receiver_')}
    for branch in [0,1]:
        hits=[]
        for block in range(50):
            b=branch if block==40 else 0;row=receptors[f'receiver_b{block}_v{b}'];hit=int(float(row['ppm_float32'])>.1)
            hits.append(hit);bank_events.append(dict(bank_id=root.name,membership_branch=branch,block_id=block,
                stop_id=block//5,frame=int(row['frame']),sensor_x=float(row['x']),sensor_y=float(row['y']),sensor_z=float(row['z']),
                PID_ppm=float(row['ppm_float32']),block_hit=hit,consumed_members=1))
        events[(root.name,branch)]=hits
folder=OUT/'source_blind_inputs';folder.mkdir()
preinputs=[];label_outputs={}
for branch in [0,1]:
    references={cid:[events[(cid+'_'+str(rep),branch)] for rep in [0,1]] for cid in ['C7','K2']}
    observations={'O0':[1]*50,**{tid:events[(bank,branch)] for bank,tid in tasks.items()}}
    source=dict(reference_events=references,observation_events=observations)
    path=folder/('branch_'+str(branch)+'.json');path.write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
    preinputs.append(dict(branch=branch,input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         scorer_sha256=hashlib.sha256(score_source.read_bytes()).hexdigest()))
labeldir=W/'native_map_labels';labeldir.mkdir()
for bank in sorted(p.name for p in R.iterdir()):
    for branch in [0,1]:
        label=labeldir/(bank+'_branch'+str(branch)+'.csv')
        with label.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['block_id','event_hit']);writer.writeheader();writer.writerows(dict(block_id=i,event_hit=v) for i,v in enumerate(events[(bank,branch)]))
    label_outputs[bank]=dict(branches_identical=events[(bank,0)]==events[(bank,1)])
with (OUT/'RAW_SOURCE_CONDITIONED_BLOCK_PREDICTIONS.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(bank_events[0]));writer.writeheader();writer.writerows(bank_events)
(OUT/'SOURCE_BLIND_PRE_SCORE_LOCK.json').write_text(json.dumps(dict(inputs=preinputs,
    selection='fixed Bernoulli log and Brier; no look-at-results smoothing/threshold/seed changes',
    tie_rule='absolute score difference <=1e-12 is tie, not correct classification',
    membership='predeclared branches evaluated separately; disagreement implies HOLD'),indent=2)+'\n',encoding='utf-8')
(OUT/'HELDOUT_GENERATOR_MAPPING_ANALYSIS_ONLY.json').write_text(json.dumps({tid:bank.split('_')[0] for bank,tid in tasks.items()},indent=2)+'\n',encoding='utf-8')
(OUT/'BRANCH_PREDICTION_EQUIVALENCE.json').write_text(json.dumps(label_outputs,indent=2)+'\n',encoding='utf-8')
print('Anonymous inputs frozen; scores not computed by this preparer.')
