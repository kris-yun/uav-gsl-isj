"""V56 source-blind finite nuisance-bank action separation gate.
This is a reference action *screen*, not a physical gas solver and not an
uncertainty-certified continuum source-position criterion. Use only when a
shared qualified source-dependent forward provides finite response templates
and an independently valid uniform response error bound.
"""
import numpy as np

def finite_min_contrast(means,q_values,sigma):
    f=np.asarray(means,float);q=np.asarray(q_values,float)
    if (f.ndim!=2 or f.shape[0]<2 or f.shape[1]<1 or q.ndim!=1 or len(q)==0
        or np.any(q<0) or np.any(f<0) or sigma<=0 or
        not np.isfinite(f).all() or not np.isfinite(q).all()):
        raise ValueError('Invalid finite nuisance/source bank')
    best=float('inf')
    for a in range(len(f)):
        for b in range(a):
            dd=q[:,None,None]*f[a,None,None,:]-q[None,:,None]*f[b,None,None,:]
            best=min(best,float(np.linalg.norm(dd,axis=-1).min()/sigma))
    return best

def select(actions,q_values,sigma):
    """actions iterable of dicts: name, finite source_shapes(H,n),
    model_error_whitened, legal.  A missing certified error bound abstains,
    rather than treating model uncertainty as zero. Caller must provide all
    candidates under identical safety/finite nuisance/measurement conditions.
    """
    rows=[]
    for a in actions:
        if not a['legal']:continue
        err=a.get('model_error_whitened')
        if err is None:
            rows.append({'name':a['name'],'status':'UNKNOWN_MODEL_ERROR'})
            continue
        if err<0 or not np.isfinite(err):raise ValueError('Bad error bound')
        nominal=finite_min_contrast(a['source_shapes'],q_values,sigma)
        robust=max(0.,nominal-2*float(err))
        rows.append({'name':a['name'],'status':'SCORED','nominal':nominal,'lower_bound':robust})
    qualified=[r for r in rows if r['status']=='SCORED']
    if not qualified:return None,{'stage':'ABSTAIN_UNQUALIFIED_FORWARD','rows':rows}
    best=min(qualified,key=lambda r:(-r['lower_bound'],r['name']))
    if best['lower_bound']<=1e-12:return None,{'stage':'ABSTAIN_NO_CERTIFIED_SEPARATION','rows':rows}
    return best['name'],{'stage':'SCORED_FINITE_BANK','best':best,'rows':rows}
