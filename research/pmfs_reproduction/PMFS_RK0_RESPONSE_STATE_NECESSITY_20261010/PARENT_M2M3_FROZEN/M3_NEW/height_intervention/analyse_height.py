import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,math,numpy as np,argparse
def read(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def analyse(root):
 boundary=root.parent/'boundary_point_experiment';old=read(boundary/'snapshot/input.csv');mask=np.array([int(r['occupancy'])==1 for r in old]);conf=np.array([float(r['confidence']) for r in old]);lo=np.array([float(r['logOdds']) for r in old]);p=1/(1+np.exp(-lo))
 rows=[];data={};percell=[]
 for field in ['NATIVE_SENSOR_PLANE','SOURCE_PLANE','COLUMN_FREE_UNIFORM_MEAN']:
  for bundle in ['T','W']:
   for cand in ['C7','K2']:
    path=boundary/'forward_calls'/f'{bundle}_{cand}_point_native' if field=='NATIVE_SENSOR_PLANE' else root/'forward_calls'/f'{field}_{bundle}_{cand}'
    r=json.loads((path/'RESULT.json').read_text());h=np.fromfile(next(x for x in (path/'maps').glob('*.f32') if '_unblurred' not in x.name),dtype='<f4').astype(float);h0=np.fromfile(next((path/'maps').glob('*_unblurred.f32')),dtype='<f4').astype(float);factor=1-conf*.4*np.abs(p-h);score=float(np.prod(factor[mask].astype(np.longdouble),dtype=np.longdouble));assert math.isclose(score,r['score'],rel_tol=3e-13,abs_tol=1e-300)
    row=dict(field=field,bundle=bundle,candidate=cand,score=r['score'],logscore=float(np.log(factor[mask]).sum()),raw_nonzero_cells=int(sum(h0[mask]>0)),blurred_nonzero_cells=int(sum(h[mask]>0)),raw_mean_hit=float(h0[mask].mean()),blurred_mean_hit=float(h[mask].mean()),release_points=r['release_points'],gaussian_before=r['gaussian_index_before'],gaussian_after=r['gaussian_index_after'],RNG_before=r['rng_before'],RNG_after=r['rng_after']);rows.append(row);data[field,bundle,cand]=(row,h,factor)
 comparisons=[]
 for field in ['NATIVE_SENSOR_PLANE','SOURCE_PLANE','COLUMN_FREE_UNIFORM_MEAN']:
  for bundle in ['T','W']:
   a,ah,af=data[field,bundle,'C7'];b,bh,bf=data[field,bundle,'K2'];ratio=b['score']/a['score'];delta=np.log(bf)-np.log(af)
   comparisons.append(dict(field=field,bundle=bundle,true_score=a['score'],wrong_score=b['score'],wrong_over_true_score=ratio,wrong_minus_true_logscore=float(sum(delta[mask])),choice='C7' if ratio<1 else 'K2'))
   for i in np.flatnonzero(mask):percell.append(dict(field=field,bundle=bundle,cell_index=int(i),grid_i=old[i]['grid_i'],grid_j=old[i]['grid_j'],measured_belief=p[i],confidence=conf[i],true_prediction=ah[i],wrong_prediction=bh[i],wrong_minus_true_logfactor=delta[i]))
 return dict(rows=rows,comparisons=comparisons,percell=percell,summary=dict(status='COMPLETED_TWO_INPUT_ONLY_WIND_HEIGHT_CONTRASTS',comparisons=comparisons,all_preserve_wrong=all(x['choice']=='K2' for x in comparisons),source_plane_candidates_true_choices=sum(x['field']=='SOURCE_PLANE' and x['choice']=='C7' for x in comparisons),column_closure_candidates_true_choices=sum(x['field']=='COLUMN_FREE_UNIFORM_MEAN' and x['choice']=='C7' for x in comparisons),scope='Exactpoint/nativewall only, same frozen map and RNG/cache, physical prediction u/v-only intervention; not a new self-consistent 3D simulation or official localization result.'))
if __name__=='__main__':
 default=Path(__file__).resolve().parent
 if not (default/'HEIGHT_FROZEN_CONTRACT.json').exists():default=Path(__file__).resolve().parents[3]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/height_intervention'
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=default);ap.add_argument('--write',action='store_true');a=ap.parse_args();r=analyse(a.root)
 if a.write:
  for n,k in [('HEIGHT_FORWARD_SCORES.csv','rows'),('HEIGHT_PAIRED_COMPARISONS.csv','comparisons'),('HEIGHT_PER_CELL_CONTRIBUTIONS.csv','percell')]:
   dest=a.root/n;assert not dest.exists()
   with dest.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,list(r[k][0]),lineterminator='\n');w.writeheader();w.writerows(r[k])
  dest=a.root/'HEIGHT_EXPERIMENT_RESULT.json';assert not dest.exists();dest.write_text(json.dumps(r['summary'],indent=2)+'\n',encoding='utf-8')
 print(json.dumps(r['summary'],indent=2))
