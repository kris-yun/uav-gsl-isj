#!/usr/bin/env python3
"""Freeze templates using geometry and candidate products, before any target run."""
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

R=Path('/home/zyc/aod_house03_f1_full624_20260927')
sys.path.insert(0,str(R/'amplitude_implementation'))
from amplitude_readout import frozen_operators

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    audit=json.loads((R/'CANDIDATE_BANK_AUDIT.json').read_text())
    assert audit['passed'] and audit['completed']==54912 and audit['source_count']==624
    I=R/'inputs';P=R/'protocol';T=R/'templates';T.mkdir(exist_ok=False)
    meta=json.loads((I/'meta.json').read_text());n=meta['width']*meta['height']
    pc=pd.read_csv(R/'f0/HOUSE03_FROZEN_30_PROBES.tsv',sep='\t').sort_values('probe_rank')
    idx=(np.floor((pc.center_x_m.to_numpy()-meta['origin_x'])/meta['resolution']).astype(int)+
         meta['width']*np.floor((pc.center_y_m.to_numpy()-meta['origin_y'])/meta['resolution']).astype(int))
    pi=pd.DataFrame(dict(probe_rank=pc.probe_rank.to_numpy(),cell_index=idx))
    ops,geometry=frozen_operators(meta,pc,pi)
    np.save(T/'footprint_W.npy',ops['footprint'].weights,allow_pickle=False)
    np.save(T/'nearest_W.npy',ops['nearest'].weights,allow_pickle=False)
    (T/'OBSERVATION_OPERATOR.json').write_text(json.dumps(geometry,indent=2)+'\n')
    sources=pd.read_csv(I/'sources.csv');paths={p:pd.read_csv(P/f'frozen/HOUSE03_PATH_{p}_10.tsv',sep='\t') for p in ['A','B']}
    arrays={}
    for kind in ['p','rawp','u','rawu']:
        nominal=[];state0=[]
        for s in range(624):
            state_means=[]
            for k in range(11):
                maps=[]
                for rep in range(8):
                    pre=R/f'candidate_forward/source_{s}/state_{k}_replica_{rep}'
                    f=Path(str(pre)+f'.{kind}.f32')
                    rec=json.loads(Path(str(pre)+'.done.json').read_text())
                    assert sha(f)==rec['hashes'][kind]
                    m=np.fromfile(f,'<f4').astype(np.float64)
                    assert m.shape==(n,) and np.isfinite(m).all() and (m>=0).all()
                    maps.append(m)
                state_means.append(np.mean(maps,axis=0))
            nominal.append(np.mean(state_means,axis=0));state0.append(state_means[0])
        for condition,full in [('nominal',np.array(nominal)),('state0_stress',np.array(state0))]:
            np.save(T/f'{condition}_{kind}_full_maps.npy',full,allow_pickle=False)
            footprint=ops['footprint'].project(full)
            np.save(T/f'{condition}_{kind}_all30_footprint.npy',footprint,allow_pickle=False)
            for path,table in paths.items():
                ranks=table.probe_rank.to_numpy(int)-1
                value=footprint[:,ranks]
                assert value.shape==(624,10)
                arrays[f'{condition}_{kind}_path_{path}']=value
        print('TEMPLATE_KIND_COMPLETE',kind,flush=True)
    np.savez(T/'candidate_path_templates.npz',**arrays)
    sources.to_csv(T/'CANDIDATE_SUPPORT.csv',index=False)
    hashes={f.name:sha(f) for f in sorted(T.iterdir()) if f.is_file()}
    (R/'TEMPLATE_FREEZE.json').write_text(json.dumps(dict(passed=True,candidates=624,states=11,replicas_per_state=8,
        nominal_averaging='mean of 8 replicas per state, then equal mean of 11 state means; float64',
        stress_averaging='same 8 state0 replicas only; reduced state coverage and Monte Carlo depth',
        score='archived B2; EPS 1e-9; strict unique minimum; no posterior',
        arrays_sha256=hashes,fresh_target_runs=0,fresh_target_values_read=False),indent=2)+'\n')
    print('FULL624_TEMPLATES_FROZEN_NO_TARGETS',flush=True)

if __name__=='__main__':main()
