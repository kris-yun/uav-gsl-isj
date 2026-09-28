#!/usr/bin/env python3
"""One-pass, train-only moment calibration for the non-neural AOD filter.

This deliberately has no hyperparameter search and never opens evaluation data.
"""
from __future__ import annotations

import argparse
import copy
import glob
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from bank import TemplateBank
from episode_io import read_archive, predicted_event_means


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cases',required=True)
    ap.add_argument('--archives',required=True)
    ap.add_argument('--bank-dir',required=True)
    ap.add_argument('--zstd',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    cases=sorted(Path(a.cases).glob('*.json'))
    selected=[]; banks={}; episode_gains=[]; residuals=[]; dts=[]; train_sources=set()
    for case_file in cases:
        case=json.loads(case_file.read_text())
        if case['split']!='train':
            continue
        env=int(case['environment_index'])
        if env not in banks:
            banks[env]=TemplateBank.load(Path(a.bank_dir)/f'env_{env}_bank.npz')
        bank=banks[env]
        source_id=case['source_id']
        if source_id not in bank.ids:
            raise RuntimeError('training truth outside legal support')
        idx=bank.ids.index(source_id)
        short=copy.copy(bank)
        short.ids=(source_id,)
        short.p=bank.p[idx:idx+1]
        short.u=bank.u[idx:idx+1]
        paths=glob.glob(str(Path(a.archives)/f'native_{case["ordinal"]:03d}_{case["case_id"]}.tar.zst'))
        if len(paths)!=1:
            raise RuntimeError('missing or duplicate training archive')
        data=read_archive(Path(paths[0]),a.zstd)
        events=predicted_event_means(short,data)
        t=np.array([x[0] for x in events]); y=np.array([x[1] for x in events]); m=np.array([x[2][0] for x in events])
        gain=max(0.,float(np.dot(m,y)/max(np.dot(m,m),1e-20)))
        episode_gains.append(gain)
        residuals.append(y-gain*m)
        dts.append(np.diff(t))
        train_sources.add((env,source_id))
        selected.append({'case_id':case['case_id'],'archive_sha256':sha(paths[0]),
                         'events':len(events),'positive_events':int((y>0).sum()),
                         'episode_gain':gain})
        print(f'[{len(selected):02d}] env={env} events={len(events)} gain={gain:.7g}',flush=True)
    if len(selected)!=40:
        raise RuntimeError(f'expected 40 frozen train episodes, got {len(selected)}')
    gains=np.array(episode_gains)
    # Cross-episode gain mean/variance, plus event residual covariance moments.
    g0=float(gains.mean())
    vg=float(gains.var(ddof=1))
    all_r=np.concatenate(residuals)
    c0=float(np.mean(all_r*all_r))
    c1=float(np.mean(np.concatenate([r[:-1]*r[1:] for r in residuals if len(r)>1])))
    rho=float(np.clip(c1/max(c0,1e-12),0.,.99))
    event_dt=float(np.median(np.concatenate(dts)))
    # The white component is a common event-level model error, not sensor noise.
    vd=max(0.,c0*rho)
    R=max(c0-vd,1e-12)
    tc=float(np.clip(-event_dt/np.log(rho),.2,300.)) if rho>0 else event_dt
    if g0<=0 or vg<=0:
        raise RuntimeError('training data cannot identify a positive gain prior')
    output={'status':'AOD_FILTER_TRAIN_ONLY_PARAMETERS_FROZEN',
            'method':'single pass source-truth episode gain and residual lag-1 moments; no grid search',
            'gain_mean':g0,'gain_variance':vg,'discrepancy_variance':vd,
            'correlation_time_s':tc,'measurement_variance':R,'positive_gain':True,
            'training_episode_count':len(selected),'training_physical_sources':len(train_sources),
            'training_archives':selected,
            'bank_sha256':{str(env):sha(Path(a.bank_dir)/f'env_{env}_bank.npz') for env in banks},
            'calibrator_sha256':sha(__file__)}
    target=Path(a.output)
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('training_archives','bank_sha256')},indent=2))

if __name__=='__main__':main()
