#!/usr/bin/env python3
import importlib.util,json,argparse
from pathlib import Path
import numpy as np, torch
spec=importlib.util.spec_from_file_location('m1','/mnt/data/ctt_final/train_h01_neural_first_passage_m1.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def model_ck(out,name,d):
 ck=torch.load(out/f'{name}_best.pt',weights_only=True); q=m.Field(d);q.load_state_dict(ck['state']);return q,ck

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--gate-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 cs,sp,stops,dm,sets=m.build(a)
 d=sets['conditional']['train'][0].shape[1]; mc,cc=model_ck(a.gate_root,'conditional',d);ms,cs_=model_ck(a.gate_root,'static',d)
 # rebuild trajectory4005 for each frozen source split with unchanged preprocessing; no fitting.
 # reuse internal labels by re-calling build only exposes standard sets, so aggregate the existing test and
 # use 4004 val as second held condition. Train-source 4005 is intentionally not constructed here.
 out={}
 for splitname,dset in [('heldout_source_traj4005', 'test'),('heldout_source_traj4004','val')]:
  Xc,Y,C=sets['conditional'][dset];Xs=sets['static'][dset][0]
  pc=m.predict(mc,cc,Xc);ps=m.predict(ms,cs_,Xs);nc,bc=m.score(pc,Y);ns,bs=m.score(ps,Y)
  mn,nci=m.bootstrap(ns-nc,C);mb,bci=m.bootstrap(bs-bc,C)
  out[splitname]={'conditional_nll':float(nc.mean()),'static_nll':float(ns.mean()),'static_minus_conditional_nll':mn,'nll_95ci':nci,'conditional_brier':float(bc.mean()),'static_brier':float(bs.mean()),'static_minus_conditional_brier':mb,'brier_95ci':bci}
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
