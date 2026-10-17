"""Leave-one-stop-out intervention on native contact log odds; fixed confidence/forward/owner.
This measures contribution to the working score, not the physical effect of a new trajectory.
"""
from pathlib import Path
import csv,json
import numpy as np
from parameters import read_parameters
R=Path(__file__).resolve().parents[1];P=R.parent/'NATIVE_PMFS_WIND_RECOVERY_20261014/PORTABLE_DATA';O=R/'results';entries=json.loads((P/'CASE_INDEX.json').read_text())['cases'];controls=json.loads((O/'STRONG_CONTROLS.json').read_text());rows=[]
for e in entries:
 c=e['case'];root=P/e['native_path'];ev=np.loadtxt(root/'runtime/measurement_events.csv',delimiter=',',ndmin=2);par,_=read_parameters(root);D=par['sourceDiscriminationPower'];prior=par.get('hitPriorProbability',.3);Lprior=np.log(prior/(1-prior));base=[a for a in controls if a['case']==c and a['arm']=='O0' and a['confidence']=='native' and a['forward']=='native_blur'];nf=None
 for a in base:
  u=a['update'];z=np.load(O/'controls'/(c+'_'+u+'.npz'));free=z['free_indices'];owner=z['owner'];h=z['forward_blurred'];n=a['windows'];nfree=len(free);replay=np.fromfile(O/'replay20'/(c+'.f64'),dtype='<f8').reshape(len(ev),nfree,4)[:n];L=replay[-1,:,0];conf=replay[-1,:,1];delta=np.diff(np.vstack([np.full((1,nfree),Lprior),replay[:,:,0]]),axis=0);m=json.loads((root/'runtime/updates'/u/'metadata.json').read_text());truth=e['metadata']['source_xyz'];ti=int((np.float32(truth[0])-np.float32(m['origin_x']))/np.float32(m['cell_size']))+int((np.float32(truth[1])-np.float32(m['origin_y']))/np.float32(m['cell_size']))*m['width'];tloc=np.flatnonzero(free==ti)
  if not len(tloc) or a['competitor_locked_cell'] is None:continue
  t=int(owner[tloc[0]]);cloc=np.flatnonzero(free==a['competitor_locked_cell']);assert len(cloc)==1;comp=int(owner[cloc[0]])
  def gap(log):
   p=np.exp(-np.logaddexp(0,-log));return float((np.log(1-D*conf*np.abs(p-h[t]))-np.log(1-D*conf*np.abs(p-h[comp]))).sum())
  withgap=gap(L);assert abs(withgap-a['source_score_gap'])<1e-8
  for stop in np.unique(ev[:n,6]):
   keep=ev[:n,6]==stop;y=ev[:n,1][keep]>par['th_gas_present'];without=gap(L-delta[keep].sum(axis=0));rows.append(dict(case=c,update=u,stop=int(stop),windows=int(keep.sum()),hits=int(y.sum()),mixed=bool(0<y.sum()<len(y)),first_stamp_ns=int(ev[:n,0][keep].min()),last_stamp_ns=int(ev[:n,0][keep].max()),competitor_locked_cell=a['competitor_locked_cell'],same_owner=t==comp,native_truth_minus_competitor=withgap,leave_stop_out_truth_minus_competitor=without,native_stop_influence_on_gap=withgap-without,interpretation='NEGATIVE_MEANS_INCLUDED_STOP_HURTS_TRUTH_RELATIVE_TO_PREVIOUS_EPOCH_COMPETITOR_AT_FIXED_MODEL',confidence_changed=False,forward_changed=False))
with (O/'STOP_INFLUENCE.csv').open('w',newline='') as f:w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
print(json.dumps([r for r in rows if r['mixed']],indent=2));print('ALL_STOP_INFLUENCE_ROWS',len(rows))
