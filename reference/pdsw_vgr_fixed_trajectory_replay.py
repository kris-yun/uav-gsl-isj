#!/usr/bin/env python3
"""PDSW fixed-trajectory replay on a frozen PMFS/VGR context bank.

PDSW = Predictive-Divergence Source Weighting.

Scientific boundary:
- trajectory, measurements, wind field, candidate bank and PMFS simulations stay frozen;
- source truth is evaluator-only and is not used to construct PDSW weights;
- the exact native PMFS per-cell likelihood is reused as the pointwise
  candidate predictive score;
- active final quadtree leaves are treated as competing source-prediction
  models and are weighted jointly on the simplex;
- no planner/refinement feedback is allowed in this replay.

The source-weight objective is the 2026 AISTATS divergence-based model-weight
form transferred to PMFS source hypotheses:

    min_w  KL(w || pi)
           - sum_i log( sum_k w_k L_ik )

where L_ik is the exact native PMFS cell likelihood and pi is the frozen source
prior mass induced by represented free-cell measure.  The crucial distinction
from native PMFS is mixture-before-log rather than candidate-wise
sum-log-then-exponentiate.

Reference:
Olav Benjamin Vassend (AISTATS 2026),
"A Divergence-Based Method for Weighting and Averaging Model Predictions",
PMLR 300:1855-1863.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

import tnqc_vgr_fixed_trajectory_replay as base


EPS = 1e-300


def pointwise_native_likelihood(
        triple: Tuple[float, float, float], power: float) -> float:
    measured, confidence, simulated = triple
    p = 1.0 - confidence * abs(measured - simulated) * power
    if not (p > 0.0 and math.isfinite(p)):
        raise ValueError(f"invalid native PMFS pointwise likelihood: {p}")
    return p


def active_measure(partition: Mapping[int, str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for cid in partition.values():
        out[cid] = out.get(cid, 0) + 1
    if not out:
        raise ValueError("empty final source partition")
    return out


def prior_weights(
        candidate_ids: Sequence[str],
        measure: Mapping[str, int],
        mode: str) -> List[float]:
    if mode == "uniform":
        return [1.0 / len(candidate_ids)] * len(candidate_ids)
    if mode != "free_cell_measure":
        raise ValueError(f"unsupported prior mode: {mode}")
    total = float(sum(measure[cid] for cid in candidate_ids))
    if not (total > 0.0):
        raise ValueError("non-positive source prior mass")
    return [float(measure[cid]) / total for cid in candidate_ids]


def build_likelihood_rows(
        alignment,
        candidate_ids: Sequence[str],
        power: float):
    supports = [set(alignment[cid]) for cid in candidate_ids]
    common = set.intersection(*supports)
    union = set.union(*supports)
    if not common:
        raise ValueError("active source candidates have no common observation support")

    rows: List[List[float]] = []
    measurement_mismatch = 0.0
    confidence_mismatch = 0.0
    neutral_rows = 0

    for idx in sorted(common):
        likelihoods = []
        measured_ref = None
        confidence_ref = None
        for cid in candidate_ids:
            triple = alignment[cid][idx]
            measured, confidence, _ = triple
            if measured_ref is None:
                measured_ref = measured
                confidence_ref = confidence
            else:
                measurement_mismatch = max(
                    measurement_mismatch, abs(measured - measured_ref))
                confidence_mismatch = max(
                    confidence_mismatch, abs(confidence - confidence_ref))
            likelihoods.append(pointwise_native_likelihood(triple, power))

        # A row where all candidates have likelihood one contains no source
        # information and contributes exactly zero to the objective.
        if max(abs(x - 1.0) for x in likelihoods) <= 1e-15:
            neutral_rows += 1
            continue
        rows.append(likelihoods)

    if not rows:
        raise ValueError("no informative common-support likelihood rows")

    return rows, {
        "common_support_count": len(common),
        "union_support_count": len(union),
        "common_support_fraction": len(common) / max(1, len(union)),
        "informative_row_count": len(rows),
        "neutral_row_count": neutral_rows,
        "max_measured_probability_mismatch": measurement_mismatch,
        "max_measured_confidence_mismatch": confidence_mismatch,
    }


def objective(
        w: Sequence[float],
        prior: Sequence[float],
        likelihood_rows: Sequence[Sequence[float]]) -> float:
    kl = 0.0
    for wk, pk in zip(w, prior):
        if wk > 0.0:
            kl += wk * math.log(wk / pk)
    data = 0.0
    for row in likelihood_rows:
        mix = sum(wk * lk for wk, lk in zip(w, row))
        if not (mix > 0.0 and math.isfinite(mix)):
            raise ValueError(f"invalid predictive mixture likelihood: {mix}")
        data -= math.log(max(mix, EPS))
    return kl + data


def gradient(
        w: Sequence[float],
        prior: Sequence[float],
        likelihood_rows: Sequence[Sequence[float]]) -> List[float]:
    g = [
        math.log(max(wk, EPS) / pk) + 1.0
        for wk, pk in zip(w, prior)
    ]
    for row in likelihood_rows:
        mix = sum(wk * lk for wk, lk in zip(w, row))
        if not (mix > 0.0):
            raise ValueError("non-positive mixture during optimization")
        inv = 1.0 / mix
        for k, lk in enumerate(row):
            g[k] -= lk * inv
    return g


def mirror_descent(
        prior: Sequence[float],
        likelihood_rows: Sequence[Sequence[float]],
        max_iter: int,
        tol: float):
    """Solve the convex simplex objective with exponentiated-gradient updates.

    Backtracking is used only to guarantee a monotone objective.  There is no
    fitted scientific hyperparameter: the step size is numerical plumbing.
    """
    w = list(prior)
    current = objective(w, prior, likelihood_rows)
    nrows = max(1, len(likelihood_rows))
    eta = 1.0 / nrows
    converged = False
    last_delta = math.inf
    accepted_steps = 0

    for iteration in range(1, max_iter + 1):
        g = gradient(w, prior, likelihood_rows)
        # Adding a constant to every gradient coordinate has no effect on a
        # simplex mirror step; centering improves numerical stability.
        mean_g = sum(wk * gk for wk, gk in zip(w, g))
        gc = [gk - mean_g for gk in g]

        step = eta
        accepted = False
        candidate = w
        candidate_obj = current

        for _ in range(40):
            logu = [
                math.log(max(wk, EPS)) - step * gk
                for wk, gk in zip(w, gc)
            ]
            m = max(logu)
            u = [math.exp(max(-700.0, x - m)) for x in logu]
            su = sum(u)
            candidate = [x / su for x in u]
            candidate_obj = objective(candidate, prior, likelihood_rows)
            if candidate_obj <= current + 1e-13:
                accepted = True
                break
            step *= 0.5

        if not accepted:
            # Numerical stationarity.  A failed line search is accepted as
            # convergence only when the weighted gradient spread is tiny.
            spread = max(gc) - min(gc)
            converged = spread <= max(1e-8, 10.0 * tol)
            break

        accepted_steps += 1
        last_delta = max(abs(a - b) for a, b in zip(candidate, w))
        w = candidate
        current = candidate_obj
        eta = min(step * 1.25, 10.0 / nrows)

        if last_delta <= tol:
            converged = True
            break

    return w, {
        "converged": converged,
        "iterations": iteration,
        "accepted_steps": accepted_steps,
        "max_weight_delta_last": last_delta,
        "objective_final": current,
        "objective_prior": objective(prior, prior, likelihood_rows),
        "tolerance": tol,
        "max_iter": max_iter,
    }


def source_cell_posterior(
        partition: Mapping[int, str],
        candidate_ids: Sequence[str],
        candidate_weights: Sequence[float],
        measure: Mapping[str, int]) -> Dict[int, float]:
    by_candidate = dict(zip(candidate_ids, candidate_weights))
    p = {
        idx: by_candidate[cid] / float(measure[cid])
        for idx, cid in partition.items()
    }
    total = sum(p.values())
    if not (total > 0.0 and math.isfinite(total)):
        raise ValueError("invalid PDSW cell posterior normalization")
    return {idx: value / total for idx, value in p.items()}


def entropy(weights: Sequence[float]) -> float:
    return -sum(w * math.log(w) for w in weights if w > 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--truth-x", type=float, required=True)
    ap.add_argument("--truth-y", type=float, required=True)
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--source-discrimination-power", type=float, default=1.0)
    ap.add_argument(
        "--prior-mode",
        choices=("free_cell_measure", "uniform"),
        default="free_cell_measure")
    ap.add_argument("--max-iter", type=int, default=1500)
    ap.add_argument("--optimizer-tol", type=float, default=1e-10)
    ap.add_argument("--native-reconstruction-max-abs", type=float, default=5e-6)
    ap.add_argument("--native-reconstruction-l1", type=float, default=5e-4)
    ap.add_argument(
        "--native-endpoint-rounding-tolerance-m",
        type=float,
        default=0.011)
    ap.add_argument("--cpp-endpoint-evaluator", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    bank = args.run_dir / "context_bank"
    uid, sim_time = base.choose_final_update(bank, args.budget_s)
    d = bank / f"source_update_{uid:04d}"

    grid_meta = base.load_grid_metadata(bank, uid)
    cells, _ = base.load_cells(d)
    candidates = base.load_candidates(d)
    alignment = base.load_alignment(d, cells)
    missing = sorted(set(candidates) - set(alignment))
    if missing:
        raise ValueError(
            f"{len(missing)} candidates missing alignment: {missing[:3]}")

    partition = base.final_partition(cells, candidates)
    measure = active_measure(partition)
    active_ids = sorted(measure)
    prior = prior_weights(active_ids, measure, args.prior_mode)

    likelihood_rows, support_audit = build_likelihood_rows(
        alignment, active_ids, args.source_discrimination_power)
    weights, optimizer = mirror_descent(
        prior,
        likelihood_rows,
        max_iter=args.max_iter,
        tol=args.optimizer_tol)
    pdsw = source_cell_posterior(partition, active_ids, weights, measure)

    # Reconstruct native PMFS independently, exactly as the frozen TNQC replay
    # does, so PDSW cannot be accepted on a corrupt context bank.
    native_scores = {
        cid: base.native_log_score(
            alignment[cid], args.source_discrimination_power)
        for cid in candidates
    }
    native_replay = base.posterior(partition, native_scores)
    native_export = base.exported_posterior(d)
    reconstruction = base.diff(native_replay, native_export)
    reconstruction_pass = (
        reconstruction["max_abs"] <= args.native_reconstruction_max_abs
        and reconstruction["l1"] <= args.native_reconstruction_l1)

    # Truth enters only after every source weight/posterior is constructed.
    native_py = base.metrics(
        native_export, cells, args.truth_x, args.truth_y)
    pdsw_py = base.metrics(
        pdsw, cells, args.truth_x, args.truth_y)

    evaluator = args.cpp_endpoint_evaluator.resolve()
    if not evaluator.is_file():
        raise FileNotFoundError(evaluator)
    endpoint_dir = args.run_dir / "pdsw_endpoint_posteriors"
    endpoint_dir.mkdir(parents=True, exist_ok=True)
    native_csv = endpoint_dir / "native_exported.csv"
    pdsw_csv = endpoint_dir / "pdsw.csv"
    base.write_endpoint_posterior(native_csv, native_export, cells)
    base.write_endpoint_posterior(pdsw_csv, pdsw, cells)

    native_cpp = base.cpp_endpoint_metrics(
        evaluator, native_csv, args.truth_x, args.truth_y, grid_meta)
    pdsw_cpp = base.cpp_endpoint_metrics(
        evaluator, pdsw_csv, args.truth_x, args.truth_y, grid_meta)

    native_engine = "gsl_utils_expected_value_linked_native_v1"
    engine_pass = (
        native_cpp.get("engine") == native_engine
        and pdsw_cpp.get("engine") == native_engine)

    native_logged = base.native_result_line(args.run_dir)
    endpoint_delta = abs(
        native_cpp["pmfs_top5_error_m"]
        - native_logged["reported_top5_error_m"])
    endpoint_pass = (
        endpoint_delta <= args.native_endpoint_rounding_tolerance_m)

    native_metrics = {**native_py, **native_cpp}
    pdsw_metrics = {**pdsw_py, **pdsw_cpp}

    sorted_weights = sorted(
        zip(active_ids, weights, prior),
        key=lambda x: x[1],
        reverse=True)
    weight_summary = {
        "entropy_nats": entropy(weights),
        "effective_candidate_count_exp_entropy": math.exp(entropy(weights)),
        "max_weight": max(weights),
        "top10": [
            {
                "candidate_id": cid,
                "weight": w,
                "prior_mass": p,
                "represented_free_cells": measure[cid],
            }
            for cid, w, p in sorted_weights[:10]
        ],
    }

    valid = (
        reconstruction_pass
        and endpoint_pass
        and engine_pass
        and optimizer["converged"])

    payload = {
        "contract":
            "PDSW_VGR_FIXED_TRAJECTORY_300S_REPLAY_V1_LINKED_NATIVE_ENDPOINT",
        "method": {
            "name": "Predictive-Divergence Source Weighting",
            "version": "PDSW_V1",
            "objective":
                "KL(w||source_prior)-sum_i log(sum_k w_k*L_ik)",
            "pointwise_score":
                "exact native PMFS cell likelihood "
                "1-confidence*abs(measured-simulated)*power",
            "mixture_semantics":
                "source hypotheses are mixed before the logarithm",
            "prior_mode": args.prior_mode,
            "truth_used_for_weighting": False,
            "planner_or_refinement_feedback": False,
        },
        "run_dir": str(args.run_dir),
        "budget_s": args.budget_s,
        "selected_source_update_id": uid,
        "selected_source_update_sim_time": sim_time,
        "budget_to_last_update_gap_s": args.budget_s - sim_time,
        "truth": [args.truth_x, args.truth_y],
        "free_cell_count": len(cells),
        "total_evaluated_candidate_count": len(candidates),
        "active_final_leaf_candidate_count": len(active_ids),
        "source_prior_measure_cells": measure,
        "candidate_scope":
            "final_partition_leaf_candidates_with_free_cell_measure_prior",
        "likelihood_support_audit": support_audit,
        "optimizer": optimizer,
        "source_weight_summary": weight_summary,
        "native_reconstruction_audit": {
            **reconstruction,
            "max_abs_threshold": args.native_reconstruction_max_abs,
            "l1_threshold": args.native_reconstruction_l1,
            "pass": reconstruction_pass,
        },
        "native_cpp_endpoint_audit": {
            "cpp_result": native_logged,
            "linked_native_top5_error_m":
                native_cpp["pmfs_top5_error_m"],
            "absolute_error_difference_m": endpoint_delta,
            "rounding_tolerance_m":
                args.native_endpoint_rounding_tolerance_m,
            "pass": endpoint_pass,
        },
        "endpoint_evaluator": {
            "engine": native_cpp.get("engine"),
            "engine_integrity_pass": engine_pass,
            "authoritative_engine": native_engine,
            "binary": str(evaluator),
            "sha256": hashlib.sha256(evaluator.read_bytes()).hexdigest(),
            "grid_metadata": {
                "width": grid_meta.width,
                "height": grid_meta.height,
                "cell_size": grid_meta.cell_size,
                "origin_x": grid_meta.origin_x,
                "origin_y": grid_meta.origin_y,
            },
            "native_posterior_csv": str(native_csv),
            "pdsw_posterior_csv": str(pdsw_csv),
        },
        "native_exported": native_metrics,
        "pdsw": pdsw_metrics,
        "pdsw_improvement_fraction_vs_native":
            (native_metrics["pmfs_top5_error_m"]
             - pdsw_metrics["pmfs_top5_error_m"])
            / max(abs(native_metrics["pmfs_top5_error_m"]), 1e-12),
        "valid_for_gate": valid,
        "gate_validity_requires": [
            "native_posterior_reconstruction",
            "linked_native_GSL_Utils_ExpectedValue_matches_native_pmfs",
            "same_linked_native_endpoint_binary_for_pdsw_counterfactual",
            "convex_weight_optimizer_converged",
        ],
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    target = args.json_out or args.run_dir / "pdsw_fixed_trajectory_evaluation.json"
    target.write_text(text + "\n", encoding="utf-8")
    if not valid:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
