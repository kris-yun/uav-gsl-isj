"""Source-response contrast geometry for synchronized paired measurements.

No posterior, source truth, wind oracle, or hidden concentration-map access is
used here. Inputs are training-ensemble predictions at proposed centers.
The first-order response model is a static branch; it is not odor motion.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable

import numpy as np

from .memory import ReturnTube, _vector


@dataclass(frozen=True)
class FormationGeometry:
    """Endpoint geometry and the caller-certified local linearization radius.

    Units must match center_xy and source_gradients. endpoint_legal may add an
    obstacle/reachability test; its output must be one bool per endpoint. Bounds
    alone do not certify a collision-free flight path or simultaneous arrival.
    """

    lower_xy: np.ndarray
    upper_xy: np.ndarray
    min_separation: float
    max_separation: float
    linearization_radius: float | np.ndarray
    endpoint_legal: Callable[[np.ndarray], np.ndarray] | None = None

    def __post_init__(self):
        lower = _vector(self.lower_xy, "lower_xy")
        upper = _vector(self.upper_xy, "upper_xy")
        if np.any(lower >= upper):
            raise ValueError("geometry lower bounds must be below upper bounds")
        if (not np.isfinite(self.min_separation) or not np.isfinite(self.max_separation)
                or self.min_separation <= 0 or self.max_separation < self.min_separation):
            raise ValueError("require 0 < min_separation <= max_separation")
        radius = np.asarray(self.linearization_radius, dtype=float)
        if radius.ndim > 1 or not np.all(np.isfinite(radius)) or np.any(radius <= 0):
            raise ValueError("linearization_radius must be a positive finite scalar or center vector")
        object.__setattr__(self, "lower_xy", lower)
        object.__setattr__(self, "upper_xy", upper)
        object.__setattr__(self, "linearization_radius", radius.copy())


@dataclass(frozen=True)
class PairedAction:
    center_index: int
    center_xy: np.ndarray
    separation: float
    orientation_rad: float
    endpoints_xy: np.ndarray  # plus endpoint first, minus endpoint second
    cost: float


@dataclass(frozen=True)
class FormationDiagnostics:
    actions: tuple[PairedAction, ...]
    pair_indices: np.ndarray  # [P,2], source indices; no cluster allocation
    predicted_even_odd: np.ndarray  # [A,S,2]
    pair_contrast: np.ndarray  # [A,P], raw design distances, not probabilities
    delta_even: np.ndarray  # [A,P]
    delta_odd: np.ndarray  # [A,P]
    in_tube: np.ndarray  # [A]
    eligible_indices: np.ndarray  # action pool for the downstream allocator
    status: str
    rejected_geometry_count: int
    covariance_model: str = "provided_joint_even_odd"
    calibrated_probabilities: bool = False

    @property
    def costs(self) -> np.ndarray:
        return np.asarray([action.cost for action in self.actions])


def _cost_grid(costs, n: int, nd: int, nu: int) -> np.ndarray:
    array = np.asarray(costs, dtype=float)
    if array.ndim == 0:
        result = np.full((n, nd, nu), float(array))
    elif array.shape == (n,):
        result = np.broadcast_to(array[:, None, None], (n, nd, nu))
    elif array.shape == (n, nd, nu):
        result = array
    else:
        raise ValueError("costs must be a scalar, [N], or [N,D,U]")
    if not np.all(np.isfinite(result)) or np.any(result <= 0):
        raise ValueError("each paired-action cost must be finite and positive")
    return result


def score_paired_formations(*, center_xy, source_means, source_gradients,
                            joint_covariance, costs, separations, orientations_rad,
                            geometry: FormationGeometry, ridge_variance: float = 0.0,
                            return_tube: ReturnTube | None = None,
                            contrast_threshold: float = 0.0,
                            gate_pair_indices=None) -> FormationDiagnostics:
    """Enumerate legal pairs and their source-pair contrast matrix.

    center_xy: [N,2]; source_means: [N,S]; source_gradients: [N,S,2].
    joint_covariance: [N,S,2,2], or [N,D,U,S,2,2] when calibration depends
    on separation/orientation. A fixed covariance is a caller-supplied model,
    not a covariance estimated secretly from the held-out world.

    For source j, z_j = (mu_j, d/2 * u.dot(gradient_j)). Each pair distance is
    (z_j-z_k)' (Sigma_j+Sigma_k+ridge*I)^-1 (z_j-z_k). The even component
    is preserved, and no raw/derived feature is counted twice.

    A direction tube restricts the proposal pool only while it contains an
    informative action. Otherwise an informative outside pool is explicitly
    released. With >2 sources, the default gate means *some pair* is separable;
    M3 may supply gate_pair_indices to request a particular challenge. M2
    neither chooses hypothesis clusters nor interprets distances as evidence.
    """
    centers = np.asarray(center_xy, dtype=float)
    means = np.asarray(source_means, dtype=float)
    gradients = np.asarray(source_gradients, dtype=float)
    if centers.ndim != 2 or centers.shape[1] != 2 or centers.shape[0] == 0:
        raise ValueError("center_xy must be nonempty [N,2]")
    n = len(centers)
    if means.ndim != 2 or means.shape[0] != n or means.shape[1] < 2:
        raise ValueError("source_means must be [N,S] with S >= 2")
    ns = means.shape[1]
    if gradients.shape != (n, ns, 2):
        raise ValueError("source_gradients must have shape [N,S,2]")
    if not all(np.all(np.isfinite(arr)) for arr in (centers, means, gradients)):
        raise ValueError("centers and source predictions must be finite")
    ds = np.atleast_1d(np.asarray(separations, dtype=float))
    angles = np.atleast_1d(np.asarray(orientations_rad, dtype=float))
    if ds.ndim != 1 or angles.ndim != 1 or not len(ds) or not len(angles):
        raise ValueError("separations and orientations must be nonempty 1-D arrays")
    if not np.all(np.isfinite(ds)) or np.any(ds <= 0) or not np.all(np.isfinite(angles)):
        raise ValueError("separations must be positive and orientations finite")
    if not np.isfinite(ridge_variance) or ridge_variance < 0:
        raise ValueError("ridge_variance must be finite and nonnegative")
    if not np.isfinite(contrast_threshold) or contrast_threshold < 0:
        raise ValueError("contrast_threshold must be finite and nonnegative")
    radius = np.asarray(geometry.linearization_radius)
    if radius.ndim == 0:
        radius = np.full(n, float(radius))
    if radius.shape != (n,):
        raise ValueError("linearization_radius vector must have one entry per center")
    cost_grid = _cost_grid(costs, n, len(ds), len(angles))
    covariance = np.asarray(joint_covariance, dtype=float)
    fixed_covariance = covariance.shape == (n, ns, 2, 2)
    action_covariance = covariance.shape == (n, len(ds), len(angles), ns, 2, 2)
    if not (fixed_covariance or action_covariance) or not np.all(np.isfinite(covariance)):
        raise ValueError("joint_covariance must be [N,S,2,2] or [N,D,U,S,2,2]")
    if not np.allclose(covariance, covariance.swapaxes(-1, -2), atol=1e-12, rtol=1e-10):
        raise ValueError("joint covariance must be symmetric, including cross-channel terms")
    if np.linalg.eigvalsh(covariance).min() < -1e-12:
        raise ValueError("joint covariance must be positive semidefinite")
    pairs = np.asarray(list(combinations(range(ns), 2)), dtype=int)
    if gate_pair_indices is None:
        gate_pairs = np.arange(len(pairs), dtype=int)
    else:
        raw_indices = np.asarray(gate_pair_indices)
        if raw_indices.ndim != 1 or not len(raw_indices) or not np.issubdtype(raw_indices.dtype, np.integer):
            raise ValueError("gate_pair_indices must be a nonempty integer vector")
        gate_pairs = raw_indices.astype(int)
        if np.any(gate_pairs < 0) or np.any(gate_pairs >= len(pairs)):
            raise ValueError("gate pair index is out of range")

    actions, predicted, contrasts, even_deltas, odd_deltas = [], [], [], [], []
    rejected = 0
    for center_index, center in enumerate(centers):
        for di, separation in enumerate(ds):
            for ui, angle in enumerate(angles):
                unit = np.array([np.cos(angle), np.sin(angle)])
                endpoints = center + np.array([1.0, -1.0])[:, None] * (separation / 2) * unit
                legal = (geometry.min_separation <= separation <= geometry.max_separation
                         and separation / 2 <= radius[center_index] + 1e-12
                         and np.all(endpoints >= geometry.lower_xy - 1e-12)
                         and np.all(endpoints <= geometry.upper_xy + 1e-12))
                if legal and geometry.endpoint_legal is not None:
                    mask = np.asarray(geometry.endpoint_legal(endpoints.copy()))
                    if mask.shape != (2,) or mask.dtype != np.bool_:
                        raise ValueError("endpoint_legal must return a bool array of shape [2]")
                    legal = bool(mask.all())
                if not legal:
                    rejected += 1
                    continue
                z = np.column_stack((means[center_index], separation / 2 * (gradients[center_index] @ unit)))
                cov = covariance[center_index] if fixed_covariance else covariance[center_index, di, ui]
                delta = z[pairs[:, 0]] - z[pairs[:, 1]]
                distance = np.empty(len(pairs))
                for pi, (j, k) in enumerate(pairs):
                    pooled = cov[j] + cov[k] + ridge_variance * np.eye(2)
                    if np.linalg.eigvalsh(pooled).min() <= 0:
                        raise ValueError("pooled covariance is singular; provide calibrated variance or an explicit ridge")
                    distance[pi] = max(0.0, float(delta[pi] @ np.linalg.solve(pooled, delta[pi])))
                actions.append(PairedAction(center_index, center.copy(), float(separation), float(angle),
                                            endpoints, float(cost_grid[center_index, di, ui])))
                predicted.append(z)
                contrasts.append(distance)
                even_deltas.append(delta[:, 0])
                odd_deltas.append(delta[:, 1])
    na, npairs = len(actions), len(pairs)
    z_array = np.asarray(predicted, dtype=float).reshape(na, ns, 2)
    contrast = np.asarray(contrasts, dtype=float).reshape(na, npairs)
    de = np.asarray(even_deltas, dtype=float).reshape(na, npairs)
    do = np.asarray(odd_deltas, dtype=float).reshape(na, npairs)
    if not na:
        return FormationDiagnostics(tuple(), pairs, z_array, contrast, de, do,
                                    np.empty(0, dtype=bool), np.empty(0, dtype=int), "no_legal_actions", rejected)
    action_centers = np.stack([a.center_xy for a in actions])
    inside = return_tube.contains(action_centers) if return_tube is not None else np.ones(na, dtype=bool)
    informative = np.any(contrast[:, gate_pairs] > contrast_threshold, axis=1)
    if return_tube is None:
        eligible = np.flatnonzero(informative)
        status = "static_unconstrained" if len(eligible) else "no_discriminating_action"
    elif np.any(inside & informative):
        eligible = np.flatnonzero(inside & informative)
        status = "inside_tube"
    elif np.any((~inside) & informative):
        eligible = np.flatnonzero((~inside) & informative)
        status = "out_of_tube_retest"
    else:
        eligible = np.empty(0, dtype=int)
        status = "need_outside_proposals" if np.all(inside) else "no_discriminating_action"
    return FormationDiagnostics(tuple(actions), pairs, z_array, contrast, de, do,
                                inside, eligible, status, rejected)


def rank_by_maxmin(result: FormationDiagnostics, *, eligible_only: bool = True) -> np.ndarray:
    """Reference ranking for unit tests, not M3's allocation policy.

    Maximin may tie at zero when each action only separates a subset. The
    caller must then use the full pair matrix, e.g. action-specific clustering.
    """
    indices = result.eligible_indices if eligible_only else np.arange(len(result.actions))
    if not len(indices):
        return np.empty(0, dtype=int)
    score = np.min(result.pair_contrast[indices], axis=1) / result.costs[indices]
    return indices[np.argsort(-score, kind="stable")]
