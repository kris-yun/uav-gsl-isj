#!/usr/bin/env python3
"""Held-out static-acquisition falsification of proper CTPI-G2 M3 H2 EID.

H01 is spent only to fit a two-parameter monotone Bernoulli observation adapter
from frozen M2 normalized concentration to a physical 0.1 ppm GADEN event.
H02/H03 are held out for both adapter validation and the four-policy gate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


EVENT_THRESHOLD_PPM = 0.1
ACTION_COUNT = 32
SOURCE_COUNT = 8
BUDGET = 10
PAIR_TOL = 1.0e-12


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_m3(path: Path):
    spec = importlib.util.spec_from_file_location("ctpi_g2_m3_nonmyopic_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CTPI_G2_M3_IMPORT")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalize_fields(value: np.ndarray) -> np.ndarray:
    fields = np.asarray(value, dtype=np.float64)
    if fields.ndim != 2 or np.any(fields < 0.0) or not np.isfinite(fields).all():
        raise ValueError("CTPI_G2_M3_FIELD_INPUT")
    maximum = np.max(fields, axis=1)
    if np.any(maximum <= 0.0):
        raise ValueError("CTPI_G2_M3_ZERO_M2_FIELD")
    return fields / maximum[:, None]


def sigmoid(value: np.ndarray) -> np.ndarray:
    x = np.asarray(value, dtype=np.float64)
    result = np.empty_like(x)
    positive = x >= 0.0
    result[positive] = 1.0 / (1.0 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    result[~positive] = exp_x / (1.0 + exp_x)
    return result


def fit_logistic_mle(feature: np.ndarray, event: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    x = np.asarray(feature, dtype=np.float64).reshape(-1)
    y = np.asarray(event, dtype=np.float64).reshape(-1)
    if x.shape != y.shape or np.any((x < 0.0) | (x > 1.0)) or not np.all((y == 0.0) | (y == 1.0)):
        raise ValueError("CTPI_G2_M3_CALIBRATION_INPUT")
    event_rate = float(np.mean(y))
    if not 0.0 < event_rate < 1.0:
        raise ValueError("CTPI_G2_M3_CALIBRATION_EVENT_RATE")
    beta = np.asarray([math.log(event_rate / (1.0 - event_rate)), 0.0])
    design = np.column_stack([np.ones_like(x), x])
    converged = False
    for iteration in range(50):
        probability = sigmoid(design @ beta)
        gradient = design.T @ (probability - y)
        weight = np.maximum(probability * (1.0 - probability), 1.0e-12)
        hessian = design.T @ (weight[:, None] * design)
        step = np.linalg.solve(hessian, gradient)
        beta -= step
        if float(np.linalg.norm(step, ord=np.inf)) <= 1.0e-10:
            converged = True
            break
    if not converged or not np.isfinite(beta).all():
        raise RuntimeError("CTPI_G2_M3_CALIBRATION_MLE")
    return beta, {
        "iterations": iteration + 1,
        "event_rate": event_rate,
        "gradient_inf_norm": float(np.linalg.norm(design.T @ (sigmoid(design @ beta) - y), ord=np.inf)),
    }


def loss(probability: np.ndarray, event: np.ndarray) -> tuple[float, float]:
    p = np.clip(np.asarray(probability, dtype=np.float64), 1.0e-12, 1.0 - 1.0e-12)
    y = np.asarray(event, dtype=np.float64)
    return (
        float(np.mean(-(y * np.log(p) + (1.0 - y) * np.log1p(-p)))),
        float(np.mean((p - y) ** 2)),
    )


def calibration_arrays(data: np.lib.npyio.NpzFile) -> tuple[np.ndarray, np.ndarray]:
    feature = normalize_fields(data["numerical_fields"])
    event = np.asarray(data["gaden_peak_fields"], dtype=np.float64) > EVENT_THRESHOLD_PPM
    # [source, member, action] and one shared M2 feature per source/action.
    expanded = np.broadcast_to(feature[:, None, :], event.shape)
    return expanded.reshape(-1), event.reshape(-1)


def farthest_actions(x: np.ndarray, y: np.ndarray, count: int) -> np.ndarray:
    points = np.column_stack([x, y]).astype(np.float64)
    if count > len(points):
        raise ValueError("CTPI_G2_M3_ACTION_COUNT")
    first = int(np.lexsort((points[:, 1], points[:, 0]))[0])
    selected = [first]
    minimum_distance = np.sum((points - points[first]) ** 2, axis=1)
    minimum_distance[first] = -1.0
    while len(selected) < count:
        candidate = int(np.flatnonzero(minimum_distance == np.max(minimum_distance))[0])
        selected.append(candidate)
        minimum_distance = np.minimum(minimum_distance, np.sum((points - points[candidate]) ** 2, axis=1))
        minimum_distance[selected] = -1.0
    return np.asarray(selected, dtype=np.int64)


def frozen_sources(house: str, carriers: np.ndarray, count: int) -> np.ndarray:
    keyed = []
    for index, carrier in enumerate(carriers.astype(str)):
        digest = hashlib.sha256(f"CTPI_G2_M3_HELDOUT_V1:{house}:{carrier}".encode()).hexdigest()
        keyed.append((digest, carrier, index))
    keyed.sort()
    return np.asarray([index for _, _, index in keyed[:count]], dtype=np.int64)


def carrier_coordinates(carriers: np.ndarray, native: np.ndarray,
                        x: np.ndarray, y: np.ndarray) -> np.ndarray:
    import re
    parsed = [tuple(int(v) for v in re.fullmatch(r"quadtree_(\d+)_(\d+)_(\d+)_(\d+)", str(c)).groups())
              for c in carriers]
    nx = max(oi + sx for oi, _, sx, _ in parsed)
    result = np.empty((len(parsed), 2), dtype=np.float64)
    for index, (oi, oj, sx, sy) in enumerate(parsed):
        mask = ((native % nx >= oi) & (native % nx < oi + sx)
                & (native // nx >= oj) & (native // nx < oj + sy))
        if not np.any(mask):
            raise ValueError(f"CTPI_G2_M3_CARRIER_COORDINATE:{carriers[index]}")
        result[index] = [float(np.mean(x[mask])), float(np.mean(y[mask]))]
    return result


def choose_best(score: np.ndarray, allowed: np.ndarray, current_xy: np.ndarray,
                action_xy: np.ndarray) -> int:
    best = float(np.max(score[allowed]))
    tied = allowed & (np.abs(score - best) <= PAIR_TOL)
    distance = np.linalg.norm(action_xy - current_xy[None, :], axis=1)
    shortest = float(np.min(distance[tied]))
    finalists = np.flatnonzero(tied & (np.abs(distance - shortest) <= PAIR_TOL))
    return int(finalists[0])


def update(posterior: np.ndarray, q1: np.ndarray, action: int, observation: int) -> np.ndarray:
    likelihood = q1[action] if observation == 1 else 1.0 - q1[action]
    result = posterior * likelihood
    mass = float(np.sum(result))
    if mass <= 0.0 or not np.isfinite(mass):
        raise RuntimeError("CTPI_G2_M3_UPDATE_MASS")
    return result / mass


def run_policy(module, policy: str, q1: np.ndarray, concentration: np.ndarray,
               outcome: np.ndarray, true_source: int, source_xy: np.ndarray,
               action_xy: np.ndarray, random_seed: int) -> dict[str, Any]:
    posterior = np.full(q1.shape[1], 1.0 / q1.shape[1], dtype=np.float64)
    allowed = np.ones(q1.shape[0], dtype=np.bool_)
    current_xy = action_xy[0].copy()
    rng = np.random.default_rng(random_seed)
    trace = []
    risk_auc = 0.0
    error_auc = 0.0
    travel = 0.0
    for step in range(BUDGET):
        if policy == "random":
            action = int(rng.choice(np.flatnonzero(allowed)))
            scores = np.zeros(len(allowed))
            branch_actions = None
        elif policy == "exploit":
            scores = module.predicted_concentration_exploit_scores(posterior, concentration)
            action = choose_best(scores, allowed, current_xy, action_xy)
            branch_actions = None
        elif policy == "myopic":
            scores = module.myopic_eid(posterior, q1)
            action = choose_best(scores, allowed, current_xy, action_xy)
            branch_actions = None
        elif policy == "h2":
            second = np.broadcast_to(allowed, (len(allowed), len(allowed))).copy()
            result = module.horizon2_eid(posterior, q1, first_feasible=allowed,
                                         second_feasible=second, allow_repeat=False)
            scores = result.value
            action = choose_best(scores, allowed, current_xy, action_xy)
            branch_actions = result.branch_best_action[:, action].tolist()
        else:
            raise ValueError(f"CTPI_G2_M3_POLICY:{policy}")
        step_travel = float(np.linalg.norm(action_xy[action] - current_xy))
        travel += step_travel
        current_xy = action_xy[action].copy()
        observation = int(outcome[action])
        before = posterior.copy()
        posterior = update(posterior, q1, action, observation)
        allowed[action] = False
        risk = 1.0 - float(posterior[true_source])
        estimate = posterior @ source_xy
        error = float(np.linalg.norm(estimate - source_xy[true_source]))
        risk_auc += risk
        error_auc += error
        rank = 1 + int(np.count_nonzero(posterior > posterior[true_source] + PAIR_TOL))
        trace.append({
            "step": step + 1,
            "action_subset_index": action,
            "observation": observation,
            "posterior_true_before": float(before[true_source]),
            "posterior_true_after": float(posterior[true_source]),
            "true_rank": rank,
            "source_risk": risk,
            "localization_error_m": error,
            "step_travel_m": step_travel,
            "score": float(scores[action]),
            "h2_second_action_by_observation": branch_actions,
        })
    return {
        "source_risk_auc": risk_auc,
        "localization_error_auc_m": error_auc,
        "final_true_rank": trace[-1]["true_rank"],
        "final_true_mass": trace[-1]["posterior_true_after"],
        "travel_m": travel,
        "unique_actions": len({row["action_subset_index"] for row in trace}),
        "trace": trace,
    }


def paired_summary(worlds: list[dict[str, Any]], left: str, right: str,
                   metric: str) -> dict[str, Any]:
    delta = np.asarray([world["policies"][right][metric] - world["policies"][left][metric]
                        for world in worlds])
    wins = int(np.count_nonzero(delta < -PAIR_TOL))
    losses = int(np.count_nonzero(delta > PAIR_TOL))
    ties = len(delta) - wins - losses
    n = wins + losses
    sign_p = float(sum(math.comb(n, k) for k in range(wins, n + 1)) / (2 ** n)) if n else 1.0
    return {
        "comparison": f"{right}-{left}",
        "metric": metric,
        "wins_losses_ties": [wins, losses, ties],
        "mean_delta": float(np.mean(delta)),
        "median_delta": float(np.median(delta)),
        "one_sided_exact_sign_p": sign_p,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--field-root", type=Path, required=True)
    parser.add_argument("--m3-module", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = load_m3(args.m3_module)
    data = {house: np.load(args.field_root / f"{house}_M2_FIELDS_V1.npz")
            for house in ("H01", "H02", "H03")}

    h01_feature, h01_event = calibration_arrays(data["H01"])
    beta, fit = fit_logistic_mle(h01_feature, h01_event)
    if beta[1] <= 0.0:
        raise RuntimeError("CTPI_G2_M3_CALIBRATION_NONMONOTONE")
    development_rate = fit["event_rate"]
    calibration = {
        "beta": beta.tolist(),
        "fit": fit,
        "held_out": {},
    }
    calibration_pass = True
    for house in ("H02", "H03"):
        feature, event = calibration_arrays(data[house])
        probability = sigmoid(beta[0] + beta[1] * feature)
        constant = np.full_like(probability, development_rate)
        model_nll, model_brier = loss(probability, event)
        constant_nll, constant_brier = loss(constant, event)
        criteria = {
            "nll_better_than_H01_rate": model_nll < constant_nll,
            "brier_better_than_H01_rate": model_brier < constant_brier,
        }
        calibration_pass = calibration_pass and all(criteria.values())
        calibration["held_out"][house] = {
            "event_rate": float(np.mean(event)),
            "model_nll": model_nll,
            "constant_nll": constant_nll,
            "model_brier": model_brier,
            "constant_brier": constant_brier,
            "criteria": criteria,
        }

    report: dict[str, Any] = {
        "contract": "CTPI_G2_M3_HELDOUT_OFFLINE_GATE_V1",
        "scope": "static max-over-300s acquisition; not a runtime closed-loop claim",
        "m3_module_sha256": sha256_file(args.m3_module),
        "event_threshold_ppm": EVENT_THRESHOLD_PPM,
        "action_count": ACTION_COUNT,
        "source_count_per_house": SOURCE_COUNT,
        "member_count_per_source": 8,
        "budget": BUDGET,
        "observation_adapter": calibration,
        "observation_adapter_pass": calibration_pass,
    }
    if not calibration_pass:
        report["status"] = "INVALID_OBSERVATION_LAW_NO_M3_GATE"
    else:
        worlds: list[dict[str, Any]] = []
        for house in ("H02", "H03"):
            item = data[house]
            carriers = item["carrier_ids"].astype(str)
            native = item["native_cells"].astype(np.int64)
            all_x = item["action_x"].astype(np.float64)
            all_y = item["action_y"].astype(np.float64)
            action_index = farthest_actions(all_x, all_y, ACTION_COUNT)
            action_xy = np.column_stack([all_x[action_index], all_y[action_index]])
            concentration_all = normalize_fields(item["numerical_fields"])
            concentration = concentration_all[:, action_index]
            q1 = sigmoid(beta[0] + beta[1] * concentration.T)
            source_xy = carrier_coordinates(carriers, native, all_x, all_y)
            source_index = frozen_sources(house, carriers, SOURCE_COUNT)
            gaden = np.asarray(item["gaden_peak_fields"], dtype=np.float64)
            for truth in source_index:
                for member in range(gaden.shape[1]):
                    outcome = gaden[truth, member, action_index] > EVENT_THRESHOLD_PPM
                    seed = int(hashlib.sha256(
                        f"CTPI_G2_M3_RANDOM_V1:{house}:{carriers[truth]}:{member}".encode()
                    ).hexdigest()[:16], 16)
                    policies = {
                        policy: run_policy(module, policy, q1, concentration,
                                           outcome, int(truth), source_xy,
                                           action_xy, seed)
                        for policy in ("random", "exploit", "myopic", "h2")
                    }
                    worlds.append({
                        "house": house,
                        "true_source_index": int(truth),
                        "true_carrier": carriers[truth],
                        "member": member,
                        "random_seed": seed,
                        "policies": policies,
                    })
                    print(f"CTPI_G2_M3_PROGRESS={house}:{len(worlds)}", flush=True)
        primary = paired_summary(worlds, "myopic", "h2", "source_risk_auc")
        by_house = {house: paired_summary([world for world in worlds if world["house"] == house],
                                          "myopic", "h2", "source_risk_auc")
                    for house in ("H02", "H03")}
        criteria = {
            "strict_majority_paired_wins": primary["wins_losses_ties"][0] > primary["wins_losses_ties"][1],
            "mean_source_risk_auc_delta_favors_h2": primary["mean_delta"] < 0.0,
            "no_house_all_worsening": all(value["wins_losses_ties"][0] > 0 for value in by_house.values()),
        }
        report.update({
            "status": "PASS" if all(criteria.values()) else "NO_GO",
            "primary": primary,
            "by_house_primary": by_house,
            "secondary": {
                "localization_error_auc": paired_summary(worlds, "myopic", "h2", "localization_error_auc_m"),
                "h2_vs_exploit_source_risk_auc": paired_summary(worlds, "exploit", "h2", "source_risk_auc"),
                "h2_vs_random_source_risk_auc": paired_summary(worlds, "random", "h2", "source_risk_auc"),
            },
            "criteria": criteria,
            "world_count": len(worlds),
            "worlds": worlds,
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CTPI_G2_M3_HELDOUT_OFFLINE_GATE={report['status']}:{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
