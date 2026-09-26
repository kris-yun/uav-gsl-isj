#!/usr/bin/env python3
import csv,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
R=Path('/home/zyc/marked_encounter_pmfs_d0_20260927');P=R/'protocol'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=lambda p,v:p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert (R/'candidate_freeze_commit.txt').exists()
freeze=json.loads((R/'CANDIDATE_FREEZE.json').read_text())
for path,h in freeze['files'].items():assert sha(R/path)==h,path
repeat='--repeat' in sys.argv
out=R/('evaluation_repeat' if repeat else 'evaluation');assert not out.exists()
cmd=[sys.executable,str(P/'evaluate_marked_forward.py'),'--bank',str(R/'forward/candidate_mark_bank.csv'),'--targets',str(P/'JTD_E2_FRESH_TARGET_10x30.npy'),'--target-manifest',str(P/'JTD_E2_FRESH_TARGET_MANIFEST.tsv'),'--panel',str(P/'E1_HOUSE_SOURCE_PANELS.tsv'),'--out',str(out/'supplied')]
subprocess.run(cmd,check=True)
spec=importlib.util.spec_from_file_location('supplied',P/'evaluate_marked_forward.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
bank=pd.read_csv(R/'forward/candidate_mark_bank.csv')
targets=np.load(P/'JTD_E2_FRESH_TARGET_10x30.npy',allow_pickle=False)
refs=np.load(P/'JTD_E2_REFERENCE_12x10x30.npy',allow_pickle=False)
assert targets.shape==(3,6,4,10,30) and refs.shape==(3,6,12,10,30)
assert np.isfinite(targets).all() and (targets>=0).all() and np.isfinite(refs).all() and (refs>=0).all()
panel=pd.read_csv(P/'E1_HOUSE_SOURCE_PANELS.tsv',sep='\t')
details=[];scores=[];summaries=[];conditions=[]
for e in range(3):
    b=bank[bank.environment_index==e];sr=b[['source_index','source_id','house','wind']].drop_duplicates().sort_values('source_index')
    house=str(sr.iloc[0].house);wind=str(sr.iloc[0].wind)
    p=[];u=[];mu=[]
    for k in range(6):
        g=b[b.source_index==k].sort_values('probe_rank');assert len(g)==30
        p.append(np.clip(g.presence_prob.to_numpy(),1e-6,1-1e-6));u.append(np.clip(g.multiplicity_mean_unconditional.to_numpy(),f.EPS,None));mu.append(np.clip(g.multiplicity_mean_conditional.to_numpy(),f.EPS,None))
    # Full positive-event conditional reference mean; no targets used.
    hit=refs[e]>0;counts=hit.sum(axis=1);total=refs[e].sum(axis=1)
    upper=np.divide(total,counts,out=np.zeros_like(total,dtype=float),where=counts>0)
    np.save(out/f'U_conditional_mark_env_{e}.npy',upper,allow_pickle=False)
    for s in range(6):
        sid=str(sr[sr.source_index==s].iloc[0].source_id);partner=f.source_partner(panel,house,sid);kpair=int(sr[sr.source_id==partner].iloc[0].source_index)
        for j in range(4):
            y=targets[e,s,j];h=(y>0).astype(int)
            occ=np.array([(h*np.log(p[k][None,:])+(1-h)*np.log1p(-p[k][None,:])).sum() for k in range(6)])
            marks=np.array([f.profiled_mark_ll(y,np.tile(mu[k],(10,1))) for k in range(6)])
            umarks=np.array([f.profiled_mark_ll(y,upper[k]) for k in range(6)])
            mse=[];rd=[];scales=[]
            for k in range(6):
                estimate=np.tile(u[k],(10,1));scale=max(0.0,float(np.sum(y*estimate)/np.sum(estimate**2)));scales.append(scale)
                mse.append(float(np.sum((y-scale*estimate)**2)));rd.append(float(np.sum((f.edf(y)-f.edf(estimate))**2)))
            values={'B0':occ,'M':occ+marks,'ICRA_rank':-np.array(rd),'B2':-np.array(mse),'U':occ+umarks}
            ranks={key:f.rank_of(v,s,True) for key,v in values.items()}
            details.append(dict(environment_index=e,house=house,wind=wind,source_index=s,source_id=sid,target_index=j,paired_neighbor=partner,**{'rank_'+key:v for key,v in ranks.items()},delta_pair_mark=float(marks[s]-marks[kpair]),delta_pair_U=float(umarks[s]-umarks[kpair])))
            for k in range(6):
                scores.append(dict(environment_index=e,source_index=s,target_index=j,candidate_index=k,candidate_id=str(sr[sr.source_index==k].iloc[0].source_id),occurrence_ll=occ[k],conditional_mark_ll=marks[k],upper_mark_ll=umarks[k],marked_ll=values['M'][k],upper_ll=values['U'][k],edf_squared_discrepancy=rd[k],scaled_value_SSE=mse[k],B2_positive_scale=scales[k]))
    d=pd.DataFrame([r for r in details if r['environment_index']==e])
    source_mean=d.groupby('source_index').mean(numeric_only=True)
    summary=dict(environment_index=e,house=house,wind=wind,mean_delta_pair_mark=float(source_mean.delta_pair_mark.mean()),mean_delta_pair_U=float(source_mean.delta_pair_U.mean()))
    for model in ('B0','M','ICRA_rank','B2','U'):
        r=d['rank_'+model];summary.update({model+'_mean_rank':float(source_mean['rank_'+model].mean()),model+'_top1':float((r==1).mean()),model+'_rescued_top1':int(((d.rank_B0>1)&(r==1)).sum()),model+'_harmed_top1':int(((d.rank_B0==1)&(r>1)).sum())})
    summaries.append(summary)
d=pd.DataFrame(details);summ=pd.DataFrame(summaries)
supplied=json.loads((out/'supplied/RESULT.json').read_text());original=pd.read_csv(out/'supplied/TARGET_DETAIL.csv')
assert np.array_equal(d.rank_B0,original.rank_B0) and np.array_equal(d.rank_M,original.rank_M) and np.array_equal(d.rank_ICRA_rank,original.rank_ICRA_rank)
assert np.allclose(d.delta_pair_mark,original.delta_pair_mark,rtol=1e-14,atol=1e-12)
ug=[bool((summ.mean_delta_pair_U>0).all()),bool((summ.U_mean_rank<=summ.B0_mean_rank).all()),bool((summ.U_mean_rank<summ.B0_mean_rank).sum()>=2),bool((summ.U_top1>=summ.B0_top1).all())]
mg=supplied['gates']
decision=('ME_PMFS_D0_MARK_FORWARD_SIGNAL' if all(mg) else ('ME_PMFS_D0_MARK_INFORMATION_FORWARD_INADEQUATE' if all(ug) else 'ME_PMFS_D0_NULL_OR_ADVERSE'))
d.to_csv(out/'TARGET_DETAIL_ALL.csv',index=False,float_format='%.17g');pd.DataFrame(scores).to_csv(out/'CANDIDATE_SCORES_ALL.csv',index=False,float_format='%.17g');summ.to_csv(out/'ENVIRONMENT_SUMMARY_ALL.csv',index=False,float_format='%.17g')
result=dict(decision=decision,M_gates=mg,U_gates=ug,environment_summary=summaries,candidate_bank_freeze_commit=(R/'candidate_freeze_commit.txt').read_text().strip(),native_parity_max_error=0.0,forward_count=1584,forward_repeat_separate_count=1584,upper_reference_budget=12,reference_U_is_deployable=False,upper_occurrence_term='same frozen PMFS B0',amendment_sha256=sha(R/'execution/U_PRE_TARGET_AMENDMENT.md'),targets_are_previously_open_development=True)
dump(out/'D0_RESULT.json',result)
if repeat:
    first=R/'evaluation';files=[]
    for p in sorted(first.rglob('*')):
        if p.is_file():
            rel=p.relative_to(first);assert sha(p)==sha(out/rel),str(rel);files.append({'file':str(rel),'sha256':sha(p)})
    dump(R/'EVALUATION_REPEAT.json',{'pass':True,'files_byte_identical':files})
print('FINAL_MARKED_DECISION',decision,flush=True)
