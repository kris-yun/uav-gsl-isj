"""Fixed marginal predictive scores, anonymous candidates, no truth metadata."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import math, json, hashlib

ALPHA=BETA=0.5
NREF=2
BLOCKS=50
def source_blind_scores(reference, observations):
    """reference={anonymous_candidate: [[50 binary events],[50 binary events]]}.
    observations={opaque_task: [50 binary events]}.
    Does not accept coordinates, true/wrong role, heldout generating label.
    """
    assert len(reference)==2
    for cid, reps in reference.items():
        assert isinstance(cid,str) and len(reps)==NREF
        assert all(len(x)==BLOCKS and all(y in (0,1) for y in x) for x in reps)
    result={'definition':'marginal/composite Bernoulli log score and Brier; not joint likelihood or calibrated posterior','smoothing':{'alpha':ALPHA,'beta':BETA,'reference_realizations_per_candidate':NREF},'candidate_reference_probabilities':{},'tasks':{}}
    for cid,reps in reference.items():
        result['candidate_reference_probabilities'][cid]=[(sum(x[j] for x in reps)+ALPHA)/(NREF+ALPHA+BETA) for j in range(BLOCKS)]
    for task,y in observations.items():
        assert len(y)==BLOCKS and all(k in (0,1) for k in y)
        taskres={}
        for cid,p in result['candidate_reference_probabilities'].items():
            logs=[a*math.log(b)+(1-a)*math.log1p(-b) for a,b in zip(y,p)]
            bri=[(a-b)**2 for a,b in zip(y,p)]
            taskres[cid]={'log_sum':math.fsum(logs),'log_mean':math.fsum(logs)/BLOCKS,'brier_sum':math.fsum(bri),'brier_mean':math.fsum(bri)/BLOCKS,'per_block_log':logs,'per_block_brier':bri,'per_stop_log_mean':[math.fsum(logs[j:j+5])/5 for j in range(0,BLOCKS,5)],'per_stop_brier_mean':[math.fsum(bri[j:j+5])/5 for j in range(0,BLOCKS,5)]}
        result['tasks'][task]=taskres
    return result

def main():
    if len(sys.argv)!=3: raise SystemExit('usage: score_source_blind.py SOURCE_BLIND_INPUT.json NEW_OUTPUT.json')
    src=Path(sys.argv[1]); dst=Path(sys.argv[2]); assert not dst.exists()
    obj=json.loads(src.read_text(encoding='utf8'));assert set(obj)=={'reference_events','observation_events'}, 'reject roles, coordinates, heldout labels'
    res=source_blind_scores(obj['reference_events'],obj['observation_events']);res['source_blind_input_sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
    dst.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
