#!/usr/bin/env python3
"""O24 saved 2D hit-map bank cross-update score-compression audit.

IMPORTANT: Native full candidate maps are needed at evaluation time. This tests
representation stability, NOT new forward speed, physical ppm, or independence
of plume worlds. Fit bases solely from update 1, test updates >=2. No truth.
"""
from __future__ import annotations
import argparse, json
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.linalg import svd
from o24_parity import saved_runs_in_package, logistic

RANKS=(2,4,8,16,32)

@dataclass
class O24Update:
    role:str
    index:int
    P:np.ndarray
    y:np.ndarray
    alpha:np.ndarray
    rows:list[dict]
    posterior:list[dict]
    nx:int
    ny:int
    grid_idxs:np.ndarray
    score:np.ndarray


def load_updates(run)->list[O24Update]:
    cms=defaultdict(list);post=defaultdict(list)
    for x in run.meta:cms[int(x['update'])].append(x)
    for x in run.posterior:post[int(x['update'])].append(x)
    out=[]
    for step,rows in sorted(cms.items()):
        ps=post[step];nx=1+max(int(x['col']) for x in ps);ny=1+max(int(x['row']) for x in ps)
        idx=np.array([int(x['row'])*nx+int(x['col']) for x in ps])
        n=nx*ny
        if any(int(c['count'])!=n for c in rows):raise ValueError('Grid-size mismatch')
        X=np.array([np.frombuffer(run.response_bytes,dtype='<f4',count=n,offset=int(c['offset_bytes']))[idx] for c in rows],dtype=np.float64)
        if np.any(X<0) or np.any(X>1):raise ValueError('hit response not [0,1] on free cells')
        alpha=np.array([float(x['hit_confidence']) for x in ps]); y=logistic(np.array([float(x['hit_log_odds']) for x in ps])); score=np.log(np.array([float(x['score']) for x in rows]));
        reread=np.log1p(-.2*alpha[None,:]*abs(X-y[None,:])).sum(axis=1)
        if max(abs(reread-score))>1e-11:raise AssertionError('Cannot reproduce O24 native scores')
        out.append(O24Update(run.role,step,X,y,alpha,rows,ps,nx,ny,idx,score))
    return out


def native_post(up:O24Update, score:np.ndarray):
    g=np.zeros((up.ny,up.nx),dtype=np.float64)
    # Native region filling: largest leaf first, finer regions overwrite.
    order=sorted(range(len(up.rows)),key=lambda i:-int(up.rows[i]['size_x'])*int(up.rows[i]['size_y']))
    for i in order:
        c=up.rows[i];x=int(c['origin_x']);y=int(c['origin_y']);sx=int(c['size_x']);sy=int(c['size_y'])
        g[y:y+sy,x:x+sx]=np.exp(score[i]-np.max(score))
    v=g.ravel()[up.grid_idxs]; v=v/v.sum()
    return v


def fit(X:np.ndarray, weights:np.ndarray,mode:str, maxrank:int):
    mu=np.zeros((1,X.shape[1])) if mode=='uncentered_pod' else X.mean(axis=0,keepdims=True)
    if mode=='train_alpha_weighted_pod':
        # Fixed prespecified positive floor allows later newly-observed cells
        # to enter the metric; choosing it from the held-out update is forbidden.
        scales=np.sqrt(np.maximum(weights,0)+0.01)
    else:scales=np.ones(X.shape[1]);
    _,_,vt=svd((X-mu)*scales,full_matrices=False,lapack_driver='gesdd',check_finite=False)
    return mu,scales,vt[:maxrank,:]


def reconstruct(X:np.ndarray,model,rank:int):
    mu,scales,v=model;r=min(rank,v.shape[0]);Z=(X-mu)*scales
    raw=(Z@v[:r].T)@v[:r]/scales+mu
    clipped=int(np.count_nonzero((raw<0)|(raw>1)))
    return np.clip(raw,0,1),clipped


def rankcorr(x,y):
    def arr(a):
        unique,inv,count=np.unique(a,return_inverse=True,return_counts=True)
        vals=np.cumsum(count)-.5*(count-1)-1
        return vals[inv].astype(float)
    a=arr(x);b=arr(y);a-=a.mean();b-=b.mean()
    den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(a@b/den) if den>1e-15 else 1.0


def run_case(run):
    updates=load_updates(run)
    if len(updates)<2:return []
    u0=updates[0]
    if any(len(u0.posterior)!=len(u.posterior) or not np.array_equal(u0.grid_idxs,u.grid_idxs) for u in updates[1:]):
        raise ValueError('Support geometry changes: no cross-update comparison')
    models={mode:fit(u0.P,u0.alpha,mode,max(RANKS)) for mode in ('uncentered_pod','centered_pod','train_alpha_weighted_pod')}
    results=[]
    for u in updates[1:]:
        basep=native_post(u,u.score)
        for method,model in models.items():
            for rank in RANKS:
                pred,clips=reconstruct(u.P,model,rank)
                score=np.log1p(-.2*u.alpha[None,:]*abs(pred-u.y[None,:])).sum(axis=1)
                pp=native_post(u,score)
                results.append({'episode':run.role,'fit_update':updates[0].index,'test_update':u.index,
                    'fit_candidates':len(u0.rows),'test_candidates':len(u.rows),'source_cells':len(basep),
                    'method':method,'rank':rank,
                    'native_logscore_rmse':float(np.sqrt(np.mean((score-u.score)**2))),
                    'native_logscore_mae':float(np.mean(abs(score-u.score))),
                    'candidate_spearman':rankcorr(score,u.score),
                    'candidate_best_identity_preserved':int(np.argmax(score)==np.argmax(u.score)),
                    'source_posterior_tvd':float(.5*np.abs(pp-basep).sum()),
                    'source_cell_argmax_preserved':int(np.argmax(pp)==np.argmax(basep)),
                    'out_of_unit_interval_before_clip':clips,
                    'new_nonzero_alpha_cells':int(np.count_nonzero((u0.alpha==0)&(u.alpha>0))),
                    'test_positive_alpha_cells':int(np.count_nonzero(u.alpha>0)),
                    'no_truth_access':True, 'not_independent_world':True, 'requires_full_test_forward_maps':True})
    return results


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--zip',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    raw=saved_runs_in_package(args.zip,True)
    results=[]
    for run in raw:
        results+=run_case(run)
    summary=[]
    for method in ('uncentered_pod','centered_pod','train_alpha_weighted_pod'):
        for rank in RANKS:
            r=[x for x in results if x['method']==method and x['rank']==rank]
            summary.append({'method':method,'rank':rank,'updates':len(r),
               'median_score_rmse':float(np.median([x['native_logscore_rmse'] for x in r])),
               'median_source_tvd':float(np.median([x['source_posterior_tvd'] for x in r])),
               'candidate_best_preserved':sum(x['candidate_best_identity_preserved'] for x in r),
               'source_cell_argmax_preserved':sum(x['source_cell_argmax_preserved'] for x in r)})
    p={'status':'FROZEN_O24_CROSS_UPDATE_POD_DIAGNOSTIC','fit':'first source update per episode, candidate bank only','eval':'all later updates for same episode, never fit basis to these responses','episode_count':len(raw),'test_update_count':len(set((r['episode'],r['test_update']) for r in results)),'results':results,'summary':summary,'scientific_limits':['All A2 runs share A2 world; do not count as independent worlds','A2 R02 is HOLD_DOMAIN, diagnostic only','Requires full test forward maps; no speedup shown','Only native 2D hit-map, not physical ppm K','No source truth or real concentration used for train-fitting']}
    args.out.parent.mkdir(exist_ok=True,parents=True);args.out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':p['status'],'episodes':len(raw),'test_updates':p['test_update_count'],'rank8_summary':[r for r in summary if r['rank']==8]},ensure_ascii=False))
if __name__=='__main__':main()
