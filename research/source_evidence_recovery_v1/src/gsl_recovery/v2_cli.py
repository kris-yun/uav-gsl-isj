"""Executable V2 teacher/student and qualification commands."""
from pathlib import Path
from dataclasses import asdict
import argparse,json,os,platform,sys,time
import numpy as np
from .io import json_default


def emit(value):print(json.dumps(value,ensure_ascii=False,indent=2,default=json_default,allow_nan=False))


def doctor(out=None):
    import torch
    report={'python':platform.python_version(),'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),
        'gpu_names':[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
        'neural_training':'READY','native_GADEN_derivative':'BLOCKED_NOT_INSTRUMENTED',
        'native_teacher_training':'REQUIRES_PHYSICALLY_QUALIFIED_MULTI_SOURCE_BANK',
        'M2_M3_interfaces':'REUSED_WITH_NORMALIZED_NEURAL_MODEL','local_RTX_5060_or_3090_accessed':False,
        'cpu_count':os.cpu_count(),'manifest_policy':'exact lineage split before reading responses; no test response library'}
    if out:Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(report,indent=2))
    return report


def neural_demo(model_path,out,rounds=2,draws=256,eig_draws=8,seed=42,variant='Bprime',m2_variant='Bprime'):
    from .v2_pipeline import load_online_model,manufactured_observation
    from .navigation.v2_session import ActiveSessionV2
    from .types import Action,Mechanism,observation_to_dict
    model=load_online_model(model_path);sources=np.array([[.5,.5],[.5,2.5],[2.5,.5],[2.5,2.5]])
    mechanisms=[Mechanism(),Mechanism('sensor_offset',onset=3,magnitude=1.2)]
    session=ActiveSessionV2(model,sources,mechanisms,seed=seed,draws=draws,eig_draws=eig_draws,wall_seconds=120.,variant=variant,m2_variant=m2_variant)
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(seed+100)
    # Truth belongs ONLY to the manufactured environment/evaluator below.
    true_source=sources[3];world=1;environment_history=[];events=[];start=time.perf_counter()
    for r in range(rounds):
        blocks=[]
        for x,y in ((.4,.5),(.5,2.4),(2.4,.5),(2.4,2.4)):
            blocks.append([Action(x+.1*k,y,z=.5,time=float(3*r+k+1)) for k in range(3)])
        req={'op':'plan','navigation_qualified':True,'action_blocks':[[asdict(a) for a in b] for b in blocks]}
        plan=session.request(req);events.append({'request':req,'response':plan})
        # Commit the complete plan before the environment is queried.
        (out/f'plan_{r:02d}.json').write_text(json.dumps(plan,default=json_default,indent=2))
        observations=[]
        for a in plan['actions']:
            obs=manufactured_observation(environment_history,Action(**a),true_source,world,mechanisms[1],rng)
            environment_history.append(obs);observations.append(observation_to_dict(obs))
        req={'op':'observe','observations':observations};answer=session.request(req);events.append({'request':req,'response':answer})
    result=session.engine.infer(session.ledger.history,m2_variant)
    from .posterior import posterior_metrics
    receipt={'status':'PASS_NEURAL_M1_M2_M3_CLOSED_LOOP','scope':'MANUFACTURED_BACKEND_ENGINEERING_ONLY',
        'observations':len(session.ledger),'rounds':rounds,'counterevidence_tests':len(session.planner.risk.tests),
        'counterevidence_rejections':sum(bool(e['response'].get('test',{}).get('rejected')) for e in events),
        'full_joint_eig_fallbacks':sum(e['response'].get('reason')=='full_gas_wind_joint_eig_fallback' for e in events),
        'risk_spent':session.planner.risk.spent,'wall_seconds':time.perf_counter()-start,
        'model_version':model.version,'teacher_or_hidden_state_in_online_input':False,'m2_variant':m2_variant,'m3_variant':variant,
        'evaluation_only':posterior_metrics(sources,result.source_posterior,true_source),
        'not_a_House_or_lakeshore_gain':True}
    (out/'events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2,default=json_default))
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,default=json_default));return receipt


def build_parser():
    p=argparse.ArgumentParser(prog='gsl-recovery-v2');sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('doctor');q.add_argument('--out')
    q=sub.add_parser('prepare-engineering');q.add_argument('--out',required=True);q.add_argument('--episodes',type=int,default=48);q.add_argument('--length',type=int,default=8);q.add_argument('--seed',type=int,default=31)
    q=sub.add_parser('prepare-house');q.add_argument('--export-root',required=True);q.add_argument('--out',required=True);q.add_argument('--paths',type=int,default=2);q.add_argument('--hidden',type=int,default=48);q.add_argument('--modes',type=int,default=4)
    for name in ('train-teacher','train-student'):
        q=sub.add_parser(name);q.add_argument('--manifest',required=True);q.add_argument('--out',required=True)
        q.add_argument('--epochs',type=int,default=8);q.add_argument('--batch-size',type=int,default=8);q.add_argument('--seed',type=int,default=23)
        q.add_argument('--learning-rate',type=float,default=.002);q.add_argument('--device',default='cpu');q.add_argument('--wall-seconds',type=float,default=900.);q.add_argument('--resume')
        if name=='train-teacher':q.add_argument('--bank',required=True)
        else:
            q.add_argument('--targets');q.add_argument('--variant',default='nll',choices=['nll','distribution','privileged_pair','mean_log','projected_evidence','projected_no_anchor'])
            q.add_argument('--no-directional',action='store_true');q.add_argument('--hidden',type=int);q.add_argument('--modes',type=int)
    q=sub.add_parser('build-targets');q.add_argument('--manifest',required=True);q.add_argument('--teacher',required=True);q.add_argument('--out',required=True);q.add_argument('--count',type=int,default=24);q.add_argument('--seed',type=int,default=23);q.add_argument('--order',type=int,default=6)
    q=sub.add_parser('evaluate');q.add_argument('--manifest',required=True);q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--split',default='development',choices=['development','frozen_test'])
    q=sub.add_parser('calibrate-adequacy');q.add_argument('--manifest',required=True);q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--block-length',type=int,default=3)
    q=sub.add_parser('demo');q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--rounds',type=int,default=2);q.add_argument('--draws',type=int,default=256);q.add_argument('--eig-draws',type=int,default=8);q.add_argument('--seed',type=int,default=42);q.add_argument('--variant',default='Bprime');q.add_argument('--m2',choices=['Aprime','B','Bprime'],default='Bprime')
    q=sub.add_parser('online-jsonl');q.add_argument('--model',required=True);q.add_argument('--setup',required=True);q.add_argument('--log',required=True)
    return p


def main(argv=None):
    args=build_parser().parse_args(argv)
    try:
        if args.command=='doctor':result=doctor(args.out)
        elif args.command=='prepare-engineering':
            from .v2_pipeline import generate_neural_engineering
            result=generate_neural_engineering(args.out,args.seed,args.episodes,args.length)
        elif args.command=='prepare-house':
            from .v2_pipeline import house_neural_manifest
            result=house_neural_manifest(args.export_root,args.out,args.paths,args.hidden,args.modes)
        elif args.command.startswith('train-'):
            from .m1_neural.training import TrainConfig,train_teacher,train_student
            cfg=TrainConfig(epochs=args.epochs,batch_size=args.batch_size,seed=args.seed,learning_rate=args.learning_rate,device=args.device,wall_seconds=args.wall_seconds,
                            variant=getattr(args,'variant','nll'),directional=not getattr(args,'no_directional',False))
            override=None
            if args.command=='train-student' and (args.hidden or args.modes):
                import torch
                from .m1_neural import NeuralConfig,Geometry,NeuralJointGenerator
                doc=json.loads(Path(args.manifest).read_text());mc=doc['config']
                if args.hidden:mc['hidden']=args.hidden
                if args.modes:mc['modes']=args.modes
                torch.manual_seed(args.seed);override=NeuralJointGenerator(NeuralConfig(**mc),Geometry(**doc['geometry']))
            result=train_teacher(args.manifest,args.bank,args.out,cfg,args.resume) if args.command=='train-teacher' else train_student(args.manifest,args.out,cfg,args.targets,args.resume,override)
        elif args.command=='build-targets':
            from .m1_neural.training import build_targets
            result=build_targets(args.manifest,args.teacher,args.out,args.count,args.seed,args.order)
        elif args.command=='evaluate':
            from .v2_pipeline import evaluate_neural
            result=evaluate_neural(args.manifest,args.model,args.out,args.split)
        elif args.command=='calibrate-adequacy':
            from .m1_neural import NeuralJointGenerator
            from .m1_neural.training import load_dataset
            from .m2_diagnosis.adequacy import fit_adequacy_guard
            from .types import Mechanism
            manifest,episodes=load_dataset(args.manifest,'development');model=NeuralJointGenerator.load(args.model)
            guard=fit_adequacy_guard(model,episodes,manifest['candidates'],[Mechanism()],args.block_length);guard.save(args.out)
            result={'status':'CALIBRATED_DEVELOPMENT_DIAGNOSTIC_ONLY','out':args.out,'samples':len(guard.calibration_scores)}
        elif args.command=='demo':result=neural_demo(args.model,args.out,args.rounds,args.draws,args.eig_draws,args.seed,args.variant,args.m2)
        elif args.command=='online-jsonl':
            from .navigation.v2_session import run_jsonl_v2
            run_jsonl_v2(args.model,args.setup,sys.stdin,sys.stdout,args.log);return 0
        else:raise ValueError('Unknown command')
        emit(result);return 0
    except (ValueError,RuntimeError,FileNotFoundError) as e:
        emit({'status':'BLOCKED' if 'BLOCKED' in str(e) else 'FAIL','command':args.command,'error':str(e)});return 2


if __name__=='__main__':raise SystemExit(main())
