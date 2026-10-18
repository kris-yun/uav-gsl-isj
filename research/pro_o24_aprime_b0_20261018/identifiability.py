#!/usr/bin/env python3
"""Physical source distinguishability, not generalizable performance claims."""
import numpy as np
from response_contract import ObservationContract, ResponseBank, check_physical_contract


def pairwise_identifiability(obs:ObservationContract, bank:ResponseBank,
                             unknown_nonnegative_release:bool=True, deployment:bool=True):
    """Known release: whitened pair distances. Unknown release: positive ray angle.

    Conditions: Gaussian sensor noise with independent, known sigma; stationary
    source amplitude for all windows; matched, time-aligned physical K columns.
    Returns necessary pairwise differences, not a sufficient test of an estimator.
    """
    check_physical_contract(obs,bank,deployment)
    K=bank.response_ppm_per_unit_release/obs.sigma_ppm[:,None]
    norms=np.linalg.norm(K,axis=0)
    out=[]
    for i in range(K.shape[1]):
        for j in range(i+1,K.shape[1]):
            distance=float(np.linalg.norm(K[:,i]-K[:,j]))
            if norms[i]==0 or norms[j]==0:
                cos=float('nan');ang=float('nan')
            else:
                cos=float(np.clip(K[:,i]@K[:,j]/(norms[i]*norms[j]),0,1))
                # Allow both amplitude profiles, so only the ray orientation is
                # source-specific when amplitude has no informative prior.
                ang=float(np.sqrt(max(0.,1-cos*cos)))
            out.append({'source_pair':(bank.source_ids[i],bank.source_ids[j]),
                'known_amplitude_whitened_separation':distance,
                'unknown_amplitude_ray_sine':ang,
                'structural_non_identifiable':bool(distance<1e-10 or
                  (unknown_nonnegative_release and np.isfinite(ang) and ang<1e-7))})
    return out
