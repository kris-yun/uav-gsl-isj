import json, os
from pathlib import Path
import numpy as np, pandas as pd, zstandard as zstd
T=200; BS=20; B=T//BS; TH=0.1; TR=np.array([-0.4,-2.9]); NNULL=500; SEED=20260923; STATIC=20.5

def pick(df,names):
 d={c.lower():c for c in df.columns}
 for n in names:
  if n in d:return d[n]
 raise KeyError((names,list(df.columns)))

def ranklo(x): return pd.Series(x).rank(method='average',ascending=True).to_numpy(float)
def crps1(x,y):
 x=np.sort(np.asarray(x,float)); n=len(x); i=np.arange(1,n+1)
 return float(np.abs(x-y).mean()-np.sum((2*i-n-1)*x)/(n*n))
def score(blocks,y): return sum(crps1(blocks[:,j],y[j]) for j in range(B))
def blocks(X,pathu,shift=None):
 p=np.arange(T)[:,None]; t=np.arange(T)[None,:]
 extra=0 if shift is None else np.asarray(shift)[pathu][None,:]
 idx=(p+t+extra)%T; uu=np.broadcast_to(pathu[None,:],(T,T))
 return X[idx,uu].reshape(T,B,BS).sum(2)
def energy(s,y):
 s=s.astype(float); y=np.asarray(y,float)
 return float(np.linalg.norm(s-y,axis=1).mean()-.5*np.linalg.norm(s[:,None]-s[None,:],axis=2).mean())

# inputs are frozen by workflow
with open('/tmp/occupied_cells.csv.zst','rb') as a, open('/tmp/occupied_cells.csv','wb') as b:zstd.ZstdDecompressor().copy_stream(a,b)
ev=pd.read_csv('/tmp/occupied_cells.csv'); par=pd.read_csv('/tmp/parity_all.csv'); sen=pd.read_csv('/tmp/sensor_trace.csv'); tim=pd.read_csv('/tmp/source_update_timing.csv')
term=par[par.terminal_leaf.astype(int)==1].copy().reset_index(drop=True)
term['td']=np.hypot(term.expected_source_x.astype(float)-TR[0],term.expected_source_y.astype(float)-TR[1])
ids=term.candidate_id.astype(str).tolist(); ti=int(term.td.to_numpy().argmin()); truth_id=ids[ti]
up=float(tim.sort_values('source_update_id').iloc[0].sim_time); obs=sen[sen.t_sim_s.astype(float)<=up+1e-6].tail(T).copy()
assert len(obs)==T
yhit=(obs.measured_gas_ppm.astype(float).to_numpy()>TH).astype(int); y=yhit.reshape(B,BS).sum(1)
tm=tim.sort_values('source_update_id').iloc[0]; w=int(tm.grid_width); h=int(tm.grid_height); cs=float(tm.cell_size); ox=float(tm.origin_x); oy=float(tm.origin_y)
gi=np.floor((obs.x.astype(float).to_numpy()-ox)/cs+1e-9).astype(int); gj=np.floor((obs.y.astype(float).to_numpy()-oy)/cs+1e-9).astype(int)
assert np.all((gi>=0)&(gi<w)&(gj>=0)&(gj<h)); pc=gj*w+gi; cells=np.array(sorted(set(map(int,pc)))); lu={c:i for i,c in enumerate(cells)}; pathu=np.array([lu[int(c)] for c in pc])
cc=pick(ev,['candidate_id','candidate','source_candidate']); ct=pick(ev,['internal_step','internal_timestep','step','timestep','time_step']); cg=pick(ev,['cell_index','cell','grid_index'])
e=ev[ev[cc].astype(str).isin(ids)&ev[cg].astype(int).isin(cells)].copy(); raw=e[ct].astype(int).to_numpy(); st=raw-raw.min(); assert st.min()>=0 and st.max()<T
ci={c:i for i,c in enumerate(ids)}; X=np.zeros((len(ids),T,len(cells)),bool)
for c,g,t in zip(e[cc].astype(str),e[cg].astype(int),st):X[ci[c],int(t),lu[int(g)]]=1
actual=[]; es=[]; mean=[]
for x in X:
 z=blocks(x,pathu); actual.append(score(z,y)); es.append(energy(z,y)); mean.append(float(np.linalg.norm(z.mean(0)-y)))
actual=np.array(actual); es=np.array(es); mean=np.array(mean); ar=ranklo(actual); er=ranklo(es); mr=ranklo(mean); atr=float(ar[ti])
rng=np.random.default_rng(SEED); nr=[]; ns=[]
for _ in range(NNULL):
 sc=[]
 for x in X:
  sh=rng.integers(0,T,size=len(cells)); sc.append(score(blocks(x,pathu,sh),y))
 rr=ranklo(sc); nr.append(float(rr[ti])); ns.append(float(sc[ti]))
nr=np.array(nr); ns=np.array(ns); frac=float(np.mean(nr<=atr)); g1=atr<STATIC; g2=frac<=.05; passed=bool(g1 and g2)
native_rank=pd.Series(-term.expected_score.astype(float)).rank(method='average').to_numpy(float)
out={
 'contract':'DISTRIBUTIONAL_FORWARD_H01_JOINT_STRUCTURE_V1','date':'2026-09-23','input_run':'H01_R2026092201',
 'source_update_time_s':up,'observation_samples':T,'gas_threshold_ppm':TH,'observed_hit_count':int(yhit.sum()),'observed_block_hit_counts':list(map(int,y)),
 'visited_unique_grid_cells':len(cells),'terminal_candidate_count':len(ids),'truth_candidate_id_evaluation_only':truth_id,'truth_candidate_distance_m':float(term.iloc[ti].td),
 'native_truth_rank':float(native_rank[ti]),'static_low_occupancy_truth_rank_reference':STATIC,
 'mean_block_count_truth_rank':float(mr[ti]),'joint_crps_truth_rank':atr,'joint_crps_truth_score':float(actual[ti]),'energy_score_truth_rank_secondary':float(er[ti]),
 'null':{'repetitions':NNULL,'seed':SEED,'truth_rank_median':float(np.median(nr)),'truth_rank_q05':float(np.quantile(nr,.05)),'truth_rank_q95':float(np.quantile(nr,.95)),'fraction_as_good_or_better':frac},
 'gate':{'joint_rank_better_than_static_20p5':bool(g1),'null_fraction_lte_0p05':bool(g2),'pass':passed},
 'interpretation':'PASS_H01_DISTRIBUTIONAL_JOINT_STRUCTURE' if passed else 'NO_GO_H01_DISTRIBUTIONAL_JOINT_STRUCTURE',
 'null_contract':'Independent circular shift per candidate x visited-cell trace; preserves each cell occupancy count and circular autocorrelation, destroys cross-cell relative plume phase.'}
outdir=Path('evidence/distributional_forward_v1'); outdir.mkdir(parents=True,exist_ok=True)
(outdir/'H01_DISTRIBUTIONAL_JOINT_STRUCTURE_RESULT_20260923.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
md=f'''# H01 distributional-forward joint-structure kill test

Date: 2026-09-23

Status: **{out['interpretation']}**

Frozen observation: last {T} sensor samples before source update {up:.3f} s; threshold {TH} ppm; observed hits {int(yhit.sum())}/{T}; 20-sample block counts {list(map(int,y))}; {len(cells)} unique visited cells; {len(ids)} terminal candidates.

| score | truth rank |
|---|---:|
| Native PMFS reference | {native_rank[ti]:.2f}/{len(ids)} |
| prior static low-occupancy reference | {STATIC:.2f}/{len(ids)} |
| mean block-count distance | {mr[ti]:.2f}/{len(ids)} |
| **joint block-CRPS (primary)** | **{atr:.2f}/{len(ids)}** |
| multivariate Energy Score (secondary) | {er[ti]:.2f}/{len(ids)} |

## Joint-destruction null

- repetitions: {NNULL}
- null truth-rank median: {np.median(nr):.2f}
- null truth-rank 5-95%: {np.quantile(nr,.05):.2f}-{np.quantile(nr,.95):.2f}
- fraction null rank as good or better than actual: {frac:.4f}

The null independently circular-shifts each visited-cell occupancy trace. It preserves each candidatexcell 200-step occupancy count and each cell's circular autocorrelation, while destroying cross-cell relative plume phase. Thus the original mean-hitMap information survives the null.

## Predeclared gate

- joint CRPS truth rank better than 20.5/121: **{g1}**
- null as-good-or-better fraction <= 0.05: **{g2}**
- **PASS: {passed}**

''' + ('H01 supports a load-bearing source-identity contribution from stochastic joint plume organization beyond the mean hitMap. Advance to independent hit-bearing H02/H03 replay before any learned generative operator.\n' if passed else 'H01 does not support a load-bearing source-identity gain from joint plume organization beyond the mean hitMap under this frozen test. Do not tune block size, threshold, phase weighting, or score coefficients to rescue H01.\n')
(outdir/'H01_DISTRIBUTIONAL_JOINT_STRUCTURE_RESULT_20260923.md').write_text(md)
print(json.dumps(out,indent=2,sort_keys=True))
