"""Executable research entrypoints. Missing native assets fail explicitly."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np


def _write(result,path=None):
    body=json.dumps(result,ensure_ascii=False,indent=2)
    if path:
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body+'\n',encoding='utf8')
    print(body)


def main(argv=None):
    p=argparse.ArgumentParser(description='GSL V7: scientific qualification precedes calibration and active sensing')
    sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('calibrate-control',help='Level 1 analytical calibration, not native training')
    q.add_argument('--out',required=True);q.add_argument('--blocks',type=int,default=32)
    q.add_argument('--variant',choices=['even','mother','fixed_two','secondary','raw_joint'],default='secondary')
    q=sub.add_parser('fit-geometry',help='Ordinary TRAIN-only response/gradient fit required by M2')
    q.add_argument('--manifest',required=True);q.add_argument('--model',required=True)
    q.add_argument('--bandwidth',type=float)
    q=sub.add_parser('demo',help='Run a paid closed loop on the analytical Level 1 backend')
    q.add_argument('--model',required=True);q.add_argument('--out',required=True)
    q.add_argument('--source',type=int,default=4);q.add_argument('--mechanism',type=int,default=1)
    q.add_argument('--seed',type=int,default=8801);q.add_argument('--budget',type=float,default=300.)
    q.add_argument('--wrong-prior',action='store_true')
    q.add_argument('--m2',choices=['none','geometry','boundary','full'],default='full')
    q.add_argument('--planner',choices=['full','joint_eig','mother','uniform','no_coverage','no_audit','variance_adapted'],default='full')
    q=sub.add_parser('control-matrix',help='Execute one frozen ablation matrix')
    q.add_argument('--config',default='configs/control_matrix.yaml');q.add_argument('--out',required=True)
    q=sub.add_parser('qualify-ocb',help='Verify the eight pinned, open discovery worlds')
    q.add_argument('--root',required=True);q.add_argument('--out')
    q=sub.add_parser('static-pilot',help='Reproduce the frozen retrospective paired spatial pilot')
    q.add_argument('--root',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('qualify-block',help='Check a standard CSV/NPZ without inventing missing capabilities')
    q.add_argument('--file',required=True);q.add_argument('--dynamic',action='store_true');q.add_argument('--wind',action='store_true');q.add_argument('--out')
    q=sub.add_parser('calibrate-blocks',help='Fit a qualified training manifest; refuses unsupported native data')
    q.add_argument('--manifest',required=True);q.add_argument('--out',required=True)
    q.add_argument('--variant',choices=['even','mother','fixed_two','secondary','raw_joint'],default='secondary')
    q=sub.add_parser('replay-blocks',help='Replay whole fixed trajectories with a frozen joint model')
    q.add_argument('--manifest',required=True);q.add_argument('--model',required=True);q.add_argument('--out',required=True)
    q.add_argument('--split',choices=['dev','final'],default='dev')
    q=sub.add_parser('plan-channel',help='Produce a legal next-action distribution from a frozen model')
    q.add_argument('--model',required=True);q.add_argument('--source-prior',help='JSON numeric array; default uniform')
    q.add_argument('--out')
    q=sub.add_parser('live',help='Run real backend JSONL bridge; physical bridge qualification remains required')
    q.add_argument('--model',required=True);q.add_argument('--bridge',required=True,help='JSON array of executable and arguments, no shell')
    q.add_argument('--out',required=True);q.add_argument('--budget',type=float,default=300.)
    q=sub.add_parser('pmfs-map-replay',help='Exact compatibility/variance operator on extracted official maps, not ROS reproduction')
    q.add_argument('--maps',required=True);q.add_argument('--out',required=True)
    q.add_argument('--difference-factor',type=float,default=1.);q.add_argument('--truth-index',type=int)
    args=p.parse_args(argv)
    if args.cmd=='calibrate-control':
        from .engine import calibrate_control
        m=calibrate_control(args.out,args.blocks,args.variant)
        _write({'status':'CALIBRATED_LEVEL1_ONLY','model':str(Path(args.out).resolve()),'shape':m.channel.shape})
    elif args.cmd=='fit-geometry':
        from .m2_boundary.calibration import fit_response_geometry
        _write(fit_response_geometry(args.manifest,args.model,args.bandwidth))
    elif args.cmd=='demo':
        from .engine import run_control
        r=run_control(args.model,args.out,truth=args.source,mechanism=args.mechanism,seed=args.seed,
                      budget_s=args.budget,planner_variant=args.planner,m2_variant=args.m2,wrong_prior=args.wrong_prior)
        _write({k:v for k,v in r.items() if k!='final'})
    elif args.cmd=='control-matrix':
        from .evaluation.matrix import run_matrix
        _write(run_matrix(args.config,args.out))
    elif args.cmd=='qualify-ocb':
        from .data import OCBDataset
        _write(OCBDataset(args.root).audit(),args.out)
    elif args.cmd=='static-pilot':
        from .evaluation.ocb_static import run_static_pilot
        r=run_static_pilot(args.root,args.out);_write({k:v for k,v in r.items() if k!='all_rows'})
    elif args.cmd=='qualify-block':
        from .data import SynchronousBlock
        b=(SynchronousBlock.load_csv if Path(args.file).suffix=='.csv' else SynchronousBlock.load_npz)(args.file)
        if args.dynamic:b.require_dynamic(with_wind=args.wind)
        _write({'status':'INPUT_VALID','shape':b.values.shape,'qualification':b.qualification.to_dict()},args.out)
    elif args.cmd=='calibrate-blocks':
        from .evaluation.block_pipeline import calibrate_manifest
        _write(calibrate_manifest(args.manifest,args.out,args.variant))
    elif args.cmd=='replay-blocks':
        from .evaluation.block_pipeline import replay_manifest
        _write(replay_manifest(args.manifest,args.model,args.out,args.split))
    elif args.cmd=='plan-channel':
        from .m1_opponent.raw_joint import load_observation_model
        from .channel import JointPosterior
        from .m3_audit import CoveragePlanner
        m=load_observation_model(args.model);post=JointPosterior(m.channel,json.loads(args.source_prior) if args.source_prior else None)
        result=CoveragePlanner().plan(m.channel,post.predict(),post.source,0)
        _write({'action_probabilities':result.probabilities.tolist(),'diagnostic':result.info},args.out)
    elif args.cmd=='live':
        from .navigation.bridge import run_bridge
        _write(run_bridge(args.model,json.loads(args.bridge),args.out,args.budget))
    elif args.cmd=='pmfs-map-replay':
        from .evaluation.pmfs_arrays import replay_pmfs_maps
        _write(replay_pmfs_maps(args.maps,args.out,args.difference_factor,args.truth_index))


if __name__=='__main__':main()
