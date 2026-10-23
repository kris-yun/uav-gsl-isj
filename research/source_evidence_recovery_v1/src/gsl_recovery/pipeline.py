"""Receding-block active loop: commit plan, execute all actions, replay once.

Environment truth is kept in a private environment object. Planner calls receive
only hypothetical source coordinates, model, history, and legal actions.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib,json,time,numpy as np
from .types import Action,Mechanism,observation_to_dict,observation_from_dict
from .io import write_json,read_json,sha256
from .m1_generator import JointObservationGenerator
from .m1_teacher import ControlledPlumeBackend,make_training_episodes
from .m2_replay import EvidenceLedger,ReplayEngine
from .m3_codebook import JointCodebookBuilder,CorruptionChannel
from .m3_planner import RobustCounterEvidencePlanner
from .navigation import RectWorld,action_blocks,route_cost
from .posterior import source_map,posterior_metrics

def default_sources():return np.array([[.5,.5],[2.5,.5],[.5,2.5],[2.5,2.5]])

def default_mechanisms():return [Mechanism(),Mechanism('sensor_offset',3,None,1.),Mechanism('sensor_offset',3,None,-1.)]

def inference_version(model,mechanisms,sources):
    payload={'generator':model.version,'mechanisms':[asdict(m) for m in mechanisms],'sources':np.asarray(sources).tolist(),'readout':'binary_hit_v1'}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:20]

def generate_controlled_dataset(out_dir,seed=11,n_train=64,length=10):
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(seed)
    backend=ControlledPlumeBackend();sources=default_sources();entries=[]
    # Three training source points, fourth source entirely held out.
    for split,count,panel,offset in [('train',n_train,sources[:3],0),('development',12,sources[:3],10000),('frozen_test',12,sources[3:],20000)]:
        for i in range(count):
            s=panel[i%len(panel)];actions=[Action(float(x),float(y),1.,float(t+1),1.) for t,(x,y) in enumerate(rng.uniform(0,3,(length,2)))]
            mechanism=default_mechanisms()[(i//len(panel))%3];obs=backend.simulate_episode(s,actions,mechanism,np.random.default_rng(seed+offset+i))
            metadata={'scene':'controlled_reference','source_group':','.join(map(str,s)),'wind_group':'AR_local_wind_v1','realization_id':f'{seed}-{offset+i}','split':split,'frame':'controlled_xy','units':{'position':'m','wind':'m/s','gas':'binary_hit'},'readout':'binary_hit','propagation_qualified':True,'geometry_qualified':True,'candidate_support_qualified':True,'qualification_scope':'controlled analytic benchmark only; not GADEN/House','holdout_axis':'source' if split=='frozen_test' else 'realization','backend':'ControlledPlumeBackend'}
            record={'schema_version':1,'metadata':metadata,'source':s.tolist(),'mechanism':asdict(mechanism),'candidates':sources.tolist(),'observations':[observation_to_dict(o) for o in obs]}
            filename=f'{split}/episode_{i:04d}.json';write_json(out/filename,record);entries.append({'path':filename,'sha256':sha256(out/filename)})
    manifest={'schema_version':1,'scope':'controlled_training_and_holdout','seed':seed,'episodes':entries,'frozen_before_training':True}
    write_json(out/'manifest.json',manifest);return {'status':'CREATED','manifest':str(out/'manifest.json'),'episodes':len(entries)}

def train_from_manifest(manifest_path,out_dir,variant='Bprime',seed=0,maxiter=200):
    from .data.qualification import audit_manifest,load_episode
    from .m1_generator.model import GeneratorConfig
    start=time.perf_counter();manifest_path=Path(manifest_path);audit=audit_manifest(manifest_path,for_training=True)
    if audit['status']!='PASS':raise ValueError('DATA_QUALIFICATION_FAILED:'+str(audit))
    manifest=read_json(manifest_path);episodes=[];controlled=True
    for e in manifest['episodes']:
        raw=read_json(manifest_path.parent/e['path'])
        if raw['metadata']['split']!='train':continue
        record,obs=load_episode(manifest_path.parent/e['path'],True)
        controlled=controlled and record['metadata'].get('backend')=='ControlledPlumeBackend'
        episodes.append({'source':np.array(record['source']),'observations':obs,'mechanism':Mechanism(**record.get('mechanism',{})),'split':'train','episode_id':e['path']})
    if not episodes:raise ValueError('No qualified training episodes')
    if variant not in ('Aprime','adapted') and not controlled:raise RuntimeError('BLOCKED_NATIVE_TEACHER: implement instrumented native JVP, wind-nullspace lift and branch trace; no synthetic teacher may label real data')
    model=JointObservationGenerator();receipt=model.fit(episodes,variant,ControlledPlumeBackend() if controlled else None,seed,maxiter)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);model.save(out/'model.npz')
    receipt.update(wall_seconds=time.perf_counter()-start,manifest_sha256=sha256(manifest_path),training_data_scope='controlled_reference' if controlled else 'qualified_external',model_sha256=sha256(out/'model.npz'),teacher_native_status='BLOCKED_NOT_INSTRUMENTED',frozen_test_used_for_training=False)
    write_json(out/'training_receipt.json',receipt);write_json(out/'data_audit.json',audit)
    return receipt

def evaluate_manifest(manifest_path,model_path,out_dir,split='frozen_test',m2_variant='Bprime'):
    from .data.qualification import load_episode
    model=JointObservationGenerator.load(model_path);manifest_path=Path(manifest_path);manifest=read_json(manifest_path);rows=[]
    for entry in manifest['episodes']:
        raw=read_json(manifest_path.parent/entry['path'])
        if raw['metadata']['split']!=split:continue
        record,history=load_episode(manifest_path.parent/entry['path']);sources=np.array(record['candidates']);engine=ReplayEngine(model,sources,default_mechanisms(),mechanism_prior=[.8,.1,.1],model_version=model.version)
        result=engine.infer(history,m2_variant)
        row={'episode':entry['path'],'split':split,**posterior_metrics(sources,result.source_posterior,record['source'])};rows.append(row)
    if not rows:raise ValueError('No episodes in requested split')
    metric_keys=['map_error_m','top5_centroid_error_m','true_log_margin','brier','true_rank']
    summary={'status':'COMPLETE_CONTROLLED_REFERENCE' if raw['metadata'].get('backend')=='ControlledPlumeBackend' else 'COMPLETE_EXTERNAL_REPLAY','split':split,'episodes':len(rows),'top1_rate':float(np.mean([x['true_top1'] for x in rows])),'model_sha256':sha256(model_path),'m2_variant':m2_variant,**{k:float(np.mean([r[k] for r in rows])) for k in metric_keys},'scientific_claim':'descriptive reference results; no native PMFS or House performance claim'}
    write_json(Path(out_dir)/'episodes.json',rows);write_json(Path(out_dir)/'summary.json',summary);return summary

class _Environment:
    def __init__(self,source,mechanism,seed):self._source=np.asarray(source);self._mechanism=mechanism;self._rng=np.random.default_rng(seed);self._backend=ControlledPlumeBackend()
    def execute(self,history,actions):return self._backend.sample_future(history,actions,self._source,self._mechanism,self._rng)

def run_closed_loop(model_path,out_dir,seed=101,rounds=3,draws=128,block_length=5,planner_variant='Bprime',m2_variant='Bprime',truth_index=3,environment_mode=1,diagnosis_path=None):
    start=time.perf_counter();out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    model=JointObservationGenerator.load(model_path);sources=default_sources();mechanisms=default_mechanisms()
    environment=_Environment(sources[truth_index],mechanisms[environment_mode],seed)
    version=inference_version(model,mechanisms,sources)
    ledger=EvidenceLedger();engine=ReplayEngine(model,sources,mechanisms,mechanism_prior=[.8,.1,.1],model_version=version)
    planner=RobustCounterEvidencePlanner(len(sources),channel=CorruptionChannel(max_flips=1),total_alpha=.05,seed=seed+1)
    builder=JointCodebookBuilder(model,model_version=version);rng=np.random.default_rng(seed+2)
    current=(1.5,1.5);now=0.;world=RectWorld(bounds=(-.5,3.5,-.5,3.5));events=[]
    diagnosis=None
    if diagnosis_path:
        from .m2_diagnosis import DifferentialDiagnoser
        diagnosis=DifferentialDiagnoser.load(diagnosis_path)
    for t in range(rounds):
        history=ledger.history;result=engine.infer(history,m2_variant)
        blocks=action_blocks(current,now,world,length=block_length,budget=4)
        books=builder.build(history,blocks,sources,mechanisms,draws,rng,delta=.01/((t+1)*(t+2)),costs=[route_cost(b,current) for b in blocks])
        plan=planner.plan(books,result.source_posterior,result.conditional_mechanism_posterior,planner_variant)
        committed={'round':t,'model_version':version,'history_ids':[o.uid for o in history],'actions':[asdict(a) for a in plan.actions],'null_source':plan.null_source,'challenge_indices':plan.challenge_indices,'reason':plan.reason,'alpha':plan.test.alpha if plan.test else None,'MC_delta':books[plan.action_index].confidence_failure_probability,'source_posterior_before':result.source_posterior,'test_power_bound':plan.test.alternative_power_bound if plan.test else None}
        # Written before any environmental acquisition; prospective audit anchor.
        write_json(out/f'round_{t:03d}_plan.json',committed)
        observations=environment.execute(history,plan.actions)
        outcome=planner.observe(plan,observations,model_version=version)
        ledger.extend(observations)
        result=engine.infer(ledger.history,m2_variant)
        budgeted=None
        if diagnosis is not None:
            b=engine.infer_budgeted(ledger.history,diagnosis,np.random.default_rng(seed+1000+t),draws=4,reference_draws=4)
            budgeted={**b,'exact_posterior_L1_error':float(np.abs(np.asarray(b['source_posterior'])-result.source_posterior).sum())}
        event={'round':t,'plan_sha256':sha256(out/f'round_{t:03d}_plan.json'),'observations':[observation_to_dict(o) for o in observations],'test_outcome':outcome,'source_posterior':result.source_posterior,'joint_posterior':result.joint_posterior,'map':source_map(sources,result.source_posterior),'replay_max_error':max([abs(r['full_recompute_error']) for r in result.records if r['full_recompute_error'] is not None]+[0]),'budgeted_diagnosis_audit':budgeted}
        write_json(out/f'round_{t:03d}_update.json',event);events.append(event)
        now=plan.actions[-1].time;current=(plan.actions[-1].x,plan.actions[-1].y)
    write_json(out/'history.json',{'observations':[observation_to_dict(o) for o in ledger.history]})
    final=engine.infer(ledger.history,m2_variant)
    summary={'status':'PASS_CONTROLLED_CLOSED_LOOP','rounds':rounds,'observations':len(ledger),'planner_variant':planner_variant,'m2_variant':m2_variant,'truth_used_by_planner':False,'whole_blocks_committed':True,'posterior_mass':float(final.source_posterior.sum()),'risk_alpha_spent':planner.risk.spent,'risk_MC_budget_spent':sum(v.get('MC_failure_budget',0) for v in planner.risk.tests),'risk_scope':'generator distribution plus MC bound; does not certify physical model misspecification','counterevidence_rejections':sum(e['test_outcome']['rejected'] for e in events),'fallback_rounds':sum(read_json(out/f'round_{t:03d}_plan.json')['reason']!='max_score' for t in range(rounds)),'replay_max_error':max(e['replay_max_error'] for e in events),'diagnosis_budgeted_used':diagnosis is not None,'wall_seconds':time.perf_counter()-start,'metrics_evaluator_only':posterior_metrics(sources,final.source_posterior,sources[truth_index],truth_index),'native_gain_claim':False}
    write_json(out/'summary.json',summary);write_json(out/'risk_ledger.json',planner.risk.tests);return summary
