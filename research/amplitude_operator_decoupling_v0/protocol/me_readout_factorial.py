import os
"""POSTHOC fixed 2x2 readout ablation. All four arms reported. No bandwidth search."""
from pathlib import Path
import numpy as np,pandas as pd,json
R=Path(os.environ['ME_REVIEW_ROOT']);O=Path(os.environ['ME_AUDIT_OUT']);pr=pd.read_csv(R/'protocol/E1_HOUSE_PROBE_CONTRACTS.tsv',sep='\t');yall=np.load(R/'protocol/JTD_E2_FRESH_TARGET_10x30.npy')
rows=[];cand=[];signatures=[];sources=[];matrices={}
for e,house in enumerate(['House01','House02','House02']):
 meta=json.loads((R/f'inputs/env_{e}/meta.json').read_text());a=meta['resolution'];nx,ny=meta['width'],meta['height'];ox,oy=meta['origin_x'],meta['origin_y'];pc=pr[pr.house==house].sort_values('probe_rank');pip=pd.read_csv(R/f'inputs/env_{e}/probes.csv').sort_values('probe_rank');idx=pip.cell_index.to_numpy(int)
 def spacing(axis):
  c=pc['center_'+axis+'_m'].to_numpy();i=(pc['native_'+axis+'0'].to_numpy()+pc['native_'+axis+'1_exclusive'].to_numpy())/2;return np.dot(c-c.mean(),i-i.mean())/np.dot(i-i.mean(),i-i.mean())
 dx,dy=spacing('x'),spacing('y');W=[]
 for _,p in pc.iterrows():
  hx=(p.native_x1_exclusive-p.native_x0)*dx/2;hy=(p.native_y1_exclusive-p.native_y0)*dy/2;xl,xh=p.center_x_m-hx,p.center_x_m+hx;yl,yh=p.center_y_m-hy,p.center_y_m+hy
  x=ox+np.arange(nx)*a;y=oy+np.arange(ny)*a;wx=np.maximum(0,np.minimum(x+a,xh)-np.maximum(x,xl));wy=np.maximum(0,np.minimum(y+a,yh)-np.maximum(y,yl));W.append((wy[:,None]*wx[None,:]/(4*hx*hy)).ravel())
 W=np.array(W);matrices[str(e)]=W
 fields={}
 for key in ['rawu','u']:
  maps=np.array([np.mean([np.fromfile(f,'<f4').astype(float) for f in sorted((R/f'forward/env_{e}/source_{k}').glob('*.'+key+'.f32'))],axis=0) for k in range(6)])
  fields[key+'_nearest']=maps[:,idx]
  fields[key+'_footprint']=maps@W.T
 for arm,field in fields.items():
  for aidx in range(0,6,2):
   va,vb=field[aidx],field[aidx+1];co=float(np.dot(va,vb)/np.linalg.norm(va)/np.linalg.norm(vb));signatures.append(dict(env=e,pair=aidx//2,arm=arm,cosine=co,angular_gap=1-co))
  pred=np.tile(np.maximum(field[:,None,:],1e-9),(1,10,1)) # same B2 EPS contract for all 4 arms
  norm=(pred*pred).sum(axis=(1,2))
  for s in range(6):
   for j in range(4):
    y=yall[e,s,j];scale=np.maximum(0,(pred*y[None]).sum(axis=(1,2))/norm);sse=((y[None]-scale[:,None,None]*pred)**2).sum(axis=(1,2));rank=int(1+(sse<sse[s]).sum());ties=int((sse==sse.min()).sum());rows.append(dict(env=e,source=s,target=j,arm=arm,rank=rank,unique_top1=bool(rank==1 and ties==1),map_source=int(np.argmin(sse)),true_sse=float(sse[s]),pair_delta_sse=float(sse[s^1]-sse[s])))
    for k in range(6):cand.append(dict(env=e,source=s,target=j,candidate=k,arm=arm,sse=float(sse[k]),scale=float(scale[k])))
  for k in range(6):
   for q in range(30):sources.append(dict(env=e,source=k,probe=q+1,arm=arm,value=float(field[k,q])))
D=pd.DataFrame(rows);D.to_csv(O/'posthoc_readout_factorial_targets.csv',index=False);pd.DataFrame(cand).to_csv(O/'posthoc_readout_factorial_candidates.csv',index=False);pd.DataFrame(signatures).to_csv(O/'posthoc_readout_factorial_pairgeometry.csv',index=False);pd.DataFrame(sources).to_csv(O/'posthoc_readout_factorial_templates.csv',index=False);np.savez(O/'geometric_projection_weights.npz',**matrices)
summary=D.groupby(['env','arm']).agg(mean_rank=('rank','mean'),unique_top1=('unique_top1','mean'),n=('rank','count')).reset_index();summary.to_csv(O/'posthoc_readout_factorial_summary.csv',index=False)
print(summary.to_string(index=False));print('pair geometry');print(pd.DataFrame(signatures).pivot(index=['env','pair'],columns='arm',values='cosine').round(7).to_string())
# Exact baseline replay on saved SSE values
old=pd.read_csv(R/'evaluation/CANDIDATE_SCORES_ALL.csv');rec=pd.DataFrame(cand);b=rec[rec.arm=='u_nearest'].sort_values(['env','source','target','candidate']);old=old.sort_values(['environment_index','source_index','target_index','candidate_index']);err=np.abs(b.sse.to_numpy()-old.scaled_value_SSE.to_numpy());print('B2 largest absolute/relative SSE diff',err.max(),np.max(err/(1+np.abs(old.scaled_value_SSE.to_numpy()))))
