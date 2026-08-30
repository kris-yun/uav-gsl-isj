#!/usr/bin/env python3
"""H01 fixed-forward-wind neural first-passage gate.

The H01 predictive8 materializer accepts one fixed native --wind input for all
reserved trajectories.  Therefore trajectory-specific H01_wind35 estimates are
NOT parents of this predictive bank and are forbidden in this corrected gate.

This gate tests the remaining temporal causal state that *is* present in the
native data: source/query geometry, absolute simulation time, route history and
persistent-sensor history.  The network predicts an 81-class first-passage
(0..79 native 0.2-s bins + never) distribution.  A capacity-matched
GEOMETRY-ONLY arm receives the same vector dimension but route/time features
are replaced by their training mean.

Frozen split follows the original CTT M1 contract:
train trajectories 4001..4003 / members 0..5;
validation trajectory 4004 / member 6;
test trajectory 4005 / member 7;
all 210 fixed source-query carriers are the known deployment grid.
"""
from __future__ import annotations
import argparse,json,random,importlib.util
from pathlib import Path
import numpy as np, torch
from torch import nn
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('base',HERE/'train_h01_neural_first_passage_m1.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
TRAIN_TRAJ=(0,1,2);VAL_TRAJ=(3,);TEST_TRAJ=(4,);TRAIN_MEM=(0,1,2,3,4,5);VAL_MEM=(6,);TEST_MEM=(7,)
SEED=20260832;BATCH=2048;MAX_EPOCHS=40;PATIENCE=6
GEOM_DIM=10;ROUTE_DIM=6

def prepare(a):
 root=a.audit_root;cs=b.carrier_rows(root/'artifacts_pf_dei_v3/source_region_3d_support_manifest.csv')
 # Schedule only.  No H01_wind35 feature is used because it was not the native
 # fixed wind input used by predictive8 generation.
 schedules=[b.read_schedule(a.maponly_root/f'H01/reserved/trajectory_seed_{4001+i}.csv') for i in range(5)]
 dummy=[np.zeros((len(x),3),np.float32) for x in schedules]
 stops=[b.stop_records(schedules[i],dummy[i]) for i in range(5)];assert [len(x) for x in stops]==[10,10,10,9,10]
 bank=root/'remote_full8/PF_DEI_H01_SOURCE_INFORMATION_AUDIT_20260829/predictive8';labels=[[None]*5 for _ in cs]
 for ci,c in enumerate(cs):
  ss=[b.read_stream(bank/f'member_{m:02d}/{c["id"]}.bin') for m in range(8)]
  for tr in range(5):
   meas=b.sensor_batch(np.stack([ss[m][tr] for m in range(8)]));labels[ci][tr]=[b.first_passage(meas,st['idx']) for st in stops[tr]]
  if (ci+1)%50==0:print(f'PREPROCESS {ci+1}/210',flush=True)
 route_train=np.array([b.base_features(c,st)[GEOM_DIM:] for c in cs for tr in TRAIN_TRAJ for st in stops[tr]],np.float32);route_mean=route_train.mean(0)
 def make(trajs,members,static):
  X=[];Y=[];C=[]
  for ci,c in enumerate(cs):
   for tr in trajs:
    for j,st in enumerate(stops[tr]):
     z=b.base_features(c,st).copy();assert len(z)==GEOM_DIM+ROUTE_DIM
     if static:z[GEOM_DIM:]=route_mean
     for m in members:X.append(z);Y.append(int(labels[ci][tr][j][m]));C.append((ci,tr,j,m))
  return np.asarray(X,np.float32),np.asarray(Y,np.int64),C
 return cs,route_mean,{arm:{'train':make(TRAIN_TRAJ,TRAIN_MEM,arm=='geometry'),'val':make(VAL_TRAJ,VAL_MEM,arm=='geometry'),'test':make(TEST_TRAJ,TEST_MEM,arm=='geometry')} for arm in ('temporal','geometry')}

class Field(b.Field):pass

def fit(name,d,out):
 X,Y,_=d['train'];XV,YV,_=d['val'];mean=X.mean(0);std=X.std(0);std[std<1e-6]=1;X=(X-mean)/std;XV=(XV-mean)/std
 torch.manual_seed(SEED);m=Field(X.shape[1]);opt=torch.optim.AdamW(m.parameters(),lr=2e-3,weight_decay=1e-5);gen=torch.Generator().manual_seed(SEED)
 loader=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.from_numpy(X),torch.from_numpy(Y)),batch_size=BATCH,shuffle=True,generator=gen)
 best=1e99;stale=0;hist=[]
 for ep in range(MAX_EPOCHS):
  m.train();tot=n=0
  for xb,yb in loader:
   loss=nn.functional.cross_entropy(m(xb),yb);opt.zero_grad(set_to_none=True);loss.backward();opt.step();tot+=float(loss.detach())*len(xb);n+=len(xb)
  m.eval();vt=0
  with torch.no_grad():
   for s in range(0,len(XV),BATCH):vt+=float(nn.functional.cross_entropy(m(torch.from_numpy(XV[s:s+BATCH])),torch.from_numpy(YV[s:s+BATCH]),reduction='sum'))
  val=vt/len(XV);hist.append({'epoch':ep,'train_nll':tot/n,'val_nll':val});print(name,ep,tot/n,val,flush=True)
  if val<best-1e-5:best=val;stale=0;torch.save({'state':m.state_dict(),'mean':torch.from_numpy(mean),'std':torch.from_numpy(std),'epoch':ep,'val_nll':val},out/f'{name}_best.pt')
  else:
   stale+=1
   if stale>=PATIENCE:break
 (out/f'{name}_history.json').write_text(json.dumps(hist,indent=2)+'\n');ck=torch.load(out/f'{name}_best.pt',weights_only=True);m.load_state_dict(ck['state']);return m,ck

def pred(m,ck,X):
 X=((X-ck['mean'].numpy())/ck['std'].numpy()).astype(np.float32);r=[];m.eval()
 with torch.no_grad():
  for s in range(0,len(X),BATCH):r.append(torch.softmax(m(torch.from_numpy(X[s:s+BATCH])),1).numpy())
 return np.concatenate(r)
def scores(P,Y):
 p=np.clip(P,1e-12,1);n=-np.log(p[np.arange(len(Y)),Y]);cdf=np.cumsum(P[:,:b.NEVER],1);o=(Y[:,None]<=np.arange(b.NEVER)[None,:]).astype(np.float32);return n,((cdf-o)**2).mean(1)
def boot(d,C,N=5000):
 ids=np.array([x[0] for x in C]);v=np.array([d[ids==u].mean() for u in np.unique(ids)]);rng=np.random.default_rng(SEED);z=np.array([rng.choice(v,len(v),replace=True).mean() for _ in range(N)]);return float(v.mean()),[float(x) for x in np.quantile(z,[.025,.975])]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.output.exists():raise SystemExit('REFUSE_OVERWRITE')
 a.output.mkdir(parents=True);random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(4);cs,rm,sets=prepare(a)
 (a.output/'CONTRACT.json').write_text(json.dumps({'contract':'CTT_H01_FIXEDWIND_TEMPORAL_FIRST_PASSAGE_GATE_V1','forward_wind_semantics':'single fixed native --wind input across 4001..4005; trajectory local wind forbidden','trajectory_split':{'train':[4001,4002,4003],'val':[4004],'test':[4005]},'transport_split':{'train':[0,1,2,3,4,5],'val':[6],'test':[7]},'arms':['temporal route/time','geometry-only capacity matched'],'objective':'simulator first-passage categorical NLL only'},indent=2)+'\n')
 mods={};cks={}
 for arm in ('temporal','geometry'):mods[arm],cks[arm]=fit(arm,sets[arm],a.output)
 raw={};res={}
 for arm in ('temporal','geometry'):
  X,Y,C=sets[arm]['test'];P=pred(mods[arm],cks[arm],X);n,br=scores(P,Y);raw[arm]=(n,br,C,P,Y);res[arm]={'test_nll':float(n.mean()),'test_brier':float(br.mean()),'val_nll':float(cks[arm]['val_nll']),'best_epoch':int(cks[arm]['epoch']),'normalization_error':float(np.max(abs(P.sum(1)-1)))}
 dn=raw['geometry'][0]-raw['temporal'][0];db=raw['geometry'][1]-raw['temporal'][1];mn,nci=boot(dn,raw['temporal'][2]);mb,bci=boot(db,raw['temporal'][2])
 X,Y,C=sets['temporal']['test'];Xp=X.copy();rng=np.random.default_rng(SEED+17);perm=rng.permutation(len(Xp));Xp[:,GEOM_DIM:]=Xp[perm,GEOM_DIM:];Pp=pred(mods['temporal'],cks['temporal'],Xp);np_,bp=scores(Pp,Y);mp,pci=boot(np_-raw['temporal'][0],C)
 gate={'temporal_beats_geometry_nll':nci[0]>0,'temporal_beats_geometry_brier':bci[0]>0,'route_time_shuffle_hurts_nll':pci[0]>0,'normalization':res['temporal']['normalization_error']<1e-6};R={'contract':'CTT_H01_FIXEDWIND_TEMPORAL_FIRST_PASSAGE_GATE_V1','results':res,'geometry_minus_temporal_nll':mn,'nll_95ci':nci,'geometry_minus_temporal_brier':mb,'brier_95ci':bci,'route_time_shuffle_minus_temporal_nll':mp,'route_time_shuffle_nll_95ci':pci,'gate':gate,'verdict':'CTT_H01_FIXEDWIND_TEMPORAL_FIRST_PASSAGE_PASS' if all(gate.values()) else 'CTT_H01_FIXEDWIND_TEMPORAL_FIRST_PASSAGE_NO_GO'};(a.output/'summary.json').write_text(json.dumps(R,indent=2)+'\n');(a.output/'VERDICT.txt').write_text(R['verdict']+'\n');print(json.dumps(R,indent=2))
if __name__=='__main__':main()
