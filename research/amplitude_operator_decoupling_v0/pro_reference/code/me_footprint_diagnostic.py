import os
"""One posthoc, deterministic geometric readout diagnostic. No optimization, simulation or randomization."""
from pathlib import Path
import numpy as np,pandas as pd,json
R=Path(os.environ['ME_REVIEW_ROOT']);O=Path(os.environ['ME_AUDIT_OUT'])
contract=pd.read_csv(R/'protocol/E1_HOUSE_PROBE_CONTRACTS.tsv',sep='\t');targets=np.load(R/'protocol/JTD_E2_FRESH_TARGET_10x30.npy')
rows=[];prows=[]
for e,house in enumerate(['House01','House02','House02']):
 meta=json.loads((R/f'inputs/env_{e}/meta.json').read_text());nx,ny=meta['width'],meta['height'];a=meta['resolution'];ox,oy=meta['origin_x'],meta['origin_y']
 pr=contract[contract.house==house].sort_values('probe_rank')
 # Native spacing is inferred from existing frozen coordinate-vs-native-index differences, not targets.
 def spacing(axis):
  centers=pr['center_'+axis+'_m'].to_numpy();idx=(pr['native_'+axis+'0'].to_numpy()+pr['native_'+axis+'1_exclusive'].to_numpy())/2
  num=np.dot(idx-idx.mean(),centers-centers.mean());den=np.dot(idx-idx.mean(),idx-idx.mean());return num/den
 dx,dy=spacing('x'),spacing('y')
 mat=[]
 for _,p in pr.iterrows():
  hx=(p.native_x1_exclusive-p.native_x0)*dx/2;hy=(p.native_y1_exclusive-p.native_y0)*dy/2
  xl,xh=p.center_x_m-hx,p.center_x_m+hx;yl,yh=p.center_y_m-hy,p.center_y_m+hy
  ix=ox+np.arange(nx)*a;iy=oy+np.arange(ny)*a
  wx=np.maximum(0,np.minimum(ix+a,xh)-np.maximum(ix,xl));wy=np.maximum(0,np.minimum(iy+a,yh)-np.maximum(iy,yl))
  area=4*hx*hy;mat.append((wy[:,None]*wx[None,:]/area).ravel())
 W=np.array(mat);free=np.fromfile(R/f'inputs/env_{e}/occupancy.u8',dtype=np.uint8)>0
 for k in range(6):
  raw=np.mean([np.fromfile(f,dtype='<f4').astype(float) for f in sorted((R/f'forward/env_{e}/source_{k}').glob('*.rawu.f32'))],axis=0)
  # u/a^2 is planar mass-density up to common particle mass; no inferred 3D concentration.
  pred=W@raw/(a*a)
  for q,v in enumerate(pred):prows.append(dict(env=e,source=k,probe_rank=q+1,projected_areal_density=float(v),covered_fraction=float(W[q].sum()),free_fraction=float(W[q,free].sum())))
 df=pd.DataFrame([r for r in prows if r['env']==e]);mu=df.projected_areal_density.to_numpy().reshape(6,30)
 for s in range(6):
  for j in range(4):
   y=targets[e,s,j];pred=np.tile(mu[:,None,:],(1,10,1));den=(pred**2).sum(axis=(1,2));num=(pred*y[None]).sum(axis=(1,2));g=np.divide(num,den,out=np.zeros(6),where=den>0);sse=((y[None]-g[:,None,None]*pred)**2).sum(axis=(1,2));rank=int(1+np.sum(sse<sse[s]));rows.append(dict(env=e,source=s,target=j,rank=rank,top1=int(np.argmin(sse)),true_sse=float(sse[s])))
pd.DataFrame(prows).to_csv(O/'posthoc_footprint_readout.csv',index=False);pd.DataFrame(rows).to_csv(O/'posthoc_footprint_B2_score.csv',index=False)
print('geometric readout, posthoc only:');print(pd.DataFrame(rows).groupby('env').agg(rank=('rank','mean'),top1=('rank',lambda x:(x==1).mean())).to_string())
print('area fraction',pd.DataFrame(prows).groupby('env').agg(min_free=('free_fraction','min'),min_covered=('covered_fraction','min')))
