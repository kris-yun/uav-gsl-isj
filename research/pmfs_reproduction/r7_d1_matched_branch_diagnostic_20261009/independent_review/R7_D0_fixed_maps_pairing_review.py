import sys
import numpy as np,csv,json,pathlib
if len(sys.argv)!=2: raise SystemExit('Usage: python R7_D0_fixed_maps_pairing_review.py EXTRACTED_DIR')
p=pathlib.Path(sys.argv[1]).resolve();j=lambda f:json.loads((p/f).read_text())
def c(f):
 with open(p/f,encoding='utf-8-sig') as f:return list(csv.DictReader(f))
a=c('diagnostic_input/input.csv');b=c('result/shadow_update/input.csv');cands=c('result/shadow_update/candidates.csv');m=j('diagnostic_input/metadata.json');mask=np.array([int(r['occupancy'])==1 for r in a]);assert mask.sum()==518
xy=np.array([[m['origin_x']+(i%m['width']+.5)*m['cell_size'],m['origin_y']+(i//m['width']+.5)*m['cell_size']] for i in range(len(a))]);ds=np.linalg.norm(xy-np.array([0,-1]),axis=1)
from scipy.special import expit
pm=[expit(np.array([float(r['logOdds']) for r in rows])) for rows in [a,b]];w=[np.minimum(1,np.array([float(r['confidence']) for r in rows])) for rows in [a,b]]
raw=[np.full(len(a),np.nan),np.full(len(a),np.nan)];diffs=[]
for row in cands:
 h=np.frombuffer((p/'result/shadow_update'/row['map_file']).read_bytes(),dtype='<f4').astype(float)
 i,ii,wi,hi=[int(row[k]) for k in ['origin_i','origin_j','size_i','size_j']];cells=[x+y*m['width'] for y in range(ii,ii+hi) for x in range(i,i+wi)]
 for t in (0,1):
  fac=1-.3*np.abs(pm[t]-h)*w[t]
  score=np.prod(fac[mask]);raw[t][cells]=score
 diffs.append((row['map_file'],raw[0][cells[0]],raw[1][cells[0]],len(cells)))
for t in (0,1):
 r=raw[t];assert np.isfinite(r[mask]).all();r[~mask]=0
 posterior=r/r.sum();avg=(xy*posterior[:,None]).sum(axis=0);v=np.sum(posterior*np.sum((xy-avg)**2,axis=1));mapxy=xy[np.argmax(posterior)];ep=-np.sum(posterior[mask]*np.log(posterior[mask]));d={"set":"old35_measured_map" if t==0 else "new40_measured_map", "MAP_xy":mapxy.tolist(),"MAP_error":float(np.linalg.norm(mapxy-[0,-1])),"mean_xy":avg.tolist(),"mean_error":float(np.linalg.norm(avg-[0,-1])),"variance":float(v),"truth_1m_mass":float(posterior[ds<=1].sum()),"max_p":float(posterior.max()),"entropy":float(ep),"effective_cells":float(np.exp(ep))};print(json.dumps(d,ensure_ascii=False))
 if t==1:
  stored=np.frombuffer((p/'result/shadow_update/posterior.f64').read_bytes(),dtype='<f8');print('stored diff max',np.max(abs(stored-posterior)))
# how many measured cells changed
for col in ('logOdds','omega','confidence'):
 v0=np.array([float(r[col]) for r in a]);v1=np.array([float(r[col]) for r in b]);idx=np.flatnonzero(v0!=v1);print('DIFF',col,'cells',len(idx),'max',abs(v1-v0).max(),'mean_free_change',abs(v1[mask]-v0[mask]).mean())
# score ordering across candidate fixed
r0=raw[0][mask];r1=raw[1][mask];print('corr log score',np.corrcoef(np.log(r0),np.log(r1))[0,1]);print('diff ratio range',np.nanmin(r1/r0),np.nanmax(r1/r0))
