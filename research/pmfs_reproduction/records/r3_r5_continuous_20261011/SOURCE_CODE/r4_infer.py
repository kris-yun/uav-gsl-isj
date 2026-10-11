"""Source-blind consumer: reads public observations/config only; no generator import."""
import hashlib,json,pathlib,time
from datetime import datetime,timezone
import numpy as np
from scipy.special import logsumexp,log_ndtr
from r4_transport import step
BASE=pathlib.Path(__file__).resolve().parents[1];OUT=BASE/'outputs/PMFS_R3_R5_CONTINUOUS_20261011'
def normalized(l):return np.exp(l-logsumexp(l,axis=-1,keepdims=True))
def likelihood(y,mu,sd=.02):
    if y==0:return log_ndtr(-mu/sd)
    return -.5*((y-mu)/sd)**2-np.log(sd*np.sqrt(2*np.pi))
def resample(fields,logq,wind,lw,rng):
    w=normalized(lw);ess=1/np.sum(w*w,axis=1);counts=0;K=w.shape[1]
    for s in np.flatnonzero(ess<K/2):
        u=(rng.random()+np.arange(K))/K;ii=np.searchsorted(np.cumsum(w[s]),u,side='right');ii=np.minimum(ii,K-1)
        fields[s]=fields[s,ii];logq[s]=logq[s,ii];wind[s]=wind[s,ii];lw[s]=-np.log(K);counts+=1
    return counts
def run_method(obs,config,seed,method,oracle_wind=None):
    K=config['inference']['particles_per_source'];sources=config['inference']['source_support'];S=len(sources)
    assert set(obs)=={'y','wind_obs','warmup','step','receiver_cells'}
    if method=='WIND_ORACLE':assert oracle_wind is not None
    else:assert oracle_wind is None
    q_rng=np.random.default_rng(seed+20);wrng=np.random.default_rng(seed+21);rrng=np.random.default_rng(seed+22)
    rows=np.array([s['row'] for s in sources]);cols=np.array([s['col'] for s in sources])
    c=np.zeros((S,K,24,24));q=q_rng.normal(0,.08,(S,K));lw=np.full((S,K),-np.log(K));ls=np.full(S,-np.log(S))
    initial=obs['warmup'].mean(axis=0);fixed=initial.copy();wm=initial.copy();wv=np.ones(2)*(.02**2/10)
    # Initial wind samples are common across source hypotheses; no source-conditioned calibration.
    w=np.broadcast_to(initial+wrng.normal(0,np.sqrt(wv),(K,2)),(S,K,2)).copy()
    rho=np.exp(-.2/10);sdq=np.sqrt(1-rho*rho)*.08;Q=.12**2*.2;R=.02**2
    forecasts=[];mixtures=[];posteriors=[];scores=[];gas_logevidence=[];wind_estimates=[];states=[];rngstates=[];ess_events=[]
    total_resamples=0;clipcount=0;maxmassres=0.;cum=np.zeros((S,K));started=time.perf_counter()
    for k in range(500):
        q=rho*q+sdq*q_rng.normal(size=(S,K))
        if method=='B2_JOINT_PF':
            if np.all(np.isfinite(obs['wind_obs'][k])):
                z=obs['wind_obs'][k];windlike=-.5*np.sum((z-w)**2/(Q+R),axis=-1)-np.log(2*np.pi*(Q+R))
                newlw=lw+windlike;inc=logsumexp(newlw,axis=1);ls+=inc;lw=newlw-inc[:,None]
                w=w+(Q/(Q+R))*(z-w)+wrng.normal(0,np.sqrt(Q*R/(Q+R)),w.shape)
            else:w=w+wrng.normal(0,np.sqrt(Q),w.shape)
            clipcount+=int(np.sum(abs(w)>1));w=np.clip(w,-1,1)
            usewind=w;estimate=np.sum(normalized(ls)[:,None,None]*normalized(lw)[:,:,None]*w,axis=(0,1))
        else:
            wv+=Q
            if np.all(np.isfinite(obs['wind_obs'][k])):
                gain=wv/(wv+R);wm=wm+gain*(obs['wind_obs'][k]-wm);wv=(1-gain)*wv
            if method=='B0_FIXED':usewind=fixed
            elif method=='B1_TRANSIENT':usewind=wm
            else:usewind=oracle_wind[k]
            estimate=np.asarray(usewind)
        massbefore=c.sum(axis=(-1,-2))*.25
        c=step(c,usewind);rate=np.exp(q-.5*.08**2);c[np.arange(S)[:,None],np.arange(K)[None,:],rows[:,None],cols[:,None]]+=.2*rate/.25
        maxmassres=max(maxmassres,float(np.max(abs(c.sum(axis=(-1,-2))*.25-massbefore-.2*rate))))
        if c.min()<-1e-12 or not np.isfinite(c).all():raise RuntimeError('Invalid plume state')
        wind_estimates.append(estimate)
        if (k+1)%10==0:
            e=(k+1)//10-1;ry,rx=obs['receiver_cells'][e];mu=c[:,:,ry,rx]
            # Prediction before seeing y_e, all previous wind and gas assimilated.
            preweights=normalized(ls)[:,None]*normalized(lw);forecasts.append(mu.copy());mixtures.append(preweights.copy())
            lg=likelihood(obs['y'][e],mu);cond=logsumexp(lw+lg,axis=1);glob=float(logsumexp(ls+cond)-logsumexp(ls));gas_logevidence.append(glob)
            ls+=cond;lw=lw+lg-cond[:,None]
            posteriors.append(normalized(ls));scores.append(ls.copy());ess_events.append(1/np.sum(normalized(lw)**2,axis=1))
            if e+1 in [20,35,50]:
                states.append(np.sum(normalized(lw)[...,None,None]*c,axis=1));rngstates.append({'prefix':e+1,'q':q_rng.bit_generator.state,'wind':wrng.bit_generator.state,'resampling':rrng.bit_generator.state})
        total_resamples+=resample(c,q,w,lw,rrng)
    result={'forecast_particle_means':np.array(forecasts),'forecast_mixture_weights':np.array(mixtures),'source_posterior':np.array(posteriors),'source_log_score':np.array(scores),'gas_prequential_log_evidence':np.array(gas_logevidence),'wind_estimate':np.array(wind_estimates),'mean_plume_prefix':np.array(states),'conditional_ESS':np.array(ess_events)}
    meta={'method':method,'wall_s':time.perf_counter()-started,'source_count':S,'particles_per_source':K,'resampling_source_events':total_resamples,'wind_boundary_clips':clipcount,'max_one_step_mass_residual_mg':maxmassres,'only_observations_available_through_current_step':True,'oracle':method=='WIND_ORACLE','random_state_prefixes':rngstates,'implementation_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
    return result,meta
def infer_split(split):
    config=json.loads((OUT/'R4_PUBLIC_MODEL_CONFIG.json').read_text(encoding='utf-8'));registry=json.loads((OUT/'R4_PUBLIC_OBSERVATION_REGISTRY.json').read_text(encoding='utf-8'))
    directory=OUT/'raw/inference';directory.mkdir(parents=True,exist_ok=True)
    for rec in registry:
        if rec['split']!=split:continue
        f=OUT/rec['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256'];obs={k:a for k,a in np.load(f).items()}
        for method in config['inference']['methods']:
            target=directory/f"{rec['task_id']}__{method}.npz"
            if target.exists():raise RuntimeError('No overwriting/retry of qualified inference')
            # Explicit oracle-only capability, absent for all deployable calls.
            ow=np.load(OUT/f"raw/evaluation_only/{rec['task_id']}.npz")['wind'] if method=='WIND_ORACLE' else None
            result,meta=run_method(obs,config,rec['inference_seed'],method,ow)
            np.savez_compressed(target,**result);meta['file_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();meta['task_id']=rec['task_id']
            (target.with_suffix('.json')).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'event':'INFERENCE_FROZEN','task':rec['task_id'],'method':method,'wall_s':round(meta['wall_s'],3)},ensure_ascii=False),flush=True)
if __name__=='__main__':
    import sys
    infer_split(sys.argv[1])
