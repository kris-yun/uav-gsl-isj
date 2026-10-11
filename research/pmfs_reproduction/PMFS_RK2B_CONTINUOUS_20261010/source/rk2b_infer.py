"""Pure source inference from candidate-owned forecasts and scalar observations only."""
import sys
sys.dont_write_bytecode=True
import numpy as np
TH=np.float32(.1)
def infer(predicted_ppm,observed_ppm,head='H0',scale=1.,blocks=None):
    x=np.asarray(predicted_ppm,dtype=np.float32);y=np.asarray(observed_ppm,dtype=np.float32)
    assert x.ndim==3 and x.shape[0]>=2 and x.shape[1] in (2,4) and x.shape[2]==50 and y.shape==(50,)
    assert np.isfinite(x).all() and np.isfinite(y).all() and (x>=0).all() and (y>=0).all()
    ix=np.arange(50) if blocks is None else np.asarray(blocks,dtype=int)
    assert len(ix)>0 and np.all((ix>=0)&(ix<50))
    hits=x>TH;p=(hits.sum(axis=1)+.5)/(x.shape[1]+1)
    z=np.log1p(x.astype(float));zy=np.log1p(y.astype(float))
    crps=np.mean(np.abs(z-zy[None,None,:]),axis=1)-.5*np.mean(np.abs(z[:,:,None,:]-z[:,None,:,:]),axis=(1,2))
    assert np.min(crps)>=-1e-12
    if head=='H0':terms=np.where(y[None,:]>TH,np.log(p),np.log1p(-p))
    else:
        assert head=='H1' and np.isfinite(scale) and scale>0;terms=-crps/scale
    scores=terms[:,ix].mean(axis=1);lp=scores-np.logaddexp.reduce(scores);prob=np.exp(lp)
    return dict(scores=scores,log_prob=lp,prob=prob,block_terms=terms,event_probability=p,CRPS=crps,
        top1=np.flatnonzero(np.isclose(scores,np.max(scores),rtol=0,atol=1e-12)),head=head)
def future(predicted_ppm,observed_ppm,source_probability):
    x=np.asarray(predicted_ppm,dtype=np.float32);y=np.asarray(observed_ppm,dtype=np.float32)[25:];w=np.asarray(source_probability,dtype=float)
    assert x.shape[0]==len(w) and np.isclose(w.sum(),1)
    p=(np.sum(x>TH,axis=1)+.5)/(x.shape[1]+1);p_mix=w@p[:,25:]
    vals=np.log1p(x[:,:,25:].astype(float)).reshape(-1,25);weights=np.repeat(w/x.shape[1],x.shape[1])
    zy=np.log1p(y.astype(float));c=weights@np.abs(vals-zy[None,:])-.5*np.einsum('i,j,ijt->t',weights,weights,np.abs(vals[:,None,:]-vals[None,:,:]))
    return dict(mean_Brier=float(np.mean((p_mix-(y>TH))**2)),mean_CRPS=float(np.mean(c)),
        predicted_hit_probability=p_mix.tolist(),CRPS_per_block=c.tolist(),future_observations_not_used_in_source_infer=True)
