"""Source-pair coverage of opponent channels, and one joint probability table.

B': a finite source-pair-cover algorithm selects *multiple* physically legal
mirrored filters instead of one centerline-turning classifier.  A ternary
odd code and a common-mode bin are calibrated JOINTLY.  There is no product
of correlated cue likelihoods and no test-world response lookup.

Counts use whole calibration blocks.  Independent realizations and native
conditional validity are a data contract, not something this estimator proves.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json
import itertools
import numpy as np
from ..channel import FiniteChannel
from .operator import OpponentBank,SamplingContract


def _js(p,q):
    m=(p+q)/2
    return 0.5*np.sum(np.where(p>0,p*np.log(p/m),0))+0.5*np.sum(np.where(q>0,q*np.log(q/m),0))


def _counts(symbols,n_symbols,alpha,smoothing_mode='fixed_total'):
    # symbols [source,nuisance,world]; never pools source labels.
    s,r,_=symbols.shape
    out=np.empty((s,r,n_symbols))
    for i in range(s):
        for j in range(r):
            cell_alpha=alpha/n_symbols if smoothing_mode=='fixed_total' else alpha
            n=np.bincount(symbols[i,j],minlength=n_symbols).astype(float)+cell_alpha
            out[i,j]=n/n.sum()
    return out


def _pair_distances(p):
    # Robust across source-specific nuisance combinations; unknown sensor
    # mechanisms should not be mistaken for source identity.
    s,r,_=p.shape
    pairs=list(itertools.combinations(range(s),2))
    d=np.zeros(len(pairs))
    for k,(i,j) in enumerate(pairs):
        d[k]=min(_js(p[i,u],p[j,v]) for u in range(r) for v in range(r))
    return pairs,d


class SourceContrastModel:
    def __init__(self,bank,channel,selection,even_thresholds,odd_thresholds,times,contract,receipt):
        self.bank=bank; self.channel=channel
        self.selection=[list(x) for x in selection]
        self.even_thresholds=np.asarray(even_thresholds)
        self.odd_thresholds=np.asarray(odd_thresholds)
        self.times=np.asarray(times)
        self.contract=contract
        self.receipt=receipt

    def encode(self,action,raw,times=None,contract=None):
        t=self.times if times is None else np.asarray(times)
        if t.shape!=self.times.shape or not np.allclose(t-t[0],self.times-self.times[0],rtol=1e-6,atol=1e-9):
            raise ValueError("window duration/sampling clock changed: recalibrate the channel")
        even,odd=self.bank.extract(raw,t,contract or self.contract)
        code=(even>self.even_thresholds[action]).astype(int)
        multiplier=2
        for f in self.selection[action]:
            z=odd[...,f]; theta=self.odd_thresholds[action,f]
            ternary=(z>theta).astype(int)+1-(z< -theta).astype(int)
            code+=multiplier*ternary
            multiplier*=3
        return int(code) if np.ndim(code)==0 else code

    def save(self,path):
        p=Path(path); p.mkdir(parents=True,exist_ok=True)
        self.channel.save(p/'channel.npz')
        (p/'operator.json').write_text(json.dumps({"bank":self.bank.to_dict(),"selection":self.selection,
             "even_thresholds":self.even_thresholds.tolist(),"odd_thresholds":self.odd_thresholds.tolist(),
             "times":self.times.tolist(),"contract":asdict(self.contract),"receipt":self.receipt},ensure_ascii=False,indent=2),encoding='utf8')

    @classmethod
    def load(cls,path):
        p=Path(path); d=json.loads((p/'operator.json').read_text())
        return cls(OpponentBank.from_dict(d['bank']),FiniteChannel.load(p/'channel.npz'),d['selection'],
                   d['even_thresholds'],d['odd_thresholds'],d['times'],SamplingContract(**d['contract']),d['receipt'])


def calibrate_source_contrast(raw,times,contract,source_xy,action_names,source_ids,costs,
                              bank=None,variant="secondary",max_filters=2,alpha=1.0,
                              separation_target=0.04,minimum_gain=1e-5,nuisance_prior=None,
                              calibration_world_ids=None,smoothing_mode='fixed_total'):
    """Fit from [action,source,nuisance,independent_block,time,2].

    variants: even (adapted amplitude-only), mother (one PNAS-like filter),
    secondary (source-pair-cover bank). Native PMFS is an external baseline;
    none of these variants is mislabeled as a reproduction of PMFS.
    """
    x=np.asarray(raw,dtype=float)
    if x.ndim!=6 or x.shape[-1]!=2 or x.shape[3]<2:
        raise ValueError("need [action,source,nuisance,block,time,2], at least two calibration blocks")
    if variant not in ('even','mother','secondary','fixed_two') or not np.isfinite([alpha,separation_target,minimum_gain]).all() or alpha<=0 or separation_target<=0 or minimum_gain<0 or not (0<=max_filters<=3):
        raise ValueError("invalid calibration options; positive smoothing and <=3 filters required")
    if smoothing_mode not in ('fixed_total','legacy_per_cell'):
        raise ValueError("unknown smoothing mode")
    bank=bank or OpponentBank()
    E,H=bank.extract(x,times,contract)
    a,s,r,w=E.shape; f=H.shape[-1]
    max_filters=min(max_filters,f)
    theta_e=np.median(E,axis=(1,2,3))
    # Symmetric thresholds preserve mirror equivariance of the ternary code.
    theta_h=np.maximum(np.quantile(np.abs(H),0.4,axis=(1,2,3)),1e-10)
    selection=[]; receipts=[]; local_tables=[]
    for ai in range(a):
        base=(E[ai]>theta_e[ai]).astype(int)
        def symbols(selected):
            z=base.copy(); mul=2
            for fi in selected:
                h=H[ai,...,fi]; th=theta_h[ai,fi]
                z+=mul*((h>th).astype(int)+1-(h< -th).astype(int));mul*=3
            return z,mul
        def evaluate(selected):
            z,n=symbols(selected); p=_counts(z,n,alpha,smoothing_mode)
            pairs,d=_pair_distances(p)
            objective=float(np.minimum(d,separation_target).sum())
            return objective,p,pairs,d
        chosen=[]; history=[]
        initial,current, pairs,dist=evaluate(chosen)
        if variant=='mother':
            # Fair best-one control on the same TRAIN bank/objective.  The
            # original fitted animal-scale coefficients are not reused.
            chosen=[max(range(f),key=lambda fi:(evaluate([fi])[0],-fi))]
            initial,current,pairs,dist=evaluate(chosen)
        elif variant=='fixed_two':
            chosen=list(dict.fromkeys([0,min(3,f-1)]))[:max_filters]
            initial,current,pairs,dist=evaluate(chosen)
        elif variant=='secondary':
            for k in range(max_filters):
                candidates=[]
                for fi in range(f):
                    if fi not in chosen:
                        obj,p,pr,dd=evaluate(chosen+[fi]);candidates.append((obj,fi,p,pr,dd))
                if not candidates:break
                obj,fi,p,pr,dd=max(candidates,key=lambda v:(v[0],-v[1]))
                gain=obj-initial
                history.append({"filter":bank.specs[fi].name,"training_objective":obj,"gain":gain})
                if gain<=minimum_gain:break
                chosen.append(fi);initial,current,pairs,dist=obj,p,pr,dd
                if np.all(dist>=separation_target):break
        selection.append(chosen);local_tables.append(current)
        receipts.append({"action":action_names[ai],"selected":[bank.specs[j].name for j in chosen],
                         "source_pairs":pairs,"robust_training_js":dist.tolist(),"search":history,
                         "unseparated_pairs":[pairs[j] for j in np.flatnonzero(dist<separation_target)],
                         "certificate":"TRAINING_DIAGNOSTIC_ONLY_NOT_A_POPULATION_GUARANTEE"})
    n_out=max(p.shape[-1] for p in local_tables)
    # Pad the common alphabet with exact zero unreachable symbols. Existing
    # table cells already have stated Dirichlet smoothing.
    prob=np.zeros((a,s,r,n_out))
    for ai,p in enumerate(local_tables):prob[ai,:,:,:p.shape[-1]]=p
    meta={"level":"L1_OR_QUALIFIED_BLOCK_REPLAY_ONLY","variant":variant,
          "observation":"one joint symbol per physical paired window","estimated":True,
          "risk_guarantee":"conditional on calibrated family covering the true process",
          "world_ids":list(calibration_world_ids or []),"alpha":alpha,"smoothing_mode":smoothing_mode,
          "calibration_version":"v7.1_projectively_consistent",
          "time_semantics":contract.provenance,"max_filters":max_filters,
          "unseen_source_support":"not established by a fitted finite table"}
    ch=FiniteChannel(prob,np.asarray(costs),np.asarray(source_xy),list(action_names),list(source_ids),nuisance_prior,meta)
    receipt={"operator":"source-pair-cover mirrored bank","variant":variant,"actions":receipts,
             "smoothing_mode":smoothing_mode,"alpha_total":alpha if smoothing_mode=='fixed_total' else None,
             "training_blocks_per_source_mechanism":w,"counts_are_not_independent_frames_by_default":True,
             "static_mode":not contract.continuous,
             "strictly_temporal_claim":bool(contract.continuous and any(bank.specs[f].kind!='gradient' for selected in selection for f in selected)),
             "known_statistics":"JS distance, histogram likelihood and Bayes normalization are not claimed new"}
    return SourceContrastModel(bank,ch,selection,theta_e,theta_h,times,contract,receipt)


def joint_error_kernel(n_bits,mask_probabilities):
    """Correlated binary error masks; no independent-bit assumption.

    An outcome is an entire word.  A burst-flip mask can carry arbitrary mass.
    Intended for binary-coded channel experiments, not arbitrary ternary codes.
    """
    n=2**int(n_bits); weights=np.asarray(mask_probabilities,dtype=float)
    if weights.shape!=(n,) or np.any(weights<0) or not np.isclose(weights.sum(),1):
        raise ValueError("one probability for every complete error mask required")
    return np.array([[weights[i^j] for j in range(n)] for i in range(n)])


def apply_joint_error_channel(channel,kernel):
    k=np.asarray(kernel,dtype=float)
    o=channel.shape[-1]
    if k.shape!=(o,o) or np.any(k<0) or not np.allclose(k.sum(1),1):
        raise ValueError("error kernel must be a row-stochastic joint-symbol matrix")
    p=np.einsum('asro,ov->asrv',channel.probabilities,k)
    return FiniteChannel(p,channel.costs.copy(),channel.source_xy.copy(),channel.action_names.copy(),
                         channel.source_ids.copy(),channel.nuisance_prior.copy(),
                         {**channel.metadata,"joint_error_model":True})

