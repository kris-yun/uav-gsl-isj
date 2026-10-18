#!/usr/bin/env python3
"""Freeze-update support shift mechanistic ablation on saved O24 2D maps.

Plain strong baseline: centered POD trained at update 1. Ordinary repair:
score newly informative observation cells exactly when they first appear.
No new forward simulations and no truth labels; this is neither A-prime ppm
physics nor B incremental proof.  Projection still requires full test maps.
"""
import argparse,json
from pathlib import Path
import numpy as np
from o24_cross_update_holdout import saved_runs_in_package,load_updates,fit,reconstruct,native_post,rankcorr

def score_components(P,y,alpha,mask):
    if not mask.any():return np.zeros(P.shape[0])
    return np.log1p(-.2*alpha[None,mask]*np.abs(P[:,mask]-y[None,mask])).sum(axis=1)

def exp(run,ranks=(8,16,32)):
    updates=load_updates(run)
    if len(updates)<2:return []
    first=updates[0]
    models={mode:fit(first.P,first.alpha,mode,max(ranks)) for mode in ('centered_pod','train_alpha_weighted_pod')}
    out=[]
    for u in updates[1:]:
        if not np.array_equal(u.grid_idxs,first.grid_idxs):raise ValueError('unsupported geometry mismatch')
        old=(first.alpha>0)&(u.alpha>0)
        new=(first.alpha==0)&(u.alpha>0)
        p_native=native_post(u,u.score)
        exact_old=score_components(u.P,u.y,u.alpha,old)
        exact_new=score_components(u.P,u.y,u.alpha,new)
        if max(abs(exact_old+exact_new-u.score))>1e-11:raise AssertionError('Nonpartitioned score')
        for method,model in models.items():
            for rank in ranks:
                pred,clips=reconstruct(u.P,model,rank)
                approx_old=score_components(pred,u.y,u.alpha,old)
                approx_new=score_components(pred,u.y,u.alpha,new)
                full_approx=approx_old+approx_new
                repair=approx_old+exact_new
                for m,s in (('plain_compressed',full_approx),('ordinary_exact_new_support_fallback',repair)):
                    post=native_post(u,s)
                    out.append({'episode':run.role,'test_update':u.index,'method':m,'pod_basis_type':method,'rank':rank,
                        'score_rmse':float(np.sqrt(np.mean((s-u.score)**2))),
                        'score_rmse_old_only':float(np.sqrt(np.mean((approx_old-exact_old)**2))),
                        'score_rmse_new_only':float(np.sqrt(np.mean((approx_new-exact_new)**2))),
                        'source_tvd':float(.5*np.abs(post-p_native).sum()),
                        'source_argmax_preserved':int(np.argmax(post)==np.argmax(p_native)),
                        'best_candidate_preserved':int(np.argmax(s)==np.argmax(u.score)),
                        'new_positive_alpha_cells':int(new.sum()),'old_positive_alpha_cells':int(old.sum()),
                        'fraction_new_alpha_mass':float(u.alpha[new].sum()/u.alpha.sum()),
                        'requires_uncompressed_new_cell_native_responses':m!='plain_compressed',
                        'not_independent_physical_world':True,'new_ROS_calls':0,'not_B_algorithm':True,
                        'full_simulator_forward_already_computed':True,'trained_on_first_update_only':True})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--zip',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rows=[]
    for case in saved_runs_in_package(a.zip,True):rows+=exp(case)
    summary=[]
    for basis in ('centered_pod','train_alpha_weighted_pod'):
        for rank in (8,16,32):
            for method in ('plain_compressed','ordinary_exact_new_support_fallback'):
                xs=[x for x in rows if x['pod_basis_type']==basis and x['rank']==rank and x['method']==method]
                summary.append({'basis':basis,'rank':rank,'method':method,'n_update':len(xs),
                    'median_rmse':float(np.median([x['score_rmse'] for x in xs])),
                    'median_tvd':float(np.median([x['source_tvd'] for x in xs])),
                    'source_map_preserved_count':sum(x['source_argmax_preserved'] for x in xs),
                    'candidate_top1_preserved_count':sum(x['best_candidate_preserved'] for x in xs)})
    a.out.write_text(json.dumps({'status':'ORDINARY_SUPPORT_SHIFT_ABLATION_ONLY', 'source':'O24 stored 2D candidate maps', 'rows':rows,'summary':summary,'limitations':['no physical ppm K','stochastic worlds not independent','all test native forward maps already computed','ordinary exact new-support fall-back is NOT a learned method or speedup','HOLD episode excluded from scientific proof but included as diagnostic']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([x for x in summary if x['rank']==8],ensure_ascii=False))
if __name__=='__main__':main()
