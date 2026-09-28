#!/usr/bin/env python3
"""Join frozen simulator competence to already-open source-level ABS outcomes."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parents[2]
EVID=ROOT/'evidence/aec_d0'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n')


def load_r075():
    path=ROOT/'evidence/r075_relative_action/R075_RESULT.json'
    original=json.loads(path.read_text())
    rows=[]
    for record in original['final_results']:
        if record['house'] not in ('House01','House02'):continue
        u=record['u']['ABS']; raw=record['rawu']['ABS']
        rows.append(dict(house=record['house'],source_id=record['source_id'],
                         episode_id=record['case_id'],env_wind=record['wind'],
                         rank_u=float(u['truth_rank']),rank_rawu=float(raw['truth_rank']),
                         top1_u=int(u['unique_top1']),top1_rawu=int(raw['unique_top1'])))
    assert len(rows)==49
    return pd.DataFrame(rows),path


def load_h03():
    path=ROOT/'evidence/r1_centered_aod/TARGET_METRICS.csv'
    d=pd.read_csv(path)
    d=d[(d.condition=='nominal')&(d.readout=='ABS')]
    assert len(d)==384
    p=d.pivot(index=['truth_source','realization','path'],columns='operator',
              values=['true_rank','unique_top1'])
    p.columns=[f'{metric}_{operator}' for metric,operator in p.columns]
    p=p.reset_index()
    assert len(p)==192
    out=[]
    for _,r in p.iterrows():
        out.append(dict(house='House03',source_id=r.truth_source,
                        episode_id=f'{r.truth_source}_rep{int(r.realization)}_path{r.path}',
                        env_wind='1-2,5_fast',rank_u=float(r.true_rank_u),
                        rank_rawu=float(r.true_rank_rawu),
                        top1_u=int(r.unique_top1_u),top1_rawu=int(r.unique_top1_rawu)))
    return pd.DataFrame(out),path


def main():
    freeze_path=EVID/'SIM_COMPETENCE_FREEZE.json'
    freeze=json.loads(freeze_path.read_text())
    assert freeze['target_gas_read'] is False
    for name,digest in freeze['files_sha256'].items():assert sha(EVID/name)==digest
    a=pd.read_csv(EVID/'SIM_DELTA_C_PER_SOURCE.csv')
    r075,r075_path=load_r075();h03,h03_path=load_h03()
    actual=pd.concat([r075,h03],ignore_index=True)
    actual['delta_g_rank_u_minus_rawu']=actual.rank_u-actual.rank_rawu
    actual['delta_top1_rawu_minus_u']=actual.top1_rawu-actual.top1_u
    source=actual.groupby(['house','source_id'],sort=True).agg(
        target_paths=('episode_id','count'),
        mean_rank_u=('rank_u','mean'),mean_rank_rawu=('rank_rawu','mean'),
        mean_top1_u=('top1_u','mean'),mean_top1_rawu=('top1_rawu','mean'),
        delta_g=('delta_g_rank_u_minus_rawu','mean'),
        delta_top1=('delta_top1_rawu_minus_u','mean'),
        top1_rescue=('delta_top1_rawu_minus_u',lambda x:int((x>0).sum())),
        top1_harm=('delta_top1_rawu_minus_u',lambda x:int((x<0).sum()))).reset_index()
    joined=a.merge(source,on=['house','source_id'],validate='one_to_one')
    assert len(joined)==len(a)==21
    joined['sign_agree']=np.where((joined.delta_c_rawu_minus_u!=0)&(joined.delta_g!=0),
                                  np.sign(joined.delta_c_rawu_minus_u)==np.sign(joined.delta_g),
                                  np.nan)
    joined['selected_operator']=np.where(joined.delta_c_rawu_minus_u>0,'rawu',
                                         np.where(joined.delta_c_rawu_minus_u<0,'u','abstain_u'))
    joined['selected_rank']=np.where(joined.delta_c_rawu_minus_u>0,
                                     joined.mean_rank_rawu,joined.mean_rank_u)
    joined.to_csv(EVID/'AEC_D0_SOURCE_RESULTS.csv',index=False,lineterminator='\n')
    houses={}
    for house,g in joined.groupby('house',sort=True):
        x=g.delta_c_rawu_minus_u.to_numpy();y=g.delta_g.to_numpy()
        corr=float(spearmanr(x,y).statistic) if np.unique(x).size>1 and np.unique(y).size>1 else None
        valid=g.sign_agree.dropna()
        signs=sorted(set(np.sign(x).astype(int)))
        mean_u=float(g.mean_rank_u.mean());mean_raw=float(g.mean_rank_rawu.mean())
        mean_selected=float(g.selected_rank.mean())
        houses[house]=dict(source_count=len(g),spearman_delta_c_vs_delta_g=corr,
            nonzero_sign_count=len(valid),sign_agreement=float(valid.mean()) if len(valid) else None,
            delta_c_signs=signs,always_u_mean_rank=mean_u,always_rawu_mean_rank=mean_raw,
            competence_selector_mean_rank=mean_selected,
            selector_better_than_both=bool(mean_selected<min(mean_u,mean_raw)),
            source_top1_rescue=int(g.top1_rescue.sum()),source_top1_harm=int(g.top1_harm.sum()),
            positive_delta_c_sources=int((x>0).sum()),negative_delta_c_sources=int((x<0).sum()),
            abstained_sources=int((x==0).sum()))
    signal=all(v['spearman_delta_c_vs_delta_g'] is not None and
               v['spearman_delta_c_vs_delta_g']>0 and
               v['sign_agreement'] is not None and v['sign_agreement']>0.5 and
               v['positive_delta_c_sources']>0 and v['negative_delta_c_sources']>0 and
               v['selector_better_than_both'] for v in houses.values())
    decision='AEC_D0_OPEN_PREDICTIVE_SIGNAL' if signal else 'AEC_D0_NO_CROSS_HOUSE_PREDICTIVE_SIGNAL'
    out=dict(decision=decision,houses=houses,physical_sources=len(joined),
             source_unit=True,top_k=10,
             no_fresh_confirmation=True,
             selector_is_oracle_diagnostic_not_online_router=True,
             frozen_competence_sha256=sha(freeze_path),
             outcome_asset_sha256={str(r075_path.relative_to(ROOT)):sha(r075_path),
                                   str(h03_path.relative_to(ROOT)):sha(h03_path)},
             joined_source_results_sha256=sha(EVID/'AEC_D0_SOURCE_RESULTS.csv'))
    write(EVID/'AEC_D0_RESULT.json',out)
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
