"""Audit full checked runs; never promote or score a failed prefix as a full run."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from ctpi_v2_score_spent_wind import summarize


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    runs=json.loads((args.stage/'RUNS.json').read_text())
    result={'status':'CHECKED_WIND_ABLATION_NOT_M1_OR_CLOSED_LOOP_PASS','arms':[]}
    for run in runs:
        directory=args.stage/run['arm']
        audit=rows(directory/'solver_audit.csv')
        predictions=rows(directory/'predictions.csv')
        complete=run['returncode']==0 and (directory/'COMPLETED.json').exists()
        summary={'arm':run['arm'],'run_complete':complete,'completed_updates':len(audit)}
        for step,row in enumerate(audit,1):
            if int(row['step'])!=step or not 2<=int(row['iterations'])<=100:
                raise ValueError('iteration audit mismatch')
            for key,limit in [('relative_change',.01),('backward_residual',1e-10),('update_mismatch',1e-12)]:
                value=float(row[key])
                if not math.isfinite(value) or not 0<=value<=limit:
                    raise ValueError('invalid numeric certificate')
            if run['arm']=='checked_cumulative' and int(row['active_observations'])!=step:
                raise ValueError('cumulative evidence was dropped')
            if not 1<=int(row['active_observations'])<=step:
                raise ValueError('invalid active observation count')
        if complete:
            if len(audit)!=1200 or len(predictions)!=1199:
                raise ValueError('false completion marker')
            for step,row in enumerate(predictions,2):
                if int(row['step'])!=step or abs(float(row['t_sim_s'])-.2*step)>1e-9 or abs(float(row['input_through_s'])-.2*(step-1))>1e-9:
                    raise ValueError('invalid prediction ordering')
            summary.update({'all':summarize(predictions),
                'same_printed_pose':summarize([r for r in predictions if r['same_printed_pose']=='1']),
                'changed_printed_pose':summarize([r for r in predictions if r['same_printed_pose']=='0']),
                'max_iterations':max(int(r['iterations']) for r in audit),
                'mean_iterations':sum(int(r['iterations']) for r in audit)/len(audit),
                'max_backward_residual':max(float(r['backward_residual']) for r in audit),
                'max_update_mismatch':max(float(r['update_mismatch']) for r in audit)})
        else:
            summary['last_log_line']=(args.stage/(run['arm']+'.log')).read_text().splitlines()[-1]
            summary['failed_update_step']=len(audit)+1
            summary['prediction_score']='NOT_REPORTED_FAILED_PREFIX'
        summary['file_hashes']={path.name:hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [directory/'predictions.csv',directory/'solver_audit.csv']}
        result['arms'].append(summary)
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['limitations']=['Linear solve checks and Picard tolerance are not transport/source identification.',
        'No local numerical result establishes a calibrated joint wind uncertainty law.',
        'The latest-cell arm, if incomplete, cannot be selected using a favorable prefix.']
    with args.out.open('x') as f:
        json.dump(result,f,indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
