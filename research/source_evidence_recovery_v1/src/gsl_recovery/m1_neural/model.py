"""Causal, normalized mixture of recurrent observation models.

The latent mode is persistent through an entire history/rollout.  Conditioning
uses each candidate source's own mode responsibilities. Missing current emission factors are integrated out under an explicit mask
protocol; this is not an exact hidden-trajectory marginal for missing history.
Unavailable values are never filled with oracle measurements. No source/map ID exists.
The continuous option is a censored lognormal with a point mass at zero.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import torch
from torch import nn
from ..types import Action, Observation, Mechanism


@dataclass
class NeuralConfig:
    hidden: int = 48
    geometry_width: int = 16
    query_width: int = 32
    modes: int = 4
    gas_model: str = 'binary'
    gas_lod: float = 1e-6
    length_scale: float = 1.0
    wind_scale: float = 1.0
    time_scale: float = 1.0
    source_height: float = 0.0
    min_wind_sigma: float = 0.02
    min_log_gas_sigma: float = 0.05
    time_semantics: str = 'seconds'
    scope: str = 'ENGINEERING_ONLY'

    def __post_init__(self):
        if self.gas_model not in ('binary','censored_lognormal'):
            raise ValueError('Unknown normalized gas readout')
        if min(self.hidden,self.geometry_width,self.query_width,self.modes) < 1:
            raise ValueError('Positive network dimensions required')
        if min(self.length_scale,self.wind_scale,self.time_scale,self.gas_lod,
               self.min_wind_sigma,self.min_log_gas_sigma) <= 0:
            raise ValueError('Physical scales and noise floors must be positive and declared')
        if self.time_semantics not in ('seconds','record_index'):
            raise ValueError('Time semantics must be explicit')


@dataclass
class Geometry:
    # Legal static boundary/terrain landmarks [N,3], optional occupancy [N].
    landmarks: list
    occupancy: list
    geometry_id: str = 'unqualified'

    @classmethod
    def empty(cls):
        return cls([], [], 'empty_geometry_engineering')

    def __post_init__(self):
        x=np.asarray(self.landmarks,float).reshape(-1,3)
        occ=np.asarray(self.occupancy,float)
        if occ.shape != (len(x),) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(occ)):
            raise ValueError('Invalid geometry; landmarks [N,3], occupancy [N] required')
        self.landmarks=x.tolist(); self.occupancy=occ.tolist()


class NeuralJointGenerator(nn.Module):
    format_version = 'gsl_neural_joint_v2'

    def __init__(self, config=None, geometry=None, *, extra_width=0):
        super().__init__()
        self.config=config or NeuralConfig()
        self.geometry=geometry or Geometry.empty()
        c=self.config; self.extra_width=int(extra_width)
        self.register_buffer('landmarks',torch.tensor(self.geometry.landmarks,dtype=torch.float32).reshape(-1,3))
        self.register_buffer('occupancy',torch.tensor(self.geometry.occupancy,dtype=torch.float32))
        self.geom_encoder=nn.Sequential(nn.Linear(7,c.geometry_width),nn.SiLU(),nn.Linear(c.geometry_width,c.geometry_width))
        self.query_encoder=nn.Sequential(nn.Linear(c.geometry_width+5+self.extra_width,c.query_width),nn.SiLU(),nn.Linear(c.query_width,c.query_width),nn.Tanh())
        self.mode_embeddings=nn.Parameter(torch.randn(c.modes,c.hidden)*0.05)
        self.initial_encoder=nn.Linear(c.geometry_width,c.hidden)
        self.prior_head=nn.Linear(c.geometry_width,c.modes)
        self.emission=nn.Sequential(nn.Linear(c.hidden+c.query_width,c.hidden),nn.SiLU(),nn.Linear(c.hidden,7))
        # Observed normalized wind, gas, channel masks, and query context.
        self.update_cell=nn.GRUCell(c.query_width+6,c.hidden)
        self.training_receipt={}

    @property
    def device(self): return self.mode_embeddings.device
    @property
    def dtype(self): return self.mode_embeddings.dtype

    def tensor(self,value): return torch.as_tensor(value,device=self.device,dtype=self.dtype)

    def _source(self,source):
        source=source.to(device=self.device,dtype=self.dtype) if torch.is_tensor(source) else self.tensor(source)
        if source.shape != (2,) or not torch.isfinite(source).all():
            raise ValueError('A continuous candidate source [x,y] is required')
        return source

    def _geom(self,source,action):
        if len(self.landmarks)==0:
            return source.sum()*0+self.tensor(np.zeros(self.config.geometry_width))
        s3=torch.cat((source,self.tensor([self.config.source_height])))
        q=self.tensor([action.x,action.y,action.z])
        features=torch.cat(((self.landmarks-s3)/self.config.length_scale,
                            (self.landmarks-q)/self.config.length_scale,
                            self.occupancy[:,None]),dim=-1)
        return self.geom_encoder(features).mean(0)

    def _extra(self,source,action):
        return torch.zeros((self.config.modes,self.extra_width),device=self.device,dtype=self.dtype)

    def _query(self,source,action,previous_time):
        if not np.isfinite([action.x,action.y,action.z,action.time,action.dwell]).all() or action.dwell<=0:
            raise ValueError('Invalid action')
        rel=torch.cat((self.tensor([action.x,action.y])-source,self.tensor([action.z-self.config.source_height])))/self.config.length_scale
        dt=0. if previous_time is None else (action.time-previous_time)/self.config.time_scale
        if dt<0: raise ValueError('Action times must be nondecreasing')
        basic=torch.cat((self._geom(source,action),rel,self.tensor([math.log(action.dwell/self.config.time_scale),dt])))
        k=self.config.modes
        return self.query_encoder(torch.cat((basic.expand(k,-1),self._extra(source,action)),dim=-1))

    def initial_state(self,source):
        source=self._source(source)
        # Source-relative geometry: no global source or geometry ID embedding.
        action=Action(float(source[0].detach()),float(source[1].detach()),self.config.source_height)
        # Initial geometry must remain differentiable in source on both sides.
        if len(self.landmarks):
            s3=torch.cat((source,self.tensor([self.config.source_height])))
            rel=(self.landmarks-s3)/self.config.length_scale
            features=torch.cat((rel,rel,self.occupancy[:,None]),-1)
            g=self.geom_encoder(features).mean(0)
        else: g=source.sum()*0+self.tensor(np.zeros(self.config.geometry_width))
        h=torch.tanh(self.mode_embeddings+self.initial_encoder(g)[None,:])
        logprior=torch.log_softmax(self.prior_head(g),dim=0)
        return h,logprior

    def _emission_parameters(self,h,q,mechanism,index,action,mode_indices=None):
        raw=self.emission(torch.cat((h,q),dim=-1))
        mean=raw[...,:2]*self.config.wind_scale
        sigma=(torch.nn.functional.softplus(raw[...,2:4])+self.config.min_wind_sigma)*self.config.wind_scale
        gas_logit=raw[...,4]
        gas_mu=raw[...,5]
        gas_sigma=torch.nn.functional.softplus(raw[...,6])+self.config.min_log_gas_sigma
        survival=1.
        m=mechanism or Mechanism()
        if m.kind not in ('nominal','wind_bias','sensor_offset','detection_loss'):
            raise ValueError('Unknown mechanism; stop instead of fitting the source to an unsupported fault')
        if m.active(index):
            if m.kind=='wind_bias': mean=mean+self.tensor([m.magnitude,0.])
            elif m.kind=='sensor_offset': gas_logit=gas_logit+m.magnitude; gas_mu=gas_mu+m.magnitude
            elif m.kind=='detection_loss':
                if not 0<=m.magnitude<1: raise ValueError('Detection loss must be in [0,1)')
                survival=1-m.magnitude
        probability=torch.sigmoid(gas_logit)*survival
        eps=torch.finfo(probability.dtype).eps
        probability=probability.clamp(eps,1-eps)
        return mean,sigma,probability,gas_mu,gas_sigma,survival

    def _log_emission(self,params,obs):
        mean,sigma,p,mu,sg,survival=params
        mask=self.tensor(obs.wind_available)
        wind=self.tensor(obs.wind)
        if wind.shape!=(2,) or mask.shape!=(2,): raise ValueError('Two local wind channels required')
        if not torch.isfinite(wind[mask.bool()]).all(): raise ValueError('Nonfinite observed wind')
        wind=torch.where(mask.bool(),wind,torch.zeros_like(wind))
        lp=((-0.5*((wind-mean)/sigma)**2-torch.log(sigma)-0.5*math.log(2*math.pi))*mask).sum(-1)
        if obs.gas_available:
            y=float(obs.gas)
            if not math.isfinite(y): raise ValueError('Nonfinite observed gas')
            if self.config.gas_model=='binary':
                if y not in (0.,1.): raise ValueError('Binary model requires explicit qualified thresholding')
                # Numerically stable but exactly normalized Bernoulli law.
                p=p.clamp(torch.finfo(p.dtype).eps,1-torch.finfo(p.dtype).eps)
                lp=lp+(torch.log(p) if y else torch.log1p(-p))
            else:
                if y<0 or (0<y<=self.config.gas_lod):
                    raise ValueError('Censored lognormal input must be zero or strictly above declared LOD')
                z=(math.log(self.config.gas_lod)-mu)/sg
                cdf=torch.special.ndtr(z)
                if y==0:
                    lp=lp+torch.log((1-survival+survival*cdf).clamp_min(torch.finfo(lp.dtype).tiny))
                else:
                    lp=lp-0.5*((math.log(y)-mu)/sg)**2-torch.log(sg)-math.log(y)-0.5*math.log(2*math.pi)+math.log(survival)
        return lp

    def _update(self,h,q,obs):
        w=np.asarray(obs.wind,float); wm=np.asarray(obs.wind_available,bool)
        w=np.where(wm,w,0.)/self.config.wind_scale
        y=(float(obs.gas) if self.config.gas_model=='binary' else math.log1p(max(float(obs.gas),0.))) if obs.gas_available else 0.
        measured=self.tensor([*w,y,*wm,float(obs.gas_available)])
        return self.update_cell(torch.cat((q,measured.expand(q.shape[0],-1)),dim=-1),h)

    def filter_torch(self,history,source,mechanism=None):
        source=self._source(source);h,prior=self.initial_state(source)
        atom=torch.zeros_like(prior);last=None
        for index,obs in enumerate(history):
            q=self._query(source,obs.action,last)
            atom=atom+self._log_emission(self._emission_parameters(h,q,mechanism,index,obs.action),obs)
            h=self._update(h,q,obs);last=obs.action.time
        logw=prior+atom
        return h,torch.log_softmax(logw,dim=0),torch.logsumexp(logw,dim=0),atom

    def log_prob_torch(self,history,source,mechanism=None):
        return self.filter_torch(history,source,mechanism)[2]

    def log_prob(self,history,source,mechanism=None):
        with torch.no_grad(): return float(self.log_prob_torch(history,source,mechanism).cpu())

    def conditional_log_prob_torch(self,history,future,source,mechanism=None):
        return self.log_prob_torch(list(history)+list(future),source,mechanism)-self.log_prob_torch(history,source,mechanism)

    def source_score(self,history,source,mechanism=None):
        s=self.tensor(source).requires_grad_(True)
        logp=self.log_prob_torch(history,s,mechanism)
        return torch.autograd.grad(logp,s)[0].detach().cpu().numpy()

    def sample_future_batch(self,history,actions,source,mechanism=None,draws=1,rng=None,return_mode_indices=False):
        if draws<1: raise ValueError('Positive rollout count required')
        rng=np.random.default_rng() if rng is None else rng
        with torch.no_grad():
            s=self._source(source);h,logw,_,_=self.filter_torch(history,s,mechanism)
            indices=rng.choice(self.config.modes,size=int(draws),p=(lambda w: w/w.sum())(torch.softmax(logw,0).cpu().numpy().astype(float)))
            idx=torch.tensor(indices,device=self.device,dtype=torch.long)
            state=h[idx];last=history[-1].action.time if history else None
            out=[[] for _ in range(draws)]
            for step,a in enumerate(actions):
                q_all=self._query(s,a,last);q=q_all[idx]
                params=self._emission_parameters(state,q,mechanism,len(history)+step,a,idx)
                mean,sd,p,mu,sg,survival=[v.cpu().numpy() if torch.is_tensor(v) else v for v in params]
                wind=mean+sd*rng.standard_normal((draws,2))
                if self.config.gas_model=='binary': gas=(rng.random(draws)<p).astype(float)
                else:
                    logy=mu+sg*rng.standard_normal(draws)
                    if np.any(logy>700): raise RuntimeError('Nonfinite concentration proposal; model unqualified')
                    gas=np.exp(logy);gas[(gas<=self.config.gas_lod)|(rng.random(draws)>survival)]=0.
                measured=[]
                for j in range(draws):
                    obs=Observation(f'v2_pred_{len(history)+step}',a,tuple(map(float,wind[j])),float(gas[j]))
                    out[j].append(obs)
                    yy=obs.gas if self.config.gas_model=='binary' else math.log1p(obs.gas)
                    measured.append([*(wind[j]/self.config.wind_scale),yy,1.,1.,1.])
                state=self.update_cell(torch.cat((q,self.tensor(measured)),dim=-1),state);last=a.time
        return (out,indices) if return_mode_indices else out

    def sample_future(self,history,actions,source,mechanism=None,rng=None):
        return self.sample_future_batch(history,actions,source,mechanism,1,rng)[0]

    def sample_future_with_mode(self,history,actions,source,mechanism=None,rng=None):
        values,indices=self.sample_future_batch(history,actions,source,mechanism,1,rng,True)
        return values[0],int(indices[0])

    @property
    def version(self):
        h=hashlib.sha256(json.dumps({'config':asdict(self.config),'geometry':asdict(self.geometry)},sort_keys=True).encode())
        for name,value in sorted(self.state_dict().items()):
            h.update(name.encode());h.update(value.detach().cpu().contiguous().numpy().tobytes())
        return h.hexdigest()[:20]

    def save(self,path):
        path=Path(path);path.mkdir(parents=True,exist_ok=True)
        torch.save(self.state_dict(),path/'weights.pt')
        meta={'format':self.format_version,'config':asdict(self.config),'geometry':asdict(self.geometry),
              'version':self.version,'parameters':sum(p.numel() for p in self.parameters()),
              'receipt':self.training_receipt,'weights_sha256':hashlib.sha256((path/'weights.pt').read_bytes()).hexdigest(),
              'deployable_inputs':'legal history, candidate coordinates, static geometry, mechanism'}
        (path/'model.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')

    @classmethod
    def load(cls,path,device='cpu'):
        path=Path(path);meta=json.loads((path/'model.json').read_text())
        if meta.get('format')!=cls.format_version: raise ValueError('Wrong neural checkpoint format')
        if hashlib.sha256((path/'weights.pt').read_bytes()).hexdigest()!=meta['weights_sha256']:
            raise ValueError('Checkpoint checksum mismatch')
        model=cls(NeuralConfig(**meta['config']),Geometry(**meta['geometry'])).to(device)
        model.load_state_dict(torch.load(path/'weights.pt',map_location=device,weights_only=True))
        model.training_receipt=meta.get('receipt',{});model.eval()
        if model.version!=meta['version']: raise ValueError('Model/config/geometry identity mismatch')
        return model
