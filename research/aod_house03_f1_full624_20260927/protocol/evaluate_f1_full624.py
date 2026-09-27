#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

BOOT_N=10000
BOOT_SEED=2026092703

def prepare(scores, condition):
    d=scores[scores.condition==condition].copy()
    # Required one candidate row per target/path/arm/candidate.
    keys=["truth_source","realization","path","arm"]
    out=[]
    for key,g in d.groupby(keys,sort=False):
        truth,real,path,arm=key
        if g.candidate_source.nunique()!=624:
            raise ValueError(f"{key}: support {g.candidate_source.nunique()} !=624")
        mins=g.SSE.min()
        winners=g[g.SSE==mins]
        unique=bool(len(winners)==1 and str(winners.iloc[0].candidate_source)==str(truth))
        # diagnostics
        tr=g[g.candidate_source.astype(str)==str(truth)].iloc[0]
        rank=float(g.SSE.rank(method="average",ascending=True).loc[tr.name])
        best=g.sort_values(["SSE","candidate_source"]).iloc[0]
        out.append(dict(truth_source=str(truth),realization=int(real),
                        path=str(path),arm=str(arm),
                        unique_top1=int(unique),true_rank=rank,
                        map_error_m=float(best.map_error_m)))
    return pd.DataFrame(out)

def d_table(metric):
    p=metric.pivot(index=["truth_source","realization","path"],
                   columns="arm",values="unique_top1").reset_index()
    if not {"u","rawu"}.issubset(p.columns): raise ValueError("missing arm")
    p["d_path"]=p.rawu-p.u
    sr=p.groupby(["truth_source","realization"],as_index=False).d_path.mean()
    return sr

def delta(sr):
    return float(sr.groupby("truth_source").d_path.mean().mean())

def paired_boot(nom_sr, stress_sr):
    sources=sorted(nom_sr.truth_source.unique())
    # require same source x realization support in both conditions
    lookupN={s:nom_sr[nom_sr.truth_source==s].sort_values("realization").d_path.to_numpy(float) for s in sources}
    lookupS={s:stress_sr[stress_sr.truth_source==s].sort_values("realization").d_path.to_numpy(float) for s in sources}
    for s in sources:
        if len(lookupN[s])!=8 or len(lookupS[s])!=8: raise ValueError((s,len(lookupN[s]),len(lookupS[s])))
    rng=np.random.Generator(np.random.PCG64(BOOT_SEED))
    bn=np.empty(BOOT_N); bs=np.empty(BOOT_N)
    for b in range(BOOT_N):
        srcN=[]; srcS=[]
        for s in sources:
            idx=rng.integers(0,8,size=8)
            srcN.append(float(lookupN[s][idx].mean()))
            srcS.append(float(lookupS[s][idx].mean()))
        bn[b]=np.mean(srcN); bs[b]=np.mean(srcS)
    q=lambda x:[float(v) for v in np.quantile(x,[.025,.975],method="linear")]
    return q(bn),q(bs),bn,bs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scores",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    scores=pd.read_csv(a.scores)
    nom=prepare(scores,"nominal")
    st=prepare(scores,"state0_stress")
    nom_sr=d_table(nom); st_sr=d_table(st)
    dn=delta(nom_sr); ds=delta(st_sr)
    ciN,ciS,bn,bs=paired_boot(nom_sr,st_sr)

    nominal_pass=(dn>=0.05 and ciN[0]>0)
    if not nominal_pass:
        decision="AOD_F1_FULL624_NOT_CONFIRMED"
    elif ciS[0]>=-0.05:
        decision="AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR"
    elif ciS[1]<0:
        decision="AOD_F1_FULL624_CONFIRMED_TRADEOFF"
    else:
        decision="AOD_F1_FULL624_CONFIRMED_STRESS_UNCERTAIN"

    result={
      "decision":decision,
      "candidate_support":624,
      "truth_sources":12,
      "realizations_per_source":8,
      "paths_per_realization":2,
      "nominal":{"Delta_acc":dn,"ci95":ciN,
                 "effect_gate_ge_0p05":bool(dn>=0.05),
                 "ci_lower_gt_0":bool(ciN[0]>0)},
      "state0_stress":{"Delta_acc":ds,"ci95":ciS,
                       "noninferiority_lower_ge_minus_0p05":bool(ciS[0]>=-0.05),
                       "supported_negative_effect_upper_lt_0":bool(ciS[1]<0)},
      "bootstrap":{"n":BOOT_N,"seed":BOOT_SEED,"rng":"PCG64",
                   "quantile_method":"linear",
                   "resampling":"within source realization; paths/arms/conditions grouped"}
    }
    nom.to_csv(a.out/"NOMINAL_FULL624_TARGET_METRICS.csv",index=False)
    st.to_csv(a.out/"STATE0_FULL624_TARGET_METRICS.csv",index=False)
    nom_sr.to_csv(a.out/"NOMINAL_SOURCE_REALIZATION_EFFECT.csv",index=False)
    st_sr.to_csv(a.out/"STATE0_SOURCE_REALIZATION_EFFECT.csv",index=False)
    np.save(a.out/"BOOT_NOMINAL.npy",bn,allow_pickle=False)
    np.save(a.out/"BOOT_STATE0.npy",bs,allow_pickle=False)
    (a.out/"F1_PRIMARY_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
