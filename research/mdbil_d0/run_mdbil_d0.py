#!/usr/bin/env python3
"""MDBIL-D0 frozen feasibility gate. No GADEN/PMFS/closed-loop execution."""
import argparse,csv,hashlib,json,random,sys
from pathlib import Path
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

ROOT=Path(__file__).resolve().parents[2]
MAN=ROOT/'evidence/cdsi_t01b/pass1/EXACT_64_RUN_MANIFEST.tsv'
INP=ROOT/'evidence/ocb_r2/mechanism_census_r0/inputs'
SEEDS=(2026100101,2026100102,2026100103)
CFG=dict(epochs=500,lr=2e-3,wd=1e-4,temp=.15,src=1.0,con=.5,align=.5,met=.5,adv=.2,ind=.05,rec=.1,rank=.5,margin=.2)

def seed(s):
 random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def tsv(p,rows):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n'); w.writeheader(); w.writerows(rows)

class GR(torch.autograd.Function):
 @staticmethod
 def forward(c,x): return x.view_as(x)
 @staticmethod
 def backward(c,g): return -g
class Block(nn.Module):
 def __init__(self,d): super().__init__(); self.a=nn.Conv1d(64,64,3,padding=d,dilation=d); self.b=nn.Conv1d(64,64,3,padding=d,dilation=d)
 def forward(self,x): return F.gelu(x+self.b(F.gelu(self.a(x))))
class Net(nn.Module):
 def __init__(self,ne):
  super().__init__(); self.stem=nn.Conv1d(30,64,1); self.b=nn.Sequential(Block(1),Block(2),Block(4)); self.h=nn.Linear(128,64)
  self.s=nn.Linear(64,8); self.m=nn.Linear(64,8); self.sh=nn.Linear(8,2); self.mh=nn.Linear(8,ne); self.ah=nn.Linear(8,ne)
  self.dec=nn.Sequential(nn.Linear(16,64),nn.GELU(),nn.Linear(64,300))
 def forward(self,x):
  q=self.b(F.gelu(self.stem(x.transpose(1,2)))); h=F.gelu(self.h(torch.cat([q.mean(-1),q.amax(-1)],1))); s,m=self.s(h),self.m(h)
  return s,m,self.sh(s),self.mh(m),self.ah(GR.apply(s)),self.dec(torch.cat([s,m],1)).view(-1,10,30)

def load():
 rows=list(csv.DictReader(MAN.open(encoding='utf-8'),delimiter='\t'))
 if len(rows)!=64 or len({r['run_id'] for r in rows})!=64 or len({r['master_seed'] for r in rows})!=64: raise ValueError('64-run contract')
 out=[]; hashes=[]
 for r in rows:
  p=INP/(r['run_id']+'.pooled.npy'); d=sha(p)
  if d!=r['frozen_tensor_sha256']: raise ValueError('SHA '+r['run_id'])
  x=np.load(p,allow_pickle=False)
  if x.shape!=(10,30) or not np.isfinite(x).all() or (x<0).any(): raise ValueError('tensor '+r['run_id'])
  out.append({**r,'x':(x>0).astype('float32')}); hashes.append(dict(run_id=r['run_id'],sha256=d))
 houses=sorted({r['house'] for r in out})
 if houses!=['House01','House02']: raise ValueError('house contract')
 meta={}
 for h in houses:
  a=[r for r in out if r['house']==h]; ctx=sorted({r['context'] for r in a}); src=sorted({r['source_id'] for r in a})
  if len(ctx)!=4 or len(src)!=2: raise ValueError('context/source contract '+h)
  for s in src:
   xyz={(r['source_x'],r['source_y'],r['source_z']) for r in a if r['source_id']==s}
   if len(xyz)!=1: raise ValueError('geometry '+h+s)
  for c in ctx:
   q=[r for r in a if r['context']==c]
   if len(q)!=8 or len({r['wind_id'] for r in q})!=1 or len({r['gas_type'] for r in q})!=1: raise ValueError('context '+c)
   if any(len([r for r in q if r['source_id']==s])!=4 for s in src): raise ValueError('replicate '+c)
   meta[c]=dict(house=h,wind=q[0]['wind_id'],gas=q[0]['gas_type'])
  for c in ctx:
   if sum(meta[d]['gas']==meta[c]['gas'] for d in ctx if d!=c)!=1: raise ValueError('same-gas sibling '+c)
 return out,hashes,meta

def cos(a,b):
 a=a/np.maximum(np.linalg.norm(a,axis=1,keepdims=True),1e-12); b=b/np.maximum(np.linalg.norm(b,axis=1,keepdims=True),1e-12); return a@b.T
def pm(ztr,ytr,zte,yte):
 P=np.stack([ztr[ytr==i].mean(0) for i in (0,1)]); s=cos(zte,P); pred=s.argmax(1); mar=s[np.arange(len(yte)),yte]-s[np.arange(len(yte)),1-yte]
 sep=max(1-cos(P[:1],P[1:])[0,0],1e-6); rat=(1-s[np.arange(len(yte)),yte])/sep
 return float((pred==yte).mean()),float(np.median(mar)),float(np.median(rat))
def windrat(ztr,ytr,enames,zte,yte,gas,meta):
 e=[x for x in sorted(set(enames)) if meta[x]['gas']==gas]
 if len(e)!=1: raise ValueError('wind sibling')
 mask=np.array([x==e[0] for x in enames]); P=np.stack([ztr[mask&(ytr==i)].mean(0) for i in (0,1)]); s=cos(zte,P)
 sep=max(1-cos(P[:1],P[1:])[0,0],1e-6); return float(np.median((1-s[np.arange(len(yte)),yte])/sep))
def envloo(z,e):
 pred=[]
 for i in range(len(z)):
  keep=np.arange(len(z))!=i; C=np.stack([z[keep&(e==j)].mean(0) for j in sorted(set(e))]); pred.append(int(np.argmax(cos(z[i:i+1],C)[0])))
 return float((np.array(pred)==e).mean())
def cov(x):
 x=x-x.mean(0,keepdim=True); return x.T@x/max(len(x)-1,1)
def losses(s,m,sl,ml,al,rec,x,y,e,variant):
 src=F.cross_entropy(sl,y); zn=F.normalize(s,dim=1); P=torch.stack([F.normalize(zn[y==i].mean(0),dim=0) for i in (0,1)]); sim=zn@P.T
 rank=F.relu(CFG['margin']-sim[torch.arange(len(y)),y]+sim[torch.arange(len(y)),1-y]).mean()
 if variant=='vanilla': return CFG['src']*src+CFG['rank']*rank
 n=len(y); S=zn@zn.T/CFG['temp']; eye=torch.eye(n,dtype=torch.bool); den=torch.logsumexp(S.masked_fill(eye,-1e9),1); pos=(y[:,None]==y[None,:])&(e[:,None]!=e[None,:])&~eye
 con=torch.stack([-(S[i,pos[i]]-den[i]).mean() for i in range(n)]).mean()
 A=[]
 for sy in (0,1):
  es=sorted(set(e[y==sy].tolist()))
  for i in range(len(es)):
   for j in range(i+1,len(es)):
    a=s[(y==sy)&(e==es[i])]; b=s[(y==sy)&(e==es[j])]; A.append((a.mean(0)-b.mean(0)).pow(2).mean()+.1*(cov(a)-cov(b)).pow(2).mean())
 align=torch.stack(A).mean(); met=F.cross_entropy(ml,e); adv=F.cross_entropy(al,e); ind=((s-s.mean(0)).T@(m-m.mean(0))/max(n-1,1)).pow(2).mean(); rc=F.binary_cross_entropy_with_logits(rec,x)
 return CFG['src']*src+CFG['con']*con+CFG['align']*align+CFG['met']*met+CFG['adv']*adv+CFG['ind']*ind+CFG['rec']*rc+CFG['rank']*rank

def train(x,y,e,variant,sd,epochs):
 # CrossEntropy requires int64 indices; NumPy's default integer is int32 on Windows.
 seed(sd); X=torch.from_numpy(x); Y=torch.from_numpy(y).long(); E=torch.from_numpy(e).long(); net=Net(len(set(e))); opt=torch.optim.Adam(net.parameters(),lr=CFG['lr'],weight_decay=CFG['wd'])
 for _ in range(epochs):
  opt.zero_grad(); o=net(X); L=losses(*o,X,Y,E,variant); L.backward(); opt.step()
 with torch.no_grad(): s,m,_,_,_,r=net(X)
 return net,s.numpy(),m.numpy(),float(F.binary_cross_entropy_with_logits(r,X))
def enc(net,x):
 with torch.no_grad(): s,m,_,_,_,r=net(torch.from_numpy(x)); return s.numpy(),m.numpy(),float(F.binary_cross_entropy_with_logits(r,torch.from_numpy(x)))

def arrays(data,h,hold):
 a=[r for r in data if r['house']==h]; src={s:i for i,s in enumerate(sorted({r['source_id'] for r in a}))}; tr=sorted([r for r in a if r['context']!=hold],key=lambda r:(r['context'],r['source_id'],r['replicate_ordinal'])); te=sorted([r for r in a if r['context']==hold],key=lambda r:(r['source_id'],r['replicate_ordinal']))
 envs=sorted({r['context'] for r in tr}); em={s:i for i,s in enumerate(envs)}
 return np.stack([r['x'] for r in tr]),np.array([src[r['source_id']] for r in tr]),np.array([em[r['context']] for r in tr]),[r['context'] for r in tr],np.stack([r['x'] for r in te]),np.array([src[r['source_id']] for r in te])
def fold(data,h,hold,meta,epochs):
 x,y,e,en,xt,yt=arrays(data,h,hold); raw=pm(x.reshape(len(x),-1),y,xt.reshape(len(xt),-1),yt); rw=windrat(x.reshape(len(x),-1),y,en,xt.reshape(len(xt),-1),yt,meta[hold]['gas'],meta); static=pm(x.mean(1),y,xt.mean(1),yt); sw=windrat(x.mean(1),y,en,xt.mean(1),yt,meta[hold]['gas'],meta); rows=[]
 for sd in SEEDS:
  for v in ('vanilla','invariant'):
   net,z,m,_=train(x,y,e,v,sd,epochs); zt,mt,rc=enc(net,xt); p=pm(z,y,zt,yt)
   rows.append(dict(house=h,heldout_context=hold,seed=sd,variant=v,accuracy=p[0],margin=p[1],ratio=p[2],wind_ratio=windrat(z,y,en,zt,yt,meta[hold]['gas'],meta),zs_env=envloo(z,e),zm_env=envloo(m,e),recon=rc))
 med=lambda v,k: float(np.median([r[k] for r in rows if r['variant']==v]))
 f=dict(house=h,heldout_context=hold,heldout_wind=meta[hold]['wind'],heldout_gas=meta[hold]['gas'],raw_accuracy=raw[0],raw_margin=raw[1],raw_ratio=raw[2],raw_wind_ratio=rw,static_accuracy=static[0],static_margin=static[1],static_ratio=static[2],static_wind_ratio=sw,vanilla_accuracy=med('vanilla','accuracy'),vanilla_margin=med('vanilla','margin'),vanilla_ratio=med('vanilla','ratio'),vanilla_wind_ratio=med('vanilla','wind_ratio'),vanilla_zs_env=med('vanilla','zs_env'),invariant_accuracy=med('invariant','accuracy'),invariant_margin=med('invariant','margin'),invariant_ratio=med('invariant','ratio'),invariant_wind_ratio=med('invariant','wind_ratio'),invariant_zs_env=med('invariant','zs_env'),invariant_zm_env=med('invariant','zm_env'),invariant_recon=med('invariant','recon'))
 f.update(ratio_gain_v=f['vanilla_ratio']-f['invariant_ratio'],ratio_gain_raw=f['raw_ratio']-f['invariant_ratio'],ratio_gain_static=f['static_ratio']-f['invariant_ratio'],wind_gain_v=f['vanilla_wind_ratio']-f['invariant_wind_ratio'],wind_gain_raw=f['raw_wind_ratio']-f['invariant_wind_ratio'],wind_gain_static=f['static_wind_ratio']-f['invariant_wind_ratio'],leak_gain=f['vanilla_zs_env']-f['invariant_zs_env'])
 return rows,f

def gates(F):
 a=np.array([x['invariant_accuracy'] for x in F]); m=np.array([x['invariant_margin'] for x in F]); r=np.array([x['invariant_ratio'] for x in F]); w=np.array([x['invariant_wind_ratio'] for x in F]); rv=np.array([x['ratio_gain_v'] for x in F]); rr=np.array([x['ratio_gain_raw'] for x in F]); rs=np.array([x['ratio_gain_static'] for x in F]); wv=np.array([x['wind_gain_v'] for x in F]); wr=np.array([x['wind_gain_raw'] for x in F]); ws=np.array([x['wind_gain_static'] for x in F]); le=np.array([x['leak_gain'] for x in F]); zm=np.array([x['invariant_zm_env'] for x in F]); ref=max(np.median([x['raw_accuracy'] for x in F]),np.median([x['static_accuracy'] for x in F]),np.median([x['vanilla_accuracy'] for x in F]))
 g1=dict(median_accuracy=float(np.median(a)),folds_acc_ge_075=int((a>=.75).sum()),median_margin=float(np.median(m)),folds_margin_pos=int((m>0).sum())); g1['pass']=g1['median_accuracy']>=.75 and g1['folds_acc_ge_075']>=6 and g1['median_margin']>0 and g1['folds_margin_pos']>=7
 g2=dict(median_ratio=float(np.median(r)),folds_ratio_lt1=int((r<1).sum()),median_wind_ratio=float(np.median(w)),folds_wind_ratio_lt1=int((w<1).sum())); g2['pass']=g2['median_ratio']<.75 and g2['folds_ratio_lt1']>=6 and g2['median_wind_ratio']<1 and g2['folds_wind_ratio_lt1']>=6
 g3=dict(best_reference_accuracy=float(ref),median_accuracy=float(np.median(a)),median_ratio_gain_v=float(np.median(rv)),median_ratio_gain_raw=float(np.median(rr)),median_ratio_gain_static=float(np.median(rs)),folds_ratio_gain_v=int((rv>0).sum()),folds_ratio_gain_raw=int((rr>0).sum()),folds_ratio_gain_static=int((rs>0).sum()),median_wind_gain_v=float(np.median(wv)),median_wind_gain_raw=float(np.median(wr)),median_wind_gain_static=float(np.median(ws))); g3['pass']=g3['median_accuracy']>=ref-.125 and g3['median_ratio_gain_v']>0 and g3['median_ratio_gain_raw']>0 and g3['median_ratio_gain_static']>0 and g3['folds_ratio_gain_v']>=6 and g3['folds_ratio_gain_raw']>=6 and g3['folds_ratio_gain_static']>=6 and g3['median_wind_gain_v']>0 and g3['median_wind_gain_raw']>0 and g3['median_wind_gain_static']>0
 g4=dict(median_zm_env=float(np.median(zm)),median_leak_gain=float(np.median(le)),folds_nonworse_leak=int((le>=-1e-12).sum())); g4['pass']=g4['median_zm_env']>=2/3-1e-12 and g4['median_leak_gain']>=-1e-12 and g4['folds_nonworse_leak']>=5
 return dict(G1=g1,G2=g2,G3=g3,G4=g4)

def selftest():
 seed(1); x=(np.random.rand(24,10,30)<.3).astype('float32'); y=np.repeat([0,1],12); e=np.tile(np.repeat([0,1,2],4),2)
 for v in ('vanilla','invariant'): net,z,m,_=train(x,y,e,v,7,3); assert z.shape==(24,8) and np.isfinite(z).all() and np.isfinite(m).all()
 print('MDBIL-D0 self-test PASS')
def main(A):
 if A.self_test: selftest(); return 0
 O=A.output.resolve(); O.mkdir(parents=True,exist_ok=True)
 try: data,hashes,meta=load()
 except Exception as ex: js(O/'MDBIL_D0_RESULT.json',dict(decision='MDBIL_D0_INVALID_INPUT_STOP',error=str(ex))); return 2
 tsv(O/'INPUT_SHA256.tsv',hashes); js(O/'DATA_CONTRACT.json',dict(decision='PASS',runs=64,contexts=meta,claim='configured xyz only; not pure XY',new_gaden=0,pmfs=0,closed_loop=0)); js(O/'MODEL_CONFIG.json',dict(cfg=CFG,seeds=SEEDS,split='leave-one-context-out per House',epochs=A.epochs,arms=['RAW','STATIC','VANILLA','MDBIL']))
 R=[]; F=[]
 for h in ('House01','House02'):
  for c in sorted(k for k,v in meta.items() if v['house']==h): rows,f=fold(data,h,c,meta,A.epochs); R+=rows; F.append(f); print(json.dumps(f,sort_keys=True),flush=True)
 tsv(O/'SEED_METRICS.tsv',R); tsv(O/'FOLD_METRICS.tsv',F); G=gates(F); decision='MDBIL_D0_NO_STABLE_SOURCE_BLOCK_STOP' if not G['G1']['pass'] else ('MDBIL_D0_SOURCE_WEATHER_BLOCK_SIGNAL_PASS' if all(x['pass'] for x in G.values()) else 'MDBIL_D0_SOURCE_BLOCK_SIGNAL_HOLD')
 res=dict(decision=decision,gates=G,prior_cdsi='CDSI_T01B_SOURCE_INFORMATION_STATIC_ONLY_HOLD',claim='source-configuration block stability only; no pure XY or PMFS claim',new_gaden=0,pmfs=0,closed_loop=0,completed_and_stopped=True); js(O/'MDBIL_D0_RESULT.json',res); (O/'DECISION.md').write_text('# MDBIL-D0\n\nDecision: '+decision+'\n\nSTOP. No GADEN/PMFS/closed loop.\n',encoding='utf-8'); print(json.dumps(res,sort_keys=True)); return 0
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,default=ROOT/'evidence/mdbil_d0/pass1'); p.add_argument('--epochs',type=int,default=500); p.add_argument('--self-test',action='store_true'); raise SystemExit(main(p.parse_args()))
