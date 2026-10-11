import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,csv,json,math,numpy as np
def readcsv(p):return list(csv.DictReader(p.open(encoding='utf-8')))
def dumpcsv(p,rows):
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def analyse(root):
 inp=readcsv(root/'snapshot/input.csv');mask=np.array([int(x['occupancy'])==1 for x in inp]);conf=np.array([float(x['confidence']) for x in inp]);lo=np.array([float(x['logOdds']) for x in inp]);p=1/(1+np.exp(-lo))
 rows=[];percell=[];data={};moves=[]
 for bundle in ['T','W']:
  for candidate,oldjob in [('C7',bundle+'_true_fine'),('K2','T_wrong_fine' if bundle=='T' else 'anchor_W_fine')]:
   for form in ['uniform','point']:
    for boundary in ['native','slide']:
     reused=form=='uniform' and boundary=='native'
     path=root/'reused_M1'/oldjob if reused else root/'forward_calls'/f'{bundle}_{candidate}_{form}_{boundary}'
     r=json.loads((path/'RESULT.json').read_text());h=np.fromfile(next(x for x in (path/'maps').glob('*.f32') if not x.name.endswith('_unblurred.f32')),dtype='<f4').astype(float)
     h0=np.fromfile(next((path/'maps').glob('*_unblurred.f32')),dtype='<f4').astype(float)
     factor=1-conf*np.abs(p-h)*.4;log=np.log(factor[mask]);score=float(np.prod(factor[mask].astype(np.longdouble),dtype=np.longdouble));assert math.isclose(score,r['score'],rel_tol=3e-13,abs_tol=1e-300)
     row=dict(bundle=bundle,candidate=candidate,source_form=form,boundary=boundary,reused_M1=reused,score=r['score'],logscore=float(log.sum()),map_nonzero_raw_cells=int(np.sum(h0[mask]>0)),map_nonzero_blurred_cells=int(np.sum(h[mask]>0)),mean_predicted_raw_hit=float(h0[mask].mean()),mean_predicted_blurred_hit=float(h[mask].mean()),mean_confidence_weighted_error=float(np.sum(conf[mask]*np.abs(p[mask]-h[mask]))/sum(conf[mask])),gaussian_index_before=r['gaussian_index_before'],gaussian_index_after=r['gaussian_index_after'],release_points=r['release_points'])
     rows.append(row);data[(bundle,candidate,form,boundary)]=dict(row=row,h=h,h0=h0,factor=factor)
     counts=root/'forward_calls'/f'anchor_{bundle}_{candidate}' if reused else path
     if (counts/'MOVEMENT_CELL_AGGREGATES.csv').exists():
      agg=readcsv(counts/'MOVEMENT_CELL_AGGREGATES.csv');counter=json.loads((counts/'MOVEMENT_COUNTERS.json').read_text())
      for phase in [0,1]:
       z=[x for x in agg if int(x['phase'])==phase];n=sum(int(x['moves']) for x in z);blocked=sum(int(x['blocked_encounters']) for x in z);zero=sum(int(x['zero_displacement']) for x in z)
       moves.append(dict(bundle=bundle,candidate=candidate,source_form=form,boundary=boundary,phase='warmup' if phase==0 else 'record',moves=n,blocked_encounters=blocked,zero_displacement=zero,zero_fraction=zero/n,total_displacement_m=sum(float(x['total_displacement_m']) for x in z),**{'global_'+k:v for k,v in counter.items()}))
 comparisons=[]
 for bundle in ['T','W']:
  for form in ['uniform','point']:
   for boundary in ['native','slide']:
    a=data[bundle,'C7',form,boundary];b=data[bundle,'K2',form,boundary];delta=np.log(b['factor'])-np.log(a['factor'])
    comparisons.append(dict(bundle=bundle,source_form=form,boundary=boundary,true_score=a['row']['score'],wrong_score=b['row']['score'],wrong_over_true_score=b['row']['score']/a['row']['score'],wrong_minus_true_logscore=float(sum(delta[mask])),selection='C7' if a['row']['score']>b['row']['score'] else 'K2'))
    for idx in np.flatnonzero(mask):
     percell.append(dict(bundle=bundle,source_form=form,boundary=boundary,cell_index=int(idx),grid_i=inp[idx]['grid_i'],grid_j=inp[idx]['grid_j'],measured_belief=p[idx],confidence=conf[idx],true_prediction=a['h'][idx],wrong_prediction=b['h'][idx],wrong_minus_true_log_factor=delta[idx]))
 effects=[]
 for bundle in ['T','W']:
  base=next(x for x in comparisons if x['bundle']==bundle and x['source_form']=='uniform' and x['boundary']=='native')
  for x in comparisons:
   if x['bundle']==bundle:effects.append(dict(**x,log_advantage_change_vs_native_uniform=x['wrong_minus_true_logscore']-base['wrong_minus_true_logscore'],odds_ratio_vs_native_uniform=x['wrong_over_true_score']/base['wrong_over_true_score']))
 summary=dict(status='FACTORIAL_COMPLETE_SOURCE_AND_BOUNDARY_DISCRIMINATION',all_8_contrasts_select_wrong=all(x['selection']=='K2' for x in comparisons),wrong_over_true_ratios=comparisons,intervention_effects=effects,physics_conclusion='Neither exact point source nor isolated tangential wall response reverses wrong-source preference in either frozen RNG bundle. These two interventions do not explain away the B4 pairwise source mismatch.',limitations='Two fixed RNG initial-state bundles are not independent physical realizations; point is truth-selected oracle; slide is GADEN-inspired 2D boundary variant rather than full GADEN; no localization/posterior update or 3D new gas.')
 return dict(summary=summary,rows=rows,comparisons=effects,percell=percell,moves=moves)
if __name__=='__main__':
 default=Path(__file__).resolve().parent
 if not (default/'snapshot').exists():default=Path(__file__).resolve().parents[3]/'outputs/PMFS_M3_PHYSICAL_ROOT_DISCRIMINATION_20261010/boundary_point_experiment'
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=default);ap.add_argument('--write',action='store_true');a=ap.parse_args();r=analyse(a.root)
 if a.write:
  for fn,rows in [('FORWARD_SCORE_AND_SUPPORT.csv',r['rows']),('PAIRWISE_FACTORIAL_EFFECTS.csv',r['comparisons']),('PAIRWISE_PER_CELL_DIFFERENCES.csv',r['percell']),('MOVEMENT_PHASE_SUMMARY.csv',r['moves'])]:
   p=a.root/fn;assert not p.exists();dumpcsv(p,rows)
  p=a.root/'FACTORIAL_RESULT.json';assert not p.exists();p.write_text(json.dumps(r['summary'],indent=2)+'\n',encoding='utf-8')
 print(json.dumps(r['summary'],indent=2))
