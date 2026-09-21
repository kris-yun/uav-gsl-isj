#!/usr/bin/env python3
"""GCSI fixed-trajectory 300-s counterfactual replay.

This is deliberately isolated from ROS/planner behavior.  It consumes the same
frozen context-bank assets and native C++ endpoint evaluator as the TNQC replay.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import gcsi_composite as gcsi
import tnqc_vgr_fixed_trajectory_replay as base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--truth-x", type=float, required=True)
    ap.add_argument("--truth-y", type=float, required=True)
    ap.add_argument("--budget-s", type=float, default=300.0)
    ap.add_argument("--source-discrimination-power", type=float, default=1.0)
    ap.add_argument("--block-size-m", type=float, default=0.9)
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
    part = base.final_partition(cells, candidates)
    active_ids = sorted(set(part.values()))

    result = gcsi.calibrated_candidate_scores(
        cells=cells,
        alignments=alignment,
        active_candidate_ids=active_ids,
        power=args.source_discrimination_power,
        block_size_m=args.block_size_m,
        origin_x=grid_meta.origin_x,
        origin_y=grid_meta.origin_y,
    )

    # Native score reconstruction is preserved for an integrity comparison.
    native_all = {
        cid: base.native_log_score(
            alignment[cid], args.source_discrimination_power)
        for cid in candidates
    }
    native_replay = base.posterior(part, native_all)
    native_export = base.exported_posterior(d)
    reconstruction = base.diff(native_replay, native_export)

    # Scores outside the final partition are irrelevant to terminal posterior.
    tempered = base.posterior(part, result["tempered_scores"])
    gcsi_posterior = base.posterior(part, result["gcsi_scores"])

    outdir = args.run_dir / "gcsi_endpoint_posteriors"
    outdir.mkdir(parents=True, exist_ok=True)
    native_csv = outdir / "native_exported.csv"
    tempered_csv = outdir / "scalar_tempered.csv"
    gcsi_csv = outdir / "gcsi_pairwise_sandwich.csv"
    base.write_endpoint_posterior(native_csv, native_export, cells)
    base.write_endpoint_posterior(tempered_csv, tempered, cells)
    base.write_endpoint_posterior(gcsi_csv, gcsi_posterior, cells)

    evaluator = args.cpp_endpoint_evaluator.resolve()
    nm = base.cpp_endpoint_metrics(
        evaluator, native_csv, args.truth_x, args.truth_y, grid_meta)
    tm = base.cpp_endpoint_metrics(
        evaluator, tempered_csv, args.truth_x, args.truth_y, grid_meta)
    gm = base.cpp_endpoint_metrics(
        evaluator, gcsi_csv, args.truth_x, args.truth_y, grid_meta)

    payload = {
        "contract": "GCSI_V1_FIXED_TRAJECTORY_300S_COUNTERFACTUAL",
        "run_dir": str(args.run_dir),
        "source_update_id": uid,
        "sim_time_s": sim_time,
        "block_size_m": args.block_size_m,
        "final_leaf_candidate_count": len(active_ids),
        "scoring_truth_blind": True,
        "native_reconstruction": reconstruction,
        "native_best_candidate": result["native_best_candidate"],
        "scalar_temperature": result["scalar_temperature"],
        "candidate_diagnostics": result["candidate_diagnostics"],
        "endpoint": {
            "native": nm,
            "scalar_tempered_control": tm,
            "gcsi": gm,
            "gcsi_minus_native_error_m":
                gm["pmfs_top5_error_m"] - nm["pmfs_top5_error_m"],
            "gcsi_minus_scalar_tempered_error_m":
                gm["pmfs_top5_error_m"] - tm["pmfs_top5_error_m"],
        },
        "posterior_csv": {
            "native": str(native_csv),
            "scalar_tempered": str(tempered_csv),
            "gcsi": str(gcsi_csv),
        },
    }

    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
