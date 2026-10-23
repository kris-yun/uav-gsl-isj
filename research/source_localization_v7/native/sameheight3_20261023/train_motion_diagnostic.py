"""Post-primary exploratory TRAIN-only necessary conditions. No DEV queries."""
import itertools,json,time
import numpy as np
from protocol import *
from analysis import load,cross,csvout
from mirror_shadow import feature_sets
from gsl_discrimination.m1_opponent import OpponentBank,SamplingContract

def main():
 assert not (OUT/'TRAIN_MOTION_NECESSITY.json').exists()
 start=time.perf_counter();c=config();v,t,r=load('train');truth=np.repeat(np.arange(3),2)
 f=json.loads((OUT/'MIRROR_MODEL_FREEZE.json').read_text());bank=OpponentBank.from_dict(f['bank']);contract=SamplingContract(**f['contract'])
 pairs=np.array(list(itertools.combinations(range(30),2)));pp=c['all_probe_pools']
 positions=np.array([[float(x['center_x_m']),float(x['center_y_m']),float(x['z_m'])] for x in pp]);sep=np.linalg.norm(positions[pairs[:,0]]-positions[pairs[:,1]],axis=-1)
 rows=[]
 for anchor in c['window_anchors_s']:
  idx=np.flatnonzero((t>=anchor)&(t<=anchor+20));tt=t[idx];x=v[:,:,idx,:]
  raw=np.stack([x[...,pairs[:,0]],x[...,pairs[:,1]]],axis=-1).transpose(0,1,3,2,4)
  features=feature_sets(raw,tt,bank,contract)
  order=np.lexsort((raw[...,1],raw[...,0]),axis=-1);unordered=np.take_along_axis(raw,order[...,None],axis=-2)
  features['unordered_mirror']=feature_sets(unordered,tt,bank,contract)['frozen_all_mirror_features']
  counts={name:np.sum(cross(a,False)[0]==truth[:,None],axis=0) for name,a in features.items()}
  # At least three positive native records on both sides in EACH B/C world.
  # This only tests ideal-readout support; the 0.1ppm scope is listed separately.
  active=np.all(np.sum(raw[1:]>0,axis=-2)>=3,axis=(0,1,3))
  active_01=np.all(np.sum(raw[1:]>=.1,axis=-2)>=3,axis=(0,1,3))
  varying=np.all(np.ptp(raw[1:],axis=-2)>0,axis=(0,1,3))
  best=np.maximum.reduce([counts[n] for n in ('static_two_means','full_joint_window','ordinary_delayed_linear')])
  mirror=counts['frozen_all_mirror_features'];un=counts['unordered_mirror']
  for k,(i,j) in enumerate(pairs):
   rows.append({'anchor_s':anchor,'probe_L':int(i+1),'probe_R':int(j+1),'separation_m':float(sep[k]),
    'eligible_geometry':bool(.3<=sep[k]<=2.),'BC_all_four_worlds_both_positive_min3':bool(active[k]),
    'BC_all_four_worlds_both_hit_0p1_min3':bool(active_01[k]),'BC_both_sides_vary_all_four':bool(varying[k]),
    'static_correct':int(counts['static_two_means'][k]),'full_joint_correct':int(counts['full_joint_window'][k]),
    'ordinary_delay_correct':int(counts['ordinary_delayed_linear'][k]),'all_mirror_correct':int(mirror[k]),
    'unordered_mirror_correct':int(un[k]),'mirror_above_best_ordinary':int(mirror[k]-best[k]),
    'mirror_above_unordered':int(mirror[k]-un[k]),
    'exploratory_necessary_condition':bool(active[k] and varying[k] and .3<=sep[k]<=2. and mirror[k]>best[k] and mirror[k]>un[k])})
 csvout('EXPLORATORY_TRAIN_MOTION_ALL_PAIRS.csv',rows)
 candidates=[x for x in rows if x['exploratory_necessary_condition']]
 write('TRAIN_MOTION_NECESSITY.json',{'status':'POST_PRIMARY_TRAIN_ONLY_EXPLORATION_NOT_VALIDATION','pair_windows':len(rows),
 'eligible_bilateral_varying_windows':sum(x['eligible_geometry'] and x['BC_all_four_worlds_both_positive_min3'] and x['BC_both_sides_vary_all_four'] for x in rows),
 'eligible_bilateral_above_0p1_varying_windows':sum(x['eligible_geometry'] and x['BC_all_four_worlds_both_hit_0p1_min3'] and x['BC_both_sides_vary_all_four'] for x in rows),
 'mirror_above_ordinary_and_unordered_candidates':candidates,
 'all_rows_retained':True,'no_new_DEV_location_or_time_read':True,'primary_selected_pair_not_changed':True,
 'limitations':['post-primary exploratory diagnostic','two TRAIN master-seed groups only','no guarantee finite nearest-profile performance equals information-theoretic necessity','not a new M1 fit or a heldout gain'],
 'wall_s':time.perf_counter()-start})
 print('TRAIN_MOTION_DIAGNOSTIC_COMPLETE',len(rows),'eligible bilateral',sum(x['eligible_geometry'] and x['BC_all_four_worlds_both_positive_min3'] and x['BC_both_sides_vary_all_four'] for x in rows),'candidate',len(candidates))
if __name__=='__main__':main()
