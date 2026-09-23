import os, glob, json
import numpy as np, pandas as pd

BASE = os.environ.get("R2_NATIVE_ROOT", "/path/to/tnqc_r2/native")
TRUTHS = {"House01": (-0.4,-2.9), "House02": (0.0,-1.0), "House03": (-0.45,1.90)}

def final_dir(house, seed):
    root=f"{BASE}/{house}_seed{seed}_off_off/context_bank"
    return sorted(x for x in glob.glob(root+"/source_update_*") if os.path.isdir(x))[-1]

def rank_desc(vals, idx):
    return float(pd.Series(-np.asarray(vals,float)).rank(method="average").iloc[idx])

def load(house, seed):
    d=final_dir(house,seed)
    man=pd.read_csv(d+"/candidate_manifest.csv")
    ali=pd.read_csv(d+"/candidate_support_alignment.csv")
    mea=pd.read_csv(d+"/measured_hit_probability.csv")
    mea=mea[(mea.occupancy.astype(str).str.lower()=="free") & (mea.confidence>0)].copy()
    tx,ty=TRUTHS[house]
    allm=pd.read_csv(d+"/measured_hit_probability.csv")
    free=allm[allm.occupancy.astype(str).str.lower()=="free"].copy()
    tr=free.loc[((free.x-tx)**2+(free.y-ty)**2).idxmin()]
    gi,gj=int(tr.grid_i),int(tr.grid_j)
    mask=(man.origin_i<=gi)&(gi<man.origin_i+man.size_i)&(man.origin_j<=gj)&(gj<man.origin_j+man.size_j)
    if mask.sum():
        inds=np.where(mask.to_numpy())[0]
        area=(man.iloc[inds].size_i*man.iloc[inds].size_j).to_numpy()
        ti=int(inds[np.argmin(area)])
    else:
        ti=int(np.argmin((man.center_x-tx)**2+(man.center_y-ty)**2))
    return man,ali,mea,ti

def evaluate(house, seed):
    man,ali,mea,ti=load(house,seed)
    oman,oali,_,_=load(house,1-seed)
    A=man[["center_x","center_y"]].to_numpy(float)
    B=oman[["center_x","center_y"]].to_numpy(float)
    D=((A[:,None,:]-B[None,:,:])**2).sum(-1)
    match=D.argmin(1)
    obs=mea.set_index("cell_index")[["probability","confidence"]]
    tg={c:g.set_index("cell_index").simulated_hit_probability for c,g in ali.groupby("candidate_id")}
    og={c:g.set_index("cell_index").simulated_hit_probability for c,g in oali.groupby("candidate_id")}
    own=[]; other=[]; nc=[]
    for i,row in man.iterrows():
        a=tg[row.candidate_id]
        b=og[oman.iloc[match[i]].candidate_id]
        cells=obs.index.intersection(a.index).intersection(b.index)
        p=obs.loc[cells,"probability"].to_numpy(float)
        c=obs.loc[cells,"confidence"].to_numpy(float)
        qa=a.loc[cells].to_numpy(float); qb=b.loc[cells].to_numpy(float)
        own.append(np.log(np.clip(1-c*np.abs(p-qa),1e-300,1)).sum())
        other.append(np.log(np.clip(1-c*np.abs(p-qb),1e-300,1)).sum())
        nc.append(len(cells))
    own=np.asarray(own); other=np.asarray(other)
    profile=np.maximum(own,other)
    m=np.maximum(own,other)
    marginal=m+np.log(0.5*(np.exp(own-m)+np.exp(other-m)))
    native=np.log(np.clip(man.native_score.to_numpy(float),1e-300,None))
    return {
        "house":house,"seed":seed,"candidate_count":len(man),
        "truth_candidate":str(man.iloc[ti].candidate_id),
        "native_rank":rank_desc(native,ti),
        "own_common_rank":rank_desc(own,ti),
        "other_seed_rank":rank_desc(other,ti),
        "profile_rank":rank_desc(profile,ti),
        "marginal_rank":rank_desc(marginal,ti),
        "common_support_cells":int(min(nc))
    }

if __name__=="__main__":
    out=[evaluate(h,s) for h in ["House01","House02","House03"] for s in [0,1]]
    print(pd.DataFrame(out).to_string(index=False))
    print(json.dumps(out,indent=2))
