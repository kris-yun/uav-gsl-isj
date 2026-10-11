"""Same-bank, same-time, same-score readout contrast, declared exploratory.
Predicted PID-threshold field vs all-height centre occupancy. Both are evaluated
with the same dense similarity, both unblurred and nav-normalized blurred.
This does not rerun transport and does not turn source-bank truth into deployable data.
"""
from pathlib import Path
import pandas as pd, numpy as np, cv2, math, json, argparse
base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--combined-root',type=Path,default=base/'combined')
parser.add_argument('--out',type=Path,default=base/'new_diagnostics')
args=parser.parse_args();root=args.combined_root;m2=root/'M2_FROZEN';m3=root/'M3_NEW';out=args.out;out.mkdir(parents=True,exist_ok=True)
meta=json.loads((m2/'native_reference_evidence/FROZEN_METADATA.json').read_text());shape=(meta['height'],meta['width'])
f=pd.read_csv(m3/'M1_REFERENCE/snapshot/input.csv');free=(f.occupancy.to_numpy()==1);p=1-1/(1+np.exp(f.logOdds.to_numpy()));c=f.confidence.to_numpy();mask=free.astype(np.float32).reshape(shape)
centres=pd.read_csv(m3/'projected_center_field/CENTER_FIELD_PER_CELL.csv')
def gb(a):return cv2.GaussianBlur(a.astype(np.float32),(0,0),1.5,1.5)
def score(a):return math.fsum(np.log1p(-.4*c[free]*np.abs(p[free]-a[free].astype(float))))
res=[]
for s in ('C7','K2'):
 per=[]
 for rep in (0,1):
  q=pd.read_csv(m2/f'native_reference_evidence/realizations/{s}_{rep}/QUERY_OUTPUT.csv')
  x=q.query_id.str.extract(r'^grid_b(\d+)_v0_c(\d+)$'); good=x[0].notna()
  dat=q[good].copy();dat['cell']=x.loc[good,1].astype(int);dat['block']=x.loc[good,0].astype(int)
  assert dat.groupby('cell').size().eq(50).all() and dat['cell'].nunique()==447
  a=np.zeros(len(free));g=dat.assign(hit=(dat.ppm_float32>.1).astype(float)).groupby('cell').hit.mean();a[g.index]=g.to_numpy();per.append(a)
 pid=np.mean(per,axis=0)
 centre=centres[(centres.candidate_id==s)&(centres.variant=='MASKED')&(centres.stage=='UNBLURRED')].sort_values('cell_index').frequency.to_numpy()
 for name,arr in (('PID_THRESHOLD',pid),('PROJECTED_CENTER',centre)):
  blurred=np.clip(gb(arr.reshape(shape))/np.where(gb(mask)>0,gb(mask),1),0,1).ravel()
  for st,a in [('UNBLURRED',arr),('SAME_NAV_BLUR',blurred)]:res.append(dict(candidate=s,readout=name,stage=st,log_score=score(a)))
tab=pd.DataFrame(res);tab.to_csv(out/'SAME_BANK_SAME_SCORER_READOUT.csv',index=False)
pairs=[]
for (name,stage),g in tab.groupby(['readout','stage'],sort=False):
 sc=g.set_index('candidate').log_score;d=float(sc.C7-sc.K2);pairs.append(dict(readout=name,stage=stage,true_minus_wrong_log=d,selected='C7' if d>0 else 'K2'))
pd.DataFrame(pairs).to_csv(out/'SAME_BANK_SAME_SCORER_MARGINS.csv',index=False)
print(json.dumps(pairs,indent=2))
