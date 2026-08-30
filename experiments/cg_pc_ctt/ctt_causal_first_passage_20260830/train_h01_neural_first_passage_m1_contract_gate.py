#!/usr/bin/env python3
"""Contract-correct H01 neural M1 physical gate.

Restores the original CTT-V13 M1 identification contract: the fixed House
candidate grid is a known physical query domain, while *complete wind/route
contexts* and *complete transport keys* are held out.  This is the deployment
contract for a pre-trained first-passage solver surrogate in a known map.

Splits are frozen:
  train trajectories 4001..4003, transport members 0..5;
  validation trajectory 4004, member 6;
  test trajectory 4005, member 7.
All 210 source carriers are present as physical query points in every split.
No source rank/localization/posterior signal is used.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
import numpy as np, torch
from torch import nn
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('m1base',HERE/'train_h01_neural_first_passage_m1.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
TRAIN_TRAJ=(0,1,2); VAL_TRAJ=(3,); TEST_TRAJ=(4,)
TRAIN_MEM=(0,1,2,3,4,5); VAL_MEM=(6,); TEST_MEM=(7,)
SEED=20260831; BATCH=2048; MAX_EPOCHS=40; PATIENCE=6

def prepare(args):
 root=args.audit_root; cs=b.carrier_rows(root/'artifacts_pf_dei_v3/source_region_3d_support_manifest.csv')
 winds=b.read_wind(root/'artifacts_pf_dei_v3/wind_library/H01_wind35.bin')[30:35]
 schedules=[b.read_schedule(args.maponly_root/f'H01/reserved/trajectory_seed_{4001+i}.csv') for i in range(5)]
 stops=[b.stop_records(schedules[i],winds[i]) for i in range(5)];assert [len(x) for x in stops]==[10,10,10,9,10]
 bank=root/'remote_full8/PF_DEI_H01_SOURCE_INFORMATION_AUDIT_20260829/predictive8'
 labels=[[None]*5 for _ in cs]
 for ci,c in enumerate(cs):
  streams=[b.read_stream(bank/f'member_{m:02d}/{c["id"]}.bin') for m in range(8)]
  for tr in range(5):
   meas=b.sensor_batch(np.stack([streams[m][tr] for m in range(8)]))
   labels[ci][tr]=[b.first_passage(meas,st['idx']) for st in stops[tr]]
  if (ci+1)%50==0:print(f'PREPROCESS {ci+1}/210',flush=True)
 dyn=[]
 for ci in range(210):
  for tr in TRAIN_TRAJ:
   for st in stops[tr]:dyn.append(b.dynamic_features(cs[ci],st))
 dyn_mean=np.mean(dyn,axis=0).astype(np.float32)
 def make(trajs,members,static):
  X=[];Y=[];C=[]
  for ci,c in enumerate(cs):
   for tr in trajs:
    for j,st in enumerate(stops[tr]):
     dd=dyn_mean if static else b.dynamic_features(c,st);x=np.concatenate([b.base_features(c,st),dd])
     for m in members:X.append(x);Y.append(int(labels[ci][tr][j][m]));C.append((ci,tr,j,m))
  return np.asarray(X,np.float32),np.asarray(Y,np.int64),C
 return cs,dyn_mean,{arm:{'train':make(TRAIN_TRAJ,TRAIN_MEM,arm=='static'),'val':make(VAL_TRAJ,VAL_MEM,arm=='static'),'test':make(TEST_TRAJ,TEST_MEM,arm=='static')} for arm in ('conditional','static')}

class Field(b.Field):pass

def fit(name,data,out):
 X,Y,_=data['train'];XV,YV,_=data['val'];mean=X.mean(0);std=X.std(0);std[std<1e-6]=1;X=(X-mean)/std;XV=(XV-mean)/std
 torch.manual_seed(SEED);m=Field(X.shape[1]);opt=torch.optim.AdamW(m.parameters(),lr=2e-3,weight_decay=1e-5);gen=torch.Generator().manual_seed(SEED)
 loader=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.from_numpy(X),torch.from_numpy(Y)),batch_size=BATCH,shuffle=True,generator=gen)
 best=1e99;stale=0;hist=[]
 for ep in range(MAX_EPOCHS):
  m.train();tot=n=0
  for xb,yb in loader:
   loss=nn.functional.cross_entropy(m(xb),yb);opt.zero_grad(set_to_none=True);loss.backward();opt.step();tot+=float(loss.detach())*len(xb);n+=len(xb)
  m.eval();vt=vn=0
  with torch.no_grad():
   for s in range(0,len(XV),BATCH):vt+=float(nn.functional.cross_entropy(m(torch.from_numpy(XV[s:s+BATCH])),torch.from_numpy(YV[s:s+BATCH]),reduction='sum'));vn+=len(XV[s:s+BATCH])
  val=vt/vn;hist.append({'epoch':ep,'train_nll':tot/n,'val_nll':val});print(name,ep,tot/n,val,flush=True)
  if val<best-1e-5:
   best=val;stale=0;torch.save({'state':m.state_dict(),'mean':torch.from_numpy(mean),'std':torch.from_numpy(std),'epoch':ep,'val_nll':val},out/f'{name}_best.pt')
  else:
   stale+=1
   if stale>=PATIENCE:break
 (out/f'{name}_history.json').write_text(json.dumps(hist,indent=2)+'\n');ck=torch.load(out/f'{name}_best.pt',weights_only=True);m.load_state_dict(ck['state']);return m,ck

def predict(m,ck,X):
 X=((X-ck['mean'].numpy())/ck['std'].numpy()).astype(np.float32);q=[];m.eval()
 with torch.no_grad():
  for s in range(0,len(X),BATCH):q.append(torch.softmax(m(torch.from_numpy(X[s:s+BATCH])),1).numpy())
 return np.concatenate(q)

def scores(P,Y):
 p=np.clip(P,1e-12,1);n=-np.log(p[np.arange(len(Y)),Y]);cdf=np.cumsum(P[:,:b.NEVER],1);obs=(Y[:,None]<=np.arange(b.NEVER)[None,:]).astype(np.float32);br=((cdf-obs)**2).mean(1);return n,br

def boot(d,C,nboot=5000):
 ids=np.array([x[0] for x in C]);vals=np.array([d[ids==u].mean() for u in np.unique(ids)]);rng=np.random.default_rng(SEED);z=np.array([rng.choice(vals,len(vals),replace=True).mean() for _ in range(nboot)]);return float(vals.mean()),[float(x) for x in np.quantile(z,[.025,.975])]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.output.exists():raise SystemExit('REFUSE_OVERWRITE');
 a.output.mkdir(parents=True);random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(4)
 cs,dm,sets=prepare(a);(a.output/'CONTRACT.json').write_text(json.dumps({'contract':'CTT_H01_NEURAL_M1_ORIGINAL_IDENTIFICATION_GATE_V1','trajectory_split':{'train':[4001,4002,4003],'val':[4004],'test':[4005]},'transport_split':{'train':[0,1,2,3,4,5],'val':[6],'test':[7]},'source_grid':'all 210 fixed physical query carriers in every split','checkpoint':'validation first-passage NLL only','objective':'simulator first-passage categorical NLL only'},indent=2)+'\n')
 mods={};cks={}
 for arm in ('conditional','static'):mods[arm],cks[arm]=fit(arm,sets[arm],a.output)
 raw={};res={}
 for arm in ('conditional','static'):
  X,Y,C=sets[arm]['test'];P=predict(mods[arm],cks[arm],X);n,br=scores(P,Y);raw[arm]=(n,br,C,P,Y);res[arm]={'test_nll':float(n.mean()),'test_brier':float(br.mean()),'val_nll':float(cks[arm]['val_nll']),'best_epoch':int(cks[arm]['epoch']),'normalization_error':float(np.max(np.abs(P.sum(1)-1)))}
 dn=raw['static'][0]-raw['conditional'][0];db=raw['static'][1]-raw['conditional'][1];mn,nci=boot(dn,raw['conditional'][2]);mb,bci=boot(db,raw['conditional'][2])
 X,Y,C=sets['conditional']['test'];base_dim=X.shape[1]-len(dm);Xp=X.copy();rng=np.random.default_rng(SEED+17);perm=rng.permutation(len(Xp));Xp[:,base_dim:]=Xp[perm,base_dim:];Pp=predict(mods['conditional'],cks['conditional'],Xp);np_,bp=scores(Pp,Y);mp,pci=boot(np_-raw['conditional'][0],C)
 gate={'conditional_beats_static_nll':nci[0]>0,'conditional_beats_static_brier':bci[0]>0,'context_shuffle_hurts_nll':pci[0]>0,'normalization':res['conditional']['normalization_error']<1e-6}
 summary={'contract':'CTT_H01_NEURAL_M1_ORIGINAL_IDENTIFICATION_GATE_V1','results':res,'static_minus_conditional_nll':mn,'nll_95ci':nci,'static_minus_conditional_brier':mb,'brier_95ci':bci,'context_shuffle_minus_conditional_nll':mp,'context_shuffle_nll_95ci':pci,'gate':gate,'verdict':'CTT_H01_NEURAL_M1_ORIGINAL_CONTRACT_PASS' if all(gate.values()) else 'CTT_H01_NEURAL_M1_ORIGINAL_CONTRACT_NO_GO'}
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(a.output/'VERDICT.txt').write_text(summary['verdict']+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
