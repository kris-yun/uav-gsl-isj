#!/usr/bin/env python3
"""Read-only reproduction of the frozen O24 source scorer, all saved updates.

Scientific scope: these are native two-dimensional PMFS hit maps, *not* a
source-to-ppm response operator. No gas or ROS forward calls are made.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import time
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import numpy as np

D_NATIVE = 0.2


def decode_csv(payload: bytes) -> list[dict]:
    return list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))


def logistic(log_odds: np.ndarray) -> np.ndarray:
    # Stable even if future exports include very high/low log-odds.
    arr = np.asarray(log_odds, dtype=np.float64)
    out = np.empty_like(arr)
    m = arr >= 0
    out[m] = 1 / (1 + np.exp(-arr[m]))
    ee = np.exp(arr[~m]); out[~m] = ee / (1 + ee)
    return out


@dataclass
class SavedRun:
    role: str
    meta: list[dict]
    posterior: list[dict]
    response_bytes: bytes


def audit_saved_run(run: SavedRun, tol=1e-10) -> dict:
    """Parity between 2D native O24, dense scoring, and alpha-support scoring.

    Truth locations are NOT used by this function.  The saved native posterior
    is read solely for numerical parity verification, not calibration/tuning.
    """
    candidates: dict[int, list] = defaultdict(list)
    posterior: dict[int, list] = defaultdict(list)
    for row in run.meta: candidates[int(row['update'])].append(row)
    for row in run.posterior: posterior[int(row['update'])].append(row)
    if set(candidates) != set(posterior):
        raise AssertionError('Update mismatch: candidate bank versus posterior')
    update_rows = []
    buffer = run.response_bytes
    total_candidates = 0
    max_post_err = 0.
    max_score_err = 0.
    for update in sorted(candidates):
        cs, ms = candidates[update], posterior[update]
        nx = 1 + max(int(m['col']) for m in ms)
        ny = 1 + max(int(m['row']) for m in ms)
        # Grid may have excluded edge cells; use binary map length to disambiguate.
        counts = {int(c['count']) for c in cs}
        if len(counts) != 1 or nx * ny != next(iter(counts)):
            raise ValueError('Grid identity unknown; do not infer/resize responses')
        idx = np.array([int(m['col']) + nx*int(m['row']) for m in ms], dtype=np.int64)
        alpha = np.array([float(m['hit_confidence']) for m in ms], dtype=np.float64)
        probs = logistic(np.array([float(m['hit_log_odds']) for m in ms],dtype=np.float64))
        if not (np.isfinite(alpha).all() and (alpha>=0).all() and (alpha<=1).all()):
            raise ValueError('Invalid O24 confidence values')
        keep = alpha > 0
        if not keep.any():
            raise ValueError('All confidence weights zero: cannot localize')
        grid = np.zeros((ny,nx), dtype=np.float64)
        full_score_errs = []; support_score_errs = []
        # Reproduce coarse-to-fine overwrite, retaining native candidate identity.
        for row in sorted(cs,key=lambda r:-int(r['size_x'])*int(r['size_y'])):
            total_candidates += 1
            off=int(row['offset_bytes']); n=int(row['count'])
            if off < 0 or (off+4*n)>len(buffer):raise ValueError('Out-of-range map offset')
            response=np.frombuffer(buffer, dtype='<f4',offset=off,count=n)
            # In native PMFS obstacle cells are deliberately not divided by
            # timesteps; they can store raw counts >1. Only free observed cells
            # participate in the score, so validate those instead of clipping.
            evaluated=response[idx]
            if not np.isfinite(evaluated).all() or np.any(evaluated<0) or np.any(evaluated>1):
                raise ValueError('Invalid native hit-frequency on evaluated free cells')
            factors=1-D_NATIVE*alpha*np.abs(probs-response[idx])
            score=float(np.prod(factors))
            support_score=float(np.prod(factors[keep]))
            old_score=float(row['score'])
            full_score_errs.append(abs(score-old_score)/max(abs(old_score),1e-280))
            support_score_errs.append(abs(support_score-score)/max(abs(score),1e-280))
            x,y,sx,sy=(int(row[k]) for k in ['origin_x','origin_y','size_x','size_y'])
            if x<0 or y<0 or sx<=0 or sy<=0 or x+sx>nx or y+sy>ny:
                raise ValueError('Invalid source region; exclude run')
            grid[y:y+sy,x:x+sx]=score
        inferred=grid.ravel()[idx]
        inferred/=inferred.sum()
        native=np.array([float(m['source_probability']) for m in ms],dtype=np.float64)
        p_err=float(np.max(np.abs(inferred-native)))
        s_err=float(max(full_score_errs)); c_err=float(max(support_score_errs))
        if max(p_err,s_err,c_err)>tol:
            raise AssertionError(f'O24 parity FAIL role={run.role} update={update}: {p_err,s_err,c_err}')
        max_post_err=max(max_post_err,p_err);max_score_err=max(max_score_err,s_err)
        update_rows.append({
          'update':update,'candidate_forward_maps':len(cs),'source_support_cells':len(ms),
          'informative_confidence_cells':int(keep.sum()),
          'informative_fraction_of_full_grid':float(keep.sum()/(nx*ny)),
          'informative_fraction_of_free_grid':float(keep.mean()),
          'native_score_relative_error_max':s_err,
          'support_mask_relative_error_max':c_err,
          'native_posterior_absolute_error_max':p_err,
          'full_grid_cells':nx*ny,
          'no_new_simulation':True,
        })
    return {'role':run.role,'status':'PASS_NATIVE_SAVED_SCORE_POSTERIOR_AND_EXACT_SUPPORT',
            'updates':update_rows,'candidate_forward_maps':total_candidates,
            'max_score_relative_error':max_score_err,'max_posterior_abs_error':max_post_err,
            'physical_ppm_prediction':'NOT_AVAILABLE',
            'task_localization_gain':'NOT_TESTED',
            'note':'Support masking reduces only scorer input cells, not simulator computation or online search time.'}


def saved_runs_in_package(path:Path, history:bool)->list[SavedRun]:
    paths=[]
    with zipfile.ZipFile(path) as z:
        files=z.namelist(); prefix='recovery/cases/'
        runnames=sorted({p.split('/')[2] for p in files if p.startswith(prefix) and p.endswith('/runtime/native_candidate_maps.csv')})
        for role in runnames:
            name=f'{prefix}{role}/runtime/'
            paths.append(SavedRun(role,decode_csv(z.read(name+'native_candidate_maps.csv')),
               decode_csv(z.read(name+'native_posterior_updates.csv')),
               z.read(name+'native_candidate_maps.f32')))
        if history:
            name='history/previous_four_episode_HOLD_evidence.zip'
            if name not in files: raise ValueError('Missing history: no silent episode selection')
            with zipfile.ZipFile(io.BytesIO(z.read(name))) as inner:
                f=inner.namelist()
                oldroles=sorted({p.split('/')[1] for p in f if p.startswith('cases/') and p.endswith('/runtime/native_candidate_maps.csv')})
                for role in oldroles:
                    pre=f'cases/{role}/runtime/'
                    paths.append(SavedRun(role,decode_csv(inner.read(pre+'native_candidate_maps.csv')),
                      decode_csv(inner.read(pre+'native_posterior_updates.csv')),
                      inner.read(pre+'native_candidate_maps.f32')))
    return paths


def main():
    ap=argparse.ArgumentParser(description='Read-only O24 2D replay, not physics A-prime')
    ap.add_argument('--zip',required=True,type=Path)
    ap.add_argument('--with-history',action='store_true',help='include R02 HOLD in bookkeeping, not validation')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    started=time.perf_counter()
    results=[audit_saved_run(r) for r in saved_runs_in_package(args.zip,args.with_history)]
    payload={'source':'frozen O24 20261018 ZIP','identity':'631145657461c41840f6844f118de57d1e747ea4',
             'status':'PASS_SAVED_NUMERICS_ONLY','episodes':results,
             'historical_HOLD_not_rescored_as_scientific_pass':['O24G_A2_R02'],
             'replay_wall_seconds':time.perf_counter()-started,
             'physical_counterfactual_columns_found':0,
             'physical_A_prime':'BLOCKED_NO_CANDIDATE_PPM_RESPONSE_COLUMNS',
             'B_incremental_value':'NOT_TESTED',
             'new_forward_calls':0,'new_ROS_goals':0}
    args.out.parent.mkdir(exist_ok=True,parents=True)
    args.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'status':payload['status'],'cases':len(results),
      'calls':sum(r['candidate_forward_maps'] for r in results),
      'updates':sum(len(r['updates']) for r in results),
      'worst_error':max(r['max_posterior_abs_error'] for r in results)},ensure_ascii=False))

if __name__=='__main__':main()
