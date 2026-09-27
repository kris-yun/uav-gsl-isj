"""Controlled Python reference for the delayed MCOS window model.

This module mirrors ``MCOSWindowModel.hpp`` for contract tests and small-scale
method development.  Its local anisotropic kernel is a declared G4 control
model, not a universal turbulent-plume attribution model.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


TARGET_SCALES = np.array([1.0, 1.0, 0.8, 0.2], dtype=float)


def interpolate(times, positions, winds, query):
    if query <= times[0]:
        return positions[0], winds[0]
    if query >= times[-1]:
        return positions[-1], winds[-1]
    upper = int(np.searchsorted(times, query, side="left"))
    lower = upper - 1
    weight = (query - times[lower]) / (times[upper] - times[lower])
    return (
        (1.0 - weight) * positions[lower] + weight * positions[upper],
        (1.0 - weight) * winds[lower] + weight * winds[upper],
    )


def plume(position, wind, parameters):
    source = parameters[:2]
    amplitude, baseline = parameters[2:4]
    relative = position - source
    wind_speed = np.linalg.norm(wind)
    if wind_speed < 0.05:
        inverse_variance = 1.0 / 1.5**2
        kernel = np.exp(-0.5 * inverse_variance * relative @ relative)
        source_derivative = kernel * inverse_variance * relative
    else:
        wind_direction = wind / wind_speed
        parallel = relative @ wind_direction
        perpendicular = relative - parallel * wind_direction
        parallel_inverse_variance = 1.0 / 2.0**2
        perpendicular_inverse_variance = 1.0 / 0.8**2
        gaussian = np.exp(-0.5 * (
            parallel**2 * parallel_inverse_variance
            + perpendicular @ perpendicular * perpendicular_inverse_variance
        ))
        gate = 1.0 / (1.0 + np.exp(-np.clip(parallel / 0.35, -60.0, 60.0)))
        kernel = gaussian * gate
        precision_relative = (
            parallel * parallel_inverse_variance * wind_direction
            + perpendicular_inverse_variance * perpendicular
        )
        source_derivative = kernel * (
            precision_relative - (1.0 - gate) / 0.35 * wind_direction
        )
    return amplitude * kernel + baseline, amplitude * source_derivative, kernel


def evaluate(times, positions, winds, parameters):
    """Return prediction and analytic Jacobian in the fixed seven-column order."""
    times = np.asarray(times, dtype=float)
    positions = np.asarray(positions, dtype=float)
    winds = np.asarray(winds, dtype=float)
    parameters = np.asarray(parameters, dtype=float)
    if times.ndim != 1 or times.size < 2:
        raise ValueError("at least two one-dimensional timestamps are required")
    if positions.shape != (times.size, 2) or winds.shape != (times.size, 2):
        raise ValueError("position and wind arrays must have shape (N, 2)")
    if parameters.shape != (7,):
        raise ValueError("parameter order is sx, sy, A, b, tau, d, z0")
    if parameters[2] < 0.0 or parameters[4] <= 0.0 or parameters[5] < 0.0:
        raise ValueError("amplitude, time constant or dead time is invalid")

    count = times.size
    predictions = np.zeros(count)
    jacobian = np.zeros((count, 7))
    predictions[0] = parameters[6]
    jacobian[0, 6] = 1.0
    state = predictions[0]
    sensitivity = jacobian[0].copy()
    tau, delay = parameters[4], parameters[5]
    for index in range(1, count):
        dt = times[index] - times[index - 1]
        if dt <= 0.0:
            raise ValueError("timestamps must be strictly increasing")
        query = times[index] - 0.5 * dt - delay
        position, wind = interpolate(times, positions, winds, query)
        forcing, source_derivative, kernel = plume(position, wind, parameters)
        forcing_sensitivity = np.zeros(7)
        forcing_sensitivity[:2] = source_derivative
        forcing_sensitivity[2] = kernel
        forcing_sensitivity[3] = 1.0
        left = max(times[0], query - 0.01)
        right = min(times[-1], query + 0.01)
        if right - left > 1e-12:
            left_cov = interpolate(times, positions, winds, left)
            right_cov = interpolate(times, positions, winds, right)
            left_forcing = plume(*left_cov, parameters)[0]
            right_forcing = plume(*right_cov, parameters)[0]
            forcing_sensitivity[5] = -(right_forcing - left_forcing) / (
                right - left
            )
        alpha = np.exp(-dt / tau)
        alpha_tau = alpha * dt / tau**2
        previous_state = state
        previous_sensitivity = sensitivity.copy()
        state = alpha * previous_state + (1.0 - alpha) * forcing
        sensitivity = (
            alpha * previous_sensitivity
            + (1.0 - alpha) * forcing_sensitivity
        )
        sensitivity[4] += alpha_tau * (previous_state - forcing)
        predictions[index] = state
        jacobian[index] = sensitivity
    return predictions, jacobian


def nuisance_design(times, positions, winds, target):
    """Exact linear design for nuisance coefficients [amplitude, baseline, z0]."""
    times = np.asarray(times, dtype=float)
    positions = np.asarray(positions, dtype=float)
    winds = np.asarray(winds, dtype=float)
    sx, sy, tau, delay = np.asarray(target, dtype=float)
    if tau <= 0.0 or delay < 0.0:
        raise ValueError("time constant and dead time must be feasible")
    design = np.zeros((times.size, 3))
    design[0, 2] = 1.0
    unit_parameters = np.array([sx, sy, 1.0, 0.0, tau, delay, 0.0])
    for index in range(1, times.size):
        dt = times[index] - times[index - 1]
        query = times[index] - 0.5 * dt - delay
        position, wind = interpolate(times, positions, winds, query)
        kernel = plume(position, wind, unit_parameters)[2]
        alpha = np.exp(-dt / tau)
        design[index, 0] = alpha * design[index - 1, 0] + (1.0 - alpha) * kernel
        design[index, 1] = alpha * design[index - 1, 1] + (1.0 - alpha)
        design[index, 2] = alpha * design[index - 1, 2]
    return design


def transport_nuisance_design(times, positions, winds, target, frequencies):
    """Linearized plume-modulation/meander nuisance dictionary.

    The first three columns remain [amplitude, baseline, z0].  For each fixed
    angular frequency, six columns are appended: kernel sin/cos modulation,
    source-x-gradient sin/cos and source-y-gradient sin/cos.  Every forcing
    column is passed through the same candidate FOPDT dynamics.
    """
    frequencies = tuple(float(value) for value in frequencies)
    if not frequencies:
        return nuisance_design(times, positions, winds, target)
    times = np.asarray(times, dtype=float)
    positions = np.asarray(positions, dtype=float)
    winds = np.asarray(winds, dtype=float)
    sx, sy, tau, delay = np.asarray(target, dtype=float)
    column_count = 3 + 6 * len(frequencies)
    design = np.zeros((times.size, column_count))
    design[0, 2] = 1.0
    unit_parameters = np.array([sx, sy, 1.0, 0.0, tau, delay, 0.0])
    for index in range(1, times.size):
        dt = times[index] - times[index - 1]
        query = times[index] - 0.5 * dt - delay
        position, wind = interpolate(times, positions, winds, query)
        _, source_derivative, kernel = plume(position, wind, unit_parameters)
        forcing = np.zeros(column_count)
        forcing[0] = kernel
        forcing[1] = 1.0
        for frequency_index, frequency in enumerate(frequencies):
            sine = np.sin(frequency * query)
            cosine = np.cos(frequency * query)
            start = 3 + 6 * frequency_index
            forcing[start:start + 6] = (
                kernel * sine,
                kernel * cosine,
                source_derivative[0] * sine,
                source_derivative[0] * cosine,
                source_derivative[1] * sine,
                source_derivative[1] * cosine,
            )
        alpha = np.exp(-dt / tau)
        design[index] = alpha * design[index - 1] + (1.0 - alpha) * forcing
    return design


@dataclass(frozen=True)
class InformationThresholds:
    minimum_profiled_eigenvalue: float = 1e-10
    minimum_normalized_sigma: float = 1e-3
    minimum_source_rank: int = 2


@dataclass(frozen=True)
class SourceInformationThresholds:
    minimum_whitened_eigenvalue: float = 1.0
    minimum_normalized_sigma: float = 0.1


def calibrated_memory_source_certificate(
    jacobian,
    measurement_variance,
    thresholds=SourceInformationThresholds(),
):
    """Source-only certificate when tau and dead time are treated as known.

    This is the deliberately strong source-only OED baseline: gain, baseline
    and initial sensor state are profiled, but the local memory columns are not.
    It can therefore certify source geometry even when source and memory are not
    jointly distinguishable.  ``source_profiled_certificate`` is the stricter
    MCOS declaration because it also profiles tau and dead-time directions.
    """
    if not np.isfinite(measurement_variance) or measurement_variance <= 0.0:
        raise ValueError("measurement variance must be positive")
    jacobian = np.asarray(jacobian, dtype=float)
    if jacobian.ndim != 2 or jacobian.shape[1] != 7:
        raise ValueError("window Jacobian must have seven columns")
    source = jacobian[:, :2]
    nuisance = jacobian[:, [2, 3, 6]]
    projected = source - nuisance @ np.linalg.lstsq(
        nuisance, source, rcond=None
    )[0]
    whitened = projected / np.sqrt(measurement_variance)
    information = whitened.T @ whitened
    information = 0.5 * (information + information.T)
    eigenvalues = np.linalg.eigvalsh(information)
    clipped = np.maximum(eigenvalues, np.finfo(float).tiny)
    lambda_min = max(0.0, float(eigenvalues[0]))
    rank = int(np.linalg.matrix_rank(information, tol=1e-10))
    norms = np.linalg.norm(whitened, axis=0)
    normalized_sigma = 0.0
    if np.all(norms > 1e-14):
        normalized_sigma = float(np.linalg.svd(
            whitened / norms, compute_uv=False
        )[-1])
    identifiable = (
        rank == 2
        and lambda_min >= thresholds.minimum_whitened_eigenvalue
        and normalized_sigma >= thresholds.minimum_normalized_sigma
    )
    return {
        "source_rank": rank,
        "lambda_min_whitened": lambda_min,
        "lambda_max_whitened": max(0.0, float(eigenvalues[-1])),
        "logdet_information": float(np.sum(np.log(clipped))),
        "normalized_sigma_min": normalized_sigma,
        "worst_axis_std_proxy_m": (
            1.0 / np.sqrt(lambda_min) if lambda_min > 0.0 else float("inf")
        ),
        "identifiable": identifiable,
        "decision": "estimate" if identifiable else "not_identifiable_yet",
        "certificate_basis": (
            "source-only information with calibrated tau/dead time and "
            "profiled gain/baseline/initial state"
        ),
    }


def information_certificate(jacobian, thresholds=InformationThresholds()):
    target = jacobian[:, [0, 1, 4, 5]] * TARGET_SCALES
    nuisance = jacobian[:, [2, 3, 6]]
    projected = target - nuisance @ np.linalg.lstsq(
        nuisance, target, rcond=None
    )[0]
    information = projected.T @ projected
    information = 0.5 * (information + information.T)
    eigenvalues = np.linalg.eigvalsh(information)
    source = information[:2, :2]
    source_rank = int(np.linalg.matrix_rank(source, tol=1e-10))
    memory_information = max(0.0, float(information[2, 2]))
    schur = 0.0
    if source_rank == 2:
        coupling = information[:2, 2]
        schur = max(0.0, float(
            memory_information - coupling @ np.linalg.solve(source, coupling)
        ))
    norms = np.linalg.norm(projected, axis=0)
    normalized_sigma = 0.0
    if np.all(norms > 1e-14):
        normalized_sigma = float(np.linalg.svd(
            projected / norms, compute_uv=False
        )[-1])
    lambda_min = max(0.0, float(eigenvalues[0]))
    identifiable = (
        source_rank >= thresholds.minimum_source_rank
        and lambda_min >= thresholds.minimum_profiled_eigenvalue
        and normalized_sigma >= thresholds.minimum_normalized_sigma
    )
    return {
        "lambda_min": lambda_min,
        "lambda_max": max(0.0, float(eigenvalues[-1])),
        "source_rank": source_rank,
        "memory_information": memory_information,
        "schur_excitation": schur,
        "r_tau": schur / memory_information if memory_information > 0.0 else 0.0,
        "normalized_sigma_min": normalized_sigma,
        "identifiable": identifiable,
        "decision": "estimate" if identifiable else "not_identifiable_yet",
    }


def source_profiled_certificate(
    jacobian,
    measurement_variance,
    thresholds=SourceInformationThresholds(),
):
    """Source-only information after profiling gain, offset, memory and z0.

    This separates the primary localization claim from the stronger claim that
    source position, time constant and dead time are jointly identifiable.
    """
    if not np.isfinite(measurement_variance) or measurement_variance <= 0.0:
        raise ValueError("measurement variance must be positive")
    source = jacobian[:, :2]
    nuisance = jacobian[:, [2, 3, 4, 5, 6]]
    projected = source - nuisance @ np.linalg.lstsq(
        nuisance, source, rcond=None
    )[0]
    whitened = projected / np.sqrt(measurement_variance)
    information = whitened.T @ whitened
    information = 0.5 * (information + information.T)
    eigenvalues = np.linalg.eigvalsh(information)
    lambda_min = max(0.0, float(eigenvalues[0]))
    rank = int(np.linalg.matrix_rank(information, tol=1e-10))
    norms = np.linalg.norm(whitened, axis=0)
    normalized_sigma = 0.0
    if np.all(norms > 1e-14):
        normalized_sigma = float(np.linalg.svd(
            whitened / norms, compute_uv=False
        )[-1])
    worst_axis_std = (
        1.0 / np.sqrt(lambda_min) if lambda_min > 0.0 else float("inf")
    )
    identifiable = (
        rank == 2
        and lambda_min >= thresholds.minimum_whitened_eigenvalue
        and normalized_sigma >= thresholds.minimum_normalized_sigma
    )
    return {
        "source_rank": rank,
        "lambda_min_whitened": lambda_min,
        "lambda_max_whitened": max(0.0, float(eigenvalues[-1])),
        "normalized_sigma_min": normalized_sigma,
        "worst_axis_std_proxy_m": worst_axis_std,
        "identifiable": identifiable,
        "decision": "estimate" if identifiable else "not_identifiable_yet",
    }


def reduced_target_certificate(
    profiled_residual_jacobian,
    measurement_variance,
    thresholds=InformationThresholds(),
):
    """Joint certificate from a residual Jacobian after nuisance optimization."""
    jacobian = np.asarray(profiled_residual_jacobian, dtype=float)
    if jacobian.ndim != 2 or jacobian.shape[1] != 4:
        raise ValueError("reduced target Jacobian must have four columns")
    scaled = jacobian * TARGET_SCALES / np.sqrt(measurement_variance)
    information = scaled.T @ scaled
    information = 0.5 * (information + information.T)
    eigenvalues = np.linalg.eigvalsh(information)
    norms = np.linalg.norm(scaled, axis=0)
    normalized_sigma = 0.0
    if np.all(norms > 1e-14):
        normalized_sigma = float(np.linalg.svd(
            scaled / norms, compute_uv=False
        )[-1])
    lambda_min = max(0.0, float(eigenvalues[0]))
    identifiable = (
        lambda_min >= thresholds.minimum_profiled_eigenvalue
        and normalized_sigma >= thresholds.minimum_normalized_sigma
    )
    return {
        "lambda_min": lambda_min,
        "lambda_max": max(0.0, float(eigenvalues[-1])),
        "normalized_sigma_min": normalized_sigma,
        "identifiable": identifiable,
        "decision": "estimate" if identifiable else "not_identifiable_yet",
        "certificate_basis": "numerical residual Jacobian after nuisance optimization",
    }


def reduced_source_certificate(
    profiled_residual_jacobian,
    measurement_variance,
    thresholds=SourceInformationThresholds(),
):
    """Source certificate after profiling reduced tau/dead-time directions."""
    jacobian = np.asarray(profiled_residual_jacobian, dtype=float)
    source = jacobian[:, :2]
    memory = jacobian[:, 2:4]
    source = source - memory @ np.linalg.lstsq(memory, source, rcond=None)[0]
    whitened = source / np.sqrt(measurement_variance)
    information = whitened.T @ whitened
    information = 0.5 * (information + information.T)
    eigenvalues = np.linalg.eigvalsh(information)
    lambda_min = max(0.0, float(eigenvalues[0]))
    norms = np.linalg.norm(whitened, axis=0)
    normalized_sigma = 0.0
    if np.all(norms > 1e-14):
        normalized_sigma = float(np.linalg.svd(
            whitened / norms, compute_uv=False
        )[-1])
    rank = int(np.linalg.matrix_rank(information, tol=1e-10))
    identifiable = (
        rank == 2
        and lambda_min >= thresholds.minimum_whitened_eigenvalue
        and normalized_sigma >= thresholds.minimum_normalized_sigma
    )
    return {
        "source_rank": rank,
        "lambda_min_whitened": lambda_min,
        "lambda_max_whitened": max(0.0, float(eigenvalues[-1])),
        "normalized_sigma_min": normalized_sigma,
        "worst_axis_std_proxy_m": (
            1.0 / np.sqrt(lambda_min) if lambda_min > 0.0 else float("inf")
        ),
        "identifiable": identifiable,
        "decision": "estimate" if identifiable else "not_identifiable_yet",
        "certificate_basis": (
            "numerical residual Jacobian after linear/dynamic nuisance optimization"
        ),
    }


RESEARCH_BOUNDARY = (
    "authorized academic low-altitude gas-sensing/ROS2 simulation only; "
    "no intrusion, vulnerability exploitation, malware, or real-network testing"
)
