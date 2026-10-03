"""Post-hoc reproduction only: narrow cone, prefixes and pooled channels; no gate changes."""
import sys,re,numpy as np,pandas as pd
from common import *
sys.path.insert(0,str(EXP/'scripts'));import score_identifiability as old
a,xy=old.load();prefixes=[10,20,30,60,90,120,180,300];rows=[]
for duration in prefixes:
 d=old.score(a[...,:duration],.001);d['margin']=d.best_false_brier-d.true_brier
 summary=d.groupby(['environment','release','height']).agg(top1=('top1','mean'),median_rank=('true_rank','median'),median_margin=('margin','median')).reset_index();summary['prefix_s']=duration;rows.append(summary)
pd.concat(rows).to_csv(OUT/'original_time_prefixes_EXPLORATORY.csv',index=False)
comb=np.repeat(np.concatenate([a[...,0,:],a[...,1,:]],axis=-1)[...,None,:],4,axis=-2)
c=old.score(comb,.001).query('height==10').copy();c['channels']='10m+30m equal weight';c['margin']=c.best_false_brier-c.true_brier
c.groupby(['environment','release','channels']).agg(top1=('top1','mean'),median_rank=('true_rank','median'),median_margin=('margin','median')).to_csv(OUT/'original_combined_channels_EXPLORATORY.csv')
angles={};geometry=[]
for p in sorted((OLD/'observations').glob('*.csv')):
 m=re.fullmatch(r'(N0|L1|F1|F2)_x(\d+)_y(-?\d+)_r10_seed(\d+)',p.stem)
 if not m:continue
 d=pd.read_csv(p);env=m[1];s=np.array([int(m[2]),int(m[3])]);bearing=s-d[['x','y']].to_numpy();up=-d[['u','v']].to_numpy();den=np.linalg.norm(bearing,axis=1)*np.linalg.norm(up,axis=1);angle=np.degrees(np.arccos(np.clip(np.divide((bearing*up).sum(axis=1),den,out=np.zeros(len(d)),where=den>0),-1,1)))
 angles.setdefault(env,[]).extend(angle[(d.concentration>=.001)&(den>0)].tolist())
 if int(m[4])==30001:geometry.append(dict(environment=env,source_x=int(m[2]),source_y=int(m[3]),all_path_cone45_fraction=float((angle[den>0]<=45).mean())))
pd.DataFrame([dict(environment=e,gas_hit_cone10_capture=float((np.array(v)<=10).mean()),gas_hit_cone45_capture=float((np.array(v)<=45).mean()),eligible_hit_count=len(v)) for e,v in angles.items()]).to_csv(OUT/'original_M1_narrow_cone_EXPLORATORY.csv',index=False)
pd.DataFrame(geometry).to_csv(OUT/'original_M1_all_path_geometry_EXPLORATORY.csv',index=False)
print('Post-hoc original checks exported; original decision untouched')
