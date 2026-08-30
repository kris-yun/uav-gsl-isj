#!/usr/bin/env python3
"""Frozen neural first-passage source-evidence gate on H01 trajectory4005/member7.

No neural training or checkpoint selection is performed here.  It consumes the
frozen geometry neural M1 checkpoint and frozen linear comparator.  For each of
210 synthetic source interventions, member7 provides the measured persistent-
sensor sequence on trajectory4005; every candidate is scored by the frozen
first-passage distribution over the ten complete physical stops.

Mandatory controls:
- survival-only (ever/never) removes arrival phase;
- within-stop sample permutation preserves hit count but destroys first passage;
- candidate phase-label shuffle preserves candidate survival but destroys the
  association between source coordinate and temporal phase distribution;
- linear field uses the same input/split but removes neural nonlinearity.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json
from pathlib import Path
import numpy as np, torch
from scipy.stats import binomtest
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('fw',HERE/'train_h01_neural_first_passage_fixedwind_gate.py');fw=importlib.util.module_from_spec(sp);sp.loader.exec_module(fw)
sl=importlib.util.spec_from_file_location('lc',HERE/'evaluate_h01_neural_m1_vs_linear_field.py');lc=importlib.util.module_from_spec(sl);sl.loader.exec_module(lc)
SEED=20260834

def digest(s):return hashlib.sha256(s.encode()).digest()
def rank(sc,t):
 x=sc[t];return float(1+np.count_nonzero(sc>x)+.5*(np.count_nonzero(sc==x)-1))
def sign(a,b):
 a=np.asarray(a);b=np.asarray(b);w=int((a<b).sum());l=int((a>b).sum());z=int((a==b).sum());n=w+l;return {'wins':w,'losses':l,'ties':z,'p':float(binomtest(w,n,.5,alternative='greater').pvalue) if n else 1.}
def summ(a):
 a=np.asarray(a);return {'mean_normalized_rank':float(((a-1)/209).mean()),'median_rank':float(np.median(a)),'top5':float((a<=5).mean()),'top10':float((a<=10).mean())}
def model_pred(model,ck,X):return fw.pred(model,ck,X)
def perm_first(binary,key):
 out=[]
 for j,row in enumerate(binary):
  rng=np.random.default_rng(int.from_bytes(digest(f'CTT-FROZEN-NM1-TIME|{key}|{j}')[:8],'big'));q=row[rng.permutation(len(row))];out.append(np.argmax(q) if q.any() else len(q))
 return np.array(out,int)
def scores(P,F):
 # P candidate x stop x 81; F stop labels.
 J=len(F);ii=np.arange(J);full=np.log(np.clip(P[:,ii,F],1e-12,1)).sum(1);pe=1-P[:,:,-1];ev=F<80;surv=np.where(ev[None,:],np.log(np.clip(pe,1e-12,1)),np.log(np.clip(1-pe,1e-12,1))).sum(1);phase=np.zeros_like(pe)
 for j in range(J):
  if ev[j]:phase[:,j]=np.log(np.clip(P[:,j,F[j]]/np.clip(pe[:,j],1e-12,1),1e-12,1))
 return full,surv,phase.sum(1)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--audit-root',type=Path,required=True);ap.add_argument('--maponly-root',type=Path,required=True);ap.add_argument('--neural-gate',type=Path,required=True);ap.add_argument('--linear-gate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);torch.set_num_threads(4)
 cs,rm,sets=fw.prepare(a);X,Y,C=sets['geometry']['test'];nstops=len(Y)//210;assert nstops==10;d=X.shape[1]
 nck=torch.load(a.neural_gate/'geometry_best.pt',weights_only=True);net=fw.Field(d);net.load_state_dict(nck['state']);Pn=model_pred(net,nck,X).reshape(210,nstops,81)
 lck=torch.load(a.linear_gate/'linear_best.pt',weights_only=True);lin=lc.Linear(d);lin.load_state_dict(lck['state']);Pl=lc.pred(lin,lck,X).reshape(210,nstops,81)
 # Reconstruct the exact member7 measured binary tape with run-persistent sensor state.
 schedule=fw.b.read_schedule(a.maponly_root/'H01/reserved/trajectory_seed_4005.csv');dummy=np.zeros((len(schedule),3),np.float32);stops=fw.b.stop_records(schedule,dummy);bank=a.audit_root/'remote_full8/PF_DEI_H01_SOURCE_INFORMATION_AUDIT_20260829/predictive8'
 F=[];B=[]
 for ci,c in enumerate(cs):
  phys=fw.b.read_stream(bank/f'member_07/{c["id"]}.bin')[4][None,:];meas=fw.b.sensor_batch(phys)[0];bb=np.stack([(meas[st['idx']]>fw.b.TH) for st in stops]);B.append(bb);F.append(np.array([np.argmax(q) if q.any() else 80 for q in bb],int))
 rows=[];labperm=np.random.default_rng(SEED).permutation(210)
 for truth in range(210):
  fn,sv,ph=scores(Pn,F[truth]);fl,_,_=scores(Pl,F[truth]);fp=perm_first(B[truth],cs[truth]['id']);fperm,_,_=scores(Pn,fp);flab=sv+ph[labperm]
  rows.append({'truth':truth,'carrier_id':cs[truth]['id'],'rank_neural_full':rank(fn,truth),'rank_survival':rank(sv,truth),'rank_time_permute':rank(fperm,truth),'rank_phase_label_shuffle':rank(flab,truth),'rank_linear_full':rank(fl,truth)})
 with open(a.output/'cases.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 keys=['rank_neural_full','rank_survival','rank_time_permute','rank_phase_label_shuffle','rank_linear_full'];A={k:np.array([r[k] for r in rows]) for k in keys};S={k:summ(A[k]) for k in keys};C={'neural_vs_survival':sign(A['rank_neural_full'],A['rank_survival']),'neural_vs_time_permute':sign(A['rank_neural_full'],A['rank_time_permute']),'neural_vs_phase_label_shuffle':sign(A['rank_neural_full'],A['rank_phase_label_shuffle']),'neural_vs_linear':sign(A['rank_neural_full'],A['rank_linear_full'])};g={'first_passage_beats_survival':S['rank_neural_full']['mean_normalized_rank']<S['rank_survival']['mean_normalized_rank'] and C['neural_vs_survival']['p']<=.01,'top10_non_degrade_vs_survival':S['rank_neural_full']['top10']>=S['rank_survival']['top10'],'time_load_bearing':S['rank_neural_full']['mean_normalized_rank']<S['rank_time_permute']['mean_normalized_rank'] and C['neural_vs_time_permute']['p']<=.01,'candidate_phase_load_bearing':S['rank_neural_full']['mean_normalized_rank']<S['rank_phase_label_shuffle']['mean_normalized_rank'] and C['neural_vs_phase_label_shuffle']['p']<=.01,'neural_nonlinearity_load_bearing':S['rank_neural_full']['mean_normalized_rank']<S['rank_linear_full']['mean_normalized_rank'] and C['neural_vs_linear']['p']<=.01};R={'contract':'CTT_H01_FROZEN_NEURAL_FIRST_PASSAGE_SOURCE_EVIDENCE_V1','neural_checkpoint':'frozen geometry_best.pt','linear_checkpoint':'frozen linear_best.pt','test':'trajectory4005/member7, all 210 synthetic source interventions','summary':S,'comparisons':C,'gate':g,'verdict':'CTT_H01_FROZEN_NEURAL_FIRST_PASSAGE_SOURCE_EVIDENCE_PASS' if all(g.values()) else 'CTT_H01_FROZEN_NEURAL_FIRST_PASSAGE_SOURCE_EVIDENCE_NO_GO'};(a.output/'summary.json').write_text(json.dumps(R,indent=2)+'\n');(a.output/'VERDICT.txt').write_text(R['verdict']+'\n');print(json.dumps(R,indent=2))
if __name__=='__main__':main()
