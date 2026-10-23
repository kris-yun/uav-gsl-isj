"""A finite, *joint* observation law, separate from the environment.

Axes are action, source, shared nuisance, joint symbol.  Nuisance is fixed
through an episode unless a new model version explicitly declares a reset.
The class samples a *predictive* channel for planning.  Evaluation backends
must use independent worlds; sampling this class is a Level 1 experiment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import numpy as np
from scipy.special import logsumexp


@dataclass
class FiniteChannel:
    probabilities: np.ndarray
    costs: np.ndarray
    source_xy: np.ndarray
    action_names: list[str]
    source_ids: list[str]
    nuisance_prior: np.ndarray | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.probabilities = np.asarray(self.probabilities, dtype=float)
        if self.probabilities.ndim != 4:
            raise ValueError("probabilities must have axes [action,source,nuisance,outcome]")
        a,s,r,o = self.probabilities.shape
        self.costs = np.asarray(self.costs,dtype=float)
        self.source_xy = np.asarray(self.source_xy,dtype=float)
        if self.costs.shape != (a,) or np.any(~np.isfinite(self.costs)) or np.any(self.costs<=0):
            raise ValueError("every action needs a positive finite full cost")
        if self.source_xy.shape != (s,2) or not np.isfinite(self.source_xy).all():
            raise ValueError("source_xy must be finite [source,2]")
        if len(self.action_names)!=a or len(self.source_ids)!=s:
            raise ValueError("label lengths do not match channel")
        if len(set(self.action_names))!=a or len(set(self.source_ids))!=s:
            raise ValueError("action and source identifiers must be unique")
        if o<2 or s<2 or r<1:
            raise ValueError("at least two sources and outcomes, one nuisance, required")
        p=self.probabilities
        if not np.isfinite(p).all() or np.any(p<0) or not np.allclose(p.sum(-1),1,atol=1e-9):
            raise ValueError("each conditional distribution must sum to one")
        if self.nuisance_prior is None:
            self.nuisance_prior=np.full((s,r),1/r)
        else:
            self.nuisance_prior=np.asarray(self.nuisance_prior,dtype=float)
            if self.nuisance_prior.shape==(r,):
                self.nuisance_prior=np.tile(self.nuisance_prior,(s,1))
            if self.nuisance_prior.shape!=(s,r) or np.any(self.nuisance_prior<=0):
                raise ValueError("nuisance prior must be positive [source,nuisance] or [nuisance]")
            if not np.allclose(self.nuisance_prior.sum(-1),1):
                raise ValueError("nuisance prior must sum to one for each source")

    @property
    def shape(self):
        return self.probabilities.shape

    def marginal(self, nuisance_weights=None):
        w=self.nuisance_prior if nuisance_weights is None else np.asarray(nuisance_weights,dtype=float)
        if w.shape != self.shape[1:3] or np.any(w<0) or not np.allclose(w.sum(-1),1):
            raise ValueError("conditional nuisance weights required")
        return np.einsum('asro,sr->aso',self.probabilities,w)

    def sample(self, action:int, source:int, nuisance:int, rng:np.random.Generator):
        return int(rng.choice(self.shape[-1],p=self.probabilities[action,source,nuisance]))

    def sample_joint(self,actions,source,rng,n_samples=1,nuisance_weights=None):
        """Joint *model* samples: one shared nuisance per future rollout.

        Conditional block independence is an explicit model assumption. This
        does not synthesize continuous CFD or query a held-out realization.
        """
        actions=np.asarray(actions,dtype=int)
        if actions.ndim!=1 or not len(actions) or np.any(actions<0) or np.any(actions>=self.shape[0]):
            raise ValueError("provide legal planned action indices")
        if not 0<=source<self.shape[1] or n_samples<1:raise ValueError("invalid source/sample count")
        w=self.nuisance_prior[source] if nuisance_weights is None else np.asarray(nuisance_weights,dtype=float)
        if w.shape!=(self.shape[2],) or np.any(w<0) or not np.isclose(w.sum(),1):
            raise ValueError("one normalized nuisance distribution required")
        states=rng.choice(self.shape[2],size=n_samples,p=w)
        samples=np.empty((n_samples,len(actions)),dtype=int)
        for row,state in enumerate(states):
            for col,a in enumerate(actions):samples[row,col]=self.sample(int(a),source,int(state),rng)
        return samples,states

    def save(self,path):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        meta={"action_names":self.action_names,"source_ids":self.source_ids,"metadata":self.metadata}
        np.savez_compressed(path,probabilities=self.probabilities,costs=self.costs,source_xy=self.source_xy,
                            nuisance_prior=self.nuisance_prior,metadata_json=np.array(json.dumps(meta,ensure_ascii=False)))

    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as z:
            meta=json.loads(str(z['metadata_json']))
            return cls(z['probabilities'],z['costs'],z['source_xy'],meta['action_names'],meta['source_ids'],
                       z['nuisance_prior'],meta['metadata'])


class JointPosterior:
    """All sources remain represented; a block is entered once by event id."""
    def __init__(self,channel:FiniteChannel,source_prior=None):
        self.channel=channel
        s,r=channel.shape[1:3]
        pi=np.ones(s)/s if source_prior is None else np.asarray(source_prior,dtype=float)
        if pi.shape!=(s,) or np.any(pi<=0) or not np.isclose(pi.sum(),1):
            raise ValueError("a strictly positive source prior is required")
        self.initial_log_weights=np.log(pi[:,None])+np.log(channel.nuisance_prior)
        self.log_weights=self.initial_log_weights.copy()
        self.events=[]
        self._event_ids=set()

    @property
    def joint(self):
        return np.exp(self.log_weights-logsumexp(self.log_weights))

    @property
    def source(self):
        return self.joint.sum(1)

    @property
    def conditional_nuisance(self):
        norm=logsumexp(self.log_weights,axis=1,keepdims=True)
        finite=np.isfinite(norm[:,0])
        out=self.channel.nuisance_prior.copy()
        out[finite]=np.exp(self.log_weights[finite]-norm[finite])
        # A structurally impossible source has no conditional posterior. Use
        # its installed predictive prior only for counterfactual proposals;
        # do not add mass to its zero source posterior or claim recovery.
        return out

    def predict(self):
        return self.channel.marginal(self.conditional_nuisance)

    def update(self,action:int,outcome:int,event_id:str):
        if event_id in self._event_ids:
            raise ValueError("a raw observation block cannot be counted twice")
        if not (0<=action<self.channel.shape[0] and 0<=outcome<self.channel.shape[-1]):
            raise ValueError("action/outcome index is out of range")
        p=self.channel.probabilities[action,:,:,outcome]
        with np.errstate(divide='ignore'):
            candidate=self.log_weights+np.log(p)
        if not np.isfinite(logsumexp(candidate)):
            raise ValueError("all modeled source/mechanism states rejected; model support failure")
        self.log_weights=candidate-logsumexp(candidate)
        self._event_ids.add(event_id)
        self.events.append({"event_id":event_id,"action":int(action),"outcome":int(outcome)})
        return self.source.copy()

    def map_points(self):
        return {sid:{"x":float(xy[0]),"y":float(xy[1]),"probability":float(p)}
                for sid,xy,p in zip(self.channel.source_ids,self.channel.source_xy,self.source)}

