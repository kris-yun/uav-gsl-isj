#!/usr/bin/env python3
"""Standalone synthetic audit for the VGR fixed-trajectory replay."""
from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tnqc_vgr_fixed_trajectory_replay as replay


def main():
    root = Path(tempfile.mkdtemp(prefix="tnqc_vgr_replay_test_"))
    try:
        bank = root / "context_bank"
        d = bank / "source_update_0001"
        d.mkdir(parents=True)
        with (bank / "source_update_timing.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run_uuid", "source_update_id", "sim_time"])
            w.writerow(["fixture", 1, 295.0])

        probs = {}
        with (d / "measured_hit_probability.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["cell_index","grid_i","grid_j","x","y","occupancy",
                        "probability","logOdds","confidence","omega",
                        "distanceFromRobot","originalPropagationDirection_x",
                        "originalPropagationDirection_y"])
            idx = 0
            for gi in range(4):
                for gj in range(4):
                    p = 0.10 + 0.05*gi + 0.02*gj
                    probs[idx] = p
                    w.writerow([idx,gi,gj,gi,gj,"Free",p,math.log(p/(1-p)),
                                0.8,0,0,0,0])
                    idx += 1

        cands = []
        for oi in (0, 2):
            for oj in (0, 2):
                cands.append((f"quadtree_{oi}_{oj}_2_2",oi,oj,2,2,oi+1,oj+1))

        align_rows = []
        native_logs = {}
        for ci,(cid,oi,oj,si,sj,cx,cy) in enumerate(cands):
            a = {}
            for idx in range(16):
                gi, gj = divmod(idx, 4)
                measured = probs[idx]
                simulated = min(max(
                    measured + (ci-1.5)*0.015 + 0.01*(gi-oj), 0.01), 0.99)
                a[idx] = (measured, 0.8, simulated)
                align_rows.append([cid,idx,gi,gj,gi,gj,measured,0.8,
                                   simulated,abs(measured-simulated)])
            native_logs[cid] = replay.native_log_score(a, 1.0)

        with (d / "candidate_manifest.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run_uuid","source_update_id","candidate_id","origin_i",
                        "origin_j","size_i","size_j","center_x","center_y",
                        "native_source_x","native_source_y","native_score",
                        "hit_map_file"])
            for cid,oi,oj,si,sj,cx,cy in cands:
                w.writerow(["fixture",1,cid,oi,oj,si,sj,cx,cy,cx,cy,
                            math.exp(native_logs[cid]),""])

        with (d / "candidate_support_alignment.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["candidate_id","cell_index","grid_i","grid_j","x","y",
                        "measured_probability","measured_confidence",
                        "simulated_hit_probability","absolute_residual"])
            w.writerows(align_rows)

        cells,_ = replay.load_cells(d)
        candidates = replay.load_candidates(d)
        part = replay.final_partition(cells, candidates)
        native = replay.posterior(part, native_logs)
        with (d / "source_posterior.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["cell_index","x","y","source_probability"])
            for idx in sorted(native):
                w.writerow([idx,cells[idx].x,cells[idx].y,native[idx]])

        exported = replay.exported_posterior(d)
        audit = replay.diff(native, exported)
        assert audit["max_abs"] < 1e-15
        assert audit["l1"] < 1e-15
        assert replay.choose_final_update(bank, 300.0) == (1, 295.0)

        fixture_metrics = replay.metrics(native, cells, 0.0, 0.0)
        reported = fixture_metrics["pmfs_top5_error_m"]
        (root / "launch.log").write_text(
            "fixture RESULT IS: Success=0, Search_t=300.00, "
            f"Error={reported:.2f}\n",
            encoding="utf-8")
        native_result = replay.native_result_line(root)
        assert native_result["search_t"] == 300.0
        assert abs(native_result["reported_top5_error_m"] - reported) <= 0.011

        # Exercise the full replay CLI, not only helper functions.  This locks
        # the endpoint anchor, final-leaf scope, reconstruction audit and JSON
        # contract together.
        out_json = root / "fixture_replay.json"
        proc = subprocess.run(
            [sys.executable, str(Path(replay.__file__)),
             "--run-dir", str(root),
             "--truth-x", "0.0", "--truth-y", "0.0",
             "--json-out", str(out_json)],
            check=False, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["contract"] == (
            "TNQC_VGR_FIXED_TRAJECTORY_300S_REPLAY_V3_FINAL_LEAF_GATE")
        assert payload["candidate_gate_scope"] == (
            "final_partition_leaf_candidates_only")
        assert payload["native_reconstruction_audit"]["pass"]
        assert payload["native_cpp_endpoint_audit"]["pass"]
        assert payload["valid_for_gate"]

        # Candidate-wise sign consistency is insufficient: naive averaging
        # can reverse the ordering between two positive candidates.  The
        # shared candidate-bank gate must detect this and abstain.
        diag = {
            "a": {"valid": True, "edge_count": 4,
                  "canonical_cosine": 0.51, "local_order_agreement": 0.01},
            "b": {"valid": True, "edge_count": 4,
                  "canonical_cosine": 0.50, "local_order_agreement": 1.00},
        }
        gate = replay.candidate_order_concordance(diag)
        assert gate["valid"]
        assert gate["pair_count"] == 1
        assert abs(gate["concordance"] + 1.0) < 1e-12
        assert gate["strength"] == 0.0

        # Agreement restores unit strength while preserving affine ordering.
        diag["a"]["local_order_agreement"] = 0.9
        diag["b"]["local_order_agreement"] = 0.2
        gate = replay.candidate_order_concordance(diag)
        assert gate["valid"]
        assert abs(gate["concordance"] - 1.0) < 1e-12
        assert abs(gate["strength"] - 1.0) < 1e-12
        assert (gate["strength"] * diag["a"]["canonical_cosine"] >
                gate["strength"] * diag["b"]["canonical_cosine"])

        # Evaluated ancestors must not influence the gate over terminal
        # hypotheses.  Here final leaves a/b agree, while a synthetic
        # subdivided ancestor c would flip the all-evaluated concordance.
        diag["c"] = {"valid": True, "edge_count": 4,
                     "canonical_cosine": 0.10,
                     "local_order_agreement": 0.95}
        final_leaf_gate = replay.candidate_order_concordance(diag, ["a", "b"])
        all_evaluated_gate = replay.candidate_order_concordance(diag)
        assert final_leaf_gate["valid"]
        assert final_leaf_gate["strength"] == 1.0
        assert all_evaluated_gate["strength"] < final_leaf_gate["strength"]

        print("TNQC_VGR_FIXED_TRAJECTORY_REPLAY_TEST_PASS")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
