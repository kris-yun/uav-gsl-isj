"""Exploratory deterministic readout audit. No forward simulation, fitting or tuning.
Four mask/denominator combinations are fixed here before execution. This is not
an independent validation task: all input fields have already been inspected.
"""
from pathlib import Path
import pandas as pd, numpy as np, math, json, cv2, hashlib, zipfile, argparse
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--combined-root',type=Path,default=root/'combined')
parser.add_argument('--m2-zip',type=Path,default=root.parent/'PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010_REVIEW.zip')
parser.add_argument('--out',type=Path,default=root/'new_diagnostics')
args=parser.parse_args();pkg=args.combined_root;m3=pkg/'M3_NEW';m2=pkg/'M2_FROZEN'
out=args.out;out.mkdir(parents=True,exist_ok=True)
meta=json.loads((m2/'native_reference_evidence/FROZEN_METADATA.json').read_text())
shape=(meta['height'],meta['width'])
inp=pd.read_csv(m3/'M1_REFERENCE/snapshot/input.csv')
free=(inp.occupancy.to_numpy()==1)
p=1-1/(1+np.exp(inp.logOdds.to_numpy()))
c=inp.confidence.to_numpy(); nav=free.astype(np.float32).reshape(shape)
def blur(a):return cv2.GaussianBlur(a.astype(np.float32),(0,0),1.5,1.5)
def ls(a,sel=free):return math.fsum(np.log1p(-.4*c[sel]*np.abs(p[sel]-a.ravel()[sel].astype(float))))
fields=pd.read_csv(m3/'projected_center_field/CENTER_FIELD_PER_CELL.csv')
results=[]
for source in ('C7','K2'):
 q=fields[(fields.candidate_id==source)&(fields.variant=='ALL_XY')&(fields.stage=='UNBLURRED')].sort_values('cell_index').frequency.to_numpy(dtype=np.float32).reshape(shape)
 assert len(q.ravel())==free.size and np.all((q>=0)&(q<=1))
 for numerator in ('NAV_MASKED','ALL_XY'):
  a=q*nav if numerator=='NAV_MASKED' else q
  for denominator in ('NAV_MASK','ALL_FRAME'):
   den=blur(nav if denominator=='NAV_MASK' else np.ones(shape,dtype=np.float32))
   num=blur(a)
   before=np.where(den!=0,num/np.where(den==0,1,den),num)
   after=np.clip(before,0,1)
   results.append(dict(source=source,numerator=numerator,denominator=denominator,
     log_score=ls(after),nav_cells_clipped_above_one=int(((before.ravel()>1)&free).sum()),
     max_nav_preclip=float(before.ravel()[free].max())))
 pd.DataFrame({'cell_index':np.arange(len(free)),'raw_frequency':q.ravel()}).to_csv(out/f'{source}_common_raw_field.csv',index=False)
tab=pd.DataFrame(results); tab.to_csv(out/'READOUT_MASK_DENOMINATOR_FACTORIAL.csv',index=False)
rows=[]
for keys,g in tab.groupby(['numerator','denominator'],sort=False):
 z=g.set_index('source').log_score
 rows.append(dict(numerator=keys[0],denominator=keys[1],true_minus_wrong_log=float(z.C7-z.K2),selected='C7' if z.C7>z.K2 else 'K2'))
pd.DataFrame(rows).to_csv(out/'READOUT_PAIRWISE_MARGINS.csv',index=False)
# Recompute domain contributions without importing delivered scoring routines.
dom=pd.read_csv(m3/'domain_support_intervention/DOMAIN_PER_CELL_CONTRIBUTIONS.csv')
recalc=np.log1p(-.4*dom.confidence*np.abs(dom.measured_belief-dom.wrong_prediction))-np.log1p(-.4*dom.confidence*np.abs(dom.measured_belief-dom.true_prediction))
maxerr=float(np.max(np.abs(recalc-dom.wrong_minus_true_logfactor)))
assert maxerr<1e-12
sumrows=[]
for keys,g in dom.groupby(['domain','bundle'],sort=False):
 gap=math.fsum(g.wrong_minus_true_logfactor)
 y=meta['origin_y']+(g.grid_j.to_numpy()+.5)*meta['cell_size']
 band=(y>=1.7)&(y<=2.7)
 sumrows.append(dict(domain=keys[0],bundle=keys[1],log_wrong_over_true=gap,wrong_over_true=math.exp(gap),preset_band_gap=math.fsum(g.wrong_minus_true_logfactor[band]),remaining_gap=math.fsum(g.wrong_minus_true_logfactor[~band])))
pd.DataFrame(sumrows).to_csv(out/'DOMAIN_GAP_AND_PRESET_BAND.csv',index=False)
# Independent integrity check and embedded M2 equality.
m=json.loads((pkg/'SHA256_MANIFEST.json').read_text())
for n,h in m.items():assert hashlib.sha256((pkg/n).read_bytes()).hexdigest()==h,n
with zipfile.ZipFile(args.m2_zip) as z:
 count=0
 for info in z.infolist():
  if not info.is_dir():assert z.read(info.filename)==(m2/info.filename).read_bytes(),info.filename;count+=1
result=dict(integrity_hashes_verified=len(m),embedded_M2_byte_identical_members=count,max_domain_factor_error=maxerr,readout_pairs=rows,domain_scores=sumrows,scope='Exploratory deterministic field reanalysis; not new physics, independent heldout evidence, calibrated probabilities, or localization performance',cv2_version=cv2.__version__)
(out/'INDEPENDENT_DIAGNOSTIC_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
