#!/usr/bin/env python3
"""Known-limitation diagnostics for frozen Gate V2.

These tests are intentionally NOT assertions that Gate V2 must fail. They
construct two scientifically important cases where a global replicated-
completeness statistic may PASS even though localization reliability is bad:

1) LOCAL_TWIN: the global 206-candidate field has strong stable structure, but
   two neighboring candidates have identical response and are not locally
   identifiable.
2) SHARED_BIAS_WRONG: all transport members share the same forward-model bias,
   making a wrong source fit the physical observation better than the true
   candidate while replication remains excellent.

The script documents the boundary: replication != correctness and global rank
!= hard-negative separation.
"""
from __future__ import annotations
import json
import numpy as np
from completeness_gate import GateConfig, compute_gate

CFG=GateConfig(gamma_min=.05,p_max=.01,rank_k=3,member_semantics="exchangeable_realizations")


def base(seed=7,S=206,M=8,D=48,noise=.05):
    rng=np.random.default_rng(seed)
    xy=np.stack([np.linspace(-1,1,S),np.sin(np.linspace(0,4*np.pi,S))],axis=1)
    latent=np.stack([xy[:,0],xy[:,1],xy[:,0]*xy[:,1]],axis=1)
    A=rng.normal(size=(3,D))
    mu=latent@A
    return mu[:,None,:]+noise*rng.normal(size=(S,M,D)),mu,xy


def main():
    x,mu,xy=base()
    strong=compute_gate(x,CFG)

    twin=x.copy(); twin[101]=twin[100]
    local_twin=compute_gate(twin,CFG)
    twin_distance=float(np.mean((twin[100]-twin[101])**2))

    # Physical observation follows the un-biased true forward response.
    true=100; wrong=101; obs=mu[true].copy()
    biased=x.copy()
    # Shared across all 8 members: move wrong candidate exactly onto obs and
    # shift true candidate away. This is systematic model error, not member noise.
    biased[wrong]=obs[None,:]+(x[wrong]-x[wrong].mean(axis=0,keepdims=True))
    shared_shift=np.ones(mu.shape[1])*1.5
    biased[true]=biased[true]+shared_shift[None,:]
    shared_bias=compute_gate(biased,CFG)
    pred=biased.mean(axis=1)
    true_err=float(np.mean((obs-pred[true])**2)); wrong_err=float(np.mean((obs-pred[wrong])**2))

    out={
      "contract":"CG_PC_CTT_KNOWN_LIMITATIONS_SYNTHETIC_V1",
      "strong_global":{"accepted":strong.accepted,"gamma":strong.gamma_cf,"p":strong.p_signflip},
      "local_twin":{"global_gate_accepted":local_twin.accepted,"global_gamma":local_twin.gamma_cf,"global_p":local_twin.p_signflip,"candidate_100_101_mse":twin_distance,"interpretation":"global PASS does not imply local injectivity"},
      "shared_bias_wrong":{"global_gate_accepted":shared_bias.accepted,"global_gamma":shared_bias.gamma_cf,"global_p":shared_bias.p_signflip,"true_candidate_model_mse_to_physical_obs":true_err,"wrong_candidate_model_mse_to_physical_obs":wrong_err,"wrong_beats_true":wrong_err<true_err,"interpretation":"cross-member replication cannot detect common-mode model bias"},
      "binding_note":"These are known limitations, not reasons to retune the frozen H03/H02 V2 gate. Use H02 hard-negative margins and observation adequacy to test whether the limitations matter in the real system."
    }
    print(json.dumps(out,indent=2))

if __name__=="__main__": main()
