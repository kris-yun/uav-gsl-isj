"""Frozen small LOHO route-utility diagnostic on all controlled cases."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np

from m2_cpo.local_prediction import features,LocalResidualRidge

ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'evidence/cstar_controlled_assets_20260907_r2'


def readlines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    code_paths=[Path(__file__),Path(__file__).parent/'m2_cpo/local_prediction.py']
    contract=dict(scope='exploratory reused-data marginal-mean diagnostic, not CPO authorization',
                  ridge=1.,history_steps=10,source_hypothesis_used=False,fit='two other Houses only',
                  success_rule='each House must beat both persistence and history-only on mean logppm MSE',
                  code_sha256={str(p.relative_to(ROOT)):sha(p) for p in code_paths},
                  manifest_sha256={h:sha(ASSETS/'manifests'/f'{h}.json') for h in ('H01','H02','H03')})
    (args.out/'FROZEN_CONFIG.json').write_text(json.dumps(contract,indent=2)+'\n')
    folds=[];raw=[]
    for held in ('H01','H02','H03'):
        m=json.loads((ASSETS/'manifests'/f'{held}.json').read_text())
        episodes={r['episode_id']:r for r in m['m1_episodes']}
        cases=[]
        for r in m['m2_route_cases']:
            ep=episodes[r['episode_id']]
            hp=ASSETS/ep['history_trace_path'];op=ASSETS/r['outcome_trace_path']
            assert sha(hp)==ep['history_trace_sha256']
            prefix=[v for v in readlines(hp) if v['t_sim_s']<=r['decision_time_s']]
            rp=ROOT/'evidence/cstar_controlled_routes_20260907'/r['house']/Path(r['planned_route_path']).name
            with rp.open() as f: route=[(float(x['x']),float(x['y'])) for x in csv.DictReader(f)][1:]
            outcome=readlines(op); y=np.array([math.log1p(v['gas_ppm']) for v in outcome])
            assert len(route)==len(y)==20
            current=math.log1p(prefix[-1]['gas_ppm'])
            cases.append(dict(meta=r,prefix=prefix,route=route,y=y,current=current,
                              response_sha256=sha(op),route_sha256=sha(rp)))
        train=[r for r in cases if r['meta']['split']=='train']
        test=[r for r in cases if r['meta']['split']=='heldout']
        assert len(test)==84 and len(train)==168
        assert all(r['meta']['house']!=held for r in train)
        models={}
        for kind,route_mode in [('history_only',False),('route',True)]:
            x=np.concatenate([features(r['prefix'],r['route'],include_route=route_mode) for r in train])
            y=np.concatenate([r['y']-r['current'] for r in train])
            models[kind]=LocalResidualRidge().fit(x,y)
        fold_rows=[]
        for r in test:
            predictions={k:model.predict(features(r['prefix'],r['route'],include_route=(k=='route')),r['current']) for k,model in models.items()}
            predictions['persistence']=np.full(len(r['y']),r['current'])
            metrics={k:float(((p-r['y'])**2).mean()) for k,p in predictions.items()}
            fold_rows.append(metrics)
            raw.append(dict(house=held,decision_id=r['meta']['decision_id'],observed_logppm=r['y'].tolist(),
                            predictions={k:v.tolist() for k,v in predictions.items()},mse=metrics,
                            response_sha256=r['response_sha256'],route_sha256=r['route_sha256']))
        scores={k:float(np.mean([r[k] for r in fold_rows])) for k in models.keys()|{'persistence'}}
        passed=scores['route']<scores['history_only'] and scores['route']<scores['persistence']
        folds.append(dict(house=held,cases=84,logppm_mse=scores,pass_=passed,
                          training_parent_ids=sorted({r['meta']['episode_id'] for r in train}),
                          fitted_models={k:dict(center=v.center.tolist(),scale=v.scale.tolist(),weight=v.weight.tolist()) for k,v in models.items()}))
    assert contract['code_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in code_paths}
    (args.out/'PREDICTIONS.json').write_text(json.dumps(raw,indent=2)+'\n')
    report=dict(verdict='LOCAL_ROUTE_SCREEN_PASS_NOT_FULL_M2' if all(f['pass_'] for f in folds) else 'LOCAL_ROUTE_SCREEN_NO_GO',
                formal_gate_authority=False,folds=folds,config_sha256=sha(args.out/'FROZEN_CONFIG.json'),
                prediction_sha256=sha(args.out/'PREDICTIONS.json'))
    (args.out/'SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['verdict']);print(json.dumps([{k:v for k,v in f.items() if k not in ('fitted_models','training_parent_ids')} for f in folds]))


if __name__=='__main__': main()
