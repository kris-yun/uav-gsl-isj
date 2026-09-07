"""Independent NumPy score recomputation for the two new M2 diagnostics."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np


def nll(y,mean,scale):
    error=np.asarray(y,dtype=np.float64)-np.asarray(mean,dtype=np.float64)
    innovations=error.copy();innovations[1:]-=.3*error[:-1]
    scale=np.asarray(scale,dtype=np.float64)
    assert (scale>0).all() and np.isfinite(scale).all()
    return float((.5*np.log(2*np.pi)+np.log(scale)+.5*(innovations/scale)**2).sum())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--physics',type=Path,required=True)
    ap.add_argument('--local',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();report=json.loads(args.physics.read_text());counts={}
    for r in report['cases']:
        observed=r['observed_logppm'];last=math.log1p(r['latest_observed_ppm'])
        assert len(r['source_components'])==1 # this artifact is prefix-assimilated, not mixture fitting
        c=r['source_components'][0]
        assert math.isclose(nll(observed,c['mean'],c['scale']),r['source_conditioned_nll'],rel_tol=1e-5,abs_tol=1e-4)
        assert math.isclose(nll(observed,c['mean'],np.ones(20)),r['source_matched_scale_nll'],rel_tol=1e-5,abs_tol=1e-4)
        assert math.isclose(nll(observed,np.full(20,last),np.ones(20)),r['persistence_nll'],rel_tol=1e-5,abs_tol=1e-4)
        mse=float(((np.asarray(observed)-np.asarray(c['mean']))**2).mean())
        assert abs(mse-r['source_logppm_mse'])<1e-10
        counts[r['house']]=counts.get(r['house'],0)+1
    assert counts==dict(H01=84,H02=84,H03=84)
    physics_summary=[]
    for f in report['summaries']:
        rows=[r for r in report['cases'] if r['house']==f['house']]
        for k,v in f.items():
            if k not in ('house','cases'): assert abs(float(np.mean([r[k] for r in rows]))-v)<1e-9
        physics_summary.append(f)
    local=json.loads((args.local/'SUMMARY.json').read_text())
    path=args.local/'PREDICTIONS.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==local['prediction_sha256']
    rows=json.loads(path.read_text());assert len(rows)==252
    for r in rows:
        for k,p in r['predictions'].items():
            assert abs(float(((np.asarray(p)-r['observed_logppm'])**2).mean())-r['mse'][k])<1e-12
    for f in local['folds']:
        subset=[r for r in rows if r['house']==f['house']]
        for k,v in f['logppm_mse'].items(): assert abs(float(np.mean([r['mse'][k] for r in subset]))-v)<1e-12
        scores=f['logppm_mse']
        assert f['pass_']==(scores['route']<scores['persistence'] and scores['route']<scores['history_only'])
    output=dict(verdict='M2_PREDICTION_SCORE_RECOMPUTATION_PASS',physics_cases=252,local_cases=252,
                physics_sha256=hashlib.sha256(args.physics.read_bytes()).hexdigest(),
                local_summary_sha256=hashlib.sha256((args.local/'SUMMARY.json').read_bytes()).hexdigest(),
                scope='artifact scores independently recomputed; no re-training or causal identification certification',
                formal_gate_authority=False)
    args.output.write_text(json.dumps(output,indent=2)+'\n');print(output['verdict'])


if __name__=='__main__': main()
