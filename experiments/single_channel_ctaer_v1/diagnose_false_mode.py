#!/usr/bin/env python3
"""Post-result CTAER window diagnosis; reports no new gate or parameter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctaer-py", type=Path, required=True)
    parser.add_argument("--taorl-py", type=Path, required=True)
    parser.add_argument("--sensor-trace", type=Path, required=True)
    parser.add_argument("--wind-trace", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--candidate-csv", type=Path, required=True)
    parser.add_argument("--loho-json", type=Path, required=True)
    parser.add_argument("--provider-py", type=Path, required=True)
    parser.add_argument("--formal-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("CTAER_DIAG_REFUSE_OVERWRITE")

    ctaer = __import__("importlib").util.spec_from_file_location("diag_ctaer", args.ctaer_py)
    if ctaer is None or ctaer.loader is None:
        raise ImportError("CTAER_DIAG_IMPORT")
    ctaer_mod = __import__("importlib").util.module_from_spec(ctaer)
    ctaer.loader.exec_module(ctaer_mod)
    taorl = ctaer_mod.import_module(args.taorl_py, "diag_taorl")
    provider = taorl.import_provider(args.provider_py)
    rows, measured, _ = taorl.load_rows(args.sensor_trace, args.wind_trace)
    candidates = taorl.read_candidates(args.candidate_csv)
    loho = json.loads(args.loho_json.read_text(encoding="utf-8"))
    parameter = next(f["selected_parameter"] for f in loho["folds"] if f["heldout_house"] == "H03")
    instant = taorl.instantaneous_response(rows, candidates, parameter, provider)
    forward, reverse, _, selected_tau = ctaer_mod.paired_scores(measured, instant, taorl)

    formal = json.loads(args.formal_result.read_text(encoding="utf-8"))
    truth_xy = np.asarray(formal["truth_xy_evaluator_only"], dtype=np.float64)
    map_xy = np.asarray(formal["results"]["CTAER_SHARED_TAU_ARROW_CONTRAST"]["map_xy"], dtype=np.float64)
    indices = {
        "true_candidate": int(np.argmin(np.sum((candidates - truth_xy) ** 2, axis=1))),
        "ctaer_map_candidate": int(np.argmin(np.sum((candidates - map_xy) ** 2, axis=1))),
    }
    n = int(round(taorl.WINDOW_S / taorl.OUTPUT_DT_S))

    def window_detail(index: int) -> dict:
        tau = float(selected_tau[index])
        f = taorl.first_order(instant[:, [index]], tau, reverse=False)[:, 0]
        r = taorl.first_order(instant[:, [index]], tau, reverse=True)[:, 0]
        windows = []
        for start in range(0, len(measured), n):
            stop = min(start + n, len(measured))
            if stop - start < 2:
                continue
            lf = float(taorl.ordinal_loss(measured[start:stop], f[start:stop, None], None)[0])
            lr = float(taorl.ordinal_loss(measured[start:stop], r[start:stop, None], None)[0])
            windows.append({
                "start_sample": start,
                "stop_sample_exclusive": stop,
                "start_t_s": float(rows[start]["t_sim_s"]),
                "stop_t_s": float(rows[stop - 1]["t_sim_s"]),
                "forward_loss": lf,
                "reverse_loss": lr,
                "reverse_minus_forward_evidence": lr - lf,
            })
        evidence = np.asarray([w["reverse_minus_forward_evidence"] for w in windows])
        positive = np.maximum(evidence, 0.0)
        return {
            "xy": candidates[index].tolist(),
            "selected_tau_s": tau,
            "aggregate_forward_loss": float(forward[index]),
            "aggregate_reverse_loss": float(reverse[index]),
            "aggregate_reverse_minus_forward": float(reverse[index] - forward[index]),
            "positive_window_fraction": float(np.mean(evidence > 0.0)),
            "median_window_evidence": float(np.median(evidence)),
            "minimum_window_evidence": float(evidence.min()),
            "maximum_window_evidence": float(evidence.max()),
            "largest_positive_share": float(positive.max() / positive.sum()) if positive.sum() else None,
            "windows": windows,
        }

    detail = {name: window_detail(index) for name, index in indices.items()}
    truth_e = np.asarray([w["reverse_minus_forward_evidence"] for w in detail["true_candidate"]["windows"]])
    map_e = np.asarray([w["reverse_minus_forward_evidence"] for w in detail["ctaer_map_candidate"]["windows"]])
    report = {
        "status": "POSTHOC_FALSE_MODE_DIAGNOSIS_NOT_A_NEW_GATE",
        "parameter_selection": False,
        "formal_result_sha256": taorl.sha256(args.formal_result),
        "candidates": detail,
        "paired_window_comparison": {
            "window_count": int(len(truth_e)),
            "map_evidence_greater_than_truth_count": int(np.sum(map_e > truth_e)),
            "truth_evidence_greater_than_map_count": int(np.sum(truth_e > map_e)),
            "ties": int(np.sum(truth_e == map_e)),
            "median_map_minus_truth_evidence": float(np.median(map_e - truth_e)),
        },
        "interpretation_rule": (
            "If the false MAP advantage is present in most windows, another pooling or abstention rule cannot recover source identity from this trace without adding information. "
            "If it is concentrated in a minority of windows, only a future independently justified and independently tested window-reliability mechanism remains plausible."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("CTAER_FALSE_MODE_DIAGNOSIS_WRITTEN")


if __name__ == "__main__":
    main()

