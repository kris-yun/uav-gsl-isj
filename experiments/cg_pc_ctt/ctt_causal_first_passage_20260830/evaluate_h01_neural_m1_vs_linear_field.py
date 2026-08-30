#!/usr/bin/env python3
"""Frozen H01 geometry neural-field vs linear-softmax comparator.

No neural retraining occurs.  The already frozen geometry neural M1 checkpoint
from CTT_H01_FIXEDWIND_TEMPORAL_FIRST_PASSAGE_GATE_V1 is compared against a
linear 81-class softmax model trained/selected on the identical simulator-only
train/validation split and identical geometry input.  Test is trajectory4005,
transport member7.  Primary scores: categorical NLL and integrated Brier.
"""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path
import numpy as np, torch
from torch import nn
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('fw',HERE/'train_h01_neural_first_passage_fixedwind_gate.py');fw=importlib.util.module_from_spec(sp);sp.loader.exec_module(fw)
SEED=20260833;BATCH=2048;MAX_EPOCHS=100;PATIENCE=10
class Linear(nn.Module):
 def __init__(self,d):super().__init__();self.fc=nn.Linear(d,fw.b.CLASSES)
 def forward(self,x):return self.fc(x)
def fit(d,out):
 X,Y,_=d['train'];XV,YV,_=d['val'];mean=X.mean(0);std=X.std(0);std[std<1e-6]=1;X=(X-mean)/std;XV=(XV-mean)/std
 torch.manual_seed(SEED);m=Linear(X.shape[1]);opt=torch.optim.AdamW(m.parameters(),lr=3e-3,weight_decay=1e-5);g=torch.Generator().manual_seed(SEED);dl=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(torch.from_numpy(X),torch.from_numpy(Y)),batch_size=BATCH,shuffle=True,generator=g)
 best=1e99;stale=0;hist=[]
 for ep in range(MAX_EPOCHS):
  m.train();tot=n=0
  for xb,yb in dl:
   l=nn.functional.cross_entropy(m(xb),yb);opt.zero_grad(set_to_none=True);l.backward();opt.step();tot+=float(l.detach())*len(xb);n+=len(xb)
  m.eval();vt=0
  with torch.no_grad():
   for s in range(0,len(XV),BATCH):vt+=float(nn.functional.cross_entropy(m(torch.from_numpy(XV[s:s+BATCH])),torch.from_numpy(YV[s:s+BATCH]),reduction='sum'))
  v=vt/len(XV);hist.append({'epoch':ep,'train_nll':tot/n,'val_nll':v})
  if ep%5==0:print('linear',ep,tot/n,v,flush=True)
  if v<best-1e-6:best=v;stale=0;torch.save({'state':m.state_dict(),'mean':torch.from_numpy(mean),'std':torch.from_numpy(std),'epoch':ep,'val_nll':v},out/'linear_best.pt')
  else:
   stale+=1
   if stale>=PATIENCE:break
 (out/'linear_history.json').write_text(json.dumps(hist,indent=2)+'\n');ck=torch.load(out/'linear_best.pt',weights_only=True);m.load_state_dict(ck['state']);return m,ck
def pred(m,ck,X):
 X=((X-ck['mean'].numpy())/ck['std'].numpy()).astype(np.float32);r=[];m.eval()
 with torch.no_grad():
  for s in range(0,len(X),BATCH):r.append(torch.softmax(m(torch.from_numpy(X[s:s+BATCH])),1).numpy())
 return np.concatenate(r)
def boot(d,C,N=5000):
 ids=np.array([x[0] for x in C]);v=np.array([d[ids==u].mean() for u in np.unique(ids)]);rng=np.random.default_rng(SEED);z=np.array([rng.choice(v,len(v),replace=True).mean() for _ in range(N)]);return float(v.mean()),[float(x) for x in np.quantile(z,[.025,.975])]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--frozen-gate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);torch.set_num_threads(4);np.random.seed(SEED);torch.manual_seed(SEED)
 cs,rm,sets=fw.prepare(a);D=sets['geometry'];lin,lck=fit(D,a.output)
 nck=torch.load(a.frozen_gate/'geometry_best.pt',weights_only=True);net=fw.Field(D['train'][0].shape[1]);net.load_state_dict(nck['state'])
 X,Y,C=D['test'];Pl=pred(lin,lck,X);Pn=fw.pred(net,nck,X);nl,bl=fw.scores(Pl,Y);nn,bn=fw.scores(Pn,Y);mn,nci=boot(nl-nn,C);mb,bci=boot(bl-bn,C)
 gate={'neural_beats_linear_nll':nci[0]>0,'neural_beats_linear_brier':bci[0]>0,'normalization':float(np.max(abs(Pn.sum(1)-1)))<1e-6};R={'contract':'CTT_H01_NEURAL_M1_NONLINEAR_FIELD_INCREMENT_V1','frozen_neural_checkpoint':'geometry_best.pt from fixedwind gate; no neural retraining','linear':{'val_nll':float(lck['val_nll']),'best_epoch':int(lck['epoch']),'test_nll':float(nl.mean()),'test_brier':float(bl.mean())},'neural':{'val_nll':float(nck['val_nll']),'best_epoch':int(nck['epoch']),'test_nll':float(nn.mean()),'test_brier':float(bn.mean())},'linear_minus_neural_nll':mn,'nll_95ci':nci,'linear_minus_neural_brier':mb,'brier_95ci':bci,'gate':gate,'verdict':'CTT_H01_NEURAL_NONLINEAR_FIELD_INCREMENT_PASS' if all(gate.values()) else 'CTT_H01_NEURAL_NONLINEAR_FIELD_INCREMENT_NO_GO'};(a.output/'summary.json').write_text(json.dumps(R,indent=2)+'\n');(a.output/'VERDICT.txt').write_text(R['verdict']+'\n');print(json.dumps(R,indent=2))
if __name__=='__main__':main()
