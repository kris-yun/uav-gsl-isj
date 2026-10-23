"""One frozen, resumable controlled matrix. Never promoted to native science."""
from __future__ import annotations
from pathlib import Path
import csv,hashlib,json,platform,sys,time
import numpy as np
import yaml
from ..engine import calibrate_control,run_control


def run_matrix(config_path,output):
    config_path=Path(config_path);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    cfg=yaml.safe_load(config_path.read_text())
    protocol={'configuration':cfg,'configuration_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(),
              'level':1,'scientific_gain_claim':False,'world_unit':'analytical seed/source/mechanism tuple',
              'python':sys.version,'platform':platform.platform(),
              'frozen_before_runs':True,'no_optional_tuning_after_outcomes':True}
    frozen=out/'FROZEN_CONTROL_PROTOCOL.json'
    if frozen.exists():
        if json.loads(frozen.read_text())['configuration_sha256']!=protocol['configuration_sha256']:
            raise ValueError('configuration differs from the frozen matrix')
    else:frozen.write_text(json.dumps(protocol,ensure_ascii=False,indent=2))
    variants=cfg['variants'];models={}
    for name in sorted({v['m1'] for v in variants}):
        dest=out/'models'/name
        if not (dest/'operator.json').exists():calibrate_control(dest,cfg['calibration_blocks'],name)
        models[name]=dest
    all_rows=[];start=time.perf_counter()
    for world in cfg['worlds']:
        for wrong in cfg['wrong_priors']:
            for v in variants:
                episode=f"s{world['source']}_r{world['mechanism']}_seed{world['seed']}_wrong{int(wrong)}"
                dest=out/'episodes'/v['name']/episode
                if (dest/'CONTROL_RESULT.json').exists():r=json.loads((dest/'CONTROL_RESULT.json').read_text())
                else:r=run_control(models[v['m1']],dest,truth=world['source'],mechanism=world['mechanism'],
                      seed=world['seed'],budget_s=cfg['budget_s'],planner_variant=v['planner'],
                      m2_variant=v['m2'],wrong_prior=wrong,max_steps=cfg.get('max_steps',100))
                final=r['final'];steps=[json.loads(x) for x in (dest/'online_steps.jsonl').read_text().splitlines()]
                recovery=next((x['physical_time_s'] for x in steps if x['top1'] and x['true_probability']>=.95),None)
                row={'variant':v['name'],'source':world['source'],'mechanism':world['mechanism'],'seed':world['seed'],
                     'wrong_prior':wrong,'steps':r['steps'],'paid_seconds':r['paid_seconds'],
                     'paid_uav_seconds':r['paid_uav_seconds'],'first_p95_recovery_s':recovery,
                     'audit_singleton_correct':final['audit_list']==[world['source']],
                     'audit_recovery_triggers':sum(x['policy'].get('audit_triggered_challenger') is not None for x in steps),
                     'travel_scalar_samples':sum(x['travel_scalar_samples'] for x in steps),
                     'dwell_scalar_samples':sum(x['dwell_scalar_samples'] for x in steps),
                     'mean_planning_ms':float(np.mean([x['planning_ms'] for x in steps])),
                     'max_planning_ms':float(max(x['planning_ms'] for x in steps)),
                     **{k:final[k] for k in ('top1','map_error_m','top5pct_error_m','true_probability','true_rank','log_margin','brier','wrong_high_confidence')}}
                all_rows.append(row)
    with (out/'per_world.csv').open('w',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=list(all_rows[0]));writer.writeheader();writer.writerows(all_rows)
    summary=[]
    for v in variants:
        for wrong in cfg['wrong_priors']:
            rows=[r for r in all_rows if r['variant']==v['name'] and r['wrong_prior']==wrong]
            summary.append({'variant':v['name'],'wrong_prior':wrong,'episodes':len(rows),
                'top1_count':sum(r['top1'] for r in rows),'mean_map_error_m':float(np.mean([r['map_error_m'] for r in rows])),
                'wrong_high_confidence_count':sum(r['wrong_high_confidence'] for r in rows),
                'p95_recovered_count':sum(r['first_p95_recovery_s'] is not None for r in rows),
                'mean_planning_ms':float(np.mean([r['mean_planning_ms'] for r in rows])),
                'mean_paid_seconds':float(np.mean([r['paid_seconds'] for r in rows])),
                'total_audit_recovery_triggers':sum(r['audit_recovery_triggers'] for r in rows)})
    result={'status':'COMPLETE_CONTROLLED_MATRIX','level':1,'total_episodes':len(all_rows),
            'configuration_sha256':protocol['configuration_sha256'],'wall_seconds':time.perf_counter()-start,
            'summary':summary,'native_improvement_verified':False,
            'limitations':['analytic model family and calibration share construction',
               'motion phase is source-invariant after uniform phase integration',
               'posterior uses dwell only; M2 geometry additionally sees travel stream',
               'known finite candidates; not an unseen-source generalization test',
               'no native PMFS, sensor downwash, lake physics or actual flight tested']}
    (out/'CONTROL_MATRIX_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result
