"""Executable V46 control/inference chain and one explicit reference backend.

All arrays crossing interfaces carry immutable physical sensor IDs. Reordering
storage rows, with their metadata, leaves decisions unchanged and reorders
velocity rows. This is not a claim about renaming physical identities or rotating
the full map and tie-breaking convention.

Inference uses raw additive Gaussian observations. M1 rectification and shape
memory never enter the likelihood. The log-noise Green contrast theorem is a
separate mathematical certificate and is not silently used as this likelihood.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from itertools import product
import json
from typing import Iterable

import numpy as np

from .m1_decoders import odor_memory, encode, decode, decode_merged


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Gate:
    status: GateStatus = GateStatus.UNKNOWN
    reason: str = "No independent qualification supplied"
    evidence: str = ""


@dataclass(frozen=True)
class Qualifications:
    """Four scientifically distinct checks; safety is evaluated separately.

    shape is an empirical screen, not proof of common release age. coherence
    needs transport evidence. model needs a specified support and error bound.
    No misclassification rate is manufactured from a Boolean pass/fail.
    """
    time: Gate = field(default_factory=Gate)
    shape: Gate = field(default_factory=Gate)
    coherence: Gate = field(default_factory=Gate)
    model: Gate = field(default_factory=Gate)


def _finite(x, shape=None, name="array"):
    a = np.asarray(x, float).copy()
    if (shape is not None and a.shape != shape) or not np.isfinite(a).all():
        raise ValueError(f"Invalid {name}: expected finite shape {shape}")
    return a


@dataclass(frozen=True)
class SensorSpec:
    physical_id: str
    gain: float = 1.0
    background: float = 0.0
    sigma: float = 0.02
    tau_s: float = 0.5
    lag_steps: int = 0
    vmax: float = 1.0

    def __post_init__(self):
        vals = [self.gain, self.background, self.sigma, self.tau_s, self.vmax]
        if (not self.physical_id or not np.isfinite(vals).all()
                or min(self.gain, self.sigma, self.vmax) <= 0
                or self.tau_s < 0 or self.lag_steps < 0
                or int(self.lag_steps) != self.lag_steps):
            raise ValueError("Invalid independently supplied sensor calibration")


@dataclass(frozen=True)
class RawFrame:
    sample_id: str
    t: float
    sensor_ids: tuple[str, ...]
    positions: np.ndarray
    velocity: np.ndarray
    ambient_wind: np.ndarray
    raw: np.ndarray
    instrument_valid: np.ndarray
    qualifications: Qualifications = field(default_factory=Qualifications)
    raw_status: tuple[str, ...] = ()

    def __post_init__(self):
        n = len(self.sensor_ids)
        if (not self.sample_id or n < 2 or len(set(self.sensor_ids)) != n
                or not np.isfinite(self.t)):
            raise ValueError("Need timestamp, unique sample ID and physical IDs")
        for key in ("positions", "velocity", "ambient_wind"):
            a=_finite(getattr(self, key), (n, 3), key);a.setflags(write=False)
            object.__setattr__(self, key, a)
        raw=_finite(self.raw, (n,), "raw readings");raw.setflags(write=False)
        object.__setattr__(self, "raw", raw)
        v = np.asarray(self.instrument_valid)
        if v.shape != (n,) or not np.isin(v, [0, 1]).all():
            raise ValueError("Instrument mask must be binary and ID-aligned")
        v=v.astype(bool).copy();v.setflags(write=False)
        object.__setattr__(self, "instrument_valid", v)
        status = self.raw_status or tuple("OK" for _ in range(n))
        if len(status) != n:
            raise ValueError("Raw status must accompany each physical sensor")
        object.__setattr__(self, "raw_status", tuple(status))

    def ordered(self, ids: tuple[str, ...]) -> "RawFrame":
        if set(ids) != set(self.sensor_ids):
            raise ValueError("Changing sensor membership requires a new run")
        index = {sensor_id:i for i,sensor_id in enumerate(self.sensor_ids)}
        ix = [index[i] for i in ids]
        return RawFrame(self.sample_id, self.t, ids, self.positions[ix],
                        self.velocity[ix], self.ambient_wind[ix], self.raw[ix],
                        self.instrument_valid[ix], self.qualifications,
                        tuple(self.raw_status[i] for i in ix))

    def digest(self) -> str:
        f = self.ordered(tuple(sorted(self.sensor_ids)))
        h = sha256((f.sample_id + repr(float(f.t))).encode())
        h.update("\0".join(f.sensor_ids).encode())
        h.update("\0".join(f.raw_status).encode())
        for x in [f.positions, f.velocity, f.ambient_wind, f.raw,
                  f.instrument_valid.astype(np.float64)]:
            h.update(np.ascontiguousarray(x, dtype="<f8").tobytes())
        return h.hexdigest()


@dataclass(frozen=True)
class RawBlock:
    block_id: str
    frames: tuple[RawFrame, ...]

    def __post_init__(self):
        if (not self.block_id or not self.frames
                or len({f.sample_id for f in self.frames}) != len(self.frames)
                or any(b.t <= a.t for a, b in zip(self.frames, self.frames[1:]))):
            raise ValueError("A raw block needs unique IDs and increasing times")


@dataclass(frozen=True)
class SourceBank:
    """Rows theta=(sx,sy,h,q), all nuisance hypotheses carried jointly.

    This finite bank is explicitly a finite approximation. Its minimum response
    distance is not a lower bound over an unrepresented continuous source domain.
    """
    theta: np.ndarray
    prior: np.ndarray
    exact_declared_domain: bool = False
    _xy: np.ndarray = field(init=False,repr=False)
    _group: np.ndarray = field(init=False,repr=False)

    def __post_init__(self):
        t = _finite(self.theta, name="source bank")
        if t.ndim != 2 or t.shape[1] != 4 or len(t) < 2 or (t[:, 3] <= 0).any():
            raise ValueError("Need positive q and columns sx,sy,h,q")
        p = _finite(self.prior, (len(t),), "prior")
        if (p < 0).any() or p.sum() <= 0 or not np.isfinite(p.sum()):
            raise ValueError("Invalid prior mass")
        p = p/p.sum()
        xy,group=np.unique(t[:,:2],axis=0,return_inverse=True)
        for a in [t,p,xy,group]:a.setflags(write=False)
        object.__setattr__(self, "theta", t)
        object.__setattr__(self, "prior", p)
        object.__setattr__(self, "_xy", xy)
        object.__setattr__(self, "_group", group)

    @property
    def xy_groups(self):
        return self._xy,self._group


class GreenZOHModel:
    """Known constant U/kappa/release time, point impulse and calibrated sensors.

    Within each dt, field input is the Green concentration at the midpoint of
    the observed straight segment; it is held constant through that interval.
    The first-order sensor ZOH recursion is exact for this *discrete input*.
    Delay is an integer number of samples. This is not a claim of exact continuous
    trajectory integration. Each theta has its own causal sensor state.
    """
    def __init__(self, bank: SourceBank, specs: Iterable[SensorSpec], positions,
                 *, t0=1.0, dt=0.5, wind=(0.2, 0.0, 0.0), kappa=1.0,
                 release_time=0.0, initial_sensor=0.0):
        supplied = tuple(specs)
        self.ids = tuple(sorted(s.physical_id for s in supplied))
        if len(set(self.ids)) != len(self.ids) or len(self.ids) < 2:
            raise ValueError("Unique sensor calibrations required")
        by_id = {s.physical_id: s for s in supplied}
        self.specs = tuple(by_id[i] for i in self.ids)
        rawp = _finite(positions, (len(self.ids), 3), "initial positions")
        # Initial rows follow supplied specs, then canonicalize together.
        supplied_index={s.physical_id:i for i,s in enumerate(supplied)}
        self.positions = rawp[[supplied_index[i] for i in self.ids]]
        self.bank = bank
        self.t = float(t0)
        self.dt = float(dt)
        self.wind = _finite(wind, (3,), "known wind")
        self.kappa = float(kappa)
        self.release_time = float(release_time)
        if not np.isfinite([t0, dt, kappa, release_time, initial_sensor]).all() or dt <= 0 or kappa <= 0:
            raise ValueError("Invalid reference transport parameters")
        shape = (len(bank.theta), len(self.ids))
        self.z = np.full(shape, float(initial_sensor))
        self.delay_history = [self.z.copy() for _ in range(max(s.lag_steps for s in self.specs) + 1)]
        self.history_whitened: list[np.ndarray] = []
        self.forward_calls = 0
        self.field_evaluations = 0

    def field(self, positions, t):
        age = float(t) - self.release_time
        if age <= 0:
            return np.zeros((len(self.bank.theta), len(self.ids)))
        src = self.bank.theta[:, :3]
        d = positions[None, :, :] - src[:, None, :] - self.wind * age
        dist = np.sum(d*d, axis=-1)
        return (self.bank.theta[:, 3, None] * (4*np.pi*self.kappa*age)**(-1.5)
                * np.exp(-dist/(4*self.kappa*age)))

    def parameter_signature(self):
        """Likelihood-defining parameters; excludes legitimate dynamic state."""
        payload={"version":"V46-GREEN-MIDPOINT-ZOH-1","theta":self.bank.theta.tolist(),
                 "prior":self.bank.prior.tolist(),"sensors":[s.__dict__ for s in self.specs],
                 "dt":self.dt,"wind":self.wind.tolist(),"kappa":self.kappa,
                 "release_time":self.release_time}
        return sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    def _advance(self, z, history, oldp, newp, oldt, newt):
        if abs((newt-oldt)-self.dt) > 1e-9:
            raise ValueError("Reference backend requires fixed dt; adapt native sampling explicitly")
        c = self.field((oldp+newp)/2, (oldt+newt)/2)
        tau = np.array([s.tau_s for s in self.specs])
        decay = np.exp(-self.dt / np.maximum(tau, np.finfo(float).tiny))
        decay[tau == 0] = 0.0
        z = decay[None, :]*z + (1-decay[None, :])*c
        history = (history + [z.copy()])[-len(self.delay_history):]
        delayed = np.column_stack([history[-1-s.lag_steps][:, i]
                                   for i, s in enumerate(self.specs)])
        gain = np.array([s.gain for s in self.specs])
        bias = np.array([s.background for s in self.specs])
        return z, history, delayed*gain[None, :]+bias[None, :]

    def preview_block(self, frames: tuple[RawFrame, ...]):
        """Compute whole-block likelihood inputs without mutating sensor state."""
        z, hist, p, t = self.z.copy(), [x.copy() for x in self.delay_history], self.positions.copy(), self.t
        means = []
        for frame in frames:
            f = frame.ordered(self.ids)
            z, hist, mu = self._advance(z, hist, p, f.positions, t, f.t)
            means.append(mu)
            p, t = f.positions, f.t
        return np.stack(means, axis=1), (z, hist, p.copy(), t)

    def commit_block(self, mean, state):
        self.z, self.delay_history, self.positions, self.t = state
        sigma = np.array([s.sigma for s in self.specs])
        self.history_whitened.append((mean/sigma[None, None, :]).reshape(len(self.bank.theta), -1))

    def predict(self, candidate: "Candidate"):
        if candidate.sensor_ids != self.ids:
            candidate = candidate.ordered(self.ids)
        nsteps = int(round(candidate.duration/self.dt))
        if nsteps < 1 or abs(nsteps*self.dt-candidate.duration)>1e-9:
            raise ValueError("Candidate horizon must be an integer number of samples")
        z, hist, p, t = self.z.copy(), [x.copy() for x in self.delay_history], self.positions.copy(), self.t
        means=[]
        for _ in range(nsteps):
            newp = p + self.dt*candidate.velocities
            z, hist, mu = self._advance(z, hist, p, newp, t, t+self.dt)
            means.append(mu)
            p, t = newp, t+self.dt
        self.forward_calls += 1
        self.field_evaluations += nsteps*len(self.bank.theta)*len(self.ids)
        return np.stack(means, axis=1)


class GaussianPosterior:
    """Exact discrete-bank raw Gaussian update for the reference backend.

    The ledger detects repeated/repackaged raw sample IDs before mutating the
    model or posterior. Derived control features have no update entry point.
    A changed likelihood/backend requires reconstructing a fresh object from
    the archived raw history; old and new likelihoods must not be multiplied.
    """
    def __init__(self, model: GreenZOHModel):
        self.model = model
        self.model_signature=model.parameter_signature()
        with np.errstate(divide="ignore"):
            self.log_mass = np.log(model.bank.prior)
        self.ledger: dict[str, str] = {}
        self.blocks: set[str] = set()
        self.raw_archive: list[RawFrame] = []
        self.received_archive: dict[str, RawFrame] = {}

    def assert_same_model(self):
        if self.model.parameter_signature()!=self.model_signature:
            raise ValueError("Likelihood model changed; construct a fresh posterior and replay archived raw")

    @property
    def mass(self):
        x = self.log_mass - np.max(self.log_mass)
        w = np.exp(x)
        return w/w.sum()

    def update_once(self, block: RawBlock):
        if block.block_id in self.blocks:
            raise ValueError("Duplicate raw block; no update performed")
        for f in block.frames:
            if f.sample_id in self.ledger:
                previous = self.ledger[f.sample_id]
                why = "duplicate" if previous == f.digest() else "conflicting"
                raise ValueError(f"{why} raw sample ID; no update performed")
        frames = tuple(f.ordered(self.model.ids) for f in block.frames)
        # Preserve acquired raw records even if the declared likelihood cannot
        # yet consume a saturated/faulted channel. That is an explicit OPEN
        # inference interface, never a deletion or a fabricated likelihood.
        for f in frames:
            if f.sample_id in self.received_archive and self.received_archive[f.sample_id].digest()!=f.digest():
                raise ValueError("Conflicting archived raw sample")
            self.received_archive[f.sample_id]=f
        self.assert_same_model()
        # Reference Gaussian model includes finite negatives. Instrument-fault
        # handling needs an explicit censored/failed-channel likelihood, not a
        # silently rectified or deleted observation. Timing qualification alone
        # may be UNKNOWN: actual timestamps still determine the raw model.
        if not all(all(s == "OK" for s in f.raw_status) for f in frames):
            raise ValueError("Fault-marked raw needs an explicit fault likelihood backend")
        mu, state = self.model.preview_block(frames)
        y = np.stack([f.raw for f in frames])
        sigma = np.array([s.sigma for s in self.model.specs])
        residual = (y[None, :, :]-mu)/sigma[None, None, :]
        ll = -0.5*np.sum(residual*residual, axis=(1,2))
        newlog = self.log_mass + ll
        if not np.isfinite(newlog).any():
            raise FloatingPointError("All hypotheses numerically impossible; retain raw for audit")
        # Transaction commits only after every validation and computation passes.
        newlog -= np.max(newlog)
        self.model.commit_block(mu, state)
        self.log_mass = newlog
        for f in frames:
            self.ledger[f.sample_id] = f.digest()
            self.raw_archive.append(f)
        self.blocks.add(block.block_id)
        return self.xy_probability()

    def xy_probability(self):
        xy, group = self.model.bank.xy_groups
        return xy, np.bincount(group, weights=self.mass, minlength=len(xy))


@dataclass(frozen=True)
class Candidate:
    semantic_id: str
    sensor_ids: tuple[str, ...]
    velocities: np.ndarray
    duration: float
    common_scale: float = 1.0

    def __post_init__(self):
        v=_finite(self.velocities, (len(self.sensor_ids),3), "velocity");v.setflags(write=False)
        object.__setattr__(self, "velocities", v)
        if not self.semantic_id or self.duration <= 0 or not np.isfinite(self.duration):
            raise ValueError("Candidate requires semantic ID and positive horizon")

    def ordered(self, ids):
        index={sensor_id:i for i,sensor_id in enumerate(self.sensor_ids)}
        ix = [index[i] for i in ids]
        return Candidate(self.semantic_id, ids, self.velocities[ix], self.duration, self.common_scale)


class ConvexBoxSafety:
    """Exact segment safety for a convex axis-aligned box and constant velocities.

    Separation uses the continuous closest point, with supplied tracking error
    added twice. This ideal reference safety is not an acceleration/flight-control
    guarantee. Native execution must supply its own full trajectory certificate.
    """
    def __init__(self, lower, upper, *, min_separation=0.5, tracking_error=0.0):
        self.lower, self.upper = _finite(lower,(3,)), _finite(upper,(3,))
        if np.any(self.upper <= self.lower) or min_separation < 0 or tracking_error < 0:
            raise ValueError("Invalid safety geometry")
        self.clearance = float(min_separation+2*tracking_error)
        self.pair_checks = 0

    def legal(self, positions, candidate):
        p = _finite(positions, candidate.velocities.shape)
        v, T = candidate.velocities, candidate.duration
        if (np.any(p < self.lower) or np.any(p > self.upper)
                or np.any(p+T*v < self.lower) or np.any(p+T*v > self.upper)):
            return False
        for i in range(len(p)):
            for j in range(i):
                self.pair_checks += 1
                r, w = p[i]-p[j], v[i]-v[j]
                ww = float(w@w)
                t = 0.0 if ww <= 1e-30 else float(np.clip(-r@w/ww,0,T))
                if np.linalg.norm(r+t*w) < self.clearance-1e-12:
                    return False
        return True


@dataclass(frozen=True)
class ControllerConfig:
    budget_s: float = 300.0
    action_s: float = 2.0
    horizon_steps: int = 8
    beta: float = 0.65
    contact_threshold: float = 0.0
    remeasure_limit_s: float = 2.0
    K: int = 8
    catalog_speed: float = 0.8
    relative_fraction: float = 0.5
    source_tolerance: float = 0.5
    path_penalty: float = 0.0
    score_kind: str = "min_separation"
    eig_samples: int = 32
    seed: int = 20261028
    confirmation_threshold: float | None = None
    confirmation_radius: float = 0.5
    scale_m: float = 5.0
    flow_floor: float = 0.1
    speed_contact: float = 0.35
    speed_flow: float = 0.8
    damping_t: float = 0.2
    speed_reconfigure: float = 0.5
    ridge_r: float = 0.15

    def __post_init__(self):
        if (self.budget_s <= 0 or self.action_s <= 0 or self.horizon_steps < 1
                or self.K < 1 or not 0 <= self.beta < 1
                or self.contact_threshold < 0 or self.remeasure_limit_s < 0
                or self.catalog_speed <= 0 or self.relative_fraction < 0
                or self.source_tolerance <= 0 or self.path_penalty < 0
                or self.eig_samples < 1 or self.score_kind not in {"min_separation", "xy_eig"}):
            raise ValueError("Invalid frozen controller settings")
        if (self.confirmation_radius <= 0 or
                (self.confirmation_threshold is not None and not 0 < self.confirmation_threshold < 1)):
            raise ValueError("A declared posterior decision rule needs valid radius/probability")
        values=[self.scale_m,self.flow_floor,self.speed_contact,self.speed_flow,
                self.damping_t,self.speed_reconfigure,self.ridge_r]
        if (not np.isfinite(values).all() or min(self.scale_m,self.flow_floor,self.damping_t,self.ridge_r)<=0
                or min(self.speed_contact,self.speed_flow,self.speed_reconfigure)<0):
            raise ValueError("Invalid M1 physical scales or regularization")


def common_scale(candidate: Candidate, specs):
    spec = {s.physical_id:s for s in specs}
    limit = np.array([spec[i].vmax for i in candidate.sensor_ids])
    speed = np.linalg.norm(candidate.velocities,axis=1)
    alpha = min(1.0,float(np.min(limit/np.maximum(speed,1e-15))))
    return Candidate(candidate.semantic_id,candidate.sensor_ids,
                     alpha*candidate.velocities,candidate.duration,alpha)


def common_catalog(ids, positions, cfg, specs):
    """Fixed 9 translation x 7 relative templates = 63 semantic candidates.

    Shared for all methods. Relative templates are ordinary affine deformations
    of the current array; M1 changes which K candidates receive expensive scores,
    not the common action domain. The geometric catalog is not a novelty claim.
    """
    delta = positions[:,:2]-positions[:,:2].mean(axis=0)
    matrices = [np.zeros((2,2)),np.eye(2),-np.eye(2),
                np.array([[0.,-1.],[1.,0.]]),np.array([[0.,1.],[-1.,0.]]),
                np.diag([1.,-1.]),np.array([[0.,1.],[1.,0.]])]
    rel=[]
    for M in matrices:
        r=delta@M.T
        r-=r.mean(axis=0)
        norm=float(np.linalg.norm(r,axis=1).max())
        rel.append(r/max(norm,1e-15)*cfg.catalog_speed*cfg.relative_fraction)
    translations=[np.zeros(2)] + [cfg.catalog_speed*np.array([np.cos(a),np.sin(a)])
                                 for a in np.arange(8)*np.pi/4]
    out=[]
    for ti,ri in product(range(len(translations)),range(len(rel))):
        vel=np.zeros_like(positions)
        vel[:,:2]=translations[ti]+rel[ri]
        out.append(common_scale(Candidate(f"T{ti:02d}_R{ri:02d}",ids,vel,cfg.action_s),specs))
    return out


class Controller:
    """Full reference ordering: Observe/UpdateOnce/Encode/Decode/Candidates/
    Safety/Shortlist/PredictScore/Execute; the next raw block updates once.
    Prediction, safety and world objects are purpose-separated. True source is
    absent from this class and from all proposer/scorer inputs.
    """
    MODES = {"m1_full","no_history","merged_r","t_only","r_only",
             "no_polarity_t","upwind","ordinary_array","gradient",
             "information_uniform"}

    def __init__(self, posterior: GaussianPosterior, safety: ConvexBoxSafety,
                 config=ControllerConfig(), mode="m1_full"):
        if mode not in self.MODES:
            raise ValueError("Unknown controlled comparison mode")
        self.posterior,self.safety,self.cfg,self.mode=posterior,safety,config,mode
        self.ids=posterior.model.ids
        self.specs=posterior.model.specs
        self.control_window: list[RawFrame]=[]
        self.fixed_mask=None
        self.last_frame=None
        self.start_time=posterior.model.t
        self.remeasure_used=0.0
        self.decisions=[]
        self.source_confirmation=False
        self.confirmation={"status":"UNCONFIRMED","reason":"No qualified decision rule"}
        self.confirmation_events=[]
        self.baseline_fallback=None
        self.has_been_confirmed=False

    def observe(self, block: RawBlock):
        # Arrival of unprocessed or unsupported data invalidates any previous
        # declaration until the complete block and its qualifications are checked.
        previous=self.source_confirmation
        self.source_confirmation=False
        self.confirmation={"status":"REVOKED" if self.has_been_confirmed else "UNCONFIRMED",
                           "reason":"New raw block awaiting qualification"}
        xy = self.posterior.update_once(block)
        for supplied in block.frames:
            f=supplied.ordered(self.ids)
            # A new qualified-set membership starts a new control window.
            if self.fixed_mask is None or not np.array_equal(f.instrument_valid,self.fixed_mask):
                self.control_window=[]
                self.fixed_mask=f.instrument_valid.copy()
            if f.qualifications.time.status != GateStatus.PASS:
                self.control_window=[]
            else:
                self.control_window.append(f)
                self.control_window=self.control_window[-self.cfg.horizon_steps:]
            self.last_frame=f
        self.refresh_confirmation(previous=previous)
        return xy

    def refresh_confirmation(self, *, previous=None):
        """Apply an optional, explicitly model-conditional finite-domain rule.

        Posterior mass is not a calibrated repeated-sampling false-positive
        guarantee. Default rule is disabled. A finite approximation to a
        continuous source domain cannot activate this finite-domain declaration.
        Coherence/shape are not universal gates for an ordinary raw likelihood.
        """
        previous=self.source_confirmation if previous is None else previous
        self.source_confirmation=False
        f=self.last_frame
        eligible=(f is not None and self.cfg.confirmation_threshold is not None
                  and self.posterior.model.bank.exact_declared_domain
                  and self.posterior.model.parameter_signature()==self.posterior.model_signature
                  and not (set(self.posterior.received_archive)-set(self.posterior.ledger))
                  and bool(self.posterior.raw_archive)
                  and all(x.qualifications.time.status==GateStatus.PASS
                          and x.qualifications.model.status==GateStatus.PASS
                          for x in self.posterior.raw_archive)
                  and f.qualifications.time.status==GateStatus.PASS
                  and f.qualifications.model.status==GateStatus.PASS)
        if eligible:
            xy,mass=self.posterior.xy_probability()
            region=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=2)<=self.cfg.confirmation_radius
            region_mass=region@mass
            ix=int(np.argmax(region_mass))
            self.source_confirmation=bool(region_mass[ix]>=self.cfg.confirmation_threshold)
            self.has_been_confirmed=self.has_been_confirmed or self.source_confirmation
            self.confirmation={"status":"CONDITIONAL_CONFIRMED" if self.source_confirmation else "UNCONFIRMED",
                               "center_xy":xy[ix].tolist(),"radius":self.cfg.confirmation_radius,
                               "posterior_mass":float(region_mass[ix]),
                               "scope":"specified finite domain and raw model only",
                               "calibrated_frequentist_error_rate":None}
        else:
            self.confirmation={"status":"REVOKED" if self.has_been_confirmed else "UNCONFIRMED",
                               "reason":"Missing rule, domain coverage, time or model qualification"}
        self.confirmation_events.append(dict(self.confirmation))
        return self.confirmation

    def _encode_decode(self):
        if not self.control_window:
            return None,None
        f=self.last_frame
        gain=np.array([s.gain for s in self.specs])
        bias=np.array([s.background for s in self.specs])
        raw=np.stack([x.raw for x in self.control_window])
        excess=(raw-bias[None,:])/gain[None,:]
        y=np.where(self.fixed_mask[None,:],np.maximum(excess,0),0)
        totals=y.sum(axis=1)
        if totals[-1] <= self.cfg.contact_threshold:
            return None,None
        invalid=np.flatnonzero(totals <= self.cfg.contact_threshold)
        start=int(invalid[-1]+1) if len(invalid) else 0
        beta=0.0 if self.mode=="no_history" else self.cfg.beta
        chi=odor_memory(y[start:],beta=beta)
        e=encode(f.positions[:,:2],(f.ambient_wind-f.velocity)[:,:2],chi,quality=self.fixed_mask,
                 scale_m=self.cfg.scale_m,flow_floor=self.cfg.flow_floor)
        d=decode(e,speed_contact=self.cfg.speed_contact,speed_flow=self.cfg.speed_flow,
                 damping_t=self.cfg.damping_t,speed_reconfigure=self.cfg.speed_reconfigure,
                 ridge_r=self.cfg.ridge_r)
        if self.mode=="merged_r":d["relative"]=decode_merged(e,self.cfg.speed_reconfigure,self.cfg.ridge_r)
        if self.mode=="t_only":d["relative"]=np.zeros_like(d["relative"])
        if self.mode=="r_only":d["translation"]=np.zeros_like(d["translation"])
        if self.mode=="no_polarity_t":
            d["translation"]=self.cfg.speed_contact*d["first_contact"]/(self.cfg.damping_t+e["inward"].sum()+e["outward"].sum())
        return e,d

    def _anchors(self,e,d):
        f=self.last_frame
        n=len(self.ids)
        valid=f.instrument_valid
        def qualified_upwind():
            if not np.any(valid):
                return np.zeros((n,2))
            w=f.ambient_wind[valid,:2].mean(axis=0)
            v=-self.cfg.catalog_speed*w/max(np.linalg.norm(w),1e-15)
            return np.tile(v,(n,1))
        if self.mode in {"m1_full","no_history","merged_r","t_only","r_only","no_polarity_t"}:
            T=np.tile(d["translation"],(n,1));R=d["relative"]
            return [T,R,T+R]
        if self.mode=="upwind":
            return [qualified_upwind()]
        if self.mode=="ordinary_array":
            delta=f.positions[:,:2]-f.positions[:,:2].mean(axis=0)
            r=self.cfg.catalog_speed*delta/max(np.linalg.norm(delta,axis=1).max(),1e-15)
            return [r]
        if self.mode=="gradient":
            gain=np.array([s.gain for s in self.specs]);bias=np.array([s.background for s in self.specs])
            c=(f.raw[valid]-bias[valid])/gain[valid]
            X=np.column_stack([np.ones(np.count_nonzero(valid)),f.positions[valid,:2]])
            if len(X)<3 or np.linalg.matrix_rank(X)<3:
                self.baseline_fallback="GRADIENT_RANK_DEFICIENT_TO_QUALIFIED_UPWIND"
                return [qualified_upwind()]
            grad=np.linalg.lstsq(X,c,rcond=None)[0][1:]
            v=self.cfg.catalog_speed*grad/max(np.linalg.norm(grad),1e-15)
            return [np.tile(v,(n,1))]
        return []

    def _shortlist(self,catalog,e,d):
        K=min(self.cfg.K,len(catalog))
        if K==len(catalog):
            return sorted(catalog,key=lambda a:a.semantic_id)
        if self.mode=="information_uniform":
            # Broad deterministic direction/shape coverage; no source truth or
            # posterior-dependent cheap preview is hidden outside the K budget.
            order=sorted(catalog,key=lambda a:a.semantic_id)
            ix=np.linspace(0,len(order)-1,K,dtype=int)
            return [order[i] for i in ix]
        anchors=self._anchors(e,d)
        def key(a):
            distance=min(float(np.mean(np.sum((a.velocities[:,:2]-x)**2,axis=1))) for x in anchors)
            return distance,a.semantic_id
        return sorted(catalog,key=key)[:K]

    def _score(self, candidate):
        model=self.posterior.model
        future=model.predict(candidate)
        sigma=np.array([s.sigma for s in self.specs])
        whitened=(future/sigma[None,None,:]).reshape(len(model.bank.theta),-1)
        # Same nuisance row carries the entire observed history and future.
        allmean=np.concatenate(model.history_whitened+[whitened],axis=1)
        source=model.bank.theta[:,:2]
        best=np.inf; pairs=0
        active=np.flatnonzero(model.bank.prior>0)
        for ii,i in enumerate(active):
            for j in active[:ii]:
                if np.linalg.norm(source[i]-source[j])>=self.cfg.source_tolerance:
                    pairs+=1
                    best=min(best,float(np.linalg.norm(allmean[i]-allmean[j])))
        separation=0.0 if pairs==0 else best
        if self.cfg.score_kind=="min_separation":
            value=separation
        else:
            value=self._xy_eig(whitened)
        path=float(candidate.duration*np.linalg.norm(candidate.velocities,axis=1).sum())
        return {"score":value-self.cfg.path_penalty*path,
                "bank_separation":separation,"pair_count":pairs,
                "continuous_source_certificate":GateStatus.UNKNOWN.value,
                "source_confirmation":False}

    def _xy_eig(self, means):
        """Finite-MC XY EIG over the stated bank, with fixed common samples.

        All heights/strengths are marginalized before entropy. Finite MC may
        yield a negative estimate and is intentionally not clipped.
        """
        rng=np.random.default_rng(self.cfg.seed+len(self.decisions))
        w=self.posterior.mass
        draws=rng.choice(len(w),size=self.cfg.eig_samples,p=w)
        y=means[draws]+rng.normal(size=(self.cfg.eig_samples,means.shape[1]))
        ll=-0.5*np.sum((y[:,None,:]-means[None,:,:])**2,axis=2)
        with np.errstate(divide="ignore"):ll+=np.log(w)[None,:]
        ll-=ll.max(axis=1,keepdims=True)
        conditional=np.exp(ll);conditional/=conditional.sum(axis=1,keepdims=True)
        xy,group=self.posterior.model.bank.xy_groups
        p0=np.bincount(group,weights=w,minlength=len(xy))
        pp=np.zeros((len(y),len(xy)))
        for i,g in enumerate(group):pp[:,g]+=conditional[:,i]
        def entropy(p):return -np.sum(p*np.log(np.maximum(p,1e-300)),axis=-1)
        return float(entropy(p0)-entropy(pp).mean())

    def _fallback(self,catalog,stage):
        # Coverage is a shared map-relative deterministic survey direction,
        # independent of source truth and method. Every branch passes safety.
        order=sorted(catalog,key=lambda a:(not a.semantic_id.endswith("R00"),a.semantic_id))
        moving=[a for a in order if np.linalg.norm(a.velocities)>1e-12]
        if stage=="REMEASURE":
            order=sorted(order,key=lambda a:(np.linalg.norm(a.velocities),a.semantic_id))
        elif moving:
            j=len(self.decisions)%len(moving)
            order=moving[j:]+moving[:j]+[a for a in order if np.linalg.norm(a.velocities)<=1e-12]
        for a in order:
            if self.safety.legal(self.last_frame.positions,a):return a
        raise RuntimeError("No safe reference action, including hold; flight supervisor required")

    def decide(self):
        if self.last_frame is None:
            raise ValueError("Observe an initial raw block before deciding")
        self.posterior.assert_same_model()
        f=self.last_frame
        self.baseline_fallback=None
        if f.t-self.start_time >= self.cfg.budget_s-1e-12:
            return None,{"stage":"STOP_BUDGET","source_confirmation":self.source_confirmation}
        remaining=self.cfg.budget_s-(f.t-self.start_time)
        if remaining+1e-12<self.cfg.action_s:
            return None,{"stage":"STOP_PARTIAL_HORIZON","source_confirmation":False}
        catalog=common_catalog(self.ids,f.positions,self.cfg,self.specs)
        is_m1=self.mode in {"m1_full","no_history","merged_r","t_only","r_only","no_polarity_t"}
        e,d=self._encode_decode() if is_m1 else (None,None)
        gain=np.array([s.gain for s in self.specs]);bias=np.array([s.background for s in self.specs])
        contact=float(np.sum(np.where(f.instrument_valid,np.maximum((f.raw-bias)/gain,0),0)))
        if contact<=self.cfg.contact_threshold:
            stage="COVER";choice=self._fallback(catalog,stage);score=None;short=[]
        elif f.qualifications.time.status != GateStatus.PASS or (is_m1 and e is None):
            stage="REMEASURE" if self.remeasure_used+self.cfg.action_s<=self.cfg.remeasure_limit_s+1e-12 else "COVER_TIME_UNKNOWN"
            if stage=="REMEASURE":self.remeasure_used+=self.cfg.action_s
            choice=self._fallback(catalog,stage);score=None;short=[]
        elif f.qualifications.model.status == GateStatus.FAIL:
            stage="COVER_MODEL_FAIL";choice=self._fallback(catalog,stage);score=None;short=[]
        else:
            safe=[a for a in catalog if self.safety.legal(f.positions,a)]
            if not safe:raise RuntimeError("No safe candidate")
            short=self._shortlist(safe,e,d)
            scored=[(self._score(a),a) for a in short]
            score,choice=min(scored,key=lambda z:(-z[0]["score"],z[1].semantic_id))
            stage="M1_TENTATIVE" if f.qualifications.model.status==GateStatus.UNKNOWN else "MODEL_CONDITIONAL"
        record={"decision":len(self.decisions),"time":f.t,"stage":stage,
                "candidate":choice.semantic_id,"catalog_count":len(catalog),
                "scored_count":len(short),"score":score,
                "qualifications":{name:getattr(f.qualifications,name).status.value
                                  for name in ["time","shape","coherence","model"]},
                "source_confirmation":self.source_confirmation,
                "baseline_fallback":self.baseline_fallback,
                "confirmation":dict(self.confirmation),"safe_under_reference_model":True}
        actual_relative=choice.velocities[:,:2]-choice.velocities[:,:2].mean(axis=0)
        record.update({"command_velocity_by_canonical_id":choice.velocities.tolist(),
                       "command_sensor_ids":list(choice.sensor_ids),
                       "common_scale":choice.common_scale,
                       "actual_relative_rank":int(np.linalg.matrix_rank(actual_relative))})
        if d is not None:
            anchors=self._anchors(e,d)
            record["m1_translation"]=d["translation"].tolist()
            record["m1_relative"]=d["relative"].tolist()
            record["m1_relative_rank"]=int(np.linalg.matrix_rank(d["relative"]))
            record["catalog_projection_mean_square_error"]=min(float(np.mean(np.sum((choice.velocities[:,:2]-x)**2,axis=1))) for x in anchors)
        self.decisions.append(record)
        return choice,record

    def execute_and_update(self, world, candidate):
        if candidate is None:return self.posterior.xy_probability()
        if not self.safety.legal(self.last_frame.positions,candidate.ordered(self.ids)):
            raise RuntimeError("Final safety check failed")
        block=world.execute(candidate)
        # Actual path, not commanded endpoint, drives the sensor prediction.
        return self.observe(block)


class ReferenceWorld:
    """Separate truth/measurement object, unavailable to candidate scoring.

    Used only for mathematical/software certificates of the explicit Green/ZOH
    reference. Noise is keyed by physical ID and world sample index, so row
    storage order does not alter measurements. It is not a native plume dataset.
    """
    def __init__(self, truth, specs, positions, *, seed=1, qualifiers=None, **model_args):
        bank=SourceBank(np.vstack([truth,truth]),np.array([0.5,0.5]))
        self.model=GreenZOHModel(bank,specs,positions,**model_args)
        self.seed=int(seed)
        self.sample_index=0
        self.block_index=0
        self.qualifications=qualifiers or Qualifications(
            time=Gate(GateStatus.PASS,"Exact declared ZOH clocks","reference-model"),
            shape=Gate(),
            coherence=Gate(GateStatus.PASS,"One specified pulse","reference-model"),
            model=Gate(GateStatus.PASS,"Exact specified finite reference model","reference-model"))

    def execute(self,candidate,*,fraction=1.0, output_order=None):
        a=candidate.ordered(self.model.ids)
        steps=int(round(a.duration/self.model.dt))
        if steps<1 or not 0<fraction<=1:raise ValueError("Invalid execution interval")
        steps=max(1,int(np.floor(steps*fraction)))
        frames=[]
        for _ in range(steps):
            m=self.model
            newp=m.positions+m.dt*a.velocities
            z,hist,mu=m._advance(m.z,m.delay_history,m.positions,newp,m.t,m.t+m.dt)
            self.sample_index+=1
            noise=[]
            for sensor in m.specs:
                key=f"{self.seed}:{self.sample_index}:{sensor.physical_id}".encode()
                seed=int.from_bytes(sha256(key).digest()[:8],"little")
                noise.append(np.random.default_rng(seed).normal()*sensor.sigma)
            raw=mu[0]+np.array(noise)
            f=RawFrame(f"sample-{self.sample_index:08d}",m.t+m.dt,m.ids,newp,a.velocities,
                       np.tile(m.wind,(len(m.ids),1)),raw,np.ones(len(m.ids),bool),self.qualifications)
            m.z,m.delay_history,m.positions,m.t=z,hist,newp,m.t+m.dt
            frames.append(f if output_order is None else f.ordered(tuple(output_order)))
        self.block_index+=1
        return RawBlock(f"block-{self.block_index:08d}",tuple(frames))
