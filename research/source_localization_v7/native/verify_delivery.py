"""Portable frozen-result recomputation. No access to original/sealed archives."""
from pathlib import Path
import csv,hashlib,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gsl_discrimination.data import SynchronousBlock
from gsl_discrimination.m1_opponent.raw_joint import load_observation_model
from gsl_discrimination.evaluation.metrics import source_metrics

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(base,name):return base/str(name).replace('\\','/')

def main():
    root=Path(__file__).resolve().parents[1];out=root/'results/native_20261023'
    freeze=json.loads((out/'MODEL_FREEZE.json').read_text())
    assert all(sha(rel(out,f))==h for f,h in freeze['models'].items())
    r1=json.loads((out/'R1_EXTRACTION_RESULT.json').read_text())
    with (out/'PER_WORLD_M1.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    checked=0;error=0.
    for r in r1['blocks']:
        assert sha(rel(out,r['path']))==r['sha256']
        if r['split']!='dev':continue
        block=SynchronousBlock.load_npz(rel(out,r['path']));truth=('A','B').index(r['source_id'])
        for name in ('even','raw_joint','mother','fixed_two','secondary'):
            model=load_observation_model(out/'models'/name)
            symbol=int(model.encode(0,block.values,block.times_s,model.contract))
            p=model.channel.probabilities[0,:,0,symbol].copy();p/=p.sum()
            original=next(x for x in rows if x['method']==name and x['world_id']==r['run_id'])
            metrics=source_metrics(p,truth,model.channel.source_xy)
            assert symbol==int(original['symbol'])
            for key in ('true_probability','map_error_m','log_margin'):
                diff=abs(metrics[key]-float(original[key]));error=max(error,diff);assert diff<1e-12
            checked+=1
    cpp=json.loads((out/'CPP_INFERENCE_QA.json').read_text())
    result={'status':'PASS_FROZEN_BLOCK_MODEL_AND_PREDICTION_RECOMPUTATION','recomputed_predictions':checked,
            'max_difference':error,'reported_original_CPP_inference_status':cpp['status'],
            'this_command_did_not_run_CPP_or_full_raw_archive_readout':True,
            'new_training':0,'new_physics':0,'new_ROS':0}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
