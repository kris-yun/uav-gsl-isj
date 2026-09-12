"""Existing-data diagnostic, NOT C2 evaluation or deployable calibration.

Opposite-wind exact traces are nominal predictions; same-wind exact traces
define evaluator-only perturbation radii. This measures how conservative V3
is for this declared crosswind change, without inventing a C2 error radius.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_m1_exact_counterfactual_transfer import read_jsonl
from m1_causal.counterfactual_likelihood import FopdtConfig, fopdt_response
from m1_causal.evidence_bounds import pairwise_bound


def main():
    root=Path(__file__).resolve().parents[2]
    observed_root=root/'evidence/cstar_current_runtime_assets240_20260907/realizations'
    forward_root=root/'evidence/cstar_m1_candidate_forward_20260909_r2'
    hashes={}; rows=[]
    def read(path):
        hashes[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
        return read_jsonl(path)
    for house in ('H01','H02','H03'):
        responses={}; histories={}
        for source in ('SA','SB'):
            for wind in ('fast','slow'):
                key=(source,wind)
                history=read(observed_root/f'{house}_{source}_{wind}/measured_history.jsonl')
                raw=read(forward_root/f'{house}_{source}_{wind}/candidate_forward_input.jsonl')
                assert [r['stamp_ns'] for r in raw]==[r['stamp_ns'] for r in history]
                stamps=tuple(r['t_sim_s'] for r in raw)
                exposure=tuple(r['candidate_forward_input_ppm'] for r in raw)
                # Transform after sensor, never transform exposure before sensor.
                responses[key]=np.log1p(fopdt_response(stamps,exposure,FopdtConfig(1.2,.4)))
                histories[key]=history
        for source in ('SA','SB'):
            decoy='SB' if source=='SA' else 'SA'
            for wind in ('fast','slow'):
                other='slow' if wind=='fast' else 'fast'
                history=histories[(source,wind)]
                for prefix in (60,120,180,240):
                    n=sum(r['t_sim_s']<=prefix for r in history)
                    y=np.log1p([r['gas_ppm'] for r in history[:n]])
                    c,d=responses[(source,other)][:n],responses[(decoy,other)][:n]
                    exact_c,exact_d=responses[(source,wind)][:n],responses[(decoy,wind)][:n]
                    ec,ed=float(np.linalg.norm(exact_c-c)),float(np.linalg.norm(exact_d-d))
                    b=pairwise_bound(y,c,d,ec,ed)
                    exact=pairwise_bound(y,exact_c,exact_d,0.,0.)['nominal']
                    assert b['lower']-1e-8<=exact<=b['upper']+1e-8
                    rows.append(dict(house=house,true_candidate_evaluator_only=source,target_wind=wind,
                        nominal_wind=other,prefix_s=prefix,samples=n,epsilon_c_oracle=ec,epsilon_d_oracle=ed,
                        exact_samewind_evidence=exact,**b))
    summary={}
    for prefix in (60,120,180,240):
        group=[r for r in rows if r['prefix_s']==prefix]
        summary[prefix]=dict(nominal_correct=sum(r['nominal']>0 for r in group),
            bound_correct=sum(r['lower']>0 for r in group),
            bound_wrong=sum(r['upper']<0 for r in group),
            abstain=sum(r['lower']<=0<=r['upper'] for r in group),cases=len(group))
    report=dict(contract='M1_V3_EXISTING12_ORACLE_CROSSWIND_SENSITIVITY',summary=summary,rows=rows,
        input_sha256=hashes,metric='log(1+concentration/1ppm), identity metric; no fitted Gaussian covariance',
        limits=['Radii use evaluator same-wind traces, forbidden runtime calibration.',
                'Crosswind perturbation is not approximate-provider error.',
                'No C2 fidelity, Gaussian law, coverage or closed-loop verdict follows.',
                'No change to observation or provider output, no new physical cells or seeds.'])
    output=root/'evidence/cstar_m1_v3_existing12_sensitivity_20260910.json'
    if output.exists():
        raise FileExistsError('refuse evidence overwrite')
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
