#!/usr/bin/env python3
"""Post-result diagnosis only; never selects a TAORL parameter or gate."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-py", type=Path, required=True)
    parser.add_argument("--sensor-trace", type=Path, required=True)
    parser.add_argument("--wind-trace", type=Path, required=True)
    parser.add_argument("--candidate-csv", type=Path, required=True)
    parser.add_argument("--loho-json", type=Path, required=True)
    parser.add_argument("--provider-py", type=Path, required=True)
    parser.add_argument("--formal-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gate = load_module(args.gate_py, "taorl_gate_diagnostic")
    provider = gate.import_provider(args.provider_py)
    rows, measured, _ = gate.load_rows(args.sensor_trace, args.wind_trace)
    candidates = gate.read_candidates(args.candidate_csv)
    loho = json.loads(args.loho_json.read_text(encoding="utf-8"))
    parameter = next(fold["selected_parameter"] for fold in loho["folds"]
                     if fold["heldout_house"] == "H03")
    instant = gate.instantaneous_response(rows, candidates, parameter, provider)
    formal = json.loads(args.formal_result.read_text(encoding="utf-8"))
    truth_xy = np.asarray(formal["truth_xy_evaluator_only"], dtype=float)
    truth = int(np.argmin(np.sum((candidates - truth_xy) ** 2, axis=1)))
    map_xy = np.asarray(formal["results"]["TAORL_FORWARD_WINDOWED"]["map_xy"], dtype=float)
    best = int(np.argmin(np.sum((candidates - map_xy) ** 2, axis=1)))
    tau = float(formal["profiled_tau_at_true_candidate_s"]["forward"])
    filtered = gate.first_order(instant, tau)
    window = int(round(gate.WINDOW_S / gate.OUTPUT_DT_S))

    def profile(index: int) -> dict:
        correlations = []
        for start in range(0, len(measured), window):
            stop = min(start + window, len(measured))
            if stop - start < 2:
                continue
            value = spearmanr(measured[start:stop], filtered[start:stop, index]).statistic
            correlations.append(None if not np.isfinite(value) else float(value))
        raw = instant[:, index]
        return {
            "xy": candidates[index].tolist(),
            "instant_exact_zero_fraction": float(np.mean(raw == 0.0)),
            "instant_positive_during_measured_hit_fraction": float(np.mean(raw[measured > 0.1] > 0.0))
                if np.any(measured > 0.1) else None,
            "window_spearman": correlations,
            "finite_window_spearman_median": float(np.median([x for x in correlations if x is not None]))
                if any(x is not None for x in correlations) else None,
        }

    report = {
        "status": "POSTHOC_FAILURE_DIAGNOSIS_NOT_A_NEW_GATE",
        "parameter_selection": False,
        "measured_hit_fraction_gt_0p1ppm": float(np.mean(measured > 0.1)),
        "true_candidate": profile(truth),
        "taorl_map_candidate": profile(best),
        "interpretation_rule": (
            "If the true candidate is nonzero during measured hits but has weak within-window rank "
            "correlation, the remaining error is response-shape/transport aliasing rather than missing support."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
