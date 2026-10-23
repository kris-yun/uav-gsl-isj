"""Explicit mother-algorithm reference for finite known iid action laws.

Action-dependent response clustering, maximin inter-cluster separation,
representative sequential likelihood ratios, then surviving-cluster recursion.
Only this controlled reference uses the iid assumptions of the ISIT model.
The gas planner's B score transfers its clustering/selection operator and
does not inherit the original sequential-testing theorem.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import rel_entr


@dataclass
class ASHTStage:
    action_index: int
    clusters: list
    representatives: list
    log_scores: np.ndarray
    threshold: float
    samples: int = 0


class ClusteredASHTReference:
    def __init__(self, action_laws, alpha=0.05, cluster_tolerance=1e-8):
        """action_laws shape [action,source,discrete observation]."""
        self.laws=np.asarray(action_laws,float)
        if self.laws.ndim!=3 or np.any(self.laws<0) or not np.allclose(self.laws.sum(-1),1):
            raise ValueError("Known action laws must be normalized")
        if not 0<alpha<1:
            raise ValueError("alpha must be in (0,1)")
        self.alpha=float(alpha);self.tolerance=float(cluster_tolerance)
        self.active=list(range(self.laws.shape[1]));self.stage=None;self.stages=[]

    def start_stage(self):
        if len(self.active)<=1:
            return None
        choices=[]
        for a,p in enumerate(self.laws):
            clusters=[]
            for s in self.active:
                match=next((k for k,c in enumerate(clusters)
                            if .5*np.abs(p[s]-p[c[0]]).sum()<=self.tolerance),None)
                if match is None:clusters.append([s])
                else:clusters[match].append(s)
            if len(clusters)<2:
                choices.append((0,a,clusters));continue
            separation=[]
            for k,c in enumerate(clusters):
                for other in clusters[k+1:]:
                    x=np.maximum(p[c[0]],1e-12);x/=x.sum()
                    y=np.maximum(p[other[0]],1e-12);y/=y.sum()
                    separation.append(min(np.sum(rel_entr(x,y)),np.sum(rel_entr(y,x))))
            choices.append((float(min(separation)),a,clusters))
        score,action,clusters=max(choices,key=lambda x:x[0])
        if score<=0:
            raise ValueError("No action separates the surviving hypotheses")
        stage_number=len(self.stages)+1
        stage_alpha=self.alpha/(stage_number*(stage_number+1))
        threshold=np.log((len(clusters)-1)/stage_alpha)
        self.stage=ASHTStage(action,clusters,[c[0] for c in clusters],np.zeros(len(clusters)),threshold)
        self.stages.append(self.stage)
        return self.stage

    def observe(self,symbol):
        if self.stage is None:
            raise ValueError("Call start_stage before observing")
        stage=self.stage;symbol=int(symbol)
        if not 0<=symbol<self.laws.shape[-1]:
            raise ValueError("Observation outside declared alphabet")
        p=self.laws[stage.action_index,stage.representatives,symbol]
        stage.log_scores+=np.log(np.maximum(p,1e-300));stage.samples+=1
        winner=int(np.argmax(stage.log_scores))
        others=np.delete(stage.log_scores,winner)
        accepted=bool(np.all(stage.log_scores[winner]-others>=stage.threshold))
        if accepted:
            self.active=list(stage.clusters[winner]);self.stage=None
        return {"stage_complete":accepted,"active_sources":list(self.active),
                "stage_samples":stage.samples,"identified":len(self.active)==1}
