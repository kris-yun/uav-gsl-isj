from common_n import *
import csv,numpy as np,importlib.util,math
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8',newline='')))
def wc(p,r):
 with Path(p).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(r[0]),lineterminator='\n');w.writeheader();w.writerows(r)
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
raw=module('nmc_spot_raw',BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010/independent_raw_query_verify/verify_raw_receiver_queries.py');cache=module('nmc_spot_components',BASE/'work/pmfs_rk2b_continuous_20261010/cache_native.py')
parent=BASE/'outputs/PMFS_M2_PROCESS_OBSERVATION_DISCRIMINATION_20261010';occ=raw.occupancy(parent/'frozen_B4_inputs/derived_B4/OccupancyGrid3D.csv');D=Path('D:/ZYC/A-gas/workspace/PMFS_NATIVE_MECHANISM_CLOSURE_R1_DATA_20261011');free=np.array([r['occupancy']=='1' for r in rows(CORE/'native_inputs/inputs/DERIVED/input.csv')]);summary=[];top=[]
for c in ['C7','K2']:
 for rep in [0,1]:
  folder=D/f'readout/B4_{c}_{rep}';events=rows(folder/'EVENTS_O1.csv');lineage=rows(folder/'SELECTED_FRAME_LINEAGE.csv')
  for b in [0,25,49]:
   frame=int(lineage[b]['frame']);fp=parent/f'native_reference_evidence/realizations/{c}_{rep}/bank/iteration_{frame}';assert sha(fp)==lineage[b]['SHA256'];desc=raw.snapshot(fp);point=np.array([[float(events[b][k]) for k in ['x','y','z']]],dtype=np.float32)
   matrix,totals,eligible,blocked,positive=cache.cutoff_and_contributions(desc['filaments'],point,desc,occ,raw);total=float(totals[0]);native=float(events[b]['concentration_ppm']);assert abs(total-native)<=3e-7+5e-6*abs(native)
   fil=desc['filaments'];xy=np.floor((fil[:,:2]-np.array([np.float32(-7.55),np.float32(-7.88)]))/.25).astype(int);inrange=(xy[:,0]>=0)&(xy[:,0]<34)&(xy[:,1]>=0)&(xy[:,1]<45);inside=np.zeros(len(fil),bool);inside[inrange]=free[xy[inrange,0]+34*xy[inrange,1]];weights=matrix[:,0].astype(float);weight=weights.sum()
   receivercell=np.floor((point[0,:2]-np.array([np.float32(-7.55),np.float32(-7.88)]))/.25).astype(int);same=(xy==receivercell).all(axis=1)
   summary.append(dict(candidate=c,reference=rep,block=b,frame=frame,physical_target_s=events[b]['physical_target_s'],native_ppm=native,independent_ppm=total,absolute_error=abs(total-native),contributors=int(positive[0]),LOS_blocked=int(blocked[0]),any_center_in_receiver_cell=bool(same.any()),PID_detected=native>float(np.float32(.1)),ppm_from_current_centres_outside_navigation=float(weights[~inside].sum()),current_outside_navigation_contribution_fraction=float(weights[~inside].sum()/weight) if weight else 0,weighted_height_m=float(np.sum(weights*fil[:,2])/weight) if weight else '',weighted_sigma_cm=float(np.sum(weights*fil[:,3])/weight) if weight else '',not_root_cause_percentage=True,no_stable_particle_trajectory_ID=True))
   for i in np.argsort(weights)[::-1][:20]:
    if weights[i]<=0:continue
    top.append(dict(candidate=c,reference=rep,block=b,frame=frame,snapshot_local_row=int(i),x=float(fil[i,0]),y=float(fil[i,1]),z=float(fil[i,2]),sigma_cm=float(fil[i,3]),receiver_ppm_contribution=weights[i],current_navigation_supported=bool(inside[i]),row_is_not_stable_particle_ID=True))
wc(CORE/'RAW_PHYSICAL_CONTRIBUTION_SPOTCHECK.csv',summary);wc(CORE/'RAW_RECEIVER_TOP_CONTRIBUTORS.csv',top);dump(CORE/'PHYSICAL_SPOTCHECK_SCOPE.json',dict(status='PASS_12_PREDEFINED_EXISTING_REFERENCE_QUERIES',new_generation=0,new_candidate_forwards=0,source_choices='C7/K2 historical posthoc pair',snapshot_blocks=[0,25,49],interpretation='Current-state sensor contributions, not reconstructed paths or percent causal responsibility',maximum_abs_ppm_difference=max(r['absolute_error'] for r in summary)))
print(json.dumps({'status':'PASS_RAW_PHYSICS_SPOTCHECK','queries':len(summary),'maximum_error':max(r['absolute_error'] for r in summary)}))
