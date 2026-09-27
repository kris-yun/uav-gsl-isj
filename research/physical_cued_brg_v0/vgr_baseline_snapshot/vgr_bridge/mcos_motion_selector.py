"""Exposure-constrained nuisance-profiled motion selector for MCOS controls."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mcos_window_reference import evaluate, information_certificate


@dataclass(frozen=True)
class SelectorConfig:
    lower_quantile: float = 0.20
    minimum_exposure_snr: float = 20.0
    minimum_normalized_sigma: float = 1e-3
    minimum_profiled_eigenvalue: float = 1e-10
    minimum_joint_pass_fraction: float = 0.80


def evaluate_motion_candidate(
    profile,
    winds,
    source_hypotheses_xy_m,
    tau_grid_s,
    delay_grid_s,
    *,
    measurement_noise_std_ppm,
    amplitude=1.3,
    baseline_ppm=0.04,
    initial_state_ppm=0.0,
    config=SelectorConfig(),
):
    """Score one feasible trajectory over posterior hypotheses, never truth."""
    source_hypotheses = np.asarray(source_hypotheses_xy_m, dtype=float)
    if source_hypotheses.ndim != 2 or source_hypotheses.shape[1] != 2:
        raise ValueError("source hypotheses must have shape (N, 2)")
    if measurement_noise_std_ppm <= 0.0:
        raise ValueError("measurement noise scale must be positive")
    exposure_snr = []
    normalized_sigma = []
    lambda_min = []
    joint_pass = []
    for source in source_hypotheses:
        for tau in tau_grid_s:
            for delay in delay_grid_s:
                parameters = np.array([
                    source[0], source[1], amplitude, baseline_ppm,
                    tau, delay, initial_state_ppm,
                ])
                prediction, jacobian = evaluate(
                    profile.time_s,
                    profile.position_xy_m,
                    winds,
                    parameters,
                )
                certificate = information_certificate(jacobian)
                exposure_snr.append(
                    float(np.ptp(prediction) / measurement_noise_std_ppm)
                )
                normalized_sigma.append(certificate["normalized_sigma_min"])
                lambda_min.append(certificate["lambda_min"])
                joint_pass.append(bool(
                    certificate["normalized_sigma_min"]
                    >= config.minimum_normalized_sigma
                    and certificate["lambda_min"]
                    >= config.minimum_profiled_eigenvalue
                ))
    exposure_quantile = float(np.quantile(exposure_snr, config.lower_quantile))
    sigma_quantile = float(np.quantile(normalized_sigma, config.lower_quantile))
    lambda_quantile = float(np.quantile(lambda_min, config.lower_quantile))
    pass_fraction = float(np.mean(joint_pass))
    exposure_passes = exposure_quantile >= config.minimum_exposure_snr
    information_passes = (
        sigma_quantile >= config.minimum_normalized_sigma
        and lambda_quantile >= config.minimum_profiled_eigenvalue
        and pass_fraction >= config.minimum_joint_pass_fraction
    )
    feasible = bool(exposure_passes and information_passes)
    reasons = []
    if not exposure_passes:
        reasons.append("posterior exposure quantile below threshold")
    if not information_passes:
        reasons.append("posterior profiled-information coverage below threshold")
    return {
        "name": profile.name,
        "feasible": feasible,
        "decision": "candidate" if feasible else "reject",
        "rejection_reasons": reasons,
        "exposure_snr_quantile": exposure_quantile,
        "normalized_sigma_quantile": sigma_quantile,
        "profiled_lambda_min_quantile": lambda_quantile,
        "joint_pass_fraction": pass_fraction,
        "selection_score": sigma_quantile if feasible else None,
        "hypothesis_evaluations": len(exposure_snr),
    }


def select_motion(candidates):
    feasible = [candidate for candidate in candidates if candidate["feasible"]]
    if not feasible:
        return {
            "decision": "not_identifiable_yet",
            "selected": None,
            "reason": "no candidate satisfies exposure and information gates",
        }
    selected = max(feasible, key=lambda candidate: candidate["selection_score"])
    return {
        "decision": "select_motion",
        "selected": selected["name"],
        "score": selected["selection_score"],
    }
