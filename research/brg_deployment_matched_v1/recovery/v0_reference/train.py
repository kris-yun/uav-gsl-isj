#!/usr/bin/env python3
"""Train an OPEN development model, not a scientific confirmation.

Fixed architecture, seed and optimization configuration. Save last plus
source-only development-loss selected checkpoint. Never use closed-loop test
outcomes to select it. Runtime requires an explicit flag for warm-start weights.
"""
import argparse,json,sys,time,random,hashlib
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pmfs_brg.model import CandidateBRG,ModelConfig,save_checkpoint
from pmfs_brg.data import OpenPaths, LoggedEpisodes
from pmfs_brg.features import FeatureConfig
from dataclasses import asdict

def evaluate(model,loader):
    model.eval(); loss=0;correct=0;n=0;brier=0.
    with torch.no_grad():
        for o,c,y in loader:
            z=model(o,c)[:,-1];p=z.softmax(-1)
            loss+=torch.nn.functional.cross_entropy(z,y,reduction='sum').item()
            correct+=(z.argmax(-1)==y).sum().item();n+=len(y)
            brier+=((p-torch.nn.functional.one_hot(y,z.shape[-1]))**2).sum().item()
    return dict(nll=loss/n,accuracy=correct/n,brier=brier/n,n_sparse_augmentations=n)

def main():
 ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--data');g.add_argument('--episodes');ap.add_argument('--out',required=True);ap.add_argument('--variant',choices=['brg','ungated','gru'],default='brg');ap.add_argument('--epochs',type=int,default=30);ap.add_argument('--hidden',type=int,default=32);ap.add_argument('--routes',type=int,default=8);ap.add_argument('--batch',type=int,default=48);ap.add_argument('--threads',type=int,default=2);ap.add_argument('--seed',type=int,default=2026092701);a=ap.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 torch.set_num_threads(a.threads);torch.manual_seed(a.seed);np.random.seed(a.seed);random.seed(a.seed);torch.use_deterministic_algorithms(True)
 fcfg=FeatureConfig()
 if a.episodes:
  train=LoggedEpisodes(a.episodes,'train',fcfg);dev=LoggedEpisodes(a.episodes,'dev',fcfg);a.batch=1
 else:
  train=OpenPaths(a.data,'train',a.routes,a.seed,fcfg);dev=OpenPaths(a.data,'dev',max(2,a.routes//2),a.seed,fcfg)
 if train.groups&dev.groups:raise RuntimeError('plume leakage')
 gen=torch.Generator().manual_seed(a.seed)
 tr=DataLoader(train,batch_size=a.batch,shuffle=True,generator=gen);dv=DataLoader(dev,batch_size=a.batch)
 model=CandidateBRG(ModelConfig(hidden=a.hidden,variant=a.variant));opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4)
 meta={'deployment_status':'OPEN_WARMSTART_NOT_VALIDATED_CLOSED_LOOP','feature_config':asdict(fcfg),'variant':a.variant,'training_args':vars(a),'training_groups':sorted(train.groups),'development_groups':sorted(dev.groups),'training_candidate_count': 'variable_per_episode' if a.episodes else 6,'weights_selected_on':'OPEN dev final-prefix NLL, not a new test','input_manifest_sha256':hashlib.sha256((Path(a.episodes) if a.episodes else Path(a.data)/'manifest.json').read_bytes()).hexdigest(),'parameter_count':model.parameter_count,'active_parameter_count':model.active_parameter_count,'temperature':1.0,'max_tested_history':max(len(x[0]) for x in train.items)}
 (out/'run_config.json').write_text(json.dumps(meta,indent=2));(out/'routes.json').write_text(json.dumps({'train':train.routes,'dev':dev.routes}))
 history=[];best=float('inf');start=time.time()
 initial=evaluate(model,dv);print('initial',initial,flush=True)
 for epoch in range(1,a.epochs+1):
  model.train();total=0;n=0
  for o,c,y in tr:
   opt.zero_grad(set_to_none=True);z=model(o,c);target=y[:,None].expand(-1,z.shape[1])
   loss=torch.nn.functional.cross_entropy(z.reshape(-1,z.shape[-1]),target.reshape(-1))
   if not torch.isfinite(loss):raise RuntimeError('nonfinite loss, no automatic recovery')
   loss.backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True);opt.step();total+=loss.item()*len(y);n+=len(y)
  metrics=evaluate(model,dv);row=dict(epoch=epoch,train_prefix_nll=total/n,**metrics);history.append(row)
  print(json.dumps(row),flush=True)
  if metrics['nll']<best:
   best=metrics['nll'];save_checkpoint(out/'best.pt',model,{**meta,'epoch':epoch,'dev':metrics})
  (out/'history.json').write_text(json.dumps(history,indent=2))
 save_checkpoint(out/'last.pt',model,{**meta,'epoch':a.epochs,'dev':metrics})
 summary={'initial':initial,'last':metrics,'best_dev_nll':best,'seconds':time.time()-start,'parameters':model.parameter_count,'active_parameters':model.active_parameter_count,'independent_train_plumes':len(train.groups),'independent_dev_plumes':len(dev.groups),'status':'TRAINING_PIPELINE_COMPLETED_NOT_SCIENTIFIC_PASS'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
