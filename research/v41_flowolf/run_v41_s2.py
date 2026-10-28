#!/usr/bin/env python3
"""Codex-facing S2 adapter: E0 real observations; E1/E2 not qualified by CLI.

Requires full original dataset locally. No labels/truth imported into controller.
The model is V34's common ordinary local-puff approximation, not native oracle.
Use this for interface integration only until model and 3-AgentSession parity PASS.
"""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from v41_flowolf import Controller,Configuration,LegacyV34MultiUAV
from v41_flowolf.native import run_native,check_root


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True,help='fully extracted original S2 data-only root')
    p.add_argument('--world',required=True,choices=['W001','W002','W003','W004','W005'])
    p.add_argument('--sources-npy',required=True,help='frozen public [S,3] candidate support, NOT labels/sources')
    p.add_argument('--start-json',required=True,help='JSON array of three public legal initial xyz positions')
    p.add_argument('--mode',default='bio',choices=('bio','ordinary_eig','ordinary_projected',
        'ordinary_coverage','ordinary_eig_full','ordinary_projected_full',
        'bio_noidentity','bio_noflow','bio_nogap'))
    p.add_argument('--seed',type=int,default=9001)
    p.add_argument('--exploratory-uncertified',action='store_true',
       help='source-model-dependent actions without external error certificate: NOT E1/E2 qualified')
    p.add_argument('--seconds',type=int,default=60)
    p.add_argument('--out',required=True)
    args=p.parse_args()
    root,meta=check_root(args.root)
    source_path=Path(args.sources_npy).resolve()
    if 'labels' in source_path.parts or 'EVAL_ONLY' in source_path.parts:
        raise ValueError('No source labels allowed as controller support')
    sources=np.asarray(np.load(source_path,allow_pickle=False),float)
    if sources.ndim!=2 or sources.shape[1]!=3 or len(sources)<4:
        raise ValueError('FROZEN_SOURCE_DOMAIN_MUST_BE_Sx3_N_GE_4')
    starts=np.asarray(json.loads(Path(args.start_json).read_text()),float)
    cfg=Configuration(mode=args.mode,strict_model_gate=not args.exploratory_uncertified,
         sensor_sigma=meta['sensor']['noise_sigma_ppm'],
         hit_threshold=meta['sensor']['hit_excess_threshold_ppm'],
         sensor_lag_s=meta['sensor']['delay_s'],
         sensor_tau_s=meta['sensor']['tau_s'])
    model=LegacyV34MultiUAV(q_reference_mol_s=1e-3)
    controller=Controller(sources,model,cfg,random_seed=args.seed+777)
    t0=time.perf_counter()
    result=run_native(root,args.world,controller,starts,
                      sensor_seed=args.seed,duration_s=args.seconds)
    result['audit'].update({'policy':args.mode,'seed':args.seed,
       'elapsed_wall_s':time.perf_counter()-t0,
       'source_candidates':len(sources),
       'sources_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
       'source_support_is_public_and_pre_frozen':'USER_MUST_AUDIT',
       'O24_native_reproduction':False,'E1_model_coverage':'UNQUALIFIED',
       'E2_localization_advance':'NOT_ESTABLISHED',
       'real_time_CPU_budget':'MEASURED_NOT_COMPUTE_MATCHED',
       'model_uncertified_exploration':args.exploratory_uncertified})
    out=Path(args.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
    print('Saved',out,'readouts',len(result['records']),
          'model parity NOT QUALIFIED; no source-location success claim')


if __name__=='__main__':main()