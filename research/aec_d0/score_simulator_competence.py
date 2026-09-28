#!/usr/bin/env python3
"""Simulator-only leave-one-realization-out competence; reads no target gas."""
from __future__ import annotations
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EVID = ROOT / 'evidence/aec_d0'
sys.path.insert(0, str(ROOT/'research/ds_pmfs_identity_d1'))
from score_shadow import bank_for_env, project  # noqa: E402

EPS = 1e-9


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):
            h.update(block)
    return h.hexdigest()


def competence(pseudo: np.ndarray, mean_bank: np.ndarray, truth: int, label: str) -> dict:
    assert pseudo.shape[0] == 88 and mean_bank.shape[1] == pseudo.shape[1]
    assert len(mean_bank) in (596,630,624)
    assert np.isfinite(pseudo).all() and (pseudo >= 0).all()
    bank_self = mean_bank[truth]
    diff = np.mean(pseudo,axis=0)-bank_self
    relative = float(np.linalg.norm(diff)/max(np.linalg.norm(bank_self),1e-12))
    assert relative <= 1e-4, ('simulator mean mismatch', label, relative)
    rank = []
    for x in pseudo:
        templates = np.maximum(mean_bank, EPS).copy()
        templates[truth] = np.maximum((88*bank_self-x)/87, EPS)
        norm = np.square(templates).sum(axis=1)
        gain = np.maximum(0,(templates@x)/norm)
        sse = np.square(x[None,:]-gain[:,None]*templates).sum(axis=1)
        true = sse[truth]
        r = int(np.count_nonzero(sse < true)) + (int(np.count_nonzero(sse==true))+1)/2
        rank.append(r)
    a = np.asarray(rank,dtype=float)
    return dict(competence_top10=float(np.mean(a<=10)),mean_pseudo_rank=float(a.mean()),
                mean_reciprocal_rank=float(np.mean(1/a)),mean_parity_relative_l2=relative)


def main():
    routes = json.loads((EVID/'ROUTE_POSITIONS_ONLY.json').read_text())
    assert len(routes)==49
    prior=json.loads((ROOT/'evidence/ds_pmfs_identity_d1/ASSET_FREEZE.json').read_text())
    for env in range(3):
        for name in (f'env_{env}_bank.npz',f'env_{env}_occupancy.u8'):
            assert sha(EVID/'assets'/name)==prior['input_sha256'][name],name
    f1_freeze=json.loads((ROOT/'evidence/aod_house03_f1_full624_20260927/TEMPLATE_FREEZE.json').read_text())
    template_path=ROOT/'research/aod_house03_f1_full624_20260927/templates/candidate_path_templates.npz'
    assert sha(template_path)==f1_freeze['arrays_sha256'][template_path.name]
    sim_manifest=json.loads((EVID/'SIMULATOR_ONLY_FREEZE.json').read_text())
    pseudo_path=EVID/'PSEUDO_VECTORS.npz'
    assert sha(pseudo_path)==sim_manifest['pseudo_vectors_sha256']
    assert sim_manifest['target_concentrations_read'] is False
    a=np.load(pseudo_path,allow_pickle=False)
    banks={e:bank_for_env(e,EVID/'assets',Path('.')) for e in range(3)}
    rows=[]
    for ri,route in enumerate(routes):
        env=int(route['env']);meta,ids,maps,_=banks[env]
        idx=ids.index(route['source_id'])
        xy=np.asarray(route['xy'],dtype=float)
        for kind in ('u','rawu'):
            m=project(maps[kind],meta,xy)
            result=competence(a[f'route_{ri}_{kind}'],m,idx,f'route_{ri}_{kind}_{route["source_id"]}')
            rows.append(dict(house=route['house'],env=env,source_id=route['source_id'],
                             route_id=route['case_id'],operator=kind,candidate_count=len(ids),
                             route_stops=len(xy),**result))
    # F1 House03 frozen source-independent two paths.
    truth=pd.read_csv(ROOT/'research/aod_house03_f1_full624_20260927/protocol/frozen/HOUSE03_F1_TRUTH_PANEL_12.tsv',sep='\t')
    support=pd.read_csv(ROOT/'research/aod_house03_f1_full624_20260927/templates/CANDIDATE_SUPPORT.csv')
    templates=np.load(ROOT/'research/aod_house03_f1_full624_20260927/templates/candidate_path_templates.npz',allow_pickle=False)
    assert len(truth)==12 and len(support)==624
    ids=support.source_id.tolist()
    for si,s in truth.iterrows():
        idx=ids.index(s.source_id)
        for path in ('A','B'):
            for kind in ('u','rawu'):
                m=templates[f'nominal_{kind}_path_{path}']
                result=competence(a[f'h03_source_{si}_path_{path}_{kind}'],m,idx,
                                  f'h03_source_{si}_path_{path}_{kind}')
                rows.append(dict(house='House03',env=3,source_id=s.source_id,
                                 route_id=f'H03_{s.source_id}_{path}',operator=kind,
                                 candidate_count=624,route_stops=10,**result))
    assert len(rows)==(49+24)*2
    route_csv=EVID/'SIM_COMPETENCE_PER_ROUTE.csv'
    pd.DataFrame(rows).sort_values(['house','env','source_id','route_id','operator']).to_csv(
        route_csv,index=False,lineterminator='\n')
    route_df=pd.read_csv(route_csv)
    src=route_df.groupby(['house','source_id','operator'],sort=True)[
        ['competence_top10','mean_pseudo_rank','mean_reciprocal_rank']].mean().reset_index()
    src.to_csv(EVID/'SIM_COMPETENCE_PER_SOURCE.csv',index=False,lineterminator='\n')
    p=src.pivot(index=['house','source_id'],columns='operator',values='competence_top10').reset_index()
    p['delta_c_rawu_minus_u']=p.rawu-p.u
    p.to_csv(EVID/'SIM_DELTA_C_PER_SOURCE.csv',index=False,lineterminator='\n')
    out=dict(route_rows=len(rows),physical_source_rows=len(p),top_k=10,
             source_counts=p.groupby('house').size().to_dict(),
             pseudo_vector_sha256=sha(pseudo_path),
             target_gas_read=False,
             files_sha256={name:sha(EVID/name) for name in (
                 'SIM_COMPETENCE_PER_ROUTE.csv','SIM_COMPETENCE_PER_SOURCE.csv',
                 'SIM_DELTA_C_PER_SOURCE.csv')})
    (EVID/'SIM_COMPETENCE_FREEZE.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
