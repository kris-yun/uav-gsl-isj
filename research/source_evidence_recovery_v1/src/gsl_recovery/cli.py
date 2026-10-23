"""Executable research contract entry points."""
import argparse,json,os,platform,sys,time
from pathlib import Path
import numpy as np
from .io import write_json,read_json,sha256,json_default

def emit(obj):print(json.dumps(obj,ensure_ascii=False,indent=2,default=json_default,allow_nan=False))

def doctor(args):
    import scipy
    roots=[Path(p) for p in args.asset_root]
    report={'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'GPU_required':False,'controlled_backend':'READY','native_teacher':'BLOCKED_NOT_INSTRUMENTED','ROS_GADEN_runtime':'NOT_STARTED','assets':[{'path':str(p),'exists':p.exists()} for p in roots],'logical_cpu_count':os.cpu_count(),'native_gate':'Use native-replay for packaged B4 fixture; House requires qualified local assets'}
    if args.out:write_json(args.out,report)
    return report

def train_diagnosis(args):
    from .m2_diagnosis import DifferentialDiagnoser,diagnostic_pairs
    from .m1_generator import JointObservationGenerator
    from .pipeline import default_mechanisms
    from .data.qualification import load_episode,audit_manifest
    path=Path(args.manifest);manifest=read_json(path);audit=audit_manifest(path,True)
    if audit['status']!='PASS':raise ValueError('DATA_QUALIFICATION_FAILED')
    model=JointObservationGenerator.load(args.model);mechanisms=default_mechanisms();A=[];B=[];Y=[];rng=np.random.default_rng(args.seed)
    for entry in manifest['episodes']:
        record=read_json(path.parent/entry['path'])
        if record['metadata']['split']!='train':continue
        _,history=load_episode(path.parent/entry['path'],True)
        # A wrong-source/no-fault reference is still labelled nominal.
        source=np.asarray(record['source']);other=np.asarray(record['candidates'])[:3]
        actual,reference=diagnostic_pairs(history,other,model,mechanisms[0],rng,draws=2)
        m=record.get('mechanism',{});label=next((i for i,e in enumerate(mechanisms) if e.kind==m.get('kind','nominal') and e.magnitude==m.get('magnitude',0)),None)
        if label is None:raise ValueError('Training mechanism outside frozen catalogue')
        A.extend(actual);B.extend(reference);Y.extend([label]*len(actual))
    network=DifferentialDiagnoser(len(mechanisms),seed=args.seed);network.bind_catalog(mechanisms)
    receipt=network.fit(np.array(A),np.array(B),np.array(Y),max_iter=args.maxiter)
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);network.save(out/'diagnosis.npz')
    receipt.update(manifest_sha256=sha256(path),generator_sha256=sha256(args.model),wrong_source_nominal_negatives=True,frozen_test_used=False,scope='trainable shared-encoder differential operator; not full author CDN reproduction')
    write_json(out/'training_receipt.json',receipt);return receipt

def matrix(args):
    import yaml
    from .pipeline import train_from_manifest,evaluate_manifest,run_closed_loop
    config=yaml.safe_load(Path(args.config).read_text());out=Path(args.out);out.mkdir(parents=True,exist_ok=True);receipts=[];started=time.perf_counter()
    for seed in config['seeds']:
        for variant in sorted({r['m1'] for r in config['rows']}):
            modeldir=out/f'seed_{seed}'/f'm1_{variant}'
            train_from_manifest(args.manifest,modeldir,variant,seed,config['maxiter'])
        for row in config['rows']:
            if time.perf_counter()-started>config['wall_cap_seconds']:raise RuntimeError('STOP_WALL_BUDGET')
            model=out/f'seed_{seed}'/f"m1_{row['m1']}"/'model.npz';dest=out/f'seed_{seed}'/row['name']
            result=evaluate_manifest(args.manifest,model,dest/'offline',split=config['evaluation_split'],m2_variant=row['m2'])
            if args.active:
                result['active']=run_closed_loop(model,dest/'active',seed=1000+seed,rounds=config['rounds'],draws=config['draws'],block_length=config['block_length'],planner_variant=row['m3'],m2_variant=row['m2'])
            receipts.append({'seed':seed,'row':row,**result});write_json(out/'matrix_receipts.json',receipts)
    return {'status':'COMPLETE_CONTROLLED_MATRIX','rows':len(receipts),'active':args.active,'native_A':'Run native-replay separately; no synthetic surrogate called full PMFS','wall_seconds':time.perf_counter()-started}

def bridge(args):
    from .m1_generator import JointObservationGenerator
    from .m2_replay import ReplayEngine
    from .m3_codebook import JointCodebookBuilder
    from .m3_planner import RobustCounterEvidencePlanner
    from .types import Action,Mechanism,observation_from_dict
    obj=read_json(args.request);model=JointObservationGenerator.load(args.model)
    forbidden={'true_source','future_true_wind','response_bank','ground_truth_source'}
    if forbidden.intersection(obj):raise ValueError('ORACLE_INPUT_FORBIDDEN')
    history=[observation_from_dict(o) for o in obj['observations']];sources=np.asarray(obj['candidates'],float);mechanisms=[Mechanism(**m) for m in obj['mechanisms']]
    # Native supervisor supplies collision-checked feasible action blocks.
    if obj.get('navigation_qualified') is not True:raise ValueError('NAVIGATION_QUALIFICATION_REQUIRED')
    blocks=[[Action(**a) for a in b] for b in obj['action_blocks']]
    result=ReplayEngine(model,sources,mechanisms,model_version=model.version).infer(history)
    books=JointCodebookBuilder(model,model_version=model.version).build(history,blocks,sources,mechanisms,args.draws,np.random.default_rng(args.seed),delta=.001)
    # Stateless bridge can propose a block; test execution and risk budget stay
    # with persistent pipeline/native supervisor. Never restart alpha per block.
    planner=RobustCounterEvidencePlanner(len(sources),seed=args.seed);plan=planner.plan(books,result.source_posterior,result.conditional_mechanism_posterior,'Aprime')
    from dataclasses import asdict
    payload={'mode':'stateless_action_proposal_only','risk_test_enabled':False,'actions':[asdict(a) for a in plan.actions],'source_posterior':result.source_posterior,'joint_posterior':result.joint_posterior,'model_version':model.version,'requires_persistent_supervisor_for_M3_Bprime':True}
    write_json(args.out,payload);return payload

def build_parser():
    p=argparse.ArgumentParser(prog='gsl-recovery');sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('doctor');q.add_argument('--asset-root',action='append',default=[]);q.add_argument('--out')
    q=sub.add_parser('generate-controlled');q.add_argument('--out',required=True);q.add_argument('--seed',type=int,default=11);q.add_argument('--episodes',type=int,default=64);q.add_argument('--length',type=int,default=10)
    q=sub.add_parser('audit-data');q.add_argument('--manifest',required=True);q.add_argument('--out',required=True);q.add_argument('--training',action='store_true')
    q=sub.add_parser('import-csv');q.add_argument('--csv',required=True);q.add_argument('--metadata',required=True);q.add_argument('--candidates',required=True);q.add_argument('--threshold',type=float,required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('legacy-audit');q.add_argument('--root',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('native-replay');q.add_argument('--root',default='examples/native_b4');q.add_argument('--out',required=True)
    q=sub.add_parser('train');q.add_argument('--manifest',required=True);q.add_argument('--out',required=True);q.add_argument('--variant',choices=['Aprime','B','Bprime','Bprime_no_boundary','Bprime_no_wind_constraint'],default='Bprime');q.add_argument('--seed',type=int,default=0);q.add_argument('--maxiter',type=int,default=200)
    q=sub.add_parser('train-diagnosis');q.add_argument('--manifest',required=True);q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--seed',type=int,default=0);q.add_argument('--maxiter',type=int,default=150)
    q=sub.add_parser('evaluate');q.add_argument('--manifest',required=True);q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--split',choices=['development','frozen_test','legacy_evaluation'],default='frozen_test');q.add_argument('--m2',choices=['Aprime','B','Bprime'],default='Bprime')
    q=sub.add_parser('demo');q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--diagnosis');q.add_argument('--seed',type=int,default=101);q.add_argument('--rounds',type=int,default=3);q.add_argument('--draws',type=int,default=128);q.add_argument('--block-length',type=int,default=5);q.add_argument('--planner',choices=['A','Aprime','B','Bprime','min_hamming','robust_eig'],default='Bprime');q.add_argument('--m2',choices=['Aprime','B','Bprime'],default='Bprime')
    q=sub.add_parser('matrix');q.add_argument('--manifest',required=True);q.add_argument('--config',default='configs/controlled_matrix.yaml');q.add_argument('--out',required=True);q.add_argument('--active',action='store_true')
    q=sub.add_parser('bridge-request');q.add_argument('--request',required=True);q.add_argument('--model',required=True);q.add_argument('--out',required=True);q.add_argument('--draws',type=int,default=128);q.add_argument('--seed',type=int,default=0)
    q=sub.add_parser('online-jsonl');q.add_argument('--model',required=True);q.add_argument('--setup',required=True);q.add_argument('--log',required=True)
    return p

def main(argv=None):
    args=build_parser().parse_args(argv)
    try:
        if args.command=='doctor':result=doctor(args)
        elif args.command=='online-jsonl':
            from .navigation.session import run_jsonl
            run_jsonl(args.model,args.setup,sys.stdin,sys.stdout,args.log);return 0
        elif args.command=='train-diagnosis':result=train_diagnosis(args)
        elif args.command=='matrix':result=matrix(args)
        elif args.command=='bridge-request':result=bridge(args)
        elif args.command=='audit-data':
            from .data.qualification import audit_manifest
            result=audit_manifest(args.manifest,args.training);write_json(args.out,result)
        elif args.command=='import-csv':
            from .data.adapters import csv_to_episode
            result=csv_to_episode(args.csv,args.metadata,args.candidates,args.out,args.threshold)
        elif args.command=='legacy-audit':
            from .data.adapters import inspect_legacy_packet
            result=inspect_legacy_packet(args.root,args.out)
        elif args.command=='native-replay':
            from .evaluation.native_pmfs import replay_native_b4
            result=replay_native_b4(args.root,args.out)
        else:
            from .pipeline import generate_controlled_dataset,train_from_manifest,evaluate_manifest,run_closed_loop
            if args.command=='generate-controlled':result=generate_controlled_dataset(args.out,args.seed,args.episodes,args.length)
            elif args.command=='train':result=train_from_manifest(args.manifest,args.out,args.variant,args.seed,args.maxiter)
            elif args.command=='evaluate':result=evaluate_manifest(args.manifest,args.model,args.out,args.split,args.m2)
            elif args.command=='demo':result=run_closed_loop(args.model,args.out,args.seed,args.rounds,args.draws,args.block_length,args.planner,args.m2,diagnosis_path=args.diagnosis)
        emit(result)
        return 1 if result.get('status')=='FAIL' else 0
    except (ValueError,RuntimeError,FileNotFoundError) as e:
        emit({'status':'BLOCKED' if 'BLOCKED' in str(e) else 'FAIL','error':str(e),'command':args.command});return 2

if __name__=='__main__':raise SystemExit(main())
