#!/usr/bin/env python3
"""One-shot H03 gate for Candidate-wise Time-Arrow Evidence Ratio (CTAER)."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"CTAER_IMPORT:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def paired_scores(measured: np.ndarray, instant: np.ndarray, taorl):
    window_samples = int(round(taorl.WINDOW_S / taorl.OUTPUT_DT_S))
    forward_by_tau = np.stack([
        taorl.ordinal_loss(
            measured, taorl.first_order(instant, tau, reverse=False), window_samples
        )
        for tau in taorl.TAU_GRID_S
    ])
    reverse_by_tau = np.stack([
        taorl.ordinal_loss(
            measured, taorl.first_order(instant, tau, reverse=True), window_samples
        )
        for tau in taorl.TAU_GRID_S
    ])
    best = np.argmin(forward_by_tau, axis=0)
    col = np.arange(instant.shape[1])
    forward = forward_by_tau[best, col]
    reverse_shared_tau = reverse_by_tau[best, col]
    contrast = forward - reverse_shared_tau
    tau = np.asarray(taorl.TAU_GRID_S, dtype=np.float64)[best]
    return forward, reverse_shared_tau, contrast, tau


def selftest(taorl_path: Path) -> None:
    taorl = import_module(taorl_path, "ctaer_taorl_selftest")
    instant = np.asarray([
        [0.0, 0.0],
        [0.0, 0.2],
        [1.0, 0.8],
        [0.4, 0.2],
        [0.0, 0.0],
        [0.0, 0.0],
    ], dtype=np.float64)
    measured = taorl.first_order(instant[:, [0]], 1.0)[:, 0]
    forward, reverse, contrast, _ = paired_scores(measured, instant, taorl)
    if not forward[0] < reverse[0]:
        raise AssertionError("CTAER_FORWARD_NOT_PREFERRED")
    if not contrast[0] < 0.0:
        raise AssertionError("CTAER_SIGN_CONVENTION")
    print("CTAER_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taorl-py", type=Path, required=True)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--sensor-trace", type=Path)
    parser.add_argument("--wind-trace", type=Path)
    parser.add_argument("--runtime-manifest", type=Path)
    parser.add_argument("--candidate-csv", type=Path)
    parser.add_argument("--loho-json", type=Path)
    parser.add_argument("--provider-py", type=Path)
    parser.add_argument("--prereg", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest(args.taorl_py)
        return

    required = (
        args.sensor_trace, args.wind_trace, args.runtime_manifest,
        args.candidate_csv, args.loho_json, args.provider_py,
        args.prereg, args.out,
    )
    if any(path is None for path in required):
        parser.error("formal run requires every input and --out")
    if args.out.exists():
        raise FileExistsError("CTAER_REFUSE_OVERWRITE_FORMAL_RESULT")

    taorl = import_module(args.taorl_py, "ctaer_frozen_taorl")
    prereg = json.loads(args.prereg.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CTAER_H03_SEED11_ONE_SHOT_V1":
        raise ValueError("CTAER_PREREG_CONTRACT")
    provider = taorl.import_provider(args.provider_py)
    rows, measured, trace_audit = taorl.load_rows(args.sensor_trace, args.wind_trace)
    candidates = taorl.read_candidates(args.candidate_csv)
    loho = json.loads(args.loho_json.read_text(encoding="utf-8"))
    parameter = next(
        fold["selected_parameter"] for fold in loho["folds"]
        if fold["heldout_house"] == "H03"
    )
    instant = taorl.instantaneous_response(rows, candidates, parameter, provider)

    # Freeze every candidate score before opening source truth.
    forward, reverse_shared_tau, contrast, selected_tau = paired_scores(
        measured, instant, taorl
    )
    frozen = {
        "TAORL_FORWARD_WINDOWED": forward,
        "CTAER_SHARED_TAU_ARROW_CONTRAST": contrast,
        "CTAER_SIGN_REVERSED_CONTROL": -contrast,
    }

    truth_xy = taorl.parse_truth(args.runtime_manifest)
    results = {
        name: taorl.evaluate(score, candidates, truth_xy)
        for name, score in frozen.items()
    }
    truth = np.asarray(truth_xy, dtype=np.float64)
    truth_index = int(np.argmin(np.sum((candidates - truth) ** 2, axis=1)))
    proposed = results["CTAER_SHARED_TAU_ARROW_CONTRAST"]
    checks = {
        "top_decile": proposed["normalized_true_rank"] <= 0.10,
        "beats_frozen_taorl_rank": proposed["true_rank"] < results["TAORL_FORWARD_WINDOWED"]["true_rank"],
        "beats_sign_reversed_rank": proposed["true_rank"] < results["CTAER_SIGN_REVERSED_CONTROL"]["true_rank"],
        "true_candidate_forward_better_than_reverse": float(forward[truth_index]) < float(reverse_shared_tau[truth_index]),
        "map_error_below_frozen_taorl_4p9851448324m": proposed["map_error_m"] < 4.9851448324,
        "map_error_below_native_pmfs_8p584385m": proposed["map_error_m"] < 8.584385,
    }
    passed = all(checks.values())
    report = {
        "contract": prereg["contract"],
        "verdict": "CTAER_H03_DEVELOPMENT_GO" if passed else "CTAER_H03_NO_GO",
        "claim_boundary": prereg["claim_if_pass"] if passed else prereg["stop_rule"],
        "truth_read_after_all_arm_scores": True,
        "truth_xy_evaluator_only": list(truth_xy),
        "trace_audit": trace_audit,
        "provider_parameter_selected_without_H03": parameter,
        "score_definition": "forward ordinal loss minus reverse ordinal loss at forward-selected shared tau; lower is better",
        "checks": checks,
        "results": results,
        "true_candidate_detail": {
            "selected_tau_s": float(selected_tau[truth_index]),
            "forward_loss": float(forward[truth_index]),
            "reverse_shared_tau_loss": float(reverse_shared_tau[truth_index]),
            "reverse_minus_forward_evidence": float(reverse_shared_tau[truth_index] - forward[truth_index]),
        },
        "input_hashes": {
            path.name: taorl.sha256(path) for path in (
                args.sensor_trace, args.wind_trace, args.runtime_manifest,
                args.candidate_csv, args.loho_json, args.provider_py,
                args.prereg, args.taorl_py,
            )
        },
        "script_sha256": taorl.sha256(Path(__file__)),
        "limitations": [
            "post-TAORL mechanism evaluated on the same exposed H03 development trace",
            "one House and one fixed historical trajectory only",
            "rank-MSE contrast is not a calibrated thermodynamic entropy-production estimate",
            "a pass would require an independent confirmation asset before cross-dataset or main-innovation language",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["verdict"])
    print(json.dumps(checks, sort_keys=True))


if __name__ == "__main__":
    main()

