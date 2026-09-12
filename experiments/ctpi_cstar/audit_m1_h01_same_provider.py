"""Same-code two-source diagnostic with evaluator-only discrepancy balls.

No fitted temperature/noise/amplitude; identity log1p working space.
Reference responses and their error radii are evaluator-only, not deployed
calibration. Abstention here is NOT evidence of improved task utility.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from m1_causal.evidence_bounds import pairwise_bound

def main():
    root=Path(__file__).resolve().parents[2]
    output=root/'evidence/cstar_m1_h01_same_provider_20260911.json'
    if output.exists(): raise FileExistsError(output)
    predictions={};references={};meta={};hashes={}
    for source in ('SA','SB'):
        p=root/f'evidence/cstar_m1_estimated_transport_h01_screen_240s_{source}_trace_v3_20260910.json'
        raw=json.loads(p.read_text());c=raw['candidates'][0]
        assert c['candidate']==source and c['status']=='PREFIX_COMPLETE'
        assert len(c['times'])==1200 and abs(c['times'][-1]-240)<1e-8
        predictions[source]=np.log1p(c['sensor_ppm']);meta[source]=raw
        path=root/f'evidence/cstar_current_runtime_assets240_20260907/realizations/H01_{source}_fast/measured_history.jsonl'
        obs=[json.loads(line) for line in path.read_text().splitlines()]
        assert len(obs)==1200 and np.allclose(c['times'],[x['t_sim_s'] for x in obs],atol=1e-9,rtol=0)
        references[source]=np.log1p([x['gas_ppm'] for x in obs])
        hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        hashes[path.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    # Identical causal code and provider assumptions, with only candidate changed.
    for k in ('code_sha256','map_sha256','wind_sha256','history_sha256','closure','initial_wind','emission'):
        assert meta['SA'][k]==meta['SB'][k],f'provider mismatch: {k}'
    eps={s:float(np.linalg.norm(predictions[s]-references[s])) for s in predictions}
    rows=[]
    for actual in ('SA','SB'):
        y=references[actual]
        losses={s:float(np.mean((y-p)**2)) for s,p in predictions.items()}
        bound=pairwise_bound(y,predictions['SA'],predictions['SB'],eps['SA'],eps['SB'])
        exact=.5*(np.sum((y-references['SB'])**2)-np.sum((y-references['SA'])**2))
        assert bound['lower']-1e-10<=exact<=bound['upper']+1e-10
        state='SA' if bound['lower']>0 else 'SB' if bound['upper']<0 else 'ABSTAIN'
        ranked=min(losses,key=losses.get)
        rows.append({'actual':actual,'log1p_mse':losses,'ordinary_rank1':ranked,
            'ordinary_correct':ranked==actual,'conditional_bound':bound,'reference_contrast':float(exact),
            'reference_ball_decision':state})
    result={'status':'SAME_PROVIDER_DIAGNOSTIC_NOT_DEPLOYABLE_M1_PASS',
        'reference_error_radii':eps,'radius_scope':'observed exact-reference discrepancy; NOT held-out coverage',
        'identity_working_metric':'not estimated sensor noise or a calibrated probability',
        'input_hashes':hashes,'cases':rows}
    with output.open('x') as f: json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
