#!/usr/bin/env python3
"""Frozen TCMA-D0 adequacy calculation; does not read source-rank outcomes."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
AEC=ROOT/'evidence/aec_d0'
OUT=ROOT/'evidence/tcma_d0'
EPS=1e-9


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def b2(observed,template):
    m=np.maximum(np.asarray(template,dtype=np.float64),EPS)
    y=np.asarray(observed,dtype=np.float64)
    assert m.shape==y.shape and np.isfinite(m).all() and np.isfinite(y).all()
    g=max(0.,float(np.dot(y,m)/np.dot(m,m)))
    return float(np.square(y-g*m).sum())


def adequacy(sim,target):
    sim=np.asarray(sim,dtype=np.float64)
    assert sim.ndim==2 and sim.shape[0]==88 and np.isfinite(sim).all() and (sim>=0).all()
    mean=sim.mean(axis=0)
    self_res=np.empty(88,dtype=np.float64)
    for k in range(88):
        loo=(88*mean-sim[k])/87
        self_res[k]=b2(sim[k],loo)
    t=b2(target,mean)
    count=int(np.count_nonzero(self_res>=t))
    a=(1+count)/89
    return dict(target_sse=t,adequacy=a,self_residual_ge_target=count,
                self_residual_mean=float(self_res.mean()),
                self_residual_median=float(np.median(self_res))),self_res


def native_targets():
    manifest_path=ROOT/'evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json'
    events_path=ROOT/'evidence/ds_pmfs_identity_d1/COMPACT_EVENTS.json'
    routes_path=AEC/'ROUTE_POSITIONS_ONLY.json'
    assert sha(manifest_path)=='c4b87c1a11571ba792bd79f1b82c9205ea17f3f32fb7e161aab42441adbd2328'
    assert sha(events_path)=='47b8fffb2764737ff0eb3b3f6a93bc495cfdf00c53e99bf8fa6a105128372051'
    routes=json.loads(routes_path.read_text())
    events={e['case_id']:e for e in json.loads(events_path.read_text())}
    assert len(routes)==49
    result=[]
    for ri,route in enumerate(routes):
        item=events[route['case_id']]
        prefix=route['event_prefix']
        assert prefix==item['prefixes'][-1] and prefix%5==0
        y=[]
        for start in range(0,prefix,5):
            block=item['events'][start:start+5]
            xy=[float(block[0]['x']),float(block[0]['y'])]
            assert all([float(b['x']),float(b['y'])]==xy for b in block)
            assert xy==route['xy'][start//5]
            y.append(float(np.mean([float(b['concentration']) for b in block])))
        result.append((ri,route,np.asarray(y,dtype=np.float64)))
    return result, [manifest_path,events_path,routes_path]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sim_freeze_path=AEC/'SIM_COMPETENCE_FREEZE.json'
    sim_freeze=json.loads(sim_freeze_path.read_text())
    pseudo_path=AEC/'PSEUDO_VECTORS.npz'
    assert sha(pseudo_path)==sim_freeze['pseudo_vector_sha256']
    assert sim_freeze['target_gas_read'] is False
    pseudo=np.load(pseudo_path,allow_pickle=False)
    native,assets=native_targets()
    h03_target=ROOT/'evidence/r1_centered_aod/assets/TARGET_PATHS_12x8x2x10.npy'
    h03_freeze=json.loads((ROOT/'evidence/aod_house03_f1_full624_20260927/amended/TARGET_DATA_FREEZE.json').read_text())
    assert sha(h03_target)==h03_freeze['all_artifact_sha256'][h03_target.name]
    y03=np.load(h03_target,allow_pickle=False)
    assert y03.shape==(12,8,2,10)
    panel=ROOT/'research/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv'
    truth=pd.read_csv(panel,sep='\t')
    assert len(truth)==12
    rows=[];residuals={}
    for ri,route,y in native:
        for kind in ('u','rawu'):
            key=f'route_{ri}_{kind}'
            r,rr=adequacy(pseudo[key],y)
            residuals[key]=rr
            rows.append(dict(house=route['house'],source_id=route['source_id'],
                target_id=route['case_id'],env=int(route['env']),path='Native',
                operator=kind,stop_count=len(y),**r))
    for si,source in truth.iterrows():
        for rep in range(8):
            for pi,path in enumerate(('A','B')):
                y=y03[si,rep,pi]
                for kind in ('u','rawu'):
                    key=f'h03_source_{si}_path_{path}_{kind}'
                    if key not in residuals:
                        # R depends on source/path/operator, not target replica.
                        _,rr=adequacy(pseudo[key],y)
                        residuals[key]=rr
                    rr=residuals[key]
                    mean=pseudo[key].mean(axis=0)
                    t=b2(y,mean)
                    count=int(np.count_nonzero(rr>=t))
                    rows.append(dict(house='House03',source_id=source.source_id,
                        target_id=f'{source.source_id}_rep{rep}_path{path}',env=3,path=path,
                        operator=kind,stop_count=10,target_sse=t,
                        adequacy=(1+count)/89,self_residual_ge_target=count,
                        self_residual_mean=float(rr.mean()),
                        self_residual_median=float(np.median(rr))))
    assert len(rows)==(49+192)*2
    target_csv=OUT/'TARGET_ADEQUACY.csv'
    d=pd.DataFrame(rows).sort_values(['house','source_id','target_id','operator'])
    d.to_csv(target_csv,index=False,lineterminator='\n')
    source=d.groupby(['house','source_id','operator'],sort=True).agg(
        target_count=('target_id','count'),mean_adequacy=('adequacy','mean'),
        median_adequacy=('adequacy','median'),mean_target_sse=('target_sse','mean')).reset_index()
    assert len(source)==42
    source.to_csv(OUT/'SOURCE_ADEQUACY.csv',index=False,lineterminator='\n')
    np.savez_compressed(OUT/'SIM_SELF_RESIDUALS.npz',**residuals)
    manifest=dict(pseudo_vector_sha256=sha(pseudo_path),
        target_inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in assets+[h03_target,panel]},
        output_sha256={n:sha(OUT/n) for n in
          ('TARGET_ADEQUACY.csv','SOURCE_ADEQUACY.csv','SIM_SELF_RESIDUALS.npz')},
        target_rows=len(d),source_operator_rows=len(source),k=88,eps=EPS,
        rank_outcomes_read=False,
        target_truth_used_for_candidate_selection_only=True,
        no_new_simulation=True)
    (OUT/'ADEQUACY_FREEZE.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(target_rows=len(d),source_operator_rows=len(source),
                          adequacy_sha256=manifest['output_sha256']['TARGET_ADEQUACY.csv']),indent=2))


if __name__=='__main__':main()
