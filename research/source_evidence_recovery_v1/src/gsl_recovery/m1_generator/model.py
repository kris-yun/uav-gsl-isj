"""CPU reference implementation of a source-score supervised joint generator.

A nonlinear, differentiable source basis and an autoregressive gas factor give
an explicitly normalized joint law. The model is intentionally small enough
that every loss, source derivative and mixed derivative can be independently
checked. This is not a diffusion-model rebranding, nor a CFD emulator claim.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from gsl_recovery.types import Action, Observation, Mechanism

VARIANTS = {'Aprime': 'adapted', 'A_prime': 'adapted', 'adapted': 'adapted',
            'B': 'mother', 'mother': 'mother',
            'Bprime': 'secondary', 'B_prime': 'secondary', 'secondary': 'secondary',
            'Bprime_no_boundary': 'constrained_only', 'constrained_only': 'constrained_only',
            'Bprime_no_wind_constraint': 'unconstrained_boundary',
            'unconstrained_boundary': 'unconstrained_boundary'}


@dataclass
class GeneratorConfig:
    wind_mean: tuple = (0.6, 0.1)
    wind_rho: float = 0.65
    wind_sigma: float = 0.45
    weak_weight: float = 0.02
    ridge: float = 1e-4
    max_teacher_records: int = 512
    maxiter: int = 150
    tolerance: float = 1e-7
    wind_calibration: str = 'fit_train_only'


def _is_active(mechanism, index):
    return mechanism is not None and mechanism.kind != 'nominal' and mechanism.active(index)


def _survival(mechanism, index):
    if _is_active(mechanism, index) and mechanism.kind == 'detection_loss':
        if not 0 <= mechanism.magnitude < 1:
            raise ValueError('detection_loss magnitude must be in [0,1)')
        return 1. - mechanism.magnitude
    return 1.


def source_features(source, history, action, wind, mechanism=None):
    """Return phi [F], d_phi/d_source [2,F], known survival probability.

    Candidate source coordinates enter continuously, with no source-ID lookup.
    Dwell and altitude are observed action covariates; the controlled backend is
    calibrated at a fixed dwell and does not claim arbitrary-dwell invariance.
    """
    source = np.asarray(source, float)
    if source.shape != (2,) or not np.all(np.isfinite(source)):
        raise ValueError('source must be finite shape (2,)')
    wind = np.asarray(wind, float)
    if wind.shape != (2,) or not np.all(np.isfinite(wind)):
        raise ValueError('wind must be finite shape (2,)')
    dx, dy = (np.array([action.x, action.y]) - source) / 2.
    wx, wy = wind
    px = np.array([-0.5, 0.]); py = np.array([0., -0.5]); zero = np.zeros(2)
    previous = float(history[-1].gas) if history else 0.
    values, gradients = [], []
    def add(value, derivative=zero):
        values.append(float(value)); gradients.append(np.asarray(derivative, float))
    add(1.); add(dx, px); add(dy, py)
    add(dx*dx, 2*dx*px); add(dy*dy, 2*dy*py); add(dx*dy, dy*px+dx*py)
    add(wx); add(wy); add(dx*wx, px*wx); add(dy*wy, py*wy)
    add(dx*wy, px*wy); add(dy*wx, py*wx); add(wx*wx); add(wy*wy)
    add(previous); add(previous*dx, previous*px); add(previous*dy, previous*py)
    add(action.z-1.); add(np.log(max(action.dwell, 1e-8)))
    offset = mechanism.magnitude if _is_active(mechanism, len(history)) and mechanism.kind == 'sensor_offset' else 0.
    add(offset)
    # Smooth source and relative-location bases resolve nonlinear branch mixtures.
    sx, sy = (source - 1.5) / 2.
    gx, gy = np.array([0.5, 0.]), np.array([0., 0.5])
    add(sx, gx); add(sy, gy); add(sx*sy, sy*gx+sx*gy)
    add(sx*sx, 2*sx*gx); add(sy*sy, 2*sy*gy)
    for value, derivative in ((dx, px), (dy, py), (sx, gx), (sy, gy)):
        t = np.tanh(value); add(t, (1-t*t)*derivative)
    for cx, cy in ((-0.75,-0.75),(-0.75,0.75),(0.75,-0.75),(0.75,0.75),(0.,0.)):
        r = (dx-cx)**2+(dy-cy)**2
        v = np.exp(-r)
        add(v, -2*v*((dx-cx)*px+(dy-cy)*py))
    phi, derivative = np.asarray(values), np.asarray(gradients).T
    return phi, derivative, _survival(mechanism, len(history))


def _score_terms(weights, features, derivatives, y, survival):
    """g=d_s log q and d_w g, including the post-logistic loss channel."""
    z = features @ weights
    f = expit(z)
    q = np.asarray(survival)
    raw_p = q*f
    active_probability = (raw_p > 1e-12) & (raw_p < 1-1e-12)
    p = np.clip(raw_p, 1e-12, 1-1e-12)
    k = (y-p)*(1-f)/(1-p)
    fp = f*(1-f)
    dk0 = -q*fp*(1-2*f+q*f*f)/np.maximum((1-q*f)**2, 1e-24)
    dk = np.where(y > 0.5, -fp, dk0)
    # Match the actual normalized, numerically floored Bernoulli likelihood.
    # At the two nonsmooth clipping knots the derivative is undefined; away
    # from them the saturated derivative is exactly zero.
    k = np.where(active_probability, k, 0.0)
    dk = np.where(active_probability, dk, 0.0)
    ds = np.einsum('nsf,f->ns', derivatives, weights)
    g = k[:, None]*ds
    jac = k[:, None, None]*derivatives + dk[:, None, None]*ds[:, :, None]*features[:, None, :]
    return p, k, g, jac


def objective_and_gradient(weights, batch, weak_batch=None, *, variant='adapted',
                           weak_weight=0.02, ridge=1e-4):
    """Public, gradient-checkable empirical NLL + variational source-score risk."""
    variant = VARIANTS.get(variant, variant)
    if variant not in ('adapted', 'mother', 'secondary', 'constrained_only', 'unconstrained_boundary'):
        raise ValueError(f'unsupported trainable M1 variant {variant}')
    x, d, y, survival = batch['features'], batch['derivatives'], batch['gas'], batch['survival']
    p, k, _, _ = _score_terms(weights, x, d, y, survival)
    nll = float(np.mean(-y*np.log(p)-(1-y)*np.log1p(-p)))
    grad = -np.mean(k[:,None]*x, axis=0)
    total = nll
    if variant != 'adapted':
        if weak_batch is None:
            raise ValueError('M1 mother/secondary training requires qualified teacher records')
        tx, td, ty, ts = [weak_batch[n] for n in ('features','derivatives','gas','survival')]
        _, _, g, jac = _score_terms(weights, tx, td, ty, ts)
        key = 'unconstrained_weight' if variant in ('mother', 'unconstrained_boundary') else 'smooth_weight'
        w = weak_batch[key]
        weak = np.sum(g*g-2*w*g, axis=1)
        gw = 2*np.einsum('nsf,ns->nf', jac, g-w)
        if variant in ('secondary', 'unconstrained_boundary'):
            _, _, gp, jp = _score_terms(weights,tx,td,weak_batch['boundary_plus'],ts)
            _, _, gm, jm = _score_terms(weights,tx,td,weak_batch['boundary_minus'],ts)
            coef = weak_batch['boundary_coefficient']
            weak -= 2*np.sum(coef*(gp-gm),axis=1)
            gw -= 2*np.einsum('ns,nsf->nf',coef,jp-jm)
        total += weak_weight*float(np.mean(weak))
        grad += weak_weight*np.mean(gw,axis=0)
    total += 0.5*ridge*float(weights@weights)
    grad += ridge*weights
    return float(total), grad


def episodes_to_batch(episodes):
    features, derivatives, gas, survival = [], [], [], []
    for ep in episodes:
        if ep.get('split','train') != 'train':
            raise ValueError('fit refuses non-training episodes; supply a separate evaluation path')
        source, observations = ep['source'], ep['observations']
        mechanism = ep.get('mechanism') or Mechanism()
        prefix=[]
        for obs in observations:
            if obs.gas not in (0.,1.):
                raise ValueError('V1 Bernoulli generator requires binary observations; do not silently threshold raw concentration')
            f,d,s=source_features(source,prefix,obs.action,obs.wind,mechanism)
            features.append(f);derivatives.append(d);gas.append(obs.gas);survival.append(s)
            prefix.append(obs)
    if not features:
        raise ValueError('empty training set')
    return {'features':np.asarray(features),'derivatives':np.asarray(derivatives),
            'gas':np.asarray(gas),'survival':np.asarray(survival)}


def teacher_records_to_batch(records):
    rows=[]
    for r in records:
        f,d,s=source_features(r.source,r.history,r.observation.action,r.observation.wind,r.mechanism)
        rows.append((f,d,r.observation.gas,s))
    if not rows:
        raise ValueError('empty teacher set')
    result={k:np.asarray([r[i] for r in rows]) for i,k in enumerate(('features','derivatives','gas','survival'))}
    for key in ('smooth_weight','unconstrained_weight','boundary_coefficient','boundary_plus','boundary_minus'):
        result[key]=np.asarray([getattr(r,key) for r in records])
    return result


class JointObservationGenerator:
    def __init__(self, config=None, weights=None):
        self.config = config or GeneratorConfig()
        f,_,_=source_features([0.,0.],[],Action(x=0.,y=0.),[0.,0.])
        self.weights=np.zeros(len(f)) if weights is None else np.asarray(weights,float).copy()
        if self.weights.shape != f.shape:
            raise ValueError('weight shape mismatch')
        self.fit_receipt=None
        self.variant='untrained'

    @property
    def version(self):
        return hashlib.sha256(self.weights.tobytes()+json.dumps(asdict(self.config),sort_keys=True).encode()).hexdigest()[:16]

    def wind_mean(self,history,mechanism=None):
        mean=np.asarray(self.config.wind_mean,float)
        previous=np.asarray(history[-1].wind,float) if history else mean
        result=mean+self.config.wind_rho*(previous-mean)
        if _is_active(mechanism,len(history)) and mechanism.kind=='wind_bias':
            result=result+np.array([mechanism.magnitude,0.])
        return result

    def next_probability(self,history,action,wind,source,mechanism=None):
        f,_,s=source_features(source,history,action,wind,mechanism)
        return float(np.clip(s*expit(f@self.weights),1e-12,1-1e-12))

    def log_prob(self,history,source,mechanism=None):
        prefix=[];value=0.;sig=self.config.wind_sigma
        for obs in history:
            if obs.gas not in (0.,1.):
                raise ValueError('V1 generator requires binary observations')
            err=(np.asarray(obs.wind)-self.wind_mean(prefix,mechanism))/sig
            value+=-0.5*float(err@err)-2*np.log(sig)-np.log(2*np.pi)
            p=self.next_probability(prefix,obs.action,obs.wind,source,mechanism)
            value+=obs.gas*np.log(p)+(1-obs.gas)*np.log1p(-p)
            prefix.append(obs)
        return float(value)

    def source_score(self,history,source,mechanism=None):
        total=np.zeros(2);prefix=[]
        for obs in history:
            f,d,s=source_features(source,prefix,obs.action,obs.wind,mechanism)
            _,_,g,_=_score_terms(self.weights,f[None,:],d[None,:,:],np.array([obs.gas]),np.array([s]))
            total+=g[0];prefix.append(obs)
        return total

    def sample_future(self,history,actions,source,mechanism=None,rng=None):
        rng=np.random.default_rng() if rng is None else rng
        prefix=list(history);future=[]
        for action in actions:
            wind=self.wind_mean(prefix,mechanism)+self.config.wind_sigma*rng.standard_normal(2)
            p=self.next_probability(prefix,action,wind,source,mechanism)
            obs=Observation(uid=f'pred_{len(prefix)}',action=action,
                            wind=tuple(map(float,wind)),gas=float(rng.random()<p))
            future.append(obs);prefix.append(obs)
        return future

    def gas_word_probability(self,history,actions,wind_sequence,word,source,mechanism=None):
        """Conditional gas-word probability for a *given* synthetic wind path.

        Used only for exact normalization tests/diagnostics. Planning must draw
        wind paths from this model, never supply future realized true wind.
        """
        if not(len(actions)==len(wind_sequence)==len(word)):
            raise ValueError('action/wind/word lengths mismatch')
        prefix=list(history);pword=1.
        for a,w,y in zip(actions,wind_sequence,word):
            p=self.next_probability(prefix,a,w,source,mechanism)
            pword*=p if y else 1-p
            prefix.append(Observation(uid=f'word_{len(prefix)}',action=a,wind=tuple(w),gas=float(y)))
        return float(pword)

    def fit_wind(self, episodes):
        """Calibrate shared AR coefficient, two-axis mean and isotropic noise.

        Uses only qualified TRAIN observations and subtracts predeclared active
        wind-bias mechanisms. A zero-noise dataset is rejected rather than
        assigned an invented Gaussian measurement-noise variance.
        """
        rows, targets, starts = [], [], []
        for ep in episodes:
            if ep.get('split', 'train') != 'train':
                raise ValueError('wind calibration refuses non-training episodes')
            observations = ep['observations']; mechanism = ep.get('mechanism') or Mechanism()
            for i, obs in enumerate(observations):
                bias = np.zeros(2)
                if _is_active(mechanism, i) and mechanism.kind == 'wind_bias':
                    bias[0] = mechanism.magnitude
                target = np.asarray(obs.wind, float) - bias
                if i == 0:
                    starts.append(target)
                    continue
                previous = np.asarray(observations[i-1].wind, float)
                for axis in range(2):
                    row = np.zeros(3); row[axis] = 1.; row[2] = previous[axis]
                    rows.append(row); targets.append(target[axis])
        if len(rows) < 16:
            raise ValueError('WIND_CALIBRATION_BLOCKED: need at least 8 training transitions or an explicitly fixed qualified wind model')
        x, y = np.asarray(rows), np.asarray(targets)
        beta = np.linalg.lstsq(x, y, rcond=None)[0]
        rho = float(np.clip(beta[2], -0.98, 0.98))
        intercept = np.array([np.mean(y[axis::2]-rho*x[axis::2,2]) for axis in range(2)])
        mean = intercept/(1.-rho)
        residual = y - (x[:,:2]@intercept + rho*x[:,2])
        if starts:
            residual = np.concatenate([residual, (np.asarray(starts)-mean).ravel()])
        sigma = float(np.sqrt(np.mean(residual*residual)))
        if not np.isfinite(sigma) or sigma < 1e-6:
            raise ValueError('WIND_CALIBRATION_BLOCKED: degenerate wind residual; supply a separately calibrated observation-noise model')
        self.config.wind_mean = tuple(map(float, mean))
        self.config.wind_rho = rho
        self.config.wind_sigma = sigma
        return {'status':'TRAIN_ONLY_FIT','training_transitions':len(rows)//2,
                'wind_mean':list(self.config.wind_mean),'wind_rho':rho,'wind_sigma':sigma,
                'model_family':'source-blind shared-rho isotropic Gaussian AR; no latent meteorological state'}

    def fit(self,episodes,variant='adapted',teacher_backend=None,seed=0,maxiter=None):
        variant=VARIANTS.get(variant,variant)
        batch=episodes_to_batch(episodes)
        if self.config.wind_calibration == 'fit_train_only':
            wind_receipt = self.fit_wind(episodes)
        elif self.config.wind_calibration == 'fixed_qualified':
            wind_receipt = {'status':'EXPLICIT_FIXED_QUALIFIED','wind_mean':list(self.config.wind_mean),'wind_rho':self.config.wind_rho,'wind_sigma':self.config.wind_sigma}
        else:
            raise ValueError('Unknown wind calibration policy')
        weak=None;receipt={'variant':variant,'n_observations':len(batch['gas']),
                           'n_episodes':len(episodes),'seed':int(seed),'teacher_status':'NOT_REQUIRED',
                           'wind_calibration':wind_receipt,'score_supervision_scope':'one-step conditional source score at fixed prefix; joint score is the sum'}
        if variant!='adapted':
            if teacher_backend is None:
                raise ValueError('BLOCKED: a qualified teacher backend is required for B/Bprime; no NLL fallback')
            rng=np.random.default_rng(seed)
            indices=[(i,j) for i,e in enumerate(episodes) for j in range(len(e['observations']))]
            selected=rng.choice(len(indices),size=min(len(indices),self.config.max_teacher_records),replace=False)
            records=[]
            for selected_index in selected:
                i,j=indices[int(selected_index)];ep=episodes[i]
                records.append(teacher_backend.teacher_record(ep['source'],ep['observations'][:j],
                               ep['observations'][j].action,ep.get('mechanism') or Mechanism(),rng))
            weak=teacher_records_to_batch(records)
            receipt.update(teacher_status='CONTROLLED_REFERENCE',n_teacher_records=len(records),
                           maximum_wind_residual=max(r.wind_residual for r in records),
                           maximum_response_residual=max(r.response_residual for r in records),
                           mean_unconstrained_wind_residual=float(np.mean([r.unconstrained_wind_residual for r in records])),
                           branch_trace_disagreement_rate=float(np.mean([r.boundary_plus!=r.boundary_minus for r in records])))
        options={'maxiter':self.config.maxiter if maxiter is None else int(maxiter),
                 'ftol':self.config.tolerance,'gtol':self.config.tolerance,'maxls':40}
        fun=lambda w:objective_and_gradient(w,batch,weak,variant=variant,
                            weak_weight=self.config.weak_weight,ridge=self.config.ridge)
        initial_value,_=fun(self.weights)
        initial_nll=objective_and_gradient(self.weights,batch,ridge=0)[0]
        result=minimize(fun,self.weights,jac=True,method='L-BFGS-B',options=options)
        if not np.isfinite(result.fun) or not np.all(np.isfinite(result.x)):
            raise RuntimeError('nonfinite generator optimization; checkpoint rejected')
        self.weights=result.x.copy();self.variant=variant
        receipt.update(initial_objective=float(initial_value),final_objective=float(result.fun),
                       initial_nll=float(initial_nll),final_nll=objective_and_gradient(self.weights,batch,ridge=0)[0],
                       optimizer_success=bool(result.success),optimizer_message=str(result.message),
                       iterations=int(result.nit),gradient_norm=float(np.linalg.norm(result.jac)),
                       model_version=self.version)
        self.fit_receipt=receipt
        return receipt

    def save(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        metadata={'schema':'gsl.m1.reference.v1','config':asdict(self.config),
                  'variant':self.variant,'fit_receipt':self.fit_receipt,'version':self.version}
        with path.open('wb') as handle:
            np.savez_compressed(handle,weights=self.weights,metadata=json.dumps(metadata,ensure_ascii=False))
        return path

    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as data:
            metadata=json.loads(str(data['metadata']))
            if metadata['schema']!='gsl.m1.reference.v1':
                raise ValueError('unsupported generator checkpoint schema')
            obj=cls(GeneratorConfig(**metadata['config']),data['weights'])
        obj.variant=metadata['variant'];obj.fit_receipt=metadata.get('fit_receipt')
        if obj.version!=metadata['version']:
            raise ValueError('checkpoint hash mismatch')
        return obj
