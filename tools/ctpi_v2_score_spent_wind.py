"""Score recorded pre-assimilation predictions; cannot certify a wind field."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def summarize(rows):
    if not rows:
        return {'n': 0}
    def rmse(a,b):
        return math.sqrt(sum((float(r[a])-float(r['u']))**2 +
                             (float(r[b])-float(r['v']))**2 for r in rows)/len(rows))
    return {'n': len(rows), 'gmrf_vector_rmse_m_s': rmse('pred_u','pred_v'),
            'persistence_vector_rmse_m_s': rmse('persist_u','persist_v')}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--predictions', type=Path, required=True)
    p.add_argument('--completion', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args=p.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    done=json.loads(args.completion.read_text())
    if done['steps']!=1200:
        raise ValueError('incomplete replay')
    with args.predictions.open() as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=1199:
        raise ValueError('missing forecasts')
    for expected,r in enumerate(rows,2):
        if int(r['step'])!=expected or abs(float(r['t_sim_s'])-.2*expected)>1e-9:
            raise ValueError('forecast cadence mismatch')
        if abs(float(r['t_sim_s'])-float(r['input_through_s'])-.2)>1e-9:
            raise ValueError('future/incorrect wind timestamp')
        if not all(math.isfinite(float(r[c])) for c in ['u','v','pred_u','pred_v','persist_u','persist_v']):
            raise ValueError('nonfinite forecast')
    result={'status':'SPENT_LOCAL_WIND_DIAGNOSTIC_NOT_SOURCE_OR_UTILITY_PASS',
            'all':summarize(rows),
            'same_printed_pose':summarize([r for r in rows if r['same_printed_pose']=='1']),
            'changed_printed_pose':summarize([r for r in rows if r['same_printed_pose']=='0']),
            'before_replay_seam':summarize([r for r in rows if float(r['t_sim_s'])<189.8]),
            'from_replay_seam':summarize([r for r in rows if float(r['t_sim_s'])>=189.8]),
            'seam_rows':[int(r['step']) for r in rows if r['replay_seam']=='1'],
            'hashes':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.predictions,args.completion,Path(__file__)]},
            'limits':['One Picard iteration means convergence is not established.',
                      'Core update returns void and catches some errors internally; finite fields do not prove solver success.',
                      'No observations were removed, no sensor positions moved, no model tuned on these scores.',
                      'Target pose is conditioned on; this is not a forecast of robot motion.',
                      'Local vector score cannot validate unobserved spatial wind or gas transport.']}
    with args.out.open('x') as f:
        json.dump(result,f,indent=2)
        f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='hashes'}))


if __name__=='__main__':
    main()
