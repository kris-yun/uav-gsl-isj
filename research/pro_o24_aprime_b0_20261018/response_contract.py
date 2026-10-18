#!/usr/bin/env python3
"""A-prime candidate: a physically matched source-to-sensor ppm scoring interface.

This is an *offline adapter*, not a transport solver and not a deployed PMFS
patch.  It deliberately rejects an O24 2D hit map as a ppm response matrix.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

class QualificationError(ValueError):
    """Required observational/physical provenance is absent or inconsistent."""

@dataclass(frozen=True)
class ResponseProvenance:
    scene_id: str
    wind_input: str          # measured_or_estimated, or truth_offline_oracle
    transport_model: str     # explicit full forward solver identity
    release_unit: str        # known physical unit, e.g. mg/s
    sensor_operator: str     # e.g. calibrated_linear_ppm
    physical_time_basis: str # e.g. seconds_from_world_start
    sensor_calibration_id: str
    run_identity: str
    physical_realization: str # weather/geometry/clock identity, NOT truth label

@dataclass(frozen=True)
class ObservationContract:
    window_ids: tuple[str, ...]
    window_time_s: np.ndarray
    receptor_xyz_m: np.ndarray
    observed_ppm: np.ndarray
    sigma_ppm: np.ndarray
    provenance: ResponseProvenance

@dataclass(frozen=True)
class ResponseBank:
    window_ids: tuple[str, ...]
    response_ppm_per_unit_release: np.ndarray # [n_windows, n_candidate_sources]
    source_xy_m: np.ndarray # [n_candidate_sources, 2]
    source_area_m2: np.ndarray
    provenance: ResponseProvenance
    # This identity exists to require explicit counterfactual source columns.
    source_ids: tuple[str,...]
    response_kind: str = 'time_aligned_linear_ppm_per_release'

@dataclass(frozen=True)
class SourcePosterior:
    source_xy_m: np.ndarray
    probability: np.ndarray
    score_log_likelihood: np.ndarray
    estimated_release: np.ndarray
    source_area_m2: np.ndarray


def check_physical_contract(obs:ObservationContract, bank:ResponseBank,
                            deployment:bool=True)->None:
    """Require simultaneous sensor/readout semantics, no online oracle fields.

    Authenticity of a solver/provenance ID requires a separate external audit;
    this structural gate never claims to verify that file contents are true.
    """
    o,b=obs.provenance,bank.provenance
    required=(o.scene_id,o.wind_input,o.transport_model,o.release_unit,o.sensor_operator,
              o.physical_time_basis,o.sensor_calibration_id,o.run_identity,o.physical_realization)
    if any(not v for v in required): raise QualificationError('Incomplete observation provenance')
    if o!=b: raise QualificationError('Observation and candidate bank are not a matched physical condition')
    if deployment and o.wind_input!='measured_or_estimated':
        raise QualificationError('Oracle/simulation truth wind is not an admissible online input')
    if o.sensor_operator!='calibrated_linear_ppm':
        raise QualificationError('Requires calibrated, continuous linear ppm sensor output')
    if bank.response_kind!='time_aligned_linear_ppm_per_release':
        raise QualificationError('O24 2D hit frequency cannot be substituted for ppm response')
    ids=obs.window_ids
    if not ids or len(ids)!=len(set(ids)) or ids!=bank.window_ids:
        raise QualificationError('Source responses must match each sensor window ID and order')
    n,m=bank.response_ppm_per_unit_release.shape
    if n!=len(ids) or m<2 or len(bank.source_ids)!=m or len(set(bank.source_ids))!=m:
        raise QualificationError('Need two or more distinct physically evaluated source hypotheses')
    if bank.source_xy_m.shape!=(m,2) or bank.source_area_m2.shape!=(m,):
        raise QualificationError('Candidate source geometry has wrong shape')
    if np.any(bank.source_area_m2<=0) or not np.isfinite(bank.source_area_m2).all():
        raise QualificationError('Positive area or source-mass prior is required')
    if obs.receptor_xyz_m.shape!=(n,3) or obs.window_time_s.shape!=(n,):
        raise QualificationError('Every concentration readout needs 3D pose and physical time')
    for a in (obs.window_time_s,obs.receptor_xyz_m,obs.observed_ppm,
              obs.sigma_ppm,bank.response_ppm_per_unit_release,bank.source_xy_m):
        if not np.isfinite(a).all():raise QualificationError('Non-finite physical input')
    if obs.observed_ppm.shape!=(n,) or obs.sigma_ppm.shape!=(n,):
        raise QualificationError('Observation vectors wrong length')
    if np.any(obs.sigma_ppm<=0) or np.any(obs.observed_ppm<0):
        raise QualificationError('Gaussian noise scale must be positive and concentrations nonnegative')
    if np.any(bank.response_ppm_per_unit_release<0):
        raise QualificationError('A passive unit-release concentration kernel cannot be negative')
    if not np.all(np.diff(obs.window_time_s)>=0):
        raise QualificationError('Physical-time windows are not ordered')
    if o.release_unit in ('hit','hit/s','occupancy','unknown'):
        raise QualificationError('Release rate must be stated in physical units')


def posterior_ppm_gaussian(obs:ObservationContract,bank:ResponseBank,
                           source_release:float|None=None,
                           background_ppm:float=0.,deployment:bool=True)->SourcePosterior:
    """Ordinary weighted-Gaussian likelihood with optional nonnegative Q profiling.

    Normalization constants cancel *within this matched candidate set*.
    Q>=0 is a nuisance shared by all sensor windows, not individually fitted
    per receptor.  Profiling is NOT the same as marginalization over Q.
    """
    check_physical_contract(obs,bank,deployment)
    if background_ppm<0 or not np.isfinite(background_ppm):
        raise QualificationError('Invalid fixed background')
    K=bank.response_ppm_per_unit_release
    centered=obs.observed_ppm-background_ppm
    weights=1/obs.sigma_ppm**2
    if source_release is None:
        numer=K.T@(weights*centered)
        denom=(weights[:,None]*K*K).sum(axis=0)
        release=np.divide(np.maximum(0,numer),denom,out=np.zeros_like(numer),where=denom>0)
    else:
        if not (np.isfinite(source_release) and source_release>=0):
            raise QualificationError('Invalid fixed positive source emission')
        release=np.full(K.shape[1],source_release,dtype=np.float64)
    mismatch=centered[:,None]-K*release
    logp=-0.5*np.sum(weights[:,None]*mismatch**2,axis=0)
    # Areas are an explicit (and debatable) uniform-density prior. Must be
    # identical for all methods; never secretly renormalize by source labels.
    scores=logp+np.log(bank.source_area_m2)
    q=np.exp(scores-scores.max());q/=q.sum()
    return SourcePosterior(bank.source_xy_m.copy(),q,logp,release,bank.source_area_m2.copy())
