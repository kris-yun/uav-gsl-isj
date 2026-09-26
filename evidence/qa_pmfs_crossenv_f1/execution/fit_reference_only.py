#!/usr/bin/env python3
"""Reference-only predictive-loglik LOO; no target inputs are read."""
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/zyc/qa_pmfs_crossenv_f1_20260926')
sys.path.insert(0,str(ROOT/'protocol'))
from qa_pmfs_core import independent_loglik,marginal_preserving_probit_loglik
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n')
def main():
    audit=json.loads((ROOT/'audit/ASSET_AUDIT.json').read_text());assert audit['status']=='EXACT_EXISTING_CROSSENV_ASSETS_FOUND'
    out=ROOT/'reference_freeze';out.mkdir(exist_ok=False)
    path=ROOT/'historical/JTD_E2_REFERENCE_12x10x30.npy'
    assert sha(path)==audit['historical_file_hashes'][path.name]
    B=(np.load(path,allow_pickle=False)>0).astype(np.int8);E,S,K,T,Q=B.shape
    assert (E,S,K,T,Q)==(3,6,12,10,30)
    probs=(B.sum(axis=2,dtype=np.int64)+0.5)/(K+1)
    np.save(out/'MARGINAL_PROBABILITIES.npy',probs,allow_pickle=False)
    grid=[(L,r/10) for L in (1,2,5,T) for r in range(1,9)]
    results=[];selected=[]
    for ei in range(E):
        totals=B[ei].sum(axis=1,dtype=np.int64)
        likelihood={}
        for L,rho in grid:
            groups=np.repeat(np.arange(T)//L,Q);score=0.0
            for si in range(S):
                for ri in range(K):
                    # One realization held out only from its own source.
                    p=(totals[si]-B[ei,si,ri]+0.5)/K
                    score+=marginal_preserving_probit_loglik(B[ei,si,ri],p,rho,groups=groups,gh_n=40)
            likelihood[(L,rho)]=score
            results.append({'environment_index':ei,'L':L,'rho':rho,'loo_predictive_loglik':score})
        choose=lambda choices:min(choices,key=lambda x:(-likelihood[x],x[0],x[1]))
        m1=choose([x for x in grid if x[0]==1]);m2=choose([x for x in grid if x[0] in (2,5,T)])
        selected.append({'environment_index':ei,'M0':{'L':0,'rho':0.0},'M1':{'L':m1[0],'rho':m1[1]},'M2':{'L':m2[0],'rho':m2[1]},'M3':{'L':T,'rho':0.6}})
        print('REFERENCE_ENVIRONMENT_FROZEN',ei,'M1',m1,'M2',m2,flush=True)
    with (out/'REFERENCE_ONLY_LOO_SELECTION.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]),lineterminator='\n');w.writeheader();w.writerows(results)
    record={'models':selected,'reference_only':True,'target_files_opened':False,'reference_tensor_sha256':sha(path),'marginal_probabilities_sha256':sha(out/'MARGINAL_PROBABILITIES.npy'),'reference_budget':12,'threshold':'pooled concentration > 0','prior':'uniform over six frozen sources within each environment','smoothing':'Jeffreys (hits+0.5)/(K+1); LOO uses K-1 references','selection':'maximize sum of true-source held-reference predictive log likelihood','selection_ties':'smaller L then smaller rho','M1_rho_grid':[r/10 for r in range(1,9)],'M2_L_grid':[2,5,T],'M2_rho_grid':[r/10 for r in range(1,9)],'GH_nodes':40,'source_support':audit['source_support'],'groups':'time_index // L repeated for all 30 probes; C-order T,Q flattening','code_sha256':{str(p.relative_to(ROOT)):sha(p) for folder in ['protocol','execution'] for p in sorted((ROOT/folder).iterdir()) if p.is_file()}}
    dump(out/'PRE_TARGET_MODEL_LOCK.json',record)
    (out/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()))
if __name__=='__main__':main()
