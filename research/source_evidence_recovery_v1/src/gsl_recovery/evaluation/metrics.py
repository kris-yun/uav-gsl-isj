"""Paired episode, not measurement-window, uncertainty summaries."""
import numpy as np

def paired_summary(baseline,candidate,seed=0,repeats=2000):
    a=np.asarray(baseline,float);b=np.asarray(candidate,float)
    if a.shape!=b.shape or a.ndim!=1 or not len(a) or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('paired inputs')
    rng=np.random.default_rng(seed);d=b-a;boot=np.mean(d[rng.integers(0,len(d),(repeats,len(d)))],axis=1)
    return {'n_independent_episodes':len(a),'baseline_mean':float(a.mean()),'candidate_mean':float(b.mean()),'paired_change':float(d.mean()),'paired_change_ci95':np.quantile(boot,[.025,.975]).tolist(),'relative_error_reduction':float((a.mean()-b.mean())/a.mean()) if a.mean()>0 else None,'warning':'cluster by scene/source/wind realization in final study; this function assumes independent pairs'}
