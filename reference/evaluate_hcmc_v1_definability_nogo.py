#!/usr/bin/env python3
"""Post-truth diagnostics after a frozen source-blind HCMC definability NO-GO."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import statistics
import sys
from pathlib import Path


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("hcmc_v1_frozen_eval", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--pretruth-root", type=Path, required=True)
    parser.add_argument("--truth-sidecar", type=Path, required=True)
    parser.add_argument("--cpp-endpoint-evaluator", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--csv-out", type=Path, required=True)
    args = parser.parse_args()
    h = load_validator(args.validator.resolve())
    freeze_path = args.pretruth_root / "PRE_TRUTH_DEFINABILITY_FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze["phase"] != "PRE_TRUTH_DEFINABILITY_FREEZE" or freeze["truth_inputs_loaded"]:
        raise ValueError("invalid pre-truth definability freeze")
    for relative, expected in freeze["generated_file_sha256"].items():
        path = args.pretruth_root / relative
        if not path.is_file() or h.sha256_file(path) != expected:
            raise ValueError(f"pre-truth hash mismatch: {relative}")
    truth_payload = json.loads(args.truth_sidecar.read_text(encoding="utf-8"))
    if truth_payload["data_independence_classification"] != "TRUE_INDEPENDENT_PLUME_VALIDATION":
        raise ValueError("wrong truth-sidecar classification")
    truths = truth_payload["cases"]
    evaluator = args.cpp_endpoint_evaluator.resolve()
    results = []
    partial_hcmc_errors = []
    native_errors = []
    partial_false_collapses = 0

    for case_dir in h.discover_case_dirs(args.native_root.resolve(), []):
        case_id = case_dir.name
        truth_x = float(truths[case_id]["truth_x"])
        truth_y = float(truths[case_id]["truth_y"])
        bank = case_dir / "context_bank"
        update_id, update_time, timing = h.select_final_update(bank, 300.0)
        metadata = h.grid_metadata(timing)
        update_dir = bank / f"source_update_{update_id:04d}"
        cells = h.load_cells(update_dir, metadata)
        final_ids, geometry, _ = h.derive_final_leaves(update_dir, cells)
        case_pretruth = args.pretruth_root / case_id
        native_path = case_pretruth / "native_posterior.csv"
        native_cells, native_posterior = h.read_posterior(native_path)
        native_endpoint = h.linked_native_endpoint(evaluator, native_path, metadata, truth_x, truth_y)
        native_diag = h.posterior_diagnostics(native_cells, native_posterior, truth_x, truth_y)
        logged = h.logged_native_endpoint(case_dir)
        parity_delta = abs(float(native_endpoint["pmfs_top5_error_m"]) - float(logged["reported_top5_error_m"]))
        native_errors.append(float(native_endpoint["pmfs_top5_error_m"]))

        rank_rows = h.read_csv(case_pretruth / "candidate_ranks.csv")
        ranks = {row["candidate_id"]: row for row in rank_rows}
        nearest = min(
            (
                ((geometry[key].origin_i + geometry[key].size_i / 2.0) * metadata.cell_size + metadata.origin_x,
                 (geometry[key].origin_j + geometry[key].size_j / 2.0) * metadata.cell_size + metadata.origin_y,
                 key)
                for key in final_ids
            ),
            key=lambda item: (item[0] - truth_x) ** 2 + (item[1] - truth_y) ** 2,
        )
        nearest_diag = {
            "candidate_id": nearest[2],
            "candidate_center_x": nearest[0],
            "candidate_center_y": nearest[1],
            "candidate_center_truth_distance_m": ((nearest[0] - truth_x) ** 2 + (nearest[1] - truth_y) ** 2) ** 0.5,
            "hcmc_average_percentile_rank": float(ranks[nearest[2]]["average_percentile_rank"]),
            "hcmc_ordinal_rank_best_is_1": int(ranks[nearest[2]]["ordinal_rank_best_is_1"]),
        }
        hcmc_path = case_pretruth / "hcmc_posterior.csv"
        hcmc_endpoint = hcmc_diag = None
        false_collapse = None
        if hcmc_path.is_file():
            hcmc_cells, hcmc_posterior = h.read_posterior(hcmc_path)
            hcmc_endpoint = h.linked_native_endpoint(evaluator, hcmc_path, metadata, truth_x, truth_y)
            hcmc_diag = h.posterior_diagnostics(hcmc_cells, hcmc_posterior, truth_x, truth_y)
            partial_hcmc_errors.append(float(hcmc_endpoint["pmfs_top5_error_m"]))
            false_collapse = (
                hcmc_diag["full_posterior_expected_source_distance_m"]
                > native_diag["full_posterior_expected_source_distance_m"] + h.NON_WORSE_NUMERICAL_TOLERANCE_M
                and hcmc_diag["effective_support_cells"] < native_diag["effective_support_cells"] - 1e-9
            )
            partial_false_collapses += int(false_collapse)
        results.append({
            "case_id": case_id,
            "truth": [truth_x, truth_y],
            "native_endpoint": native_endpoint,
            "hcmc_endpoint": hcmc_endpoint,
            "native_logged_endpoint": logged,
            "endpoint_parity_delta_m": parity_delta,
            "endpoint_parity_pass": parity_delta <= h.ENDPOINT_PARITY_TOLERANCE_M,
            "native_diagnostics": native_diag,
            "hcmc_diagnostics": hcmc_diag,
            "nearest_truth_candidate": nearest_diag,
            "false_confident_collapse": false_collapse,
            "hcmc_status": "DEFINED" if hcmc_endpoint else "UNDEFINED_ALL_CANDIDATES_INVALID",
        })

    output = {
        "contract": "HCMC_V1_INDEPENDENT_DEFINABILITY_NOGO_DIAGNOSTICS_V1",
        "data_independence_classification": "TRUE_INDEPENDENT_PLUME_VALIDATION",
        "pretruth_freeze_sha256": h.sha256_file(freeze_path),
        "truth_sidecar_sha256": h.sha256_file(args.truth_sidecar),
        "endpoint_evaluator_sha256": h.sha256_file(evaluator),
        "native_errors_m": native_errors,
        "hcmc_errors_m": [None if item["hcmc_endpoint"] is None else item["hcmc_endpoint"]["pmfs_top5_error_m"] for item in results],
        "native_mean_m": statistics.mean(native_errors),
        "hcmc_six_case_mean_m": None,
        "pooled_six_case_improvement_percent": None,
        "non_worse_six_case_count": None,
        "defined_five_case_hcmc_mean_m_diagnostic_only": statistics.mean(partial_hcmc_errors),
        "endpoint_parity_all_six_pass": all(item["endpoint_parity_pass"] for item in results),
        "random_leaf_control": "NOT_EVALUABLE_ON_SIX_CASES_BECAUSE_REAL_HCMC_POSTERIOR_UNDEFINED",
        "spatial_shuffle_control": "NOT_EVALUABLE_ON_SIX_CASES_BECAUSE_REAL_HCMC_POSTERIOR_UNDEFINED",
        "false_confident_collapse_six_case_count": None,
        "defined_five_case_false_confident_collapse_count_diagnostic_only": partial_false_collapses,
        "cases": results,
        "verdict": "HCMC_V1_INDEPENDENT_OFFLINE_NO_GO",
        "reason": "H01_R2026092201 has zero valid HCMC candidates under the frozen formula, so the six-case HCMC posterior/error vector is undefined",
    }
    args.json_out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with args.csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("case_id", "native_error_m", "hcmc_error_m", "hcmc_status", "endpoint_parity_delta_m", "endpoint_parity_pass", "false_confident_collapse"), lineterminator="\n")
        writer.writeheader()
        for item in results:
            writer.writerow({
                "case_id": item["case_id"],
                "native_error_m": item["native_endpoint"]["pmfs_top5_error_m"],
                "hcmc_error_m": "" if item["hcmc_endpoint"] is None else item["hcmc_endpoint"]["pmfs_top5_error_m"],
                "hcmc_status": item["hcmc_status"],
                "endpoint_parity_delta_m": item["endpoint_parity_delta_m"],
                "endpoint_parity_pass": item["endpoint_parity_pass"],
                "false_confident_collapse": "" if item["false_confident_collapse"] is None else item["false_confident_collapse"],
            })
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
