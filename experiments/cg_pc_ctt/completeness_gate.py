#!/usr/bin/env python3
"""CG-PC-CTT V2 completeness / identifiability gate.

V1 was INVALID_PROTOCOL because whitening full-sample candidate means by
transport-member residual covariance leaves an O(1/sqrt(M)) finite-member mean
noise term. With M=8 that noise can create rank-3 and alpha>1 under a true null.

V2 removes that positive self-correlation by using four disjoint member folds.
Noise covariance is estimated only from WITHIN-FOLD residuals, which is
invariant to independent candidate-label permutations across folds. Each fold
selects its own source-contrast basis and is cross-evaluated only against the
other three folds. The signed third cross-moment eigenvalue is therefore not
forced positive under a null.

Primary statistics (rank_k=3):
  alpha_cf = lambda_3 of replicated cross-fold source contrast (signed)
  gamma_cf = max(lambda_3,0) / max(lambda_1,eps)
  p_perm   = permutation p-value for lambda_3 under broken cross-fold
             candidate alignment

PASS requires alpha_cf>0, gamma_cf>=gamma_min, and p_perm<=p_max.
There is NO development-tuned alpha threshold in V2.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np

@dataclass(frozen=True)
class GateConfig:
    gamma_min: float = 0.05
    p_max: float = 0.01
    rank_k: int = 3
    n_folds: int = 4
    n_permutations: int = 999
    permutation_seed: int = 20260827
    ridge_rel: float = 1e-3
    eig_floor: float = 1e-9
    member_semantics: str = "exchangeable_realizations"

    def validate(self):
        if self.gamma_min < 0: raise ValueError("gamma_min must be >=0")
        if not (0 < self.p_max < 1): raise ValueError("p_max must be in (0,1)")
        if self.rank_k < 1: raise ValueError("rank_k must be >=1")
        if self.n_folds < 2: raise ValueError("n_folds must be >=2")
        if self.n_permutations < int(np.ceil(1.0/self.p_max))-1:
            raise ValueError("n_permutations too small to resolve p_max")
        if self.ridge_rel < 0 or self.eig_floor <= 0: raise ValueError("invalid regularization")
        if self.member_semantics not in {"exchangeable_realizations","fixed_nuisance_design"}:
            raise ValueError("member_semantics must be exchangeable_realizations or fixed_nuisance_design")

@dataclass(frozen=True)
class GateResult:
    alpha_cf: float
    gamma_cf: float
    lambda_1: float
    lambda_k: float
    p_perm: float
    target_rank: int
    n_folds: int
    fold_size: int
    accepted: bool
    inferential_valid: bool
    reason: str
    ridge: float
    member_semantics: str
    def to_dict(self): return asdict(self)

def _as_finite_3d(phi):
    x=np.asarray(phi,dtype=np.float64)
    if x.ndim!=3: raise ValueError(f"phi must be [S,M,D], got {x.shape}")
    S,M,D=x.shape
    if S<2 or M<4 or D<1: raise ValueError(f"need S>=2,M>=4,D>=1, got {x.shape}")
    if not np.all(np.isfinite(x)): raise ValueError("phi contains NaN/Inf")
    return x

def _folds(M,n_folds):
    if M % n_folds != 0:
        raise ValueError(f"M={M} must be divisible by n_folds={n_folds}; V2 requires disjoint equal folds")
    return [np.asarray(a,dtype=int) for a in np.array_split(np.arange(M),n_folds)]

def _fold_invariant_whitener(x,folds,cfg):
    """Estimate nuisance covariance without cross-fold candidate mean coupling."""
    S,_,D=x.shape
    Csum=np.zeros((D,D),dtype=np.float64); df=0
    for f in folds:
        muf=x[:,f,:].mean(axis=1)
        R=(x[:,f,:]-muf[:,None,:]).reshape(-1,D)
        Csum += R.T@R
        df += S*max(len(f)-1,1)
    C=Csum/max(df,1)
    scale=float(np.trace(C)/max(D,1))
    ridge=max(cfg.eig_floor,cfg.ridge_rel*max(scale,cfg.eig_floor))
    evals,evecs=np.linalg.eigh(C+ridge*np.eye(D))
    evals=np.maximum(evals,cfg.eig_floor)
    W=(evecs*(1.0/np.sqrt(evals)))@evecs.T
    return W,ridge

def compute_gate(phi,cfg=GateConfig()):
    cfg.validate(); x=_as_finite_3d(phi); S,M,D=x.shape
    fs=_folds(M,cfg.n_folds); fold_size=len(fs[0])
    target_rank=min(cfg.rank_k,S-1,D)
    if target_rank < cfg.rank_k:
        return GateResult(0.,0.,0.,0.,1.,target_rank,cfg.n_folds,fold_size,False,False,"INSUFFICIENT_SOURCE_DIMENSION",cfg.eig_floor,cfg.member_semantics)

    W,ridge=_fold_invariant_whitener(x,fs,cfg)
    X=[]
    for f in fs:
        mu=x[:,f,:].mean(axis=1)
        X.append((mu-mu.mean(axis=0,keepdims=True))@W)

    # Each reference fold chooses its own basis. Held-out folds never influence
    # that basis, removing the finite-M self-selection bias that invalidated V1.
    refs=[]
    for r in range(cfg.n_folds):
        _,_,vt=np.linalg.svd(X[r],full_matrices=False)
        Q=vt[:target_rank].T
        refs.append((Q,X[r]@Q))

    def cross_stat(perms):
        l1=[]; lk=[]
        for r,(Q,A0) in enumerate(refs):
            A=A0[perms[r]]
            C=np.zeros((target_rank,target_rank),dtype=np.float64); n=0
            for h in range(cfg.n_folds):
                if h==r: continue
                B=(X[h]@Q)[perms[h]]
                C += (A.T@B+B.T@A)/(2.0*max(S-1,1)); n+=1
            C/=max(n,1)
            ev=np.linalg.eigvalsh(C)[::-1]
            l1.append(float(ev[0])); lk.append(float(ev[target_rank-1]))
        return float(np.mean(l1)),float(np.mean(lk))

    identity=[np.arange(S,dtype=int) for _ in range(cfg.n_folds)]
    lambda_1,lambda_k=cross_stat(identity)

    rng=np.random.default_rng(cfg.permutation_seed)
    null_k=np.empty(cfg.n_permutations,dtype=np.float64)
    for b in range(cfg.n_permutations):
        perms=[rng.permutation(S) for _ in range(cfg.n_folds)]
        _,null_k[b]=cross_stat(perms)
    p_perm=float((1+np.sum(null_k>=lambda_k))/(cfg.n_permutations+1))
    alpha_cf=float(lambda_k)  # signed; not rectified before testing
    gamma_cf=float(max(lambda_k,0.0)/max(lambda_1,cfg.eig_floor))

    inferential_valid=(cfg.member_semantics=="exchangeable_realizations")
    reasons=[]
    if not inferential_valid: reasons.append("FIXED_DESIGN_DESCRIPTIVE_ONLY")
    if alpha_cf<=0: reasons.append("NONPOSITIVE_ALPHA_CF")
    if gamma_cf<cfg.gamma_min: reasons.append("GAMMA_CF")
    if p_perm>cfg.p_max: reasons.append("PERMUTATION_NULL")
    accepted=(not reasons)
    return GateResult(alpha_cf,gamma_cf,float(lambda_1),float(lambda_k),p_perm,target_rank,cfg.n_folds,fold_size,accepted,inferential_valid,"PASS" if accepted else "+".join(reasons),ridge,cfg.member_semantics)

def no_update_posterior(previous_q):
    """Exact ABSTAIN contract."""
    q=np.asarray(previous_q,dtype=np.float64)
    if q.ndim!=1 or q.size<2 or np.any(q<0) or not np.all(np.isfinite(q)): raise ValueError("invalid posterior")
    z=q.sum()
    if z<=0: raise ValueError("posterior must have positive mass")
    return (q/z).copy()
