"""A runnable sensor→M1→posterior→M2→M3→sensor research loop.

Only run_control is bundled as an environment. Native ROS/GADEN actions require
a qualified backend, not access to future held-out cubes by the policy.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import json,time
import numpy as np
from .channel import JointPosterior,FiniteChannel
from .ledger import RawObservationLedger
from .data import SynchronousBlock,DataQualification
from .m1_opponent import SourceContrastModel,OpponentBank,calibrate_source_contrast
from .m1_opponent.raw_joint import calibrate_raw_joint,load_observation_model
from .m2_boundary import BoundaryMemoryConfig,CausalBoundaryMemory,FormationGeometry,score_paired_formations,rank_by_maxmin
from .m3_audit import CoveragePlanner,AuditLedger
from .navigation.geometry import make_actions,simultaneous_paths_clear
from .navigation.crossings import CrossingDetector
from .evaluation.control_backend import ControlledPlume
from .evaluation.metrics import source_metrics
from .evaluation.maps import export_source_map
from .baselines import joint_eig,standard_chernoff


CONTROL_SOURCES=np.array([[-1.,-2.],[-1.,0.],[-1.,2.],[1.,-2.],[1.,0.],[1.,2.]])
CONTROL_CENTERS=np.array([[2.,-2.],[2.,0.],[2.,2.],[4.,-2.],[4.,0.],[4.,2.]])


def control_backend():
    return ControlledPlume(CONTROL_SOURCES,make_actions(CONTROL_CENTERS,separations=(.8,1.6),angles=(0.,np.pi/2)))


def calibrate_control(directory,n_worlds=32,variant='secondary'):
    out=Path(directory);out.mkdir(parents=True,exist_ok=True)
    if (out/'operator.json').exists():raise ValueError("model exists; do not overwrite a frozen calibration")
    env=control_backend();raw=env.calibration(n_worlds)
    if variant=='raw_joint':
        model=calibrate_raw_joint(raw,env.times,env.contract,env.sources,
            [a.name for a in env.actions],[f's{i}' for i in range(len(env.sources))],[a.cost_s for a in env.actions])
    else:
        model=calibrate_source_contrast(raw,env.times,env.contract,env.sources,
            [a.name for a in env.actions],[f's{i}' for i in range(len(env.sources))],
            [a.cost_s for a in env.actions],OpponentBank.causal_default(),variant=variant,
            max_filters=2,calibration_world_ids=[f'control_cal_seed7721_block{i}' for i in range(n_worlds)])
    model.channel.metadata['action_points_m']=[a.points.tolist() for a in env.actions]
    model.channel.metadata['geometry']='controlled obstacle-free 2D; no UAV downwash model'
    model.save(out)
    # Predictive geometry comes from the calibration backend, not the runtime
    # world's source label or its future realization.
    means,grads=env.response_geometry(CONTROL_CENTERS)
    np.savez_compressed(out/'formation_predictions.npz',centers=CONTROL_CENTERS,means=means,gradients=grads,
                        action_readout_means=raw.mean(axis=(3,4,5)))
    return model


def _execute_control(env,action,truth,mechanism,rng,start,memory,detector,travel_rng=None,motion_samples=None):
    """Paid excursion with observed travel for M2 and a paired dwell for M1.

    The environment/evaluator owns truth. The planner never receives it.
    Control flight readout is analytical; dwell is calibrated by the same
    controlled law. This deliberately does not claim native sensor dynamics.
    """
    a=env.actions[action];dwell=a.dwell_s;travel=(a.cost_s-dwell)/2
    travel_rng=rng if travel_rng is None else travel_rng
    homes=np.array([[.4,0.],[-.4,0.]]);goals=a.points
    if not simultaneous_paths_clear(homes,goals,[[-5,-5],[8,8]],minimum_separation=.5):
        raise ValueError("paired trajectories violate the controlled safety geometry")
    raw,window_times=env.observe(action,truth,mechanism,rng,physical_start_s=start+travel)
    steps=int(round(a.cost_s/.1));entry_events=0;rejected_events=[];travel_frames=0
    for k in range(1,steps+1):
        elapsed=k*.1;now=start+elapsed
        if elapsed<=travel:
            travel_frames+=1
            pos=homes+(goals-homes)*elapsed/max(travel,1e-12)
            heading=float(np.arctan2(a.center[1],a.center[0]))
            sensed=env.mean_response(pos,truth,mechanism)*np.exp(travel_rng.normal(0,.15,2))
        elif elapsed<=travel+dwell+1e-8:
            pos=goals;heading=float(np.arctan2(a.center[1],a.center[0]))
            idx=min(len(raw)-1,max(0,int(round((elapsed-travel)/.1))))
            sensed=raw[idx]
        else:
            travel_frames+=1
            frac=(elapsed-travel-dwell)/max(travel,1e-12)
            pos=goals+(homes-goals)*min(1.,frac)
            heading=float(np.arctan2(-a.center[1],-a.center[0]))
            sensed=env.mean_response(pos,truth,mechanism)*np.exp(travel_rng.normal(0,.15,2))
        event=detector.update(now,bool(np.mean(sensed)>.3))
        if motion_samples is not None:
            motion_samples.append({'time_s':now,'position_xy':pos.mean(0).tolist(),'heading_rad':heading,
                                   'gas_detected':bool(np.mean(sensed)>.3)})
        try:
            result=memory.update(timestamp_s=now,position_xy=pos.mean(0),heading_rad=heading,event=event)
            entry_events+=int(result.event_used and event is not None and event.kind=='entry')
        except ValueError as exc:
            if event is None:raise
            rejected_events.append(str(exc))
            # A rejected event does not erase the legitimate motion sample.
            memory.update(timestamp_s=now,position_xy=pos.mean(0),heading_rad=heading)
    return raw,window_times,entry_events,rejected_events,travel_frames


def run_control(model_directory,output,*,truth=4,mechanism=1,seed=8801,budget_s=300.,
                planner_variant='full',m2=True,wrong_prior=False,max_steps=100,m2_variant=None):
    out=Path(output)
    if (out/'CONTROL_RESULT.json').exists():raise ValueError("output exists; keep receipts immutable")
    out.mkdir(parents=True,exist_ok=True)
    model=load_observation_model(model_directory);env=control_backend()
    m2_variant=('full' if m2 else 'none') if m2_variant is None else m2_variant
    if m2_variant not in ('none','geometry','boundary','full'):raise ValueError("unknown M2 variant")
    m2=m2_variant!='none'
    if model.channel.action_names!=[a.name for a in env.actions]:raise ValueError("model/control geometry mismatch")
    rng=np.random.default_rng(seed);prng=np.random.default_rng(seed+100000)
    prior=np.ones(len(env.sources))/len(env.sources)
    if wrong_prior:
        incumbent=(truth+1)%len(prior)
        prior=np.full(len(prior),1/(14874.6+len(prior)-1));prior[incumbent]*=14874.6
    posterior=JointPosterior(model.channel,prior)
    planner=CoveragePlanner(epsilon=0. if planner_variant=='no_coverage' else .2);audit=AuditLedger(model.channel,.05)
    ledger=RawObservationLedger(out/'raw_ledger')
    config=BoundaryMemoryConfig(mode='entry_only',entry_decay=.65,entry_gain=1.,min_pre_s=.2,min_post_s=.2,
           direction_window_s=.4,max_observation_gap_s=.101,max_memory_age_s=90.,min_speed=.02,max_speed=1.05,
           timing_validated=True,direction_noise_variance=.01)
    memory=CausalBoundaryMemory(config);detector=CrossingDetector(.2,.2)
    memory.update(timestamp_s=0.,position_xy=[0,0],heading_rad=0.)
    detector.update(0.,False)
    with np.load(Path(model_directory)/'formation_predictions.npz') as z:
        centers=z['centers'];means=z['means'];gradients=z['gradients']
        action_readout_means=z['action_readout_means'] if 'action_readout_means' in z else None
    geometry=FormationGeometry(np.array([-5.,-5.]),np.array([8.,8.]),.5,2.,1.)
    # A declared control covariance, not a measured native certainty claim.
    cov=np.broadcast_to(np.diag([1.,.5]),(len(centers),len(prior),2,2)).copy()
    costs=np.array([a.cost_s for a in env.actions]).reshape(len(centers),2,2)
    elapsed=0.;rows=[];events=0;startwall=time.perf_counter()
    for step in range(max_steps):
        affordable=model.channel.costs<=budget_s-elapsed+1e-9
        if not affordable.any():break
        tube=None
        try:
            tube=memory.make_return_tube(timestamp_s=elapsed,current_position_xy=[0,0],length=7.,base_radius=.5,
                 position_covariance=np.eye(2)*.05,drift_variance_rate=.02,sensor_delay_uncertainty_s=.03)
        except ValueError:
            tube=None
        f=score_paired_formations(center_xy=centers,source_means=means,source_gradients=gradients,
             joint_covariance=cov,costs=costs,separations=[.8,1.6],orientations_rad=[0,np.pi/2],geometry=geometry,
             return_tube=tube if m2_variant in ('boundary','full') else None,contrast_threshold=1e-9)
        if len(f.actions)!=model.channel.shape[0]:raise RuntimeError("formation/action index mismatch")
        mask=np.ones(len(env.actions),dtype=bool)
        if m2:
            if m2_variant=='boundary':
                # Direct direction-memory proposal: legal centers in the
                # tube, ordered by paid action cost, no source contrast.
                eligible=np.flatnonzero(f.in_tube)
                if len(eligible)==0:eligible=np.arange(len(f.actions))
                ranked=sorted(eligible,key=lambda i:(model.channel.costs[i],i))
            else:ranked=rank_by_maxmin(f)
            mask[:]=False
            mask[ranked[:max(1,len(env.actions)//3)]]=True
        mask &= affordable
        t0=time.perf_counter();predictive=posterior.predict()
        available=np.flatnonzero(affordable)
        if planner_variant in ('full','no_coverage','no_audit'):
            affordable_channel=FiniteChannel(model.channel.probabilities[available],model.channel.costs[available],
                model.channel.source_xy,[model.channel.action_names[j] for j in available],model.channel.source_ids,
                model.channel.nuisance_prior,model.channel.metadata)
            incumbent=int(np.argmax(posterior.source));challenger=None
            if planner_variant!='no_audit' and incumbent not in audit.compatible_now:
                candidates=[j for j in audit.compatible_now if j!=incumbent]
                if candidates:challenger=min(candidates,key=lambda j:(audit.log_e_values[j],j))
            plan=planner.plan(affordable_channel,predictive[available],posterior.source,step,
                             challenger=challenger,exploit_mask=mask[available])
            frequencies=np.zeros(len(env.actions));frequencies[available]=plan.probabilities;info=plan.info
            info['planning_action_indices']=available.tolist()
            info['audit_triggered_challenger']=challenger
        elif planner_variant=='joint_eig':
            value=joint_eig(predictive,posterior.source,model.channel.costs)
            value[~affordable]=-np.inf;frequencies=np.eye(len(env.actions))[int(np.argmax(value))]
            info={'reason':'joint_eig','no_automatic_stopping':True}
        elif planner_variant=='mother':
            allocation=standard_chernoff(predictive[available],posterior.source,model.channel.costs[available])
            frequencies=np.zeros(len(env.actions));frequencies[available]=allocation.probabilities
            info={'reason':'direct_cost_chernoff_no_coverage'}
        elif planner_variant=='uniform':
            frequencies=np.ones(len(env.actions))/len(env.actions);info={'reason':'uniform_coverage'}
        elif planner_variant=='variance_adapted':
            if action_readout_means is None:raise ValueError("recalibration required for readout means")
            means_a=np.einsum('asr,sr->as',action_readout_means,posterior.conditional_nuisance)
            central=means_a@posterior.source
            score=(means_a-central[:,None])**2@posterior.source
            score[~affordable]=-np.inf
            frequencies=np.eye(len(env.actions))[int(np.argmax(score))]
            info={'reason':'adapted_source_mean_variance','native_PMFS':False,
                  'confidence_map':'none in this adapted finite joint channel'}
        else:raise ValueError("unknown planner variant")
        # Budget truncation is declared: only affordable actions remain at
        # the end. Infinite-horizon coverage theorems do not apply there.
        frequencies[~affordable]=0
        if frequencies.sum()==0:frequencies=affordable.astype(float)
        frequencies/=frequencies.sum();action=int(prng.choice(len(frequencies),p=frequencies))
        info['executed_frequencies']=frequencies.tolist()
        info['budget_limited_action_set']=bool(not affordable.all())
        info['executed_expected_cost']=float(frequencies@model.channel.costs)
        planning_ms=1000*(time.perf_counter()-t0)
        audit.prepare(action,model_version='frozen-control-v7')
        dwell_rng=np.random.default_rng(np.random.SeedSequence([seed,step,0]))
        travel_rng=np.random.default_rng(np.random.SeedSequence([seed,step,1]))
        raw,times,used,rejected,travel_frames=_execute_control(env,action,truth,mechanism,dwell_rng,elapsed,memory,detector,travel_rng)
        events+=used
        xyz=np.column_stack([env.actions[action].points,np.ones(2)])
        block=SynchronousBlock(raw,times,xyz,('plus','minus'),DataQualification(
              synchronous_spatial=True,physical_clock=True,continuous_window=True,
              sensor_response_calibrated=True,scope='CONTROLLED_ANALYTICAL_LEVEL1_ONLY'),
              f'control-{seed}-{step}',f'control-world-{seed}',metadata={'truth_included':False,'synthetic':True})
        entry=ledger.append(block,action);symbol=model.encode(action,raw,times,env.contract)
        posterior.update(action,symbol,block.block_id);snapshot=audit.update(action,symbol,block.block_id)
        elapsed+=env.actions[action].cost_s
        row={'step':step,'action':action,'action_name':env.actions[action].name,'symbol':symbol,
             'physical_time_s':elapsed,'uav_seconds':2*elapsed,'posterior':posterior.source.tolist(),
             'map':posterior.map_points(),'audit_list':list(snapshot.compatible_now),
             'anytime_not_rejected_list':list(snapshot.not_rejected_since_start),
             'log_e_values':snapshot.log_e_values.tolist(),'m2_status':f.status,
             'm2_memory_entry_events':used,'rejected_boundary_events':rejected,
             'travel_scalar_samples':2*travel_frames,'dwell_scalar_samples':int(raw.size),
             'm2_has_causal_tube':tube is not None,'planning_ms':planning_ms,
             'policy':info,'ledger':entry,**source_metrics(posterior.source,truth,env.sources)}
        rows.append(row)
        with (out/'online_steps.jsonl').open('a',encoding='utf8') as fp:fp.write(json.dumps(row,ensure_ascii=False)+'\n')
    result={'level':1,'status':'RUNNABLE_CONTROLLED_LOOP_ONLY','native_scientific_benefit':False,
       'planner_variant':planner_variant,'m2_enabled':m2,'m2_variant':m2_variant,'m1_variant':model.channel.metadata['variant'],
       'wrong_prior_stress':wrong_prior,'truth_for_evaluator_only':truth,'mechanism_for_evaluator_only':mechanism,
       'seed':seed,'budget_s':budget_s,'paid_seconds':elapsed,'paid_uav_seconds':2*elapsed,'steps':len(rows),
       'entry_memory_updates':events,'wall_seconds':time.perf_counter()-startwall,
       'final':rows[-1] if rows else None,'risk_statement':audit.guarantee_scope,
       'all_source_candidates_retained':len(posterior.source)==len(env.sources),
       'audit_decisions_not_reused_as_likelihood':True,
       'posterior_scope':'paired dwell blocks only; travel stream informs geometry, not posterior likelihood',
       'fairness_limit':'M2 uses travel readout; matched policy ablations share it. Full-stream joint baseline is required for native scientific claims.',
       'phase_information_limit':'uniform phase absorbs source-dependent phase shift; this backend does not validate novel source information in motion phase',
       'randomness_contract':'dwell and travel streams independently keyed by (world seed, step); no sequential trajectory draw shifts subsequent dwell randomness',
       'model':'2D analytic footprint + controlled intermittent patches; no validated lake/rotor/ROS physics',
       'native_window_generation':'BLOCKED pending native GADEN qualification',
       'clock_semantics':'0.1s controlled clock; never inferred from House record indices'}
    (out/'CONTROL_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    export_source_map(model.channel.source_xy,posterior.source,out/'source_probability_map.npz')
    return result

