#!/usr/bin/env python3
"""ATC V1 Stage-A: leave-one-House-out structured discrepancy screen.

This is a read-only fixed-trajectory development screen. It does not modify
PMFS/GADEN/TNQC state and it is not the final ANI/alternating-composition test.
Its only purpose is to decide whether the frozen candidate transport family
contains a transferable, candidate-shared structured discrepancy worth a
Stage-B alternating corrector implementation.

For each held-out House, fit a lightweight residual map on the final source
updates of the other two Houses using only the training-House true-source
owner candidate. Apply the frozen map to every candidate in the held-out House,
score candidates with the unchanged native PMFS cell likelihood, reconstruct a
counterfactual source posterior, and evaluate it with the linked-native PMFS
ExpectedValue(..., 0.05) endpoint.

Truth from the held-out House is used only for evaluator-side rank/endpoint
metrics. The correction is shared across all candidates and has no House or
source-ID feature.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np

import tnqc_vgr_fixed_trajectory_replay as replay

EPS = 1e-6
HOUSES = ("House01", "House02", "House03")
SEEDS = (0, 1)
TRUTH = {
    "House01": (-0.40, -2.90),
    "House02": (0.00, -1.00),
    "House03": (-0.45, 1.90),
}


@dataclass
class Case:
    house: str
    seed: int
    run_dir: Path
    update_dir: Path
    grid_meta: replay.GridMetadata
    cells: Mapping[int, replay.Cell]
    candidates: Mapping[str, replay.Candidate]
    alignment: Mapping[str, Mapping[int, Tuple[float, float, float]]]
    partition: Mapping[int, str]
    truth_x: float
    truth_y: float
    truth_cell: int
    truth_owner: str
    active_ids: Sequence[str]
    native_scores: Mapping[str, float]
    native_export: Mapping[int, float]
    native_replay: Mapping[int, float]
    native_reconstruction: Mapping[str, float]


def sigmoid(x: float) -> float:
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def nearest_free_cell(cells: Mapping[int, replay.Cell], x: float, y: float) -> int:
    return min(cells, key=lambda idx: (
        (cells[idx].x - x) ** 2 + (cells[idx].y - y) ** 2,
        idx,
    ))


def load_case(run_root: Path, house: str, seed: int, budget_s: float,
              source_power: float) -> Case:
    run_dir = run_root / f"{house}_seed{seed}_off_off"
    bank = run_dir / "context_bank"
    uid, _ = replay.choose_final_update(bank, budget_s)
    d = bank / f"source_update_{uid:04d}"
    meta = replay.load_grid_metadata(bank, uid)
    cells, _ = replay.load_cells(d)
    candidates = replay.load_candidates(d)
    alignment = replay.load_alignment(d, cells)
    missing = sorted(set(candidates) - set(alignment))
    if missing:
        raise ValueError(f"{house}/seed{seed}: missing candidate alignment: {missing[:3]}")
    partition = replay.final_partition(cells, candidates)
    active_ids = sorted(set(partition.values()))
    native_scores = {
        cid: replay.native_log_score(alignment[cid], source_power)
        for cid in candidates
    }
    native_replay = replay.posterior(partition, native_scores)
    native_export = replay.exported_posterior(d)
    audit = replay.diff(native_replay, native_export)
    tx, ty = TRUTH[house]
    truth_cell = nearest_free_cell(cells, tx, ty)
    truth_owner = partition[truth_cell]
    return Case(
        house=house, seed=seed, run_dir=run_dir, update_dir=d,
        grid_meta=meta, cells=cells, candidates=candidates,
        alignment=alignment, partition=partition, truth_x=tx, truth_y=ty,
        truth_cell=truth_cell, truth_owner=truth_owner, active_ids=active_ids,
        native_scores=native_scores, native_export=native_export,
        native_replay=native_replay, native_reconstruction=audit,
    )


def feature_row(case: Case, cid: str, idx: int, simulated: float,
                structured: bool) -> np.ndarray:
    cell = case.cells[idx]
    cand = case.candidates[cid]
    scale = max(
        case.grid_meta.cell_size,
        math.hypot(case.grid_meta.width * case.grid_meta.cell_size,
                   case.grid_meta.height * case.grid_meta.cell_size),
    )
    dx = (cell.x - cand.center_x) / scale
    dy = (cell.y - cand.center_y) / scale
    rr = math.hypot(dx, dy)
    z = replay.safe_logit(simulated)
    if not structured:
        return np.asarray([1.0, z], dtype=float)
    return np.asarray([
        1.0, z, dx, dy, rr,
        z * dx, z * dy, z * rr,
        dx * dx - dy * dy, dx * dy,
    ], dtype=float)


def collect_training(cases: Sequence[Case], structured: bool):
    xs: List[np.ndarray] = []
    ys: List[float] = []
    ws: List[float] = []
    per_case = []
    for case in cases:
        cid = case.truth_owner
        support_rows = []
        for idx, (measured, confidence, simulated) in case.alignment[cid].items():
            if idx not in case.cells or confidence <= 0.0:
                continue
            if not all(map(math.isfinite, (measured, confidence, simulated))):
                continue
            x = feature_row(case, cid, idx, simulated, structured)
            target = replay.safe_logit(measured) - replay.safe_logit(simulated)
            support_rows.append((x, target, confidence))
        if len(support_rows) < 4:
            raise ValueError(
                f"{case.house}/seed{case.seed}: too little truth-owner support")
        sw = sum(r[2] for r in support_rows)
        if not (sw > 0.0):
            raise ValueError("non-positive training confidence weight")
        # Equal total weight per training run: map cells are not iid replications.
        for x, target, confidence in support_rows:
            xs.append(x)
            ys.append(target)
            ws.append(confidence / sw)
        per_case.append({
            "house": case.house,
            "seed": case.seed,
            "truth_owner": cid,
            "support_rows": len(support_rows),
        })
    return np.vstack(xs), np.asarray(ys), np.asarray(ws), per_case


def fit_ridge(x: np.ndarray, y: np.ndarray, w: np.ndarray,
              ridge: float) -> np.ndarray:
    sw = np.sqrt(np.maximum(w, 0.0))
    xw = x * sw[:, None]
    yw = y * sw
    gram = xw.T @ xw
    penalty = np.eye(x.shape[1]) * ridge
    penalty[0, 0] = 0.0
    rhs = xw.T @ yw
    return np.linalg.solve(gram + penalty, rhs)


def corrected_scores(case: Case, beta: np.ndarray, structured: bool,
                     residual_clip: float, source_power: float):
    scores: Dict[str, float] = {}
    correction_stats = {}
    for cid in case.candidates:
        corrected = {}
        residuals = []
        for idx, (measured, confidence, simulated) in case.alignment[cid].items():
            x = feature_row(case, cid, idx, simulated, structured)
            residual = float(x @ beta)
            residual = max(-residual_clip, min(residual_clip, residual))
            p = sigmoid(replay.safe_logit(simulated) + residual)
            corrected[idx] = (
                measured, confidence, min(max(p, EPS), 1.0 - EPS))
            residuals.append(residual)
        scores[cid] = replay.native_log_score(corrected, source_power)
        correction_stats[cid] = {
            "mean_abs_logit_correction": (
                float(np.mean(np.abs(residuals))) if residuals else None),
            "max_abs_logit_correction": (
                float(np.max(np.abs(residuals))) if residuals else None),
        }
    return scores, correction_stats


def candidate_rank(scores: Mapping[str, float], active_ids: Sequence[str],
                   truth_owner: str) -> int:
    ranked = sorted(active_ids, key=lambda cid: (-scores[cid], cid))
    return ranked.index(truth_owner) + 1


def endpoint_for(case: Case, p: Mapping[int, float], evaluator: Path,
                 out_csv: Path):
    replay.write_endpoint_posterior(out_csv, p, case.cells)
    return replay.cpp_endpoint_metrics(
        evaluator, out_csv, case.truth_x, case.truth_y, case.grid_meta)


def case_result(case: Case, scalar_beta: np.ndarray,
                structured_beta: np.ndarray, args, fold_dir: Path):
    if (case.native_reconstruction["max_abs"]
            > args.native_reconstruction_max_abs
            or case.native_reconstruction["l1"]
            > args.native_reconstruction_l1):
        raise ValueError(
            f"{case.house}/seed{case.seed}: native reconstruction failed: "
            f"{case.native_reconstruction}")

    scalar_scores, scalar_corr = corrected_scores(
        case, scalar_beta, False, args.residual_clip,
        args.source_discrimination_power)
    structured_scores, structured_corr = corrected_scores(
        case, structured_beta, True, args.residual_clip,
        args.source_discrimination_power)

    scalar_p = replay.posterior(case.partition, scalar_scores)
    structured_p = replay.posterior(case.partition, structured_scores)

    case_dir = fold_dir / f"{case.house}_seed{case.seed}"
    case_dir.mkdir(parents=True, exist_ok=True)
    native_csv = case_dir / "native_export.csv"
    scalar_csv = case_dir / "scalar_calibrated.csv"
    structured_csv = case_dir / "structured_corrected.csv"

    native_ep = endpoint_for(
        case, case.native_export, args.cpp_endpoint_evaluator, native_csv)
    native_logged = replay.native_result_line(case.run_dir)
    native_endpoint_delta = abs(
        native_ep["pmfs_top5_error_m"]
        - native_logged["reported_top5_error_m"])
    if native_ep.get("engine") != "gsl_utils_expected_value_linked_native_v1":
        raise ValueError(
            f"{case.house}/seed{case.seed}: non-authoritative endpoint engine "
            f"{native_ep.get('engine')}")
    if native_endpoint_delta > args.native_endpoint_rounding_tolerance_m:
        raise ValueError(
            f"{case.house}/seed{case.seed}: linked-native endpoint parity failed: "
            f"{native_endpoint_delta} m")
    scalar_ep = endpoint_for(
        case, scalar_p, args.cpp_endpoint_evaluator, scalar_csv)
    structured_ep = endpoint_for(
        case, structured_p, args.cpp_endpoint_evaluator, structured_csv)

    native_rank = candidate_rank(
        case.native_scores, case.active_ids, case.truth_owner)
    scalar_rank = candidate_rank(
        scalar_scores, case.active_ids, case.truth_owner)
    structured_rank = candidate_rank(
        structured_scores, case.active_ids, case.truth_owner)

    return {
        "house": case.house,
        "seed": case.seed,
        "truth": [case.truth_x, case.truth_y],
        "truth_cell": case.truth_cell,
        "truth_owner": case.truth_owner,
        "final_leaf_candidate_count": len(case.active_ids),
        "native_reconstruction": dict(case.native_reconstruction),
        "native_logged_result": native_logged,
        "native_endpoint_parity_abs_m": native_endpoint_delta,
        "native_endpoint_parity_tolerance_m":
            args.native_endpoint_rounding_tolerance_m,
        "native_rank": native_rank,
        "scalar_rank": scalar_rank,
        "structured_rank": structured_rank,
        "rank_improved_vs_native": structured_rank < native_rank,
        "rank_nonworse_vs_native": structured_rank <= native_rank,
        "native_endpoint": native_ep,
        "scalar_endpoint": scalar_ep,
        "structured_endpoint": structured_ep,
        "structured_improvement_fraction_vs_native": (
            native_ep["pmfs_top5_error_m"]
            - structured_ep["pmfs_top5_error_m"]
        ) / max(native_ep["pmfs_top5_error_m"], 1e-12),
        "scalar_improvement_fraction_vs_native": (
            native_ep["pmfs_top5_error_m"]
            - scalar_ep["pmfs_top5_error_m"]
        ) / max(native_ep["pmfs_top5_error_m"], 1e-12),
        "true_owner_structured_correction":
            structured_corr[case.truth_owner],
        "max_structured_candidate_correction": max(
            v["max_abs_logit_correction"] or 0.0
            for v in structured_corr.values()),
        "max_scalar_candidate_correction": max(
            v["max_abs_logit_correction"] or 0.0
            for v in scalar_corr.values()),
    }


def pooled_error(rows: Sequence[Mapping], key: str) -> float:
    return float(np.mean([
        float(r[key]["pmfs_top5_error_m"]) for r in rows
    ]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--cpp-endpoint-evaluator", type=Path, required=True)
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--source-discrimination-power", type=float, default=1.0)
    ap.add_argument("--ridge", type=float, default=1e-3)
    ap.add_argument("--residual-clip", type=float, default=3.0)
    ap.add_argument("--native-reconstruction-max-abs",
                    type=float, default=5e-6)
    ap.add_argument("--native-reconstruction-l1",
                    type=float, default=5e-4)
    ap.add_argument("--native-endpoint-rounding-tolerance-m",
                    type=float, default=0.011)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    args.cpp_endpoint_evaluator = args.cpp_endpoint_evaluator.resolve()
    if not args.cpp_endpoint_evaluator.is_file():
        raise FileNotFoundError(args.cpp_endpoint_evaluator)

    all_cases = {
        (h, s): load_case(
            args.run_root, h, s, args.budget_s,
            args.source_discrimination_power)
        for h in HOUSES for s in SEEDS
    }

    output_root = (
        args.json_out.parent if args.json_out
        else args.run_root / "atc_v1_stage_a")
    output_root.mkdir(parents=True, exist_ok=True)
    all_rows = []
    folds = []

    for held in HOUSES:
        training = [
            all_cases[(h, s)]
            for h in HOUSES if h != held
            for s in SEEDS
        ]
        testing = [all_cases[(held, s)] for s in SEEDS]

        xs, ys, ws, _ = collect_training(training, False)
        scalar_beta = fit_ridge(xs, ys, ws, args.ridge)
        xg, yg, wg, train_structured = collect_training(training, True)
        structured_beta = fit_ridge(xg, yg, wg, args.ridge)

        fold_dir = output_root / f"holdout_{held}"
        fold_dir.mkdir(parents=True, exist_ok=True)
        rows = [
            case_result(c, scalar_beta, structured_beta, args, fold_dir)
            for c in testing
        ]
        all_rows.extend(rows)
        folds.append({
            "held_out_house": held,
            "training_cases": train_structured,
            "scalar_beta": scalar_beta.tolist(),
            "structured_beta": structured_beta.tolist(),
            "cases": rows,
        })

    native_pool = pooled_error(all_rows, "native_endpoint")
    scalar_pool = pooled_error(all_rows, "scalar_endpoint")
    structured_pool = pooled_error(all_rows, "structured_endpoint")
    structured_gain = (
        native_pool - structured_pool) / max(native_pool, 1e-12)
    scalar_gain = (
        native_pool - scalar_pool) / max(native_pool, 1e-12)
    nonworse = sum(
        r["structured_endpoint"]["pmfs_top5_error_m"]
        <= r["native_endpoint"]["pmfs_top5_error_m"] + 1e-12
        for r in all_rows)
    improved_rank = sum(r["rank_improved_vs_native"] for r in all_rows)
    nonworse_rank = sum(r["rank_nonworse_vs_native"] for r in all_rows)

    gates = {
        "pooled_endpoint_improvement_ge_2pct": structured_gain >= 0.02,
        "at_least_4_of_6_endpoint_nonworse": nonworse >= 4,
        "true_owner_rank_improves_at_least_4_of_6":
            improved_rank >= 4,
        "true_owner_rank_nonworse_at_least_5_of_6":
            nonworse_rank >= 5,
        "structured_beats_scalar_calibration":
            structured_gain > scalar_gain,
        "structured_max_correction_within_clip": all(
            r["max_structured_candidate_correction"]
            <= args.residual_clip + 1e-12
            for r in all_rows),
    }
    pass_stage_a = all(gates.values())

    payload = {
        "contract": "ATC_V1_STAGE_A_LOHO_STRUCTURED_DISCREPANCY_V1",
        "status": (
            "PASS_FOR_STAGE_B" if pass_stage_a
            else "NO_GO_AT_STAGE_A"),
        "claim_boundary": (
            "This screen establishes only transferable structured "
            "discrepancy. It does not establish alternating-neural-integrator "
            "dynamics or closed-loop benefit."),
        "config": {
            "run_root": str(args.run_root),
            "budget_s": args.budget_s,
            "source_discrimination_power":
                args.source_discrimination_power,
            "ridge": args.ridge,
            "residual_clip": args.residual_clip,
            "truth": TRUTH,
            "feature_policy": (
                "candidate-shared low-order relative-geometry/logit "
                "residual; no House/source-ID feature; equal total "
                "weight per training run"),
        },
        "aggregate": {
            "pooled_native_error_m": native_pool,
            "pooled_scalar_error_m": scalar_pool,
            "pooled_structured_error_m": structured_pool,
            "scalar_improvement_fraction": scalar_gain,
            "structured_improvement_fraction": structured_gain,
            "endpoint_nonworse_cases": int(nonworse),
            "truth_owner_rank_improved_cases": int(improved_rank),
            "truth_owner_rank_nonworse_cases": int(nonworse_rank),
        },
        "gates": gates,
        "folds": folds,
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    out = args.json_out or output_root / "atc_v1_stage_a.json"
    out.write_text(text + "\n", encoding="utf-8")
    raise SystemExit(0 if pass_stage_a else 10)


if __name__ == "__main__":
    main()
