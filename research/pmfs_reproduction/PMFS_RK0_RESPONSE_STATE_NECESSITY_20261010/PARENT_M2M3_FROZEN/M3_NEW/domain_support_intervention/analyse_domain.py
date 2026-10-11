import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,math,numpy as np,argparse
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def analyse(root):
 inp=read(root/'snapshot/input.csv');mask=np.array([int(r['occupancy'])==1 for r in inp]);lo=np.array([float(r['logOdds']) for r in inp]);p=1/(1+np.exp(-lo));conf=np.array([float(r['confidence']) for r in inp]);rows=[];data={};cells=[];movement=[]
 for domain in ['NATIVE_NAV_DOMAIN','COLUMN_FREE_UNION_DOMAIN']:
  for b in ['T','W']:
   for cand in ['C7','K2']:
    path=root.parent/'height_intervention/forward_calls'/f'COLUMN_FREE_UNIFORM_MEAN_{b}_{cand}' if domain=='NATIVE_NAV_DOMAIN' else root/'forward_calls'/f'union_{b}_{cand}'
    r=json.loads((path/'RESULT.json').read_text());raw=np.fromfile(next((path/'maps').glob('*_unblurred.f32')),dtype='<f4').astype(float);h=np.fromfile(next(x for x in (path/'maps').glob('*.f32') if '_unblurred' not in x.name),dtype='<f4').astype(float);assert not np.any(raw[~mask]);factor=1-conf*.4*np.abs(p-h);score=float(np.prod(factor[mask].astype(np.longdouble),dtype=np.longdouble));assert math.isclose(score,r['score'],rel_tol=3e-13,abs_tol=1e-300)
    row=dict(domain=domain,bundle=b,candidate=cand,score=r['score'],logscore=float(np.log(factor[mask]).sum()),warmup_steps=r['release_points']//5-200,record_steps=200,release_points=r['release_points'],raw_nonzero_nav_cells=int(sum(raw[mask]>0)),blurred_nonzero_nav_cells=int(sum(h[mask]>0)),raw_mean_nav_hit=float(raw[mask].mean()),blurred_mean_nav_hit=float(h[mask].mean()),gaussian_before=r['gaussian_index_before'],gaussian_after=r['gaussian_index_after'],engine_before=r['rng_before'],engine_after=r['rng_after']);rows.append(row);data[domain,b,cand]=(row,h,factor)
    if domain=='COLUMN_FREE_UNION_DOMAIN':
     z=json.loads((path/'GAS_DOMAIN_COUNTERS.json').read_text());agg=read(path/'MOVEMENT_CELL_AGGREGATES.csv')
     for phase in [0,1]:
      aa=[x for x in agg if int(x['phase'])==phase];n=sum(int(x['moves']) for x in aa);ends=sum(int(x['moves']) for x in aa if 0<=int(x['end_i'])<34 and 0<=int(x['end_j'])<45 and not mask[int(x['end_i'])+34*int(x['end_j'])]);starts=sum(int(x['moves']) for x in aa if 0<=int(x['start_i'])<34 and 0<=int(x['start_j'])<45 and not mask[int(x['start_i'])+34*int(x['start_j'])]);zero=sum(int(x['zero_displacement']) for x in aa)
      movement.append(dict(bundle=b,candidate=cand,phase='warmup' if phase==0 else 'record',moves=n,start_nav_obstacle_instances=starts,end_nav_obstacle_instances=ends,end_nav_obstacle_fraction=ends/n,zero_displacement=zero,**{'global_'+k:v for k,v in z.items()}))
 comparisons=[]
 for domain in ['NATIVE_NAV_DOMAIN','COLUMN_FREE_UNION_DOMAIN']:
  for b in ['T','W']:
   a,ah,af=data[domain,b,'C7'];z,zh,zf=data[domain,b,'K2'];ratio=z['score']/a['score'];delta=np.log(zf)-np.log(af)
   comparisons.append(dict(domain=domain,bundle=b,true_score=a['score'],wrong_score=z['score'],wrong_over_true_score=ratio,wrong_minus_true_logscore=float(sum(delta[mask])),choice='C7' if ratio<1 else 'K2'))
   for i in np.flatnonzero(mask):cells.append(dict(domain=domain,bundle=b,cell_index=int(i),grid_i=inp[i]['grid_i'],grid_j=inp[i]['grid_j'],measured_belief=p[i],confidence=conf[i],true_prediction=ah[i],wrong_prediction=zh[i],wrong_minus_true_logfactor=delta[i]))
 return dict(rows=rows,comparisons=comparisons,cells=cells,movement=movement,summary=dict(status='COMPLETED_TRANSPORT_DOMAIN_ORACLE_DISCRIMINATION',comparisons=comparisons,union_true_choices=sum(x['domain']=='COLUMN_FREE_UNION_DOMAIN' and x['choice']=='C7' for x in comparisons),gasfree_cells=1530,navfree_cells=447,scope='Complete column-union support is an upper-bound diagnostic, possibly connecting disjoint heights, with native nav map/readout/score unchanged; not a deployable or self-consistent 3D prediction.'))
if __name__=='__main__':
 default=Path(__file__).resolve().parent
 if not (default/'DOMAIN_SUPPORT_FROZEN_CONTRACT.json').exists():default=Path(__file__).resolve().parents[3]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/domain_support_intervention'
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=default);ap.add_argument('--write',action='store_true');a=ap.parse_args();r=analyse(a.root)
 if a.write:
  for n,k in [('DOMAIN_FORWARD_SCORES.csv','rows'),('DOMAIN_PAIRED_COMPARISONS.csv','comparisons'),('DOMAIN_PER_CELL_CONTRIBUTIONS.csv','cells'),('DOMAIN_MOVEMENT_SUMMARY.csv','movement')]:
   p=a.root/n;assert not p.exists()
   with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,list(r[k][0]),lineterminator='\n');w.writeheader();w.writerows(r[k])
  p=a.root/'DOMAIN_EXPERIMENT_RESULT.json';assert not p.exists();p.write_text(json.dumps(r['summary'],indent=2)+'\n',encoding='utf-8')
 print(json.dumps(r['summary'],indent=2))
