#!/usr/bin/env python3
"""One-shot CFIR gate using frozen LMBT chronological/reversed footprints.

All source scores are frozen before the evaluator-only source coordinate is
opened. Full CFD wind is explicitly an oracle diagnostic input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_KAPPA = 0.03
GRID_SPACING_M = 0.10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lmbt(path: Path):
    spec = importlib.util.spec_from_file_location("cfir_lmbt_frozen", path)
    if spec is None or spec.loader is None:
        raise ImportError("CFIR_LMBT_IMPORT")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def cfir_scores(forward: dict[float, np.ndarray],
                reverse: dict[float, np.ndarray]) -> dict[float, np.ndarray]:
    if set(forward) != set(reverse):
        raise ValueError("CFIR_KAPPA_KEY_MISMATCH")
    output = {}
    for kappa in sorted(forward):
        if forward[kappa].shape != reverse[kappa].shape:
            raise ValueError("CFIR_SCORE_SHAPE_MISMATCH")
        output[kappa] = np.asarray(forward[kappa]) - np.asarray(reverse[kappa])
    return output


def selftest(lmbt_path: Path) -> None:
    lmbt = load_lmbt(lmbt_path)
    lmbt.selftest()
    forward = {0.03: np.asarray([-1.0, -2.0, -4.0])}
    reverse = {0.03: np.asarray([-3.0, -1.0, -4.5])}
    got = cfir_scores(forward, reverse)[0.03]
    if not np.array_equal(got, np.asarray([2.0, -1.0, 0.5])):
        raise AssertionError("CFIR_RATIO_SELFTEST")
    if int(np.argmax(got)) != 0 or int(np.argmax(-got)) != 1:
        raise AssertionError("CFIR_SIGN_CONTROL_SELFTEST")
    print("CFIR_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--lmbt-py", type=Path, required=True)
    parser.add_argument("--trace-dir", type=Path)
    parser.add_argument("--realization", type=Path)
    parser.add_argument("--occupancy", type=Path)
    parser.add_argument("--environment-runtime-py", type=Path)
    parser.add_argument("--candidate-csv", type=Path)
    parser.add_argument("--reference-lmbt-json", type=Path)
    parser.add_argument("--prereg", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.selftest:
        selftest(args.lmbt_py)
        return

    required = (args.trace_dir, args.realization, args.occupancy,
                args.environment_runtime_py, args.candidate_csv,
                args.reference_lmbt_json, args.prereg, args.out)
    if any(value is None for value in required):
        parser.error("formal run requires every input and output argument")
    if args.out.exists():
        raise FileExistsError("CFIR_REFUSE_OVERWRITE_FORMAL_RESULT")

    prereg = json.loads(args.prereg.read_text(encoding="utf-8"))
    if prereg.get("contract") != "CFIR_H03_SEED11_ONE_SHOT_V1":
        raise ValueError("CFIR_PREREG_CONTRACT")
    reference = json.loads(args.reference_lmbt_json.read_text(encoding="utf-8"))
    lmbt = load_lmbt(args.lmbt_py)
    candidate_xy = pd.read_csv(args.candidate_csv,
                               usecols=["x", "y"]).to_numpy(np.float64)
    runtime_wind = lmbt.load_runtime_wind(
        args.realization, args.occupancy, args.environment_runtime_py)
    wind_schedule, wind_binding = lmbt.infer_wind_schedule(
        runtime_wind, args.trace_dir)
    events, event_audit = lmbt.load_events(args.trace_dir, memory_on=True)

    # Freeze every model score before opening evaluator-only source truth.
    forward = lmbt.freeze_arm_scores(
        events, runtime_wind, wind_schedule, candidate_xy)
    reverse = lmbt.freeze_arm_scores(
        events, runtime_wind, wind_schedule, candidate_xy,
        reversed_sequence=True)
    cfir = cfir_scores(forward, reverse)
    sign_reverse = {kappa: -score for kappa, score in cfir.items()}
    frozen = {
        "LMBT_CHRONOLOGICAL": forward,
        "LMBT_REVERSED": reverse,
        "CFIR_CHRONOLOGICAL_OVER_REVERSED": cfir,
        "CFIR_SIGN_REVERSED_CONTROL": sign_reverse,
    }

    truth_xy = lmbt.parse_truth_after_scoring(
        args.trace_dir / "formal_runtime_manifest.json")
    results = {
        arm: {str(kappa): lmbt.evaluate(score, candidate_xy, truth_xy)
              for kappa, score in by_kappa.items()}
        for arm, by_kappa in frozen.items()
    }

    key = str(DEFAULT_KAPPA)
    new_f = results["LMBT_CHRONOLOGICAL"][key]
    new_r = results["LMBT_REVERSED"][key]
    old_f = reference["results"]["LMBT_MEMORY_ON_ACTUAL_WIND"][key]
    old_r = reference["results"]["LMBT_MEMORY_ON_REVERSED_WIND_SEQUENCE"][key]
    lineage_checks = {
        "chronological_rank_exact": new_f["true_rank"] == old_f["true_rank"],
        "chronological_map_exact": abs(new_f["map_error_m"] - old_f["map_error_m"]) <= 1e-12,
        "reversed_rank_exact": new_r["true_rank"] == old_r["true_rank"],
        "reversed_map_exact": abs(new_r["map_error_m"] - old_r["map_error_m"]) <= 1e-12,
    }

    cfir_default = results["CFIR_CHRONOLOGICAL_OVER_REVERSED"][key]
    sign_default = results["CFIR_SIGN_REVERSED_CONTROL"][key]
    cfir_map_values = [row["map_error_m"]
                       for row in results["CFIR_CHRONOLOGICAL_OVER_REVERSED"].values()]
    f_map_values = [row["map_error_m"]
                    for row in results["LMBT_CHRONOLOGICAL"].values()]
    cfir_rank_values = [row["normalized_true_rank"]
                        for row in results["CFIR_CHRONOLOGICAL_OVER_REVERSED"].values()]
    f_rank_values = [row["normalized_true_rank"]
                     for row in results["LMBT_CHRONOLOGICAL"].values()]
    checks = {
        **lineage_checks,
        "default_map_improves_one_grid_spacing":
            cfir_default["map_error_m"] <= new_f["map_error_m"] - GRID_SPACING_M,
        "default_rank_beats_chronological":
            cfir_default["true_rank"] < new_f["true_rank"],
        "default_rank_beats_reversed":
            cfir_default["true_rank"] < new_r["true_rank"],
        "default_rank_top_decile":
            cfir_default["normalized_true_rank"] <= 0.10,
        "default_beats_sign_reversed_control":
            cfir_default["true_rank"] < sign_default["true_rank"],
        "median_map_improves":
            float(np.median(cfir_map_values)) < float(np.median(f_map_values)),
        "median_rank_improves":
            float(np.median(cfir_rank_values)) < float(np.median(f_rank_values)),
    }
    passed = all(checks.values())

    report = {
        "contract": prereg["contract"],
        "verdict": "CFIR_H03_ORACLE_PREMISE_PASS" if passed else "CFIR_H03_ORACLE_PREMISE_NO_GO",
        "claim_boundary": prereg["claim_if_pass"] if passed else prereg["stop_rule"],
        "truth_read_after_all_arm_scores": True,
        "truth_xy_evaluator_only": list(truth_xy),
        "score_definition": "S_chronological(candidate,kappa) - S_reversed(candidate,kappa)",
        "wind_binding": wind_binding,
        "event_audit": event_audit,
        "checks": checks,
        "median_map_error_m": {
            arm: float(np.median([row["map_error_m"] for row in by_kappa.values()]))
            for arm, by_kappa in results.items()
        },
        "median_normalized_true_rank": {
            arm: float(np.median([row["normalized_true_rank"] for row in by_kappa.values()]))
            for arm, by_kappa in results.items()
        },
        "results": results,
        "input_hashes": {
            "sensor_trace.csv": sha256(args.trace_dir / "sensor_trace.csv"),
            "wind_trace.csv": sha256(args.trace_dir / "wind_trace.csv"),
            "formal_runtime_manifest.json": sha256(args.trace_dir / "formal_runtime_manifest.json"),
            "candidate.csv": sha256(args.candidate_csv),
            "occupancy": sha256(args.occupancy),
            "environment_runtime.py": sha256(args.environment_runtime_py),
            "lmbt_py": sha256(args.lmbt_py),
            "reference_lmbt_json": sha256(args.reference_lmbt_json),
            "prereg": sha256(args.prereg),
            "script": sha256(Path(__file__)),
            "runtime_wind": {
                path.name: sha256(path)
                for path in sorted((args.realization / "wind").glob("wind_iteration_*"))
            },
        },
        "limitations": prereg["claims_forbidden_even_if_pass"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(report["verdict"])
    print(json.dumps(checks, sort_keys=True))
    print(json.dumps({
        "cfir_default": cfir_default,
        "sign_reversed_default": sign_default,
    }, sort_keys=True))


if __name__ == "__main__":
    main()

