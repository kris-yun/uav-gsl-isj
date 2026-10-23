"""V2 datasets, evaluation and compatibility with the retained M2/M3 loop."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib,json,math,time
import numpy as np
from scipy.special import expit,logsumexp
from .types import Action,Observation,Mechanism,observation_to_dict


def generate_neural_engineering(out,seed=31,episodes=48,length=8):
    """Manufactured 3D wind bank + intermittent sensor system, explicitly not CFD."""
    from .m1_neural import NeuralConfig,Geometry
    from .m1_neural.teacher import PhysicalBank
    from .m1_neural.training import write_dataset
    out=Path(out);rng=np.random.default_rng(seed)
    candidates=np.array([[.5,.5],[.5,2.5],[2.5,.5],[2.5,2.5]])
    vectors=np.array([[.7,.1,0.],[-.2,.6,.03],[-.6,-.1,-.02],[.1,-.6,0.]])
    grid=np.array([[x,y,z] for x in (0.,1.5,3.) for y in (0.,1.5,3.) for z in (.2,1.2)])
    points=np.array([np.c_[grid,np.zeros(len(grid)),np.repeat(w[None,:],len(grid),axis=0)] for w in vectors],np.float32)
    bank=PhysicalBank(points,np.zeros(4),{'split':'train','source_independent_exogenous':True,
         'wind_units':'m/s','position_units':'m','time_units':'s','scope':'ENGINEERING_ONLY','static_wind':True,
         'world_ids':[f'manufactured_wind_{i}' for i in range(4)],'not_GADEN':True,
         'interpretation':'manufactured smooth wind contexts; not measured/CFD physics'})
    bank.save(out/'bank')
    geom=Geometry([[0.,0.,.2],[0.,3.,.2],[3.,0.,.2],[3.,3.,.2]],[1.]*4,'manufactured_square_boundary')
    cfg=NeuralConfig(length_scale=2.,wind_scale=1.,time_scale=1.,source_height=.2,scope='ENGINEERING_ONLY')
    records=[]
    for i in range(int(episodes)+12):
        split='train' if i<episodes else 'development';sid=int(rng.integers(3)) if split=='train' else 3
        source=candidates[sid];world=int(rng.integers(4));observations=[];history=[]
        mode=Mechanism() if i%4 else Mechanism('sensor_offset',onset=length//2,magnitude=1.2)
        for k in range(length):
            a=Action(float(rng.uniform(.1,2.9)),float(rng.uniform(.1,2.9)),z=.5,time=float(k+1),dwell=1.)
            o=manufactured_observation(history,a,source,world,mode,rng)
            history.append(o);observations.append(observation_to_dict(o))
        records.append({'id':f'engineering_{i}','source':source.tolist(),'world_index':world,'mechanism':asdict(mode),
            'observations':observations,'metadata':{'split':split,'scope':'ENGINEERING_ONLY','training_allowed':split=='train',
             'lineage_group':f'manufactured_plume_{seed}_{i}','bank_world_id':bank.metadata['world_ids'][world],
             'source_group':f's{sid}','wind_program':f'manufactured_wind_{world}','realization':f'{seed}_{i}',
             'physics':'manufactured smooth wind and threshold sensor; NOT native GADEN'}})
    manifest=write_dataset(out,records,cfg,geom,candidates,{'readout':'Bernoulli event; 2D local wind; source-independent precommitted queries',
                       'purpose':'neural implementation/conditional-law tests, not research localization efficacy'})
    return {'status':'CREATED_ENGINEERING_ONLY','manifest':str(manifest),'bank':str(out/'bank'),'train_episodes':episodes,'development_episodes':12}


def manufactured_observation(history,action,source,world,mechanism,rng):
    vectors=np.array([[.7,.1],[-.2,.6],[-.6,-.1],[.1,-.6]])
    wind=vectors[world]+rng.normal(0,.12,2)
    if mechanism.kind=='wind_bias' and mechanism.active(len(history)):wind[0]+=mechanism.magnitude
    r=np.array([action.x,action.y])-np.asarray(source)-.7*vectors[world]
    logits=1.4-.85*np.sum(r*r)+.7*(history[-1].gas if history else 0.)
    if mechanism.kind=='sensor_offset' and mechanism.active(len(history)):logits+=mechanism.magnitude
    probability=expit(logits)
    if mechanism.kind=='detection_loss' and mechanism.active(len(history)):probability*=1-mechanism.magnitude
    return Observation(f'env_{len(history)}',action,tuple(map(float,wind)),float(rng.random()<probability))


def house_neural_manifest(export_root,out,paths=2,hidden=48,modes=4):
    """Convert already authorized numerical arrays; never open original test data.

    A predeclared sparse probe schedule selects one saved response per record.
    It is NOT a feasible aircraft route and record indices are NOT seconds.
    """
    from .m1_neural import NeuralConfig,Geometry
    from .m1_neural.training import write_dataset,sha256
    root=Path(export_root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():raise FileExistsError('Refuse to overwrite frozen House numerical manifest')
    auth=json.loads((root/'AUTHORIZATION_EVIDENCE.json').read_text());qual=json.loads((root/'QUALIFICATION_RECEIPT.json').read_text())
    if auth.get('decision')!='AUTHORIZED_NUMERICAL_OFFLINE_FIT_ON_ORIGINAL_TRAIN_SOURCES_ONLY' or auth.get('original_test_response_bytes_opened') is not False:
        raise ValueError('BLOCKED_HOUSE_AUTHORIZATION')
    if not 1<=paths<=3:raise ValueError('Freeze one to three numerical query schedules')
    schedules=[[(3*t+shift)%30 for t in range(10)] for shift in (0,11,22)[:paths]]
    protocol={'scope':'NUMERICAL_ONLY','native_active_qualified':False,'physical_time_available':False,
              'gas_lod_numerical_ppm':.1,'readout':'original four-native-cell pooled gas; censor at original first ordinal boundary 0.1 ppm',
              'probe_schedules':schedules,'schedule_choice':'fixed before fitting; no response-based probe selection',
              'test_response_bytes_opened':False,'source_authorization_sha256':sha256(root/'AUTHORIZATION_EVIDENCE.json')}
    (out/'PROTOCOL_FREEZE.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2))
    records=[];candidates=None;scale=None
    for role in ('train','dev'):
        expected=next(r['sha256'] for r in qual['artifacts'] if r['role']==role)
        if sha256(root/f'{role}.npz')!=expected:raise ValueError('House exported artifact checksum mismatch')
        with np.load(root/f'{role}.npz',allow_pickle=False) as d:
            if bool(d['physical_time_available']) or bool(d['wind_available'].any()):raise ValueError('Unexpected House readout; requalify adapter')
            candidates=d['candidate_xy'];probes=d['probe_xyz'];sourcez=float(d['source_xyz'][0,2])
            if scale is None:scale=max(float(np.linalg.norm(np.ptp(probes[:,:2],axis=0)))/2,1.)
            for i in range(len(d['gas'])):
                for route,schedule in enumerate(schedules if role=='train' else schedules[:1]):
                    obs=[]
                    for t,probe in enumerate(schedule):
                        gas=float(d['gas'][i,t,probe]);gas=0. if gas<=.1 else gas
                        a=Action(*map(float,probes[probe]),time=float(t),dwell=1.)
                        obs.append(observation_to_dict(Observation(f'h02_{i}_{route}_{t}',a,(0.,0.),gas,(False,False),True)))
                    split='train' if role=='train' else 'development'
                    records.append({'id':str(d['sample_ids'][i])+f'_schedule{route}','source':d['source_xyz'][i,:2].astype(float).tolist(),
                         'observations':obs,'mechanism':asdict(Mechanism()),
                         'metadata':{'split':split,'scope':'NUMERICAL_ONLY','training_allowed':role=='train',
                            'lineage_group':str(d['realization_ids'][i]),'source_group':str(d['source_ids'][i]),
                            'readout':'four_cell_mean_numerical_ppm','time_semantics':'record_index',
                            'wind_observed':False,'physical_3D_teacher_state':False}})
    cfg=NeuralConfig(hidden=hidden,modes=modes,gas_model='censored_lognormal',gas_lod=.1,length_scale=scale,
                   source_height=sourcez,time_semantics='record_index',scope='NUMERICAL_ONLY')
    # Probes are observation locations, not obstacles. Do not label them terrain.
    manifest=write_dataset(out,records,cfg,Geometry.empty(),candidates,protocol)
    return {'status':'PASS_NUMERICAL_ONLY_NEURAL_MANIFEST','manifest':str(manifest),'train_sequences':sum(r['metadata']['split']=='train' for r in records),
            'distinct_train_cube_groups':len({r['metadata']['lineage_group'] for r in records if r['metadata']['split']=='train'}),
            'development_sequences':sum(r['metadata']['split']=='development' for r in records),'sealed_test_values_opened':0,
            'teacher_3d_status':'BLOCKED_MISSING_FULL_WIND_AND_CLOCK','active_status':'BLOCKED_RECORD_INDEX_NOT_FLIGHT_TIME'}


def evaluate_neural(manifest_path,model_path,out,split='development'):
    from .m1_neural import NeuralJointGenerator
    from .m1_neural.training import load_dataset,sha256
    from .posterior import source_map
    manifest,episodes=load_dataset(manifest_path,split);model=NeuralJointGenerator.load(model_path)
    sources=np.asarray(manifest['candidates']);rows=[];start=time.perf_counter()
    for ep in episodes:
        logp=np.array([model.log_prob(ep['observations'],s,Mechanism()) for s in sources])
        logs=logp-logsumexp(logp);p=np.exp(logs);distance=np.linalg.norm(sources-ep['source'],axis=1)
        true=int(np.argmin(distance))
        if distance[true]>1e-5:raise ValueError('True source outside candidate support; audit before scoring')
        wrong=np.delete(logp,true);margin=logp[true]-wrong.max();order=np.argsort(-p,kind='stable');k=max(1,math.ceil(.05*len(p)))
        top5=np.average(sources[order[:k]],axis=0,weights=p[order[:k]])
        rows.append({'id':ep['id'],'lineage_group':ep['metadata']['lineage_group'],'source_group':ep['metadata'].get('source_group'),
             'true_index':true,'predicted_index':int(np.argmax(p)),'top1':bool(np.argmax(p)==true),
             'map_error_m':float(distance[np.argmax(p)]),'top5_error_m':float(np.linalg.norm(top5-ep['source'])),
             'true_log_margin':float(margin),'true_rank':1+int(np.sum(logp>logp[true])),
             'truth_nll':float(-logs[true]),'brier':float(np.sum((p-np.eye(len(p))[true])**2)),
             'max_posterior':float(p.max()),'source_posterior':p.tolist(),'log_likelihood':logp.tolist()})
    groups={r['source_group'] for r in rows};balanced={}
    for metric in ('top1','map_error_m','top5_error_m','true_log_margin','truth_nll','brier'):
        balanced[metric]=float(np.mean([np.mean([r[metric] for r in rows if r['source_group']==g]) for g in groups]))
    report={'status':'COMPLETE_OFFLINE_DEVELOPMENT','scope':model.config.scope,'split':split,'episodes':len(rows),'source_groups':len(groups),
            'lineage_groups':len({r['lineage_group'] for r in rows}),'source_balanced_metrics':balanced,
            'wrong_high_confidence_count':sum((not r['top1']) and r['max_posterior']>=.9 for r in rows),
            'manifest_sha256':sha256(manifest_path),'model_version':model.version,'wall_seconds':time.perf_counter()-start,
            'not_native_PMFS_comparison':True,'not_frozen_confirmation':split!='frozen_test','rows':rows}
    out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'evaluation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    return {k:v for k,v in report.items() if k!='rows'}


def load_online_model(path,device='cpu',require_physical=False):
    from .m1_neural import NeuralJointGenerator
    model=NeuralJointGenerator.load(path,device)
    if model.config.time_semantics!='seconds' or model.config.scope=='NUMERICAL_ONLY':
        raise ValueError('BLOCKED_ACTIVE_SCOPE: record-index/no-wind numerical model is not an active flight predictor')
    if require_physical and model.config.scope!='PHYSICALLY_QUALIFIED':raise ValueError('BLOCKED_PHYSICAL_MODEL_QUALIFICATION')
    if model.training_receipt.get('normalized_density_anchor') is False:raise ValueError('BLOCKED_NO_GENERATIVE_ANCHOR')
    return model
