"""Bounded variable-projection estimator for the controlled MCOS window model."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.optimize import least_squares, lsq_linear

from mcos_window_reference import (
    evaluate,
    information_certificate,
    nuisance_design,
    reduced_source_certificate,
    reduced_target_certificate,
    source_profiled_certificate,
    transport_nuisance_design,
)


@dataclass(frozen=True)
class EstimatorConfig:
    tau_grid_s: tuple[float, ...] = (0.4, 1.2, 4.0)
    delay_grid_s: tuple[float, ...] = (0.0, 0.4, 0.8)
    source_margin_m: float = 1.5
    tau_bounds_s: tuple[float, float] = (0.2, 6.0)
    delay_bounds_s: tuple[float, float] = (0.0, 1.2)
    maximum_function_evaluations: int = 180
    near_optimal_relative_cost: float = 0.02
    measurement_noise_std_ppm: float = 0.005
    maximum_reduced_chi_square: float = 4.0
    maximum_abs_lag1_residual_correlation: float = 0.5
    transport_nuisance_frequencies_rad_s: tuple[float, ...] = ()
    transport_nuisance_coefficient_bound: float = 2.0
    transport_nuisance_ridge: float = 0.01


@dataclass(frozen=True)
class WindowEstimate:
    parameters: np.ndarray
    target: np.ndarray
    nuisance: np.ndarray
    residual_sum_squares: float
    source_spread_m: float
    target_spread_scaled: float
    starts: int
    converged_starts: int
    near_optimal_starts: int
    certificate: dict
    source_certificate: dict
    joint_decision: str
    decision: str


def _profiled_residual_jacobian(
    times, positions, winds, gas, target, lower, upper, config
):
    base = _fit_nuisance(
        times, positions, winds, gas, target, config
    )[1]
    jacobian = np.zeros((gas.size, 4))
    nominal_steps = np.array([1e-4, 1e-4, 1e-4, 1e-4])
    for column, nominal in enumerate(nominal_steps):
        step = nominal * max(1.0, abs(float(target[column])))
        can_minus = target[column] - step >= lower[column]
        can_plus = target[column] + step <= upper[column]
        if can_minus and can_plus:
            plus = target.copy()
            minus = target.copy()
            plus[column] += step
            minus[column] -= step
            plus_residual = _fit_nuisance(
                times, positions, winds, gas, plus, config
            )[1]
            minus_residual = _fit_nuisance(
                times, positions, winds, gas, minus, config
            )[1]
            jacobian[:, column] = (plus_residual - minus_residual) / (2.0 * step)
        elif can_plus:
            plus = target.copy()
            plus[column] += step
            plus_residual = _fit_nuisance(
                times, positions, winds, gas, plus, config
            )[1]
            jacobian[:, column] = (plus_residual - base) / step
        elif can_minus:
            minus = target.copy()
            minus[column] -= step
            minus_residual = _fit_nuisance(
                times, positions, winds, gas, minus, config
            )[1]
            jacobian[:, column] = (base - minus_residual) / step
        else:
            raise ValueError("target bound is narrower than differentiation step")
    return jacobian


def _fit_nuisance(times, positions, winds, gas, target, config):
    design = transport_nuisance_design(
        times,
        positions,
        winds,
        target,
        config.transport_nuisance_frequencies_rad_s,
    )
    coefficient_count = design.shape[1]
    lower = np.full(coefficient_count, -np.inf)
    upper = np.full(coefficient_count, np.inf)
    lower[0] = 0.0
    if coefficient_count > 3:
        bound = config.transport_nuisance_coefficient_bound
        lower[3:] = -bound
        upper[3:] = bound
        ridge = np.sqrt(config.transport_nuisance_ridge)
        penalty = np.zeros((coefficient_count - 3, coefficient_count))
        penalty[:, 3:] = ridge * np.eye(coefficient_count - 3)
        fit_design = np.vstack((design, penalty))
        fit_gas = np.concatenate((gas, np.zeros(coefficient_count - 3)))
    else:
        fit_design = design
        fit_gas = gas
    fit = lsq_linear(
        fit_design,
        fit_gas,
        bounds=(lower, upper),
        lsmr_tol="auto",
    )
    prediction = design @ fit.x
    return fit.x, prediction - gas


def _source_seeds(positions, winds, gas) -> list[np.ndarray]:
    peak = positions[int(np.argmax(gas))]
    center = np.mean(positions, axis=0)
    mean_wind = np.mean(winds, axis=0)
    norm = np.linalg.norm(mean_wind)
    if norm < 1e-9:
        cross = np.array([0.0, 1.0])
    else:
        direction = mean_wind / norm
        cross = np.array([-direction[1], direction[0]])
    raw = [
        center,
        peak,
        peak + cross,
        peak - cross,
        center + cross,
        center - cross,
    ]
    unique = []
    for candidate in raw:
        if not any(np.linalg.norm(candidate - item) < 1e-10 for item in unique):
            unique.append(np.asarray(candidate, dtype=float))
    return unique


def _target_starts(positions, winds, gas, config: EstimatorConfig):
    for source in _source_seeds(positions, winds, gas):
        for tau in config.tau_grid_s:
            for delay in config.delay_grid_s:
                yield np.array([source[0], source[1], tau, delay], dtype=float)


def estimate_window(times, positions, winds, gas, config=EstimatorConfig()):
    """Estimate [sx, sy, A, b, tau, delay, z0] without source-truth input."""
    times = np.asarray(times, dtype=float)
    positions = np.asarray(positions, dtype=float)
    winds = np.asarray(winds, dtype=float)
    gas = np.asarray(gas, dtype=float)
    source_lower = np.min(positions, axis=0) - config.source_margin_m
    source_upper = np.max(positions, axis=0) + config.source_margin_m
    lower = np.array([
        source_lower[0], source_lower[1], config.tau_bounds_s[0],
        config.delay_bounds_s[0],
    ])
    upper = np.array([
        source_upper[0], source_upper[1], config.tau_bounds_s[1],
        config.delay_bounds_s[1],
    ])

    solutions = []
    starts = list(_target_starts(positions, winds, gas, config))
    for initial in starts:
        initial = np.minimum(np.maximum(initial, lower + 1e-9), upper - 1e-9)

        def residual(target):
            return _fit_nuisance(
                times, positions, winds, gas, target, config
            )[1]

        fit = least_squares(
            residual,
            initial,
            bounds=(lower, upper),
            x_scale=np.array([1.0, 1.0, 1.0, 0.2]),
            max_nfev=config.maximum_function_evaluations,
            ftol=1e-10,
            xtol=1e-10,
            gtol=1e-10,
        )
        nuisance, fit_residual = _fit_nuisance(
            times, positions, winds, gas, fit.x, config
        )
        solutions.append({
            "target": fit.x,
            "nuisance": nuisance,
            "cost": float(fit_residual @ fit_residual),
            "success": bool(fit.success),
        })

    best = min(solutions, key=lambda item: item["cost"])
    cost_limit = best["cost"] * (1.0 + config.near_optimal_relative_cost)
    cost_limit += max(1e-12, np.finfo(float).eps * gas.size)
    near = [item for item in solutions if item["cost"] <= cost_limit]
    source_spread = max(
        np.linalg.norm(left["target"][:2] - right["target"][:2])
        for left in near for right in near
    )
    target_scale = np.array([1.0, 1.0, 0.8, 0.2])
    target_spread = max(
        np.linalg.norm((left["target"] - right["target"]) / target_scale)
        for left in near for right in near
    )
    sx, sy, tau, delay = best["target"]
    amplitude, baseline, initial = best["nuisance"][:3]
    parameters = np.array([
        sx, sy, amplitude, baseline, tau, delay, initial
    ])
    _, jacobian = evaluate(times, positions, winds, parameters)
    if config.transport_nuisance_frequencies_rad_s:
        reduced_jacobian = _profiled_residual_jacobian(
            times, positions, winds, gas, best["target"], lower, upper, config
        )
        certificate = reduced_target_certificate(
            reduced_jacobian,
            config.measurement_noise_std_ppm**2,
        )
        source_certificate = reduced_source_certificate(
            reduced_jacobian,
            config.measurement_noise_std_ppm**2,
        )
    else:
        certificate = information_certificate(jacobian)
        source_certificate = source_profiled_certificate(
            jacobian,
            config.measurement_noise_std_ppm**2,
        )
    target_on_boundary = bool(np.any(
        np.minimum(best["target"] - lower, upper - best["target"]) < 1e-5
    ))
    source_on_boundary = bool(np.any(
        np.minimum(
            best["target"][:2] - lower[:2],
            upper[:2] - best["target"][:2],
        ) < 1e-5
    ))
    certificate = dict(certificate)
    certificate["target_on_bound"] = target_on_boundary
    certificate["near_optimal_source_spread_m"] = float(source_spread)
    certificate["near_optimal_target_spread_scaled"] = float(target_spread)
    joint_decision = certificate["decision"]
    if target_on_boundary:
        joint_decision = "not_identifiable_yet"
        certificate["identifiable"] = False
        certificate["decision"] = joint_decision
        certificate["abstention_reason"] = "best target touches search bound"
    source_certificate = dict(source_certificate)
    source_certificate["source_on_bound"] = source_on_boundary
    degrees_of_freedom = max(1, gas.size - 7)
    reduced_chi_square = (
        best["cost"]
        / (degrees_of_freedom * config.measurement_noise_std_ppm**2)
    )
    best_residual = _fit_nuisance(
        times, positions, winds, gas, best["target"], config
    )[1]
    lag1_correlation = 0.0
    if best_residual.size > 2:
        left = best_residual[:-1] - np.mean(best_residual[:-1])
        right = best_residual[1:] - np.mean(best_residual[1:])
        denominator = np.linalg.norm(left) * np.linalg.norm(right)
        if denominator > 1e-15:
            lag1_correlation = float(left @ right / denominator)
    lack_of_fit = bool(
        reduced_chi_square > config.maximum_reduced_chi_square
        or abs(lag1_correlation)
        > config.maximum_abs_lag1_residual_correlation
    )
    source_certificate["reduced_chi_square"] = float(reduced_chi_square)
    source_certificate["lag1_residual_correlation"] = lag1_correlation
    source_certificate["transport_attribution_gate_passes"] = not lack_of_fit
    decision = source_certificate["decision"]
    if source_on_boundary:
        decision = "not_identifiable_yet"
        source_certificate["identifiable"] = False
        source_certificate["decision"] = decision
        source_certificate["abstention_reason"] = (
            "best source position touches search bound"
        )
    elif lack_of_fit:
        decision = "not_identifiable_yet"
        source_certificate["identifiable"] = False
        source_certificate["decision"] = decision
        source_certificate["abstention_reason"] = (
            "residual magnitude/correlation is inconsistent with declared "
            "measurement noise; transport attribution is unresolved"
        )

    return WindowEstimate(
        parameters=parameters,
        target=best["target"],
        nuisance=best["nuisance"],
        residual_sum_squares=best["cost"],
        source_spread_m=float(source_spread),
        target_spread_scaled=float(target_spread),
        starts=len(starts),
        converged_starts=sum(item["success"] for item in solutions),
        near_optimal_starts=len(near),
        certificate=certificate,
        source_certificate=source_certificate,
        joint_decision=joint_decision,
        decision=decision,
    )
