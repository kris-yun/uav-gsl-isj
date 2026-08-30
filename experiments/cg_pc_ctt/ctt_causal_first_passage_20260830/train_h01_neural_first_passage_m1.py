#!/usr/bin/env python3
"""H01 neural M1 physical gate: wind/route-conditioned first-passage field.

Scientific contract
-------------------
This network is a simulator solver surrogate, never a source classifier or
posterior corrector.  It predicts the native 0.2-s first-passage distribution
for one candidate source and one causal measurement stop.  Supervision is
obtained only from native physical concentration -> persistent sensor traces.
No localization/rank/PMFS posterior/planner outcome is read by training or
checkpoint selection.

Frozen split:
- source carriers: deterministic SHA256 order 150 train / 30 val / 30 test;
- trajectories: 4001..4003 train, 4004 validation, 4005 test;
- all eight simulator transport/placement members are stochastic labels.

Capacity-matched arms:
- CONDITIONAL: physical geometry + causal route context + actual wind context;
- STATIC-WIND: same architecture/dimension but dynamic wind features are
  replaced by their train-set mean.  This is a physical-context ablation, not a
  fitted reliability gate.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct,time
from pathlib import Path
import numpy as np
import torch
from torch import nn

MAGIC=b'PFV3STR1'; WIND_MAGIC=b'PFV3WND1'; U32=struct.Struct('<I')
DT=0.2; TH=0.1; STOP_SAMPLES=80; NEVER=80; CLASSES=81
TAU=1.2; DELAY=2
SEED=20260830; HIDDEN=128; BATCH=2048; MAX_EPOCHS=40; PATIENCE=6
TRAIN_TRAJ=(0,1,2); VAL_TRAJ=(3,); TEST_TRAJ=(4,)


def sha256_text(s): return hashlib.sha256(s.encode()).hexdigest()
def sha256_file(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()

def read_stream(p):
 raw=Path(p).read_bytes(); assert raw[:8]==MAGIC
 off=8;(n,)=U32.unpack_from(raw,off);off+=4
 L=struct.unpack_from(f'<{n}I',raw,off);off+=4*n
 a=np.frombuffer(raw,dtype='<f4',offset=off);out=[];s=0
 for z in L: out.append(a[s:s+z].copy());s+=z
 return out

def read_wind(p):
 raw=Path(p).read_bytes(); assert raw[:8]==WIND_MAGIC
 off=8;(n,)=U32.unpack_from(raw,off);off+=4
 L=struct.unpack_from(f'<{n}I',raw,off);off+=4*n
 a=np.frombuffer(raw,dtype='<f4',offset=off);out=[];s=0
 for z in L:
  q=a[s:s+3*z].reshape(z,3).copy();out.append(q);s+=3*z
 return out

def sensor_batch(x):
 x=np.asarray(x,dtype=np.float64); state=np.zeros(x.shape[0]); y=np.empty_like(x); a=math.exp(-DT/TAU)
 for t in range(x.shape[1]):
  target=x[:,t-DELAY] if t>=DELAY else 0.0
  state=a*state+(1-a)*target; y[:,t]=state
 return y

def carrier_rows(support):
 g={}
 with open(support,newline='') as f:
  for r in csv.DictReader(f):
   if r['house']=='H01':g.setdefault(int(r['carrier_index']),[]).append(r)
 out=[]
 for i in sorted(g):
  rr=g[i]; out.append(dict(index=i,id=rr[0]['carrier_id'],x=float(np.mean([float(r['pmfs_x']) for r in rr])),y=float(np.mean([float(r['pmfs_y']) for r in rr])),size_i=float(rr[0]['size_i']),size_j=float(rr[0]['size_j'])))
 assert len(out)==210
 return out

def source_split(cs):
 order=sorted(range(len(cs)),key=lambda i:hashlib.sha256(('CTT-M1-H01-SOURCE-SPLIT|'+cs[i]['id']).encode()).digest())
 return {'train':order[:150],'val':order[150:180],'test':order[180:]}

def read_schedule(path):
 rows=[]
 with open(path,newline='') as f:
  for r in csv.DictReader(f): rows.append({k:float(r[k]) for k in ('t_sim_s','x','y','z','yaw')}|{'moving':int(r['is_moving']),'stop_id':int(r['stop_id'])})
 return rows

def stop_records(rows,w):
 assert len(rows)==len(w)
 stops=[]; prev_xy=None; path=0.0
 xy=np.array([[r['x'],r['y']] for r in rows],dtype=np.float64)
 if len(xy)>1: cum=np.concatenate([[0.],np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))])
 else: cum=np.zeros(1)
 for sid in sorted(set(r['stop_id'] for r in rows)):
  idx=np.array([i for i,r in enumerate(rows) if r['stop_id']==sid and r['moving']==0],dtype=int)
  if len(idx)<STOP_SAMPLES: continue
  # Strictly use the first 8x10 samples as the completed PMFS blocks.  Sensor
  # state itself is propagated over the complete trajectory outside this helper.
  idx=idx[:STOP_SAMPLES]; start=int(idx[0]); end=int(idx[-1])+1
  q=rows[start]; cur=np.array([q['x'],q['y']],dtype=float)
  dprev=np.zeros(2) if prev_xy is None else cur-prev_xy
  wc=w[idx]
  wp=w[:end]
  feat_route=np.array([q['t_sim_s'],cum[start],dprev[0],dprev[1],math.sin(q['yaw']),math.cos(q['yaw'])],dtype=np.float32)
  feat_w=np.concatenate([wc.mean(0),wc.std(0),wc[-1],wp.mean(0),wp.std(0)]).astype(np.float32) # 15
  stops.append(dict(sid=sid,start=start,end=end,idx=idx,xy=cur,route=feat_route,wind=feat_w))
  prev_xy=cur
 return stops

def first_passage(measured,idx):
 h=measured[:,idx]>TH
 anyh=h.any(1); f=np.argmax(h,axis=1).astype(np.int64);f[~anyh]=NEVER
 return f

def base_features(c,st):
 sx,sy=c['x'],c['y']; qx,qy=st['xy']; dx=qx-sx;dy=qy-sy;dist=math.hypot(dx,dy);ux=dx/max(dist,1e-6);uy=dy/max(dist,1e-6)
 # carrier half diagonal on the PMFS 0.3-m grid; geometry only.
 halfdiag=.5*.3*math.hypot(c['size_i'],c['size_j'])
 return np.array([sx,sy,qx,qy,dx,dy,dist,ux,uy,halfdiag,*st['route']],dtype=np.float32)

def dynamic_features(c,st):
 w=st['wind']; mean=w[:3]; dx=st['xy'][0]-c['x'];dy=st['xy'][1]-c['y'];d=max(math.hypot(dx,dy),1e-6);ux=dx/d;uy=dy/d
 along=mean[0]*ux+mean[1]*uy;perp=-mean[0]*uy+mean[1]*ux
 return np.concatenate([w,np.array([along,perp],dtype=np.float32)])

def build(args):
 root=args.audit_root
 cs=carrier_rows(root/'artifacts_pf_dei_v3/source_region_3d_support_manifest.csv'); split=source_split(cs)
 winds=read_wind(root/'artifacts_pf_dei_v3/wind_library/H01_wind35.bin')[30:35]
 schedules=[read_schedule(args.maponly_root/f'H01/reserved/trajectory_seed_{4001+i}.csv') for i in range(5)]
 stops=[stop_records(schedules[i],winds[i]) for i in range(5)]
 assert [len(s) for s in stops]==[10,10,10,9,10], [len(s) for s in stops]
 bank=root/'remote_full8/PF_DEI_H01_SOURCE_INFORMATION_AUDIT_20260829/predictive8'
 # labels[c][traj] = list stop arrays of 8 first-passage labels.
 labels=[[None]*5 for _ in cs]
 for ci,c in enumerate(cs):
  streams=[]
  for m in range(8): streams.append(read_stream(bank/f'member_{m:02d}/{c["id"]}.bin'))
  for tr in range(5):
   phys=np.stack([streams[m][tr] for m in range(8)])
   meas=sensor_batch(phys)
   labels[ci][tr]=[first_passage(meas,st['idx']) for st in stops[tr]]
  if (ci+1)%50==0: print(f'PREPROCESS {ci+1}/210',flush=True)
 # train dynamic mean is calculated without test trajectory/source.
 dyn_train=[]
 for ci in split['train']:
  for tr in TRAIN_TRAJ:
   for st in stops[tr]: dyn_train.append(dynamic_features(cs[ci],st))
 dyn_mean=np.mean(dyn_train,axis=0).astype(np.float32)
 def make(src_ids,trajs,static=False):
  X=[];Y=[];clusters=[]
  for ci in src_ids:
   for tr in trajs:
    for j,st in enumerate(stops[tr]):
     b=base_features(cs[ci],st); d=dyn_mean if static else dynamic_features(cs[ci],st)
     x=np.concatenate([b,d])
     for m,y in enumerate(labels[ci][tr][j]): X.append(x);Y.append(int(y));clusters.append((ci,tr,j,m))
  return np.asarray(X,np.float32),np.asarray(Y,np.int64),clusters
 sets={}
 for arm in ('conditional','static'):
  static=arm=='static'
  sets[arm]={
   'train':make(split['train'],TRAIN_TRAJ,static),
   'val':make(split['val'],VAL_TRAJ,static),
   'test':make(split['test'],TEST_TRAJ,static),
  }
 return cs,split,stops,dyn_mean,sets

class Field(nn.Module):
 def __init__(self,d):
  super().__init__(); self.net=nn.Sequential(nn.Linear(d,HIDDEN),nn.SiLU(),nn.Linear(HIDDEN,HIDDEN),nn.SiLU(),nn.Linear(HIDDEN,HIDDEN),nn.SiLU(),nn.Linear(HIDDEN,CLASSES))
 def forward(self,x): return self.net(x)

def fit(name,data,out):
 X,Y,_=data['train'];XV,YV,_=data['val']
 mean=X.mean(0);std=X.std(0);std[std<1e-6]=1
 X=(X-mean)/std;XV=(XV-mean)/std
 torch.manual_seed(SEED);model=Field(X.shape[1]);opt=torch.optim.AdamW(model.parameters(),lr=2e-3,weight_decay=1e-5)
 gen=torch.Generator().manual_seed(SEED); ds=torch.utils.data.TensorDataset(torch.from_numpy(X),torch.from_numpy(Y)); loader=torch.utils.data.DataLoader(ds,batch_size=BATCH,shuffle=True,generator=gen)
 best=1e99;best_epoch=-1;stale=0;history=[]
 for ep in range(MAX_EPOCHS):
  model.train();tot=n=0
  for xb,yb in loader:
   loss=nn.functional.cross_entropy(model(xb),yb);opt.zero_grad(set_to_none=True);loss.backward();opt.step();tot+=float(loss.detach())*len(xb);n+=len(xb)
  model.eval();vt=vn=0
  with torch.no_grad():
   for s in range(0,len(XV),BATCH): vt+=float(nn.functional.cross_entropy(model(torch.from_numpy(XV[s:s+BATCH])),torch.from_numpy(YV[s:s+BATCH]),reduction='sum'));vn+=len(XV[s:s+BATCH])
  val=vt/vn;history.append({'epoch':ep,'train_nll':tot/n,'val_nll':val})
  print(name,ep,tot/n,val,flush=True)
  if val<best-1e-5:
   best=val;best_epoch=ep;stale=0;torch.save({'state':model.state_dict(),'mean':torch.from_numpy(mean),'std':torch.from_numpy(std),'epoch':ep,'val_nll':val},out/f'{name}_best.pt')
  else:
   stale+=1
   if stale>=PATIENCE:break
 (out/f'{name}_history.json').write_text(json.dumps(history,indent=2)+'\n')
 ck=torch.load(out/f'{name}_best.pt',weights_only=True);model.load_state_dict(ck['state']);return model,ck

def predict(model,ck,X):
 mean=ck['mean'].numpy();std=ck['std'].numpy();X=((X-mean)/std).astype(np.float32);P=[];model.eval()
 with torch.no_grad():
  for s in range(0,len(X),BATCH):P.append(torch.softmax(model(torch.from_numpy(X[s:s+BATCH])),1).numpy())
 return np.concatenate(P)

def score(P,Y):
 p=np.clip(P,1e-12,1);nll=-np.log(p[np.arange(len(Y)),Y]);cdf=np.cumsum(P[:,:NEVER],axis=1);obs=(Y[:,None]<=np.arange(NEVER)[None,:]).astype(np.float32);brier=((cdf-obs)**2).mean(1);return nll,brier

def bootstrap(delta,clusters,nboot=5000):
 # cluster by source carrier to respect repeated stops/members.
 ids=np.array([c[0] for c in clusters]); uniq=np.unique(ids); vals=np.array([delta[ids==u].mean() for u in uniq]);rng=np.random.default_rng(SEED);means=np.empty(nboot)
 for i in range(nboot):means[i]=rng.choice(vals,len(vals),replace=True).mean()
 return float(vals.mean()),[float(x) for x in np.quantile(means,[.025,.975])]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 if args.output.exists():raise SystemExit('REFUSE_OVERWRITE')
 args.output.mkdir(parents=True);random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(4)
 cs,split,stops,dyn_mean,sets=build(args)
 contract={'contract':'CTT_H01_NEURAL_M1_FIRST_PASSAGE_PHYSICAL_GATE_V1','seed':SEED,'classes':CLASSES,'dt_s':DT,'stop_samples':STOP_SAMPLES,'threshold_ppm':TH,'source_split':{k:[cs[i]['id'] for i in v] for k,v in split.items()},'trajectory_split':{'train':[4001,4002,4003],'val':[4004],'test':[4005]},'training_objective':'categorical_first_passage_NLL_only','checkpoint_selection':'validation NLL only','forbidden':['source rank','localization error','PMFS posterior','planner outcome','future observation'],'arms':['conditional','static-wind capacity matched']}
 (args.output/'CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n')
 models={};cks={}
 for arm in ('conditional','static'):models[arm],cks[arm]=fit(arm,sets[arm],args.output)
 results={}
 raw={}
 for arm in ('conditional','static'):
  X,Y,C=sets[arm]['test'];P=predict(models[arm],cks[arm],X);n,b=score(P,Y);raw[arm]=(n,b,C,P,Y);results[arm]={'test_nll':float(n.mean()),'test_brier':float(b.mean()),'best_epoch':int(cks[arm]['epoch']),'val_nll':float(cks[arm]['val_nll']),'normalization_error':float(np.max(abs(P.sum(1)-1)))}
 dn=raw['static'][0]-raw['conditional'][0];db=raw['static'][1]-raw['conditional'][1]
 mn,nci=bootstrap(dn,raw['conditional'][2]);mb,bci=bootstrap(db,raw['conditional'][2])
 # Destructive context control: conditional model evaluated with dynamic features shuffled among test stop contexts, independently of candidate/source label.
 X,Y,C=sets['conditional']['test']; base_dim=X.shape[1]-len(dyn_mean); Xp=X.copy(); rng=np.random.default_rng(SEED+17); perm=rng.permutation(len(Xp));Xp[:,base_dim:]=Xp[perm,base_dim:]
 Pp=predict(models['conditional'],cks['conditional'],Xp);np_,bp=score(Pp,Y);dperm_n=np_-raw['conditional'][0];dperm_b=bp-raw['conditional'][1];mpn,pnci=bootstrap(dperm_n,C);mpb,pbci=bootstrap(dperm_b,C)
 gate={'conditional_beats_static_nll':nci[0]>0,'conditional_beats_static_brier':bci[0]>0,'context_shuffle_hurts_nll':pnci[0]>0,'normalization_pass':results['conditional']['normalization_error']<1e-6}
 summary={'contract':contract['contract'],'train_examples':len(sets['conditional']['train'][0]),'val_examples':len(sets['conditional']['val'][0]),'test_examples':len(sets['conditional']['test'][0]),'test_sources':len(split['test']),'test_trajectory':4005,'results':results,'static_minus_conditional_nll_cluster_mean':mn,'static_minus_conditional_nll_95ci':nci,'static_minus_conditional_brier_cluster_mean':mb,'static_minus_conditional_brier_95ci':bci,'context_shuffle_minus_conditional_nll_cluster_mean':mpn,'context_shuffle_minus_conditional_nll_95ci':pnci,'context_shuffle_minus_conditional_brier_cluster_mean':mpb,'context_shuffle_minus_conditional_brier_95ci':pbci,'gate':gate,'verdict':'CTT_H01_NEURAL_M1_PHYSICAL_GATE_PASS' if all(gate.values()) else 'CTT_H01_NEURAL_M1_PHYSICAL_GATE_NO_GO'}
 (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(args.output/'VERDICT.txt').write_text(summary['verdict']+'\n')
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
