#!/usr/bin/env python3
"""Truth-free offline audit for the reconstructed PF-DEI method.

Input NPZ: candidate_physical_ppm[S,M,T], source_id[S], transport_id[M],
geometry_prior[S], optional sample_time_s[T].  No localization outcome is read.

The audit separates four claims:
  (A) source separability from held-out physical trajectories;
  (B) chronological information beyond pointwise level matching;
  (C) benefit of preserving one nuisance member as one coherent trajectory;
  (D) optional amplitude/Q robustness stress for later real-world deployment.

LOMO removes held-out member j from *every* source ensemble. CROSS compares an
independent observation/reserved bank against the predictive/train bank.
"""
from __future__ import annotations
import argparse, json, math
from dataclasses import dataclass
from pathlib import Path
import numpy as np

EPS=1e-12

@dataclass(frozen=True)
class Bank:
    x: np.ndarray
    source_id: tuple[str,...]
    member_id: tuple[str,...]
    q0: np.ndarray
    t: np.ndarray|None
    path: str


def load_bank(path: Path)->Bank:
    with np.load(path,allow_pickle=False) as d:
        if 'candidate_physical_ppm' not in d: raise ValueError('missing candidate_physical_ppm')
        x=np.asarray(d['candidate_physical_ppm'],dtype=np.float64)
        if x.ndim!=3 or min(x.shape)<2 or not np.all(np.isfinite(x)) or np.min(x)<-1e-10:
            raise ValueError('candidate_physical_ppm must be finite nonnegative [S,M,T]')
        x=np.maximum(x,0.0); S,M,T=x.shape
        sid=tuple(str(v) for v in d['source_id'].tolist()) if 'source_id' in d else tuple(f's{i}' for i in range(S))
        mid=tuple(str(v) for v in d['transport_id'].tolist()) if 'transport_id' in d else tuple(f'm{i}' for i in range(M))
        if len(sid)!=S or len(set(sid))!=S or len(mid)!=M or len(set(mid))!=M: raise ValueError('unstable IDs')
        q=np.asarray(d['geometry_prior'],dtype=np.float64) if 'geometry_prior' in d else np.ones(S)
        if q.shape!=(S,) or np.any(q<0) or not np.all(np.isfinite(q)) or q.sum()<=0: raise ValueError('bad q0')
        q=q/q.sum(); t=None
        if 'sample_time_s' in d:
            t=np.asarray(d['sample_time_s'],dtype=np.float64)
            if t.shape!=(T,) or not np.all(np.diff(t)>0): raise ValueError('bad time grid')
    return Bank(x,sid,mid,q,t,str(path))


def ppm_transform(x,mode='log1p',threshold=0.1):
    a=np.asarray(x,dtype=np.float64)
    if mode=='raw': return a
    if mode=='log1p':
        if threshold<=0: raise ValueError('threshold must be positive')
        return np.log1p(np.maximum(a,0.0)/threshold)
    raise ValueError(mode)


def causal_embed(x,lags=(1,5,10),scales=None):
    """Level + causal lag increments; scales come only from predictive bank."""
    a=np.asarray(x,dtype=np.float64); T=a.shape[-1]
    if any(l<=0 or l>=T for l in lags): raise ValueError('bad lags')
    ch=[a]
    for l in lags:
        d=np.zeros_like(a); d[...,l:]=a[...,l:]-a[...,:-l]; ch.append(d)
    if scales is None:
        scales=tuple(max(float(np.sqrt(np.mean(c*c))),1e-8) for c in ch)
    if len(scales)!=len(ch): raise ValueError('bad channel scales')
    return np.concatenate([c/s for c,s in zip(ch,scales)],axis=-1),tuple(scales)


class Energy:
    """Fast multivariate energy score for candidate ensemble [S,M,D]."""
    def __init__(self,x):
        x=np.asarray(x,dtype=np.float64)
        if x.ndim!=3 or min(x.shape)<2 or not np.all(np.isfinite(x)): raise ValueError('bad candidate tensor')
        self.x=x; self.S,self.M,self.D=x.shape; self.flat=x.reshape(self.S*self.M,self.D)
        self.mx2=np.mean(self.flat*self.flat,axis=1)
        self.spread=np.empty(self.S)
        for s in range(self.S):
            z=x[s]; n=np.mean(z*z,axis=1); g=(z@z.T)/self.D
            self.spread[s]=0.5*np.mean(np.sqrt(np.maximum(n[:,None]+n[None,:]-2*g,0)))
    def score(self,y,batch=32):
        y=np.asarray(y,dtype=np.float64)
        if y.ndim==1: y=y[None,:]
        if y.ndim!=2 or y.shape[1]!=self.D: raise ValueError('bad observations')
        out=np.empty((len(y),self.S))
        for i in range(0,len(y),batch):
            yy=y[i:i+batch]; my=np.mean(yy*yy,axis=1); cross=(yy@self.flat.T)/self.D
            d=np.sqrt(np.maximum(my[:,None]+self.mx2[None,:]-2*cross,0)).reshape(len(yy),self.S,self.M)
            out[i:i+len(yy)]=d.mean(axis=2)-self.spread
        return out


def ranks(scores,truth):
    s=np.asarray(scores); tr=np.asarray(truth,dtype=int); B,S=s.shape
    ts=s[np.arange(B),tr]; less=np.sum(s<ts[:,None]-1e-14,axis=1); eq=np.sum(np.abs(s-ts[:,None])<=1e-14,axis=1)
    r=1+less+0.5*np.maximum(eq-1,0); nr=(r-1)/max(S-1,1)
    rival=np.min(np.where(np.arange(S)[None,:]==tr[:,None],np.inf,s),axis=1)
    return r,nr,rival-ts


def metrics(scores,truth):
    r,nr,margin=ranks(scores,truth); S=scores.shape[1]
    return {'cases':len(r),'sources':S,'top1':float(np.mean(r<=1)),'top5':float(np.mean(r<=5)),
            'top10':float(np.mean(r<=10)),'random_top5':float(min(5,S)/S),
            'median_rank':float(np.median(r)),'median_norm_rank':float(np.median(nr)),
            'mean_norm_rank':float(np.mean(nr)),'mean_rival_margin':float(np.mean(margin))}


def permutation_test(scores,truth,n=199,seed=20260829):
    r,nr,_=ranks(scores,truth); obs5=float(np.mean(r<=5)); obsm=float(np.median(nr)); S=scores.shape[1]
    rng=np.random.default_rng(seed); nt=[]; nm=[]; tr=np.asarray(truth,dtype=int)
    for _ in range(n):
        p=rng.permutation(S); rr,nn,_=ranks(scores,p[tr]); nt.append(np.mean(rr<=5)); nm.append(np.median(nn))
    nt=np.asarray(nt); nm=np.asarray(nm)
    return {'n':n,'top5_p':float((1+np.sum(nt>=obs5-EPS))/(n+1)),'rank_p':float((1+np.sum(nm<=obsm+EPS))/(n+1)),
            'null_top5_mean':float(nt.mean()),'null_median_norm_rank_mean':float(nm.mean())}


def sign_test(first_scores,second_scores,truth):
    _,a,_=ranks(first_scores,truth); _,b,_=ranks(second_scores,truth); d=b-a
    pos=int(np.sum(d>1e-14)); neg=int(np.sum(d<-1e-14)); n=pos+neg
    p=1.0 if n==0 else sum(math.comb(n,k) for k in range(pos,n+1))/(2.0**n)
    return {'first_better':pos,'second_better':neg,'ties':len(d)-n,'median_rank_gain':float(np.median(d)),'one_sided_p':float(p)}


def scramble_members(x,block=10):
    """Preserve every time marginal exactly, destroy long-run member identity."""
    a=np.asarray(x); S,M,T=a.shape; out=np.empty_like(a)
    for st in range(0,T,block):
        b=st//block; idx=(np.arange(M)+(1+3*b)%M)%M; out[:,:,st:min(T,st+block)]=a[:,idx,st:min(T,st+block)]
    if not np.array_equal(np.sort(a,axis=1),np.sort(out,axis=1)): raise AssertionError('marginal changed')
    return out


def time_permutation(T,block=10,seed=20260829):
    blocks=[np.arange(i,min(T,i+block)) for i in range(0,T,block)]; order=np.arange(len(blocks)); np.random.default_rng(seed).shuffle(order)
    return np.concatenate([blocks[i] for i in order])


def evaluate(pred,obs,truth,mode,threshold,lags,batch):
    px=ppm_transform(pred,mode,threshold); oy=ppm_transform(obs,mode,threshold)
    level=Energy(px).score(oy,batch); pe,sc=causal_embed(px,lags); oe,_=causal_embed(oy,lags,sc); causal=Energy(pe).score(oe,batch)
    sx=scramble_members(pred); se,_=causal_embed(ppm_transform(sx,mode,threshold),lags); scrambled=Energy(se).score(oe,batch)
    perm=time_permutation(pred.shape[-1]); tx=pred[:,:,perm]; te,_=causal_embed(ppm_transform(tx,mode,threshold),lags); tshuf=Energy(te).score(oe,batch)
    return {'level':metrics(level,truth),'level_perm':permutation_test(level,truth),
            'causal':metrics(causal,truth),'causal_perm':permutation_test(causal,truth),
            'coherence_scramble':metrics(scrambled,truth),'coherence_test':sign_test(causal,scrambled,truth),
            'time_shuffle':metrics(tshuf,truth),'order_test':sign_test(causal,tshuf,truth),
            'channel_scales':[float(v) for v in sc],
            'note':'level energy is invariant to common time permutation; do not use it alone as temporal-order evidence'}


def lomo(bank,args):
    folds=[]; S,M,T=bank.x.shape
    if M<3: raise ValueError('LOMO needs M>=3')
    for j in range(M):
        keep=[m for m in range(M) if m!=j]
        r=evaluate(bank.x[:,keep,:],bank.x[:,j,:],np.arange(S),args.transform,args.threshold,args.lags,args.batch)
        r['heldout_member']=bank.member_id[j]; folds.append(r)
    def avg(section,key): return float(np.mean([f[section][key] for f in folds]))
    agg={'folds':M,'level_top5':avg('level','top5'),'causal_top5':avg('causal','top5'),
         'causal_median_norm_rank':avg('causal','median_norm_rank'),'scrambled_top5':avg('coherence_scramble','top5'),
         'time_shuffle_top5':avg('time_shuffle','top5')}
    return {'contract':'PF_DEI_COHERENT_OFFLINE_AUDIT_V1','mode':'LOMO','bank':bank.path,'shape':[S,M,T],'folds':folds,'aggregate':agg}


def cross(pred,obs,args):
    if pred.source_id!=obs.source_id or pred.x.shape[2]!=obs.x.shape[2]: raise ValueError('cross bank mismatch')
    if pred.t is not None and obs.t is not None and np.max(np.abs(pred.t-obs.t))>1e-9: raise ValueError('time grid mismatch')
    y=np.transpose(obs.x,(1,0,2)).reshape(obs.x.shape[1]*obs.x.shape[0],obs.x.shape[2]); truth=np.tile(np.arange(obs.x.shape[0]),obs.x.shape[1])
    r=evaluate(pred.x,y,truth,args.transform,args.threshold,args.lags,args.batch)
    if args.amplitude_stress:
        r['amplitude_stress']=[]
        for a in (0.5,0.75,1.0,1.5,2.0):
            px=ppm_transform(pred.x,args.transform,args.threshold); yy=ppm_transform(y*a,args.transform,args.threshold)
            pe,sc=causal_embed(px,args.lags); oe,_=causal_embed(yy,args.lags,sc); scs=Energy(pe).score(oe,args.batch)
            r['amplitude_stress'].append({'scale':a,**metrics(scs,truth)})
    return {'contract':'PF_DEI_COHERENT_OFFLINE_AUDIT_V1','mode':'CROSS','predictive_bank':pred.path,'observation_bank':obs.path,
            'predictive_shape':list(pred.x.shape),'observation_shape':list(obs.x.shape),'result':r}


def selftest():
    rng=np.random.default_rng(7); S,M,T=8,4,160; tt=np.arange(T); x=np.empty((S,M,T))
    for s in range(S):
        base=.15+.07*np.sin((.025+.004*s)*tt+.45*s)+.12*(np.sin(.085*tt+.6*s)>.78)
        for m in range(M): x[s,m]=np.maximum(0,np.roll(base,2*m)*(0.9+.05*m)+rng.normal(0,.003,T))
    b=Bank(x,tuple(f's{s}' for s in range(S)),tuple(f'm{m}' for m in range(M)),np.ones(S)/S,np.arange(T)*.2,'synthetic')
    class A: pass
    a=A(); a.transform='log1p'; a.threshold=.1; a.lags=(1,5,10); a.batch=16; a.amplitude_stress=False
    out=lomo(b,a); assert out['aggregate']['causal_top5']>.7
    y=x[0,0]; z=ppm_transform(x,'log1p',.1); e0=Energy(z).score(ppm_transform(y,'log1p',.1))[0]; p=time_permutation(T)
    e1=Energy(z[:,:,p]).score(ppm_transform(y[p],'log1p',.1))[0]; assert np.max(np.abs(e0-e1))<1e-7
    ze,sc=causal_embed(z); ye,_=causal_embed(ppm_transform(y,'log1p',.1),scales=sc); s0=Energy(ze).score(ye)[0]
    s1=Energy(ze[:,::-1,:]).score(ye)[0]; assert np.max(np.abs(s0-s1))<1e-7
    print('PF_DEI_COHERENT_OFFLINE_AUDIT_SELFTEST PASS')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--selftest',action='store_true'); ap.add_argument('--mode',choices=['lomo','cross'])
    ap.add_argument('--bank',type=Path); ap.add_argument('--predictive-bank',type=Path); ap.add_argument('--observation-bank',type=Path); ap.add_argument('--output',type=Path)
    ap.add_argument('--transform',choices=['raw','log1p'],default='log1p'); ap.add_argument('--threshold',type=float,default=.1); ap.add_argument('--lags',type=int,nargs='+',default=[1,5,10]); ap.add_argument('--batch',type=int,default=32); ap.add_argument('--amplitude-stress',action='store_true')
    a=ap.parse_args()
    if a.selftest: selftest(); return
    if a.mode=='lomo':
        if not a.bank: ap.error('--bank required')
        out=lomo(load_bank(a.bank),a)
    elif a.mode=='cross':
        if not a.predictive_bank or not a.observation_bank: ap.error('both cross banks required')
        out=cross(load_bank(a.predictive_bank),load_bank(a.observation_bank),a)
    else: ap.error('choose --selftest or --mode')
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(text)
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding='utf-8')

if __name__=='__main__': main()
