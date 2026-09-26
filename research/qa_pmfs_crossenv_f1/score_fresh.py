#!/usr/bin/env python3
"""QA-PMFS F1: score only after frozen reference models and G7 amendment."""
import argparse,csv,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
ROOT=Path('/home/zyc/qa_pmfs_crossenv_f1_20260926')
sys.path.insert(0,str(ROOT/'protocol'))
from qa_pmfs_core import independent_loglik,marginal_preserving_probit_loglik
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def csvout(p,records):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
def aggregate(records):
    per=[]
    for key in sorted({(r['environment_index'],r['source_index']) for r in records}):
        rr=[r for r in records if (r['environment_index'],r['source_index'])==key]
        per.append({k:float(np.mean([r[k] for r in rr])) for k in ('rank','top1','top3','reciprocal_rank','posterior_nll','map_spatial_error_m','map_tie')})
    return {'source_units':len(per),'target_count':len(records),'mean_rank':float(np.mean([r['rank'] for r in per])),'top1':float(np.mean([r['top1'] for r in per])),'top3':float(np.mean([r['top3'] for r in per])),'MRR':float(np.mean([r['reciprocal_rank'] for r in per])),'posterior_NLL':float(np.mean([r['posterior_nll'] for r in per])),'MAP_spatial_error_m':float(np.mean([r['map_spatial_error_m'] for r in per])),'MAP_tie_fraction':float(np.mean([r['map_tie'] for r in per]))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
    assert (ROOT/'pre_target_freeze_commit.txt').is_file()
    lock=json.loads((ROOT/'PRE_TARGET_FREEZE.json').read_text())
    for name,expected in lock['frozen_hashes'].items():assert sha(ROOT/name)==expected,name
    model=json.loads((ROOT/'reference_freeze/PRE_TARGET_MODEL_LOCK.json').read_text())
    audit=json.loads((ROOT/'audit/ASSET_AUDIT.json').read_text())
    path=ROOT/'historical/JTD_E2_FRESH_TARGET_10x30.npy'
    assert sha(path)==audit['historical_file_hashes'][path.name]
    # First opening of fresh target concentration values occurs here.
    C=np.load(path,allow_pickle=False);assert C.shape==(3,6,4,10,30) and C.dtype==np.float32
    assert np.isfinite(C).all() and (C>=0).all()
    B=(C>0).astype(np.int8);P=np.load(ROOT/'reference_freeze/MARGINAL_PROBABILITIES.npy',allow_pickle=False)
    assert P.shape==(3,6,10,30)
    out=ROOT/a.out;out.mkdir(exist_ok=False)
    candidate=[];target=[];source=[];env=[]
    support=model['source_support']
    for ei in range(3):
        sg=sorted([s for s in support if s['environment_index']==ei],key=lambda s:s['source_index'])
        xy=np.asarray([s['xy'] for s in sg]); params=model['models'][ei]
        for mn in ('M0','M1','M2','M3'):
            rho=params[mn]['rho'];L=params[mn]['L'];groups=np.repeat(np.arange(10)//max(1,L),30)
            for si in range(6):
                for ti in range(4):
                    h=B[ei,si,ti]
                    ll=np.asarray([independent_loglik(h,p) if mn=='M0' else marginal_preserving_probit_loglik(h,p,rho,groups=groups,gh_n=40) for p in P[ei]])
                    logpost=ll-logsumexp(ll) # equal prior cancels; no posterior clipping
                    assert np.isfinite(logpost).all()
                    mapidx=int(np.argmax(ll));rank=1+int(np.sum(ll>ll[si]))
                    base={'environment_index':ei,'house':sg[0]['house'],'wind':sg[0]['wind'],'source_index':si,'true_source_id':sg[si]['source_id'],'target_index':ti,'model':mn}
                    target.append({**base,'rank':rank,'top1':int(mapidx==si),'top3':int(rank<=3),'reciprocal_rank':1/rank,'posterior_nll':float(-logpost[si]),'true_source_log_posterior':float(logpost[si]),'map_source_id':sg[mapidx]['source_id'],'map_spatial_error_m':float(np.linalg.norm(xy[mapidx]-xy[si])),'map_tie':int(np.sum(ll==ll.max())>1)})
                    for ci in range(6):candidate.append({**base,'candidate_index':ci,'candidate_source_id':sg[ci]['source_id'],'log_likelihood':float(ll[ci]),'log_posterior':float(logpost[ci]),'posterior':float(np.exp(logpost[ci]))})
            for si in range(6):
                rr=[r for r in target if r['environment_index']==ei and r['source_index']==si and r['model']==mn]
                source.append({'environment_index':ei,'house':sg[0]['house'],'wind':sg[0]['wind'],'source_index':si,'source_id':sg[si]['source_id'],'model':mn,**aggregate(rr)})
        for mn in ('M0','M1','M2','M3'):
            rr=[r for r in target if r['environment_index']==ei and r['model']==mn]
            baseline=[r for r in source if r['environment_index']==ei and r['model']=='M0']
            current=[r for r in source if r['environment_index']==ei and r['model']==mn]
            improved=sum(r['mean_rank']<b['mean_rank'] for r,b in zip(current,baseline));harmed=sum(r['mean_rank']>b['mean_rank'] for r,b in zip(current,baseline))
            env.append({'environment_index':ei,'house':sg[0]['house'],'wind':sg[0]['wind'],'model':mn,**aggregate(rr),'improved_sources_vs_M0':improved,'harmed_sources_vs_M0':harmed,'neutral_sources_vs_M0':6-improved-harmed,'selected_L':params[mn]['L'],'selected_rho':params[mn]['rho']})
        print('QA_F1_ENVIRONMENT_SCORED',ei,flush=True)
    pooled={m:aggregate([r for r in target if r['model']==m]) for m in ('M0','M1','M2','M3')}
    em=lambda ei,m:next(r for r in env if r['environment_index']==ei and r['model']==m)
    delta=[em(e,'M3')['posterior_NLL']-em(e,'M0')['posterior_NLL'] for e in range(3)]
    gates={'G1_M3_rank_nonadverse_all':all(em(e,'M3')['mean_rank']<=em(e,'M0')['mean_rank'] for e in range(3)),
           'G2_M3_rank_improves_at_least_two':sum(em(e,'M3')['mean_rank']<em(e,'M0')['mean_rank'] for e in range(3))>=2,
           'G3_M3_top1_loss_at_most_one_target_each':all(sum(r['top1'] for r in target if r['environment_index']==e and r['model']=='M0')-sum(r['top1'] for r in target if r['environment_index']==e and r['model']=='M3')<=1 for e in range(3)),
           'G4_M2_persistent_at_least_two':sum(m['M2']['L']>1 for m in model['models'])>=2,
           'G5_M2_rank_no_worse_than_M1_at_least_two':sum(em(e,'M2')['mean_rank']<=em(e,'M1')['mean_rank'] for e in range(3))>=2,
           'G6_M3_pooled_NLL_lower':pooled['M3']['posterior_NLL']<pooled['M0']['posterior_NLL'],
           'G7_all_M3_NLL_deltas_lte_ln10':all(d<=2.302585092994046 for d in delta)}
    neutral=all(em(e,'M3')['mean_rank']==em(e,'M0')['mean_rank'] for e in range(3))
    if not gates['G7_all_M3_NLL_deltas_lte_ln10']:decision='QA_F1_NOT_CROSS_ENV_GENERAL'
    elif all(gates.values()):decision='QA_F1_CROSS_ENV_CONFIRMED'
    elif neutral and gates['G3_M3_top1_loss_at_most_one_target_each'] and gates['G6_M3_pooled_NLL_lower']:decision='QA_F1_CALIBRATION_ONLY'
    else:decision='QA_F1_NOT_CROSS_ENV_GENERAL'
    comparisons=[]
    for ei in range(3):
        m1=[r for r in source if r['environment_index']==ei and r['model']=='M1'];m2=[r for r in source if r['environment_index']==ei and r['model']=='M2']
        comparisons.append({'environment_index':ei,'improved_sources_M2_vs_M1':sum(b['mean_rank']<a['mean_rank'] for a,b in zip(m1,m2)),'harmed_sources_M2_vs_M1':sum(b['mean_rank']>a['mean_rank'] for a,b in zip(m1,m2))})
    result={'decision':decision,'gates':gates,'G7_M3_minus_M0_environment_NLL_deltas':delta,'G7_threshold':2.302585092994046,'G7_amendment_sha256':sha(ROOT/'execution/G7_PRE_TARGET_AMENDMENT.md'),'environment_metrics':env,'pooled_metrics':pooled,'M2_vs_M1_source_comparisons':comparisons,'asset_audit_commit':(ROOT/'asset_audit_commit.txt').read_text().strip(),'pre_target_freeze_commit':(ROOT/'pre_target_freeze_commit.txt').read_text().strip(),'new_plume_runs':0,'posterior_NLL_clipped':False}
    csvout(out/'CANDIDATE_SCORES.csv',candidate);csvout(out/'TARGET_METRICS.csv',target);csvout(out/'SOURCE_METRICS.csv',source);csvout(out/'ENVIRONMENT_METRICS.csv',env);dump(out/'F1_RESULT.json',result)
    print(json.dumps({'decision':decision,'gates':gates,'pooled_metrics':pooled},indent=2,sort_keys=True))
if __name__=='__main__':main()
