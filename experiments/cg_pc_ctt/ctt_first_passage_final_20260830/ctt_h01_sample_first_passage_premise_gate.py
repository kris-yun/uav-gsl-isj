#!/usr/bin/env python3
"""Sample-grid first-passage/survival premise gate on H01 predictive8.

Uses the frozen native 0.2-s measured-sensor sequence, not 10-sample block
compression, to test the exact scientific premise required by neural M1:
candidate-conditioned first passage must contain source information beyond
integrated ever/never reachability, and that increment must disappear under
order destruction and candidate temporal-label destruction.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,struct
from pathlib import Path
import numpy as np
from scipy.stats import binomtest

MAGIC=b'PFV3STR1'; U32=struct.Struct('<I')
DT=.2; TH=.1; STOP_SAMPLES=80; J=.5; NTEST=32
TAU=1.2; DELAY=2

def read_stream(p):
 raw=Path(p).read_bytes(); assert raw[:8]==MAGIC
 off=8;(n,)=U32.unpack_from(raw,off);off+=4
 L=struct.unpack_from(f'<{n}I',raw,off);off+=4*n
 a=np.frombuffer(raw,dtype='<f4',offset=off);out=[];s=0
 for z in L:out.append(a[s:s+z].copy());s+=z
 return out

def sensor_batch(x):
 x=np.asarray(x,dtype=np.float64); state=np.zeros(x.shape[0]); y=np.empty_like(x); a=math.exp(-DT/TAU)
 for t in range(x.shape[1]):
  target=x[:,t-DELAY] if t>=DELAY else 0.
  state=a*state+(1-a)*target;y[:,t]=state
 return y

def digest(s): return hashlib.sha256(s.encode()).digest()

def carriers(support):
 g={}
 with open(support,newline='') as f:
  for r in csv.DictReader(f):
   if r['house']=='H01':g.setdefault(int(r['carrier_index']),[]).append(r)
 out=[]
 for i in sorted(g):
  rr=g[i];out.append((rr[0]['carrier_id'],np.mean([float(r['pmfs_x']) for r in rr]),np.mean([float(r['pmfs_y']) for r in rr])))
 assert len(out)==210;return out

def select(cs,n=NTEST):
 xy=np.array([[c[1],c[2]] for c in cs]);xy=(xy-xy.min(0))/np.maximum(np.ptp(xy,axis=0),1e-12)
 tie=[digest('CTT-FP-PREMISE|'+c[0]) for c in cs];sel=[min(range(len(cs)),key=lambda i:tie[i])];rem=set(range(len(cs)))-set(sel)
 while len(sel)<n:
  q=min(rem,key=lambda i:(-min(float(np.sum((xy[i]-xy[j])**2)) for j in sel),tie[i]));sel.append(q);rem.remove(q)
 return sel

def stop_idx(path):
 with open(path,newline='') as f:r=list(csv.DictReader(f))
 mov=np.array([int(x['is_moving']) for x in r]);sid=np.array([int(x['stop_id']) for x in r]);out=[]
 for s in np.unique(sid):
  idx=np.flatnonzero(sid==s);lm=mov[idx];fm=next((i for i,v in enumerate(lm) if v),len(idx))
  if fm>=STOP_SAMPLES:out.append(idx[:STOP_SAMPLES])
 return out

def load(bank,cs,tr,stops):
 T=len(read_stream(bank/'member_00'/f'{cs[0][0]}.bin')[tr]);x=np.empty((len(cs)*8,T),np.float32);q=0
 for cid,_,_ in cs:
  for k in range(8):x[q]=read_stream(bank/f'member_{k:02d}'/f'{cid}.bin')[tr];q+=1
 y=sensor_batch(x).reshape(len(cs),8,T)
 return y[:,:,np.stack(stops)] # [S,K,J,80]

def first_index(binary):
 # [...,T] -> 0..T-1 or T never
 anyhit=binary.any(-1);idx=np.argmax(binary,axis=-1);return np.where(anyhit,idx,binary.shape[-1])

def fp_model(pred):
 # pred binary [S,K,J,T]. Empirical discrete first-passage with symmetric Jeffreys Dirichlet.
 F=first_index(pred);S,K,N=F.shape;T=pred.shape[-1];counts=np.zeros((S,N,T+1),np.float64)
 for f in range(T+1):counts[:,:,f]=(F==f).sum(1)
 p=(counts+J)/(K+J*(T+1)); pever=1-p[:,:,-1]
 return p,pever

def score(obs_binary,p,pever):
 F=first_index(obs_binary);S,N,_=p.shape;j=np.arange(N);F=np.asarray(F)
 full=np.log(np.clip(p[:,j,F],1e-300,1)).sum(1)
 ever=(F<obs_binary.shape[-1]); surv=np.where(ever[None,:],np.log(np.clip(pever,1e-300,1)),np.log(np.clip(1-pever,1e-300,1))).sum(1)
 # conditional phase score: zero on no-event stops.
 phase=np.zeros((S,N),np.float64)
 for jj in range(N):
  if ever[jj]: phase[:,jj]=np.log(np.clip(p[:,jj,F[jj]]/np.clip(pever[:,jj],1e-300,1),1e-300,1))
 return full,surv,phase.sum(1)

def permute(obs,key):
 out=obs.copy()
 for j in range(len(out)):
  rng=np.random.default_rng(int.from_bytes(digest(f'CTT-FP-ORDER|{key}|{j}')[:8],'big'));out[j]=out[j,rng.permutation(STOP_SAMPLES)]
 assert np.array_equal(out.sum(1),obs.sum(1));return out

def rank(s,t):
 x=s[t];return float(1+np.count_nonzero(s>x)+.5*(np.count_nonzero(s==x)-1))

def signs(a,b):
 a=np.asarray(a);b=np.asarray(b);w=int((a<b).sum());l=int((a>b).sum());z=int((a==b).sum());n=w+l
 return {'wins':w,'losses':l,'ties':z,'p':float(binomtest(w,n,.5,alternative='greater').pvalue) if n else 1.}

def summ(rows,k):
 r=np.array([x[k] for x in rows]);return {'mean_norm':float(((r-1)/209).mean()),'median':float(np.median(r)),'top5':float((r<=5).mean()),'top10':float((r<=10).mean())}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bank',type=Path,required=True);ap.add_argument('--support',type=Path,required=True);ap.add_argument('--schedules',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise SystemExit('refuse overwrite')
 a.out.mkdir(parents=True);cs=carriers(a.support);sel=select(cs);rows=[]
 for tr in range(5):
  stops=stop_idx(a.schedules/f'trajectory_seed_{4001+tr}.csv');meas=load(a.bank,cs,tr,stops);binary=meas>TH
  print('tr',4001+tr,'stops',len(stops),'sample_hit_rate',binary.mean(),flush=True)
  for held in range(8):
   pred=binary[:,[k for k in range(8) if k!=held]];p,pe=fp_model(pred)
   labperm=np.random.default_rng(int.from_bytes(digest(f'CTT-FP-LABEL|{tr}|{held}')[:8],'big')).permutation(210)
   for truth in sel:
    obs=binary[truth,held];full,surv,phase=score(obs,p,pe);po=permute(obs,f'{tr}|{held}|{cs[truth][0]}');fullp,_,phasep=score(po,p,pe)
    # destroy candidate/phase association only: keep candidate survival term, shuffle conditional phase score.
    full_lab=surv+phase[labperm]
    rows.append({'trajectory':4001+tr,'member':held,'truth':truth,'id':cs[truth][0],
     'rank_survival':rank(surv,truth),'rank_phase':rank(phase,truth),'rank_full':rank(full,truth),
     'rank_full_time_permute':rank(fullp,truth),'rank_full_temporal_label_shuffle':rank(full_lab,truth)})
 assert len(rows)==1280
 with open(a.out/'cases.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 ks=['rank_survival','rank_phase','rank_full','rank_full_time_permute','rank_full_temporal_label_shuffle'];S={k:summ(rows,k) for k in ks};A={k:np.array([r[k] for r in rows]) for k in ks}
 C={'full_vs_survival':signs(A['rank_full'],A['rank_survival']),'full_vs_time_permute':signs(A['rank_full'],A['rank_full_time_permute']),'full_vs_label_shuffle':signs(A['rank_full'],A['rank_full_temporal_label_shuffle'])}
 gate={
  'first_passage_adds_beyond_survival':S['rank_full']['mean_norm']<S['rank_survival']['mean_norm'] and C['full_vs_survival']['p']<=.01,
  'top10_non_degrade_vs_survival':S['rank_full']['top10']>=S['rank_survival']['top10'],
  'time_order_load_bearing':S['rank_full']['mean_norm']<S['rank_full_time_permute']['mean_norm'] and C['full_vs_time_permute']['p']<=.01,
  'candidate_phase_load_bearing':S['rank_full']['mean_norm']<S['rank_full_temporal_label_shuffle']['mean_norm'] and C['full_vs_label_shuffle']['p']<=.01,
 }
 R={'contract':'CTT_H01_NATIVE_SAMPLE_FIRST_PASSAGE_PREMISE_V1','historical_truth_used':False,'case_count':len(rows),'threshold_ppm':TH,'dt_s':DT,'stop_samples':STOP_SAMPLES,'jeffreys':J,'summary':S,'comparisons':C,'gate':gate,'verdict':'CTT_H01_NATIVE_FIRST_PASSAGE_PREMISE_PASS' if all(gate.values()) else 'CTT_H01_NATIVE_FIRST_PASSAGE_PREMISE_NO_GO'}
 (a.out/'summary.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n');(a.out/'VERDICT.txt').write_text(R['verdict']+'\n');print(json.dumps(R,indent=2,sort_keys=True))
if __name__=='__main__':main()
