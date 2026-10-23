"""Strong same-alphabet baseline: vector quantization of complete raw windows.

This uses no opponent filter, no source-pair-cover objective, and no neural
network. Both methods get the same calibration blocks and a joint law.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import asdict
import json
import numpy as np
from scipy.cluster.vq import kmeans2
from scipy.spatial.distance import cdist
from ..channel import FiniteChannel
from .operator import SamplingContract


class RawJointModel:
    def __init__(self,channel,centers,scales,times,contract):
        self.channel=channel;self.centers=np.asarray(centers);self.scales=np.asarray(scales)
        self.times=np.asarray(times);self.contract=contract

    def encode(self,action,raw,times=None,contract=None):
        times=self.times if times is None else np.asarray(times)
        (contract or self.contract).validate(times,temporal=len(times)>1)
        if times.shape!=self.times.shape or not np.allclose(times-times[0],self.times-self.times[0]):
            raise ValueError("raw joint clock changed")
        raw=np.asarray(raw,dtype=float)
        if raw.shape!=self.times.shape+(2,) or not np.isfinite(raw).all():
            raise ValueError("raw joint model expects one complete finite paired window")
        z=np.log1p(np.maximum(raw,0)).ravel()/self.scales[action]
        return int(np.argmin(np.sum((self.centers[action]-z)**2,axis=1)))

    def save(self,directory):
        p=Path(directory);p.mkdir(parents=True,exist_ok=True);self.channel.save(p/'channel.npz')
        np.savez_compressed(p/'raw_joint_quantizer.npz',centers=self.centers,scales=self.scales,times=self.times)
        (p/'operator.json').write_text(json.dumps({'model_kind':'raw_joint','contract':asdict(self.contract)},indent=2),encoding='utf8')

    @classmethod
    def load(cls,directory):
        p=Path(directory);d=json.loads((p/'operator.json').read_text())
        with np.load(p/'raw_joint_quantizer.npz') as z:
            return cls(FiniteChannel.load(p/'channel.npz'),z['centers'],z['scales'],z['times'],SamplingContract(**d['contract']))


def calibrate_raw_joint(raw,times,contract,source_xy,action_names,source_ids,costs,n_symbols=18,alpha_total=1.):
    x=np.asarray(raw,dtype=float)
    if x.ndim!=6 or x.shape[-1]!=2:raise ValueError("expected [action,source,nuisance,world,time,2]")
    contract.validate(times,temporal=x.shape[-2]>1)
    a,s,r,w,t,_=x.shape
    if n_symbols>s*r*w or n_symbols<2 or alpha_total<=0:raise ValueError("invalid alphabet/calibration count")
    centers=[];scales=[];probs=[]
    for ai in range(a):
        z=np.log1p(np.maximum(x[ai],0)).reshape(-1,t*2)
        scale=max(float(np.std(z)),1e-8);z=z/scale
        code,labels=kmeans2(z,n_symbols,iter=30,minit='++',seed=7722+ai,missing='warn')
        labels=np.argmin(cdist(z,code,'sqeuclidean'),axis=1).reshape(s,r,w)
        p=np.empty((s,r,n_symbols))
        for j in range(s):
            for k in range(r):
                counts=np.bincount(labels[j,k],minlength=n_symbols)+alpha_total/n_symbols
                p[j,k]=counts/counts.sum()
        centers.append(code);scales.append(scale);probs.append(p)
    ch=FiniteChannel(np.array(probs),costs,source_xy,list(action_names),list(source_ids),metadata={
        'variant':'raw_joint','model_kind':'full-window vector quantizer joint likelihood',
        'estimated':True,'n_symbols':n_symbols,'alpha_total':alpha_total,
        'level':'CONTROLLED_OR_QUALIFIED_BLOCKS_ONLY','selection':'unsupervised calibration-only kmeans++',
        'unseen_source_support':'not established by a fitted finite table'})
    return RawJointModel(ch,np.array(centers),np.array(scales),times,contract)


def load_observation_model(directory):
    d=json.loads((Path(directory)/'operator.json').read_text())
    if d.get('model_kind')=='raw_joint':return RawJointModel.load(directory)
    from .calibration import SourceContrastModel
    return SourceContrastModel.load(directory)

