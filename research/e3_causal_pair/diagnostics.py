"""Additional read-only attribution from already completed trajectories.
No new predictor, retuning, bypassed-LOS scoring, or physical runs.
"""
import struct,csv,json,math
from pathlib import Path
import numpy as np
from analyze import O,OLD,rows,load,table,put
def main():
 schedule=rows(O/'schedule/QUERIES.csv');points=rows(O/'schedule/UNIQUE_POINTS.csv');constant=load(O/'event_control/CONSTANTS.json');xy=np.array([[float(p['x']),float(p['y'])] for p in points]);z=np.array([float(p['z']) for p in points]);plans=load(O/'PREREGISTERED_CAUSAL_CONTRACT.json');bounds=[]
 for source in ['true','rival']:
  for pred in plans['prediction_streams']:
   ident=source+'_'+pred['id'];values=[]
   with (O/'event_control'/(ident+'.particles.bin')).open('rb') as f:
    while b:=f.read(8):
     step,n=struct.unpack('<2I',b);v=np.frombuffer(f.read(n*16),dtype='<f4').reshape(n,4).astype(float)
     diff=v[:,None,:2]-xy[None,:,:];dcm2=(np.sum(diff**2,axis=2)+(.7-z[None,:])**2)*1e4
     centers=1e6*constant['moles_per_filament']/(math.sqrt(8*math.pi**3)*v[:,2]**3*constant['air_moles_per_cm3'])*v[:,3]
     values.append(np.sum(centers[:,None]*np.exp(-dcm2/(2*v[:,2,None]**2)),axis=0))
   values=np.array(values);assert values.shape==(200,65)
   for stop in range(8,14):
    q=next(r for r in schedule if r['group']=='historical' and int(r['stop'])==stop);pid=int(q['point_id']);v=values[:,pid]
    for count in [3,4,5]:
     mean=v[:200//count*count].reshape(-1,count).mean(1)
     bounds.append(dict(source=source,prediction=pred['id'],stop=stop,point_id=pid,samples_per_window=count,max_untruncated_no_LOS_gaussian_window_upper_ppm=float(mean.max()),upper_bound_never_crosses_threshold=bool(mean.max()<.1),scope='diagnostic analytic upper envelope only; never used to score/select/rescue; actual operator keeps nativeLOS and3sigma cutoff'))
 table(O/'READOUT_SUPPORT_UPPER_BOUND_DIAGNOSTIC.csv',bounds)
 # All previous actions remain frozen; only compare their realized signals.
 rr=rows(O/'PHYSICAL_WINDOWS.csv');group={}
 for r in rr:
  if r['group']=='action':group.setdefault((int(r['update']),r['action']),{}).setdefault(r['world'],[]).append(r)
 selected={r['update']:r['selection'] for r in load(OLD/'ORDINARY_EIG_SELECTED_BEFORE_READOUT.json')}
 observed=[]
 for (update,action),worlds in group.items():
  seq={k:np.array([float(r['mean_ppm']) for r in sorted(rs,key=lambda r:int(r['window']))]) for k,rs in worlds.items()}
  for arm in ['known_release_continuous_MSE','unknown_amplitude','binary_Brier']:
   wins=[]
   for tr,te in [(0,1),(1,0)]:
    for actual in ['true','rival']:
     y=seq[f'{actual}_r{te}'];loss={}
     for h in ['true','rival']:
      x=seq[f'{h}_r{tr}'];gain=max(0,float(x@y)/max(float(x@x),1e-30)) if arm=='unknown_amplitude' else 1.
      loss[h]=float(np.mean(((y>.1).astype(float)-(x>.1).astype(float))**2)) if arm=='binary_Brier' else float(np.mean((y-gain*x)**2))
     other='rival' if actual=='true' else 'true';wins.append(.5 if abs(loss[actual]-loss[other])<1e-12 else float(loss[actual]<loss[other]))
   observed.append(dict(update=update,action=action,arm=arm,correct_tie_aware_of4=sum(wins),original_IG_selected=action==selected[update],true_r0_pattern=''.join(map(str,(seq['true_r0']>.1).astype(int))),true_r1_pattern=''.join(map(str,(seq['true_r1']>.1).astype(int))),rival_r0_pattern=''.join(map(str,(seq['rival_r0']>.1).astype(int))),rival_r1_pattern=''.join(map(str,(seq['rival_r1']>.1).astype(int))),same_time_budget_s=4.5,gas_windows_per_action=5,source_label_used_in_selection=False,scope='realized opportunity diagnostic; no reference library enters deployment or a new action choice'))
 table(O/'FIXED_ACTION_PHYSICAL_OBSERVABILITY.csv',observed)
 # Mole-flux conservation is algebraic, independent of target outcomes.
 put(O/'MASS_WEIGHT_ACCOUNTING.json',dict(warmup=dict(paths_per_step=5,dt_s=.2,filament_equivalent_weight_per_path=.4,total_equivalent_filaments_per_second=5*.4/.2),record=dict(paths_per_step=5,dt_s=.1,filament_equivalent_weight_per_path=.2,total_equivalent_filaments_per_second=5*.2/.1),both_equal_physical10=True,physical_moles_per_filament=constant['moles_per_filament'],fitted_gain_in_predictor=False,diagnostic_unknown_gain_fit='separate physical-observability reference control only'))
 print(json.dumps(dict(true_upper_bounds=[r for r in bounds if r['source']=='true' and r['samples_per_window']==4],selected_action_results=[r for r in observed if r['original_IG_selected']]),indent=2))
if __name__=='__main__':main()
