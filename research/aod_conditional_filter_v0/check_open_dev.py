#!/usr/bin/env python3
"""Read-only check of frozen AOD filter on the eight OPEN dev episodes."""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

from bank import TemplateBank
from episode_io import read_archive, predicted_event_means
from gain_innovation_bank import GainInnovationBank


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cases',required=True)
    ap.add_argument('--archives',required=True)
    ap.add_argument('--bank-dir',required=True)
    ap.add_argument('--zstd',required=True)
    ap.add_argument('--calibration',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    cfg=json.loads(Path(a.calibration).read_text())
    if cfg['status']!='AOD_FILTER_TRAIN_ONLY_PARAMETERS_FROZEN':
        raise RuntimeError('calibration missing')
    output=[];banks={}
    for case_file in sorted(Path(a.cases).glob('*.json')):
        case=json.loads(case_file.read_text())
        if case['split']!='dev':continue
        env=int(case['environment_index'])
        if env not in banks:banks[env]=TemplateBank.load(Path(a.bank_dir)/f'env_{env}_bank.npz')
        bank=banks[env]
        paths=glob.glob(str(Path(a.archives)/f'native_{case["ordinal"]:03d}_{case["case_id"]}.tar.zst'))
        if len(paths)!=1:raise RuntimeError('frozen dev archive missing')
        events=predicted_event_means(bank,read_archive(Path(paths[0]),a.zstd))
        model=GainInnovationBank(np.ones(len(bank.ids))/len(bank.ids),
                                 gain_mean=cfg['gain_mean'],gain_variance=cfg['gain_variance'],
                                 discrepancy_variance=cfg['discrepancy_variance'],
                                 correlation_time_s=cfg['correlation_time_s'],
                                 measurement_variance=cfg['measurement_variance'],
                                 positive_gain=cfg['positive_gain'])
        last_t=0.;all_log=[]
        for event_id,(t,y,m) in enumerate(events):
            u=model.update(event_id,t-last_t,y,m)
            last_t=t
            all_log.append(float(u.predictive_log_likelihood[bank.ids.index(case['source_id'])]))
        q=u.source_probability
        truth_idx=bank.ids.index(case['source_id'])
        rank=1+int(np.sum(q>q[truth_idx]))
        keep=max(1,int(np.ceil(.05*len(q))))
        top=np.argsort(-q,kind='stable')[:keep]
        estimate=np.average(bank.xy[top],axis=0,weights=q[top])
        result={'case_id':case['case_id'],'truth_rank':rank,
                'true_source_nll':float(-np.log(q[truth_idx])) if q[truth_idx]>0 else 'positive_infinity',
                'final_source_error_m':float(np.linalg.norm(estimate-np.array(case['truth_xy']))),
                'estimate_xy':estimate.tolist(),'events':len(events),
                'zero_events':sum(y==0 for _,y,_ in events),
                'mean_truth_innovation_log_density':float(np.mean(all_log))}
        output.append(result)
        print(f'[dev {len(output)}] rank={rank} error={result["final_source_error_m"]:.3f}m',flush=True)
    if len(output)!=8:raise RuntimeError('expected eight OPEN dev cases')
    target=Path(a.output)
    if target.exists():raise FileExistsError(target)
    target.write_text(json.dumps({'status':'AOD_FILTER_OPEN_DEV_CHECK_ONLY','cases':output},indent=2)+'\n')

if __name__=='__main__':main()
