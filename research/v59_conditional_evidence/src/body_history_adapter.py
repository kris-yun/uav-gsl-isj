"""V59 complete-direction wrapper around the preserved V58 research proposal.

Adds explicitly tagged world-axis channels only for center-coincident sensors,
where radial/tangential axes are undefined. This is a correctness repair, not
an information gain or biological superiority claim. Input qualification is
enforced by the V58 encoder; no missing wind or timestamps are fabricated.
"""
from pathlib import Path
import json
import numpy as np
from m1_source_feedback import encode_causal_history, body_feedback_proposals


def encode_history_v59(times,positions,relative_wind,odor_eligibility,*,now,
                       lag_edges,support_qualified,quality=None,sample_weights=None):
    groups=encode_causal_history(times,positions,relative_wind,odor_eligibility,
        now=now,lag_edges=lag_edges,support_qualified=support_qualified,
        quality=quality,sample_weights=sample_weights)
    p,w,o,t,edges=map(lambda x:np.asarray(x,float),
                    (positions,relative_wind,odor_eligibility,times,lag_edges))
    nt,ns,_=p.shape
    at_center=np.linalg.norm(p-p.mean(axis=1,keepdims=True),axis=-1)<=1e-12
    if not at_center.any():
        return groups
    qual=np.ones((nt,ns),bool) if quality is None else np.asarray(quality,bool)
    sw=np.ones(nt) if sample_weights is None else np.asarray(sample_weights,float)
    age=now-t
    for ell in range(len(edges)-1):
        take=(age>=edges[ell])&(age<edges[ell+1])
        if ell==len(edges)-2:
            take|=age==edges[ell+1]
        for b in (0,1):
            axis=np.eye(2)[b]
            for sign in (-1,1):
                a=np.maximum(sign*w[...,b],0.)*qual*at_center*(take*sw)[:,None]
                for modality,elig in [('wind',np.ones_like(o)),('odor_tagged',o)]:
                    weight=a*elig
                    vector=(-sign)*weight.sum(axis=0)[:,None]*axis[None,:]
                    groups.append({'lag':ell,'axis':'world_'+('x' if b==0 else 'y'),
                                   'polarity':sign,'modality':modality,
                                   'mass':float(weight.sum()),'vector':vector,
                                   'basis_reason':'radial_undefined_at_center'})
    return groups


def verify_center_and_history():
    times=np.array([1.,2.,3.])
    positions=np.broadcast_to(np.array([[0.,-1.],[0.,0.],[0.,1.]]),(3,3,2)).copy()
    wind=np.array([[[1.,.2],[1.,.2],[1.,.2]],
                   [[-.3,1.],[-.3,1.],[-.3,1.]],
                   [[.6,-.5],[.6,-.5],[.6,-.5]]])
    odors=np.array([[0.,1.,0.],[.2,0.,1.],[0.,.4,0.]])
    weights=np.array([.2,.3,.5])
    groups=encode_history_v59(times,positions,wind,odors,now=3.,lag_edges=[0.,1.,3.],
                             support_qualified=True,sample_weights=weights)
    wind_readout=sum(g['vector'] for g in groups if g['modality']=='wind')
    odor_readout=sum(g['vector'] for g in groups if g['modality']=='odor_tagged')
    wind_expected=-np.sum(weights[:,None,None]*wind,axis=0)
    odor_expected=-np.sum(weights[:,None,None]*odors[...,None]*wind,axis=0)
    wind_error=float(np.max(np.abs(wind_readout-wind_expected)))
    odor_error=float(np.max(np.abs(odor_readout-odor_expected)))
    assert wind_error<1e-12 and odor_error<1e-12
    rejected=False
    try:
        encode_history_v59(times,positions,wind,odors,now=3.,lag_edges=[0.,3.],support_qualified=False)
    except ValueError:
        rejected=True
    assert rejected
    return {'status':'PASS','wind_reconstruction_max_error':wind_error,
            'odor_tagged_reconstruction_max_error':odor_error,
            'unqualified_history_rejected':rejected,
            'scope':'complete-direction encoding and history qualification; not native action benefit'}


if __name__=='__main__':
    p=Path(__file__).resolve().parent/'results';p.mkdir(exist_ok=True)
    result=verify_center_and_history()
    (p/'body_history_adapter.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
