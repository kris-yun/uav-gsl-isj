#!/usr/bin/env python3
"""Executable LEVEL-1 JSONL backend example, not a ROS or GADEN emulator."""
from pathlib import Path
from dataclasses import asdict
import argparse,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gsl_discrimination.engine import control_backend,_execute_control,CONTROL_CENTERS
from gsl_discrimination.m2_boundary import BoundaryMemoryConfig,CausalBoundaryMemory
from gsl_discrimination.navigation.crossings import CrossingDetector
from gsl_discrimination.data import SynchronousBlock,DataQualification

p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source',type=int,default=4)
p.add_argument('--mechanism',type=int,default=1);p.add_argument('--seed',type=int,default=8804)
args=p.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
env=control_backend();clock=0.;step=0
cfg=BoundaryMemoryConfig(mode='entry_only',entry_decay=.65,entry_gain=1.,min_pre_s=.2,min_post_s=.2,
    direction_window_s=.4,max_observation_gap_s=.101,max_memory_age_s=90.,min_speed=.02,max_speed=1.05,
    timing_validated=True,direction_noise_variance=.01)
memory=CausalBoundaryMemory(cfg);memory.update(timestamp_s=0.,position_xy=[0,0],heading_rad=0.)
detector=CrossingDetector(.2,.2);detector.update(0.,False)
for line in sys.stdin:
    request=json.loads(line)
    try:
        if request['method']=='describe':
            result={'schema':'gsl-action-bridge-1','scope':'CONTROLLED_LEVEL1',
              'future_truth_available_to_policy':False,'action_names':[a.name for a in env.actions],
              'action_cost_upper_bounds_s':[a.cost_s for a in env.actions],'safety_checked_before_execute':True,
              'boundary_config':asdict(cfg),'initial_state':{'position_xy':[0,0],'time_s':0.,'heading_rad':0.,'gas_detected':False},
              'formation_geometry':{'lower_xy':[-5,-5],'upper_xy':[8,8],'min_separation':.5,'max_separation':2.,
                  'linearization_radius':1.,'separations':[.8,1.6],'orientations_rad':[0,np.pi/2],
                  'tube_length':7.,'tube_base_radius':.5,'position_covariance':(np.eye(2)*.05).tolist(),
                  'drift_variance_rate':.02,'sensor_delay_uncertainty_s':.03},
              'calibrated_even_odd_covariance':np.broadcast_to(np.diag([1.,.5]),(len(CONTROL_CENTERS),len(env.sources),2,2)).tolist(),
              'qualification_receipt':'analytical construction only; no physical or flight qualification'}
        elif request['method']=='execute':
            action=int(request['action']);cost=env.actions[action].cost_s
            if cost>request['remaining_budget_s']:raise ValueError('action cannot fit declared budget')
            motion=[]
            raw,times,_,_,_=_execute_control(env,action,args.source,args.mechanism,
                np.random.default_rng(np.random.SeedSequence([args.seed,step,0])),clock,memory,detector,
                np.random.default_rng(np.random.SeedSequence([args.seed,step,1])),motion_samples=motion)
            q=DataQualification(synchronous_spatial=True,physical_clock=True,continuous_window=True,
                                sensor_response_calibrated=True,scope='CONTROLLED_LEVEL1')
            block=SynchronousBlock(raw,times,np.column_stack([env.actions[action].points,np.ones(2)]),
                  ('plus','minus'),q,f'bridge-{args.seed}-{step}',f'bridge-world-{args.seed}')
            path=out/f'block{step:04d}.npz';block.save_npz(path);clock+=cost;step+=1
            result={'block_path':str(path),'cost_s':cost,'safety_passed':True,'motion_samples':motion,
                    'end_state':{'time_s':clock,'position_xy':[0,0],'heading_rad':0.}}
        else:raise ValueError('unsupported method')
        print(json.dumps({'id':request['id'],'result':result}),flush=True)
    except Exception as exc:print(json.dumps({'id':request['id'],'error':str(exc)}),flush=True)
