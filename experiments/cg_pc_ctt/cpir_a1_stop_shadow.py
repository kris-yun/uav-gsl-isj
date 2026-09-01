#!/usr/bin/env python3
"""Stop-only A1 diagnostic on the frozen CPIR bank.

This is deliberately *not* the formal A0/A1/A2/A3 nested shadow.  A1 needs
only the first 80 samples of each completed stop, so it can be evaluated when
historical motion poses fall on occupied cells that are absent from the
free-cell bank.  A2/A3 remain fail-closed in ``cpir_three_module_shadow.py``
because their continuous sensor state requires every native trajectory sample.

Stage 1 freezes A1 posteriors before opening PMFS final posteriors or truth;
stage 2 then computes the official top-5%-expected-value endpoints.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from cpir_three_module_shadow import (
    CONTRACT, HOUSES, SOURCE_UPDATES, BankHouse, Case, carrier_scores,
    endpoint, load_case, projection, read_csv, read_world_streams, sha256_file,
)


def build_a1_events(bank: BankHouse, cases: list[Case]) -> np.ndarray:
    max_stops = max(len(c.stops) for c in cases)
    result = np.zeros((len(cases), len(bank.carriers), 8, max_stops), dtype=np.bool_)
    # Only stop samples are read.  This is the exact A1 raw-event definition;
    # unsupported motion sentinels are never dereferenced.
    stop_streams = []
    for case in cases:
        streams = []
        for stop in case.stops:
            streams.extend(int(case.stream_indices[t]) for t in stop)
        if any(s < 0 for s in streams):
            raise RuntimeError(f"CPIR_A1_STOP_SENTINEL:{case.house}:{case.seed}")
        stop_streams.extend(streams)
    union = np.unique(np.asarray(stop_streams, dtype=np.int64))
    positions = {int(v): i for i, v in enumerate(union)}
    for carrier_i, carrier in enumerate(bank.carriers):
        for member in range(8):
            values = read_world_streams(bank.world_paths[carrier_i][member], union)
            for case_i, case in enumerate(cases):
                for stop_i, stop in enumerate(case.stops):
                    samples = np.asarray([positions[int(case.stream_indices[t])] for t in stop], dtype=np.int64)
                    # values[stream,time] -> diagonal along the historical
                    # pose/time tape, exactly as the bank contract defines.
                    physical = values[samples, stop]
                    result[case_i, carrier_i, member, stop_i] = bool(np.max(physical) > 0.1)
            done = carrier_i * 8 + member + 1
            if done % 100 == 0:
                print(f"CPIR_A1_PROGRESS={bank.house}:{done}/{len(bank.carriers)*8}", flush=True)
    return result


def stage1(bank_root: Path, historical_root: Path, support: Path, output: Path):
    output.mkdir(parents=True, exist_ok=False)
    support_rows = read_csv(support)
    all_meta = []
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        events = build_a1_events(bank, cases)
        np.savez_compressed(output / f"{house}_A1_EVENTS.npz", events=events,
                            carrier_ids=np.asarray(bank.carriers),
                            cell_indices=bank.cell_indices,
                            cell_to_carrier=bank.cell_to_carrier,
                            carrier_cell_counts=bank.carrier_cell_counts)
        posterior_rows = []
        for case_i, case in enumerate(cases):
            q = (events[case_i, :, :, :len(case.stops)].sum(axis=1) + 0.5) / 9.0
            for update_i, visible in enumerate(case.visible, start=1):
                _, carrier = carrier_scores(bank.q0, q, case.observed_events, visible, "count_only")
                posterior_rows.append(carrier)
                all_meta.append({"house": house, "seed": case.seed, "update_id": update_i,
                                 "visible_stops": [int(v) for v in visible],
                                 "missing_motion_samples": int(np.count_nonzero(case.stream_indices < 0))})
        np.savez_compressed(output / f"{house}_A1_POSTERIORS.npz",
                            a1=np.stack(posterior_rows))
        print(f"CPIR_A1_STAGE1_{house}=PASS", flush=True)
    files = {p.name: sha256_file(p) for p in sorted(output.iterdir()) if p.is_file()}
    manifest = {"contract": "CPIR_A1_STOP_ONLY_DIAGNOSTIC_V1",
                "status": "A1_FROZEN_BEFORE_A0_OR_TRUTH",
                "base_formula_contract": CONTRACT,
                "bank_root": str(bank_root), "historical_root": str(historical_root),
                "support_sha256": sha256_file(support), "files": files,
                "formula": {"members": 8, "threshold_ppm": 0.1,
                            "stop_samples": 80, "score": "count_only",
                            "motion_policy": "not_read_for_A1"},
                "metadata": all_meta}
    manifest["manifest_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()
    (output / "PRETRUTH_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage2(bank_root: Path, historical_root: Path, support: Path, stage1_dir: Path, output: Path):
    manifest = json.loads((stage1_dir / "PRETRUTH_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "A1_FROZEN_BEFORE_A0_OR_TRUTH":
        raise RuntimeError("CPIR_A1_STAGE1_CONTRACT")
    for name, digest in manifest["files"].items():
        if sha256_file(stage1_dir / name) != digest:
            raise RuntimeError(f"CPIR_A1_STAGE1_HASH:{name}")
    output.mkdir(parents=True, exist_ok=False)
    support_rows = read_csv(support)
    pairs = []
    for house in HOUSES:
        bank = BankHouse.load(house, bank_root, support_rows)
        events_post = np.load(stage1_dir / f"{house}_A1_POSTERIORS.npz")["a1"]
        cases = [load_case(historical_root, house, seed, bank, strict_full_coverage=False)
                 for seed in range(10)]
        for case_i, case in enumerate(cases):
            final_dir = case.runtime.parent.parent
            posterior_path = final_dir / "final_posterior.csv"
            result_path = final_dir / "case_result.json"
            native_rows = read_csv(posterior_path)
            result = json.loads(result_path.read_text(encoding="utf-8"))
            truth = tuple(float(v) for v in result["truth_eval_only"])
            baseline = endpoint(native_rows, np.asarray([float(r["source_probability"]) for r in native_rows]), truth)
            mass = projection(events_post[case_i * SOURCE_UPDATES + SOURCE_UPDATES - 1],
                              bank.cell_to_carrier, bank.carrier_cell_counts)
            cell_rows = [{"cell_index": str(int(c)), "x": str(float(x)), "y": str(float(y))}
                         for c, x, y in zip(bank.cell_indices, bank.cell_x, bank.cell_y)]
            a1 = endpoint(cell_rows, mass, truth)
            pairs.append({"house": house, "seed": case.seed,
                          "pmfs_error_m": baseline["error_m"], "a1_error_m": a1["error_m"],
                          "relative_improvement": (baseline["error_m"] - a1["error_m"]) / baseline["error_m"],
                          "missing_motion_samples": int(np.count_nonzero(case.stream_indices < 0))})
    with (output / "A1_PAIRS.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(pairs[0])); writer.writeheader(); writer.writerows(pairs)
    x = np.asarray([p["pmfs_error_m"] for p in pairs]); y = np.asarray([p["a1_error_m"] for p in pairs])
    summary = {"contract": "CPIR_A1_STOP_ONLY_DIAGNOSTIC_V1",
               "status": "A1_STOP_ONLY_SHADOW_COMPLETE_NOT_NESTED",
               "closed_loop": False, "gaden_runs": 0, "neural_training": False,
               "pairs": len(pairs), "pmfs_mean_m": float(x.mean()), "a1_mean_m": float(y.mean()),
               "pmfs_median_m": float(np.median(x)), "a1_median_m": float(np.median(y)),
               "pooled_relative_improvement": float((x.sum()-y.sum())/x.sum()),
               "wins": int(np.count_nonzero(y < x - 1e-12)),
               "losses": int(np.count_nonzero(y > x + 1e-12)),
               "ties": int(np.count_nonzero(np.abs(y-x) <= 1e-12)),
               "by_house": {h: {"pairs": [p for p in pairs if p["house"] == h]}
                            for h in HOUSES},
               "note": "A1 uses only covered completed-stop samples; A2/A3 formal replay is blocked by missing motion cells."}
    (output / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "VERDICT.txt").write_text("A1_STOP_ONLY_SHADOW_COMPLETE_NOT_NESTED\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("status", "pmfs_mean_m", "a1_mean_m", "pooled_relative_improvement", "wins", "losses", "ties")}, indent=2), flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=("1", "2"), required=True)
    p.add_argument("--bank-root", type=Path, required=True)
    p.add_argument("--historical-root", type=Path, required=True)
    p.add_argument("--support", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--stage1", type=Path)
    a = p.parse_args()
    if a.stage == "1":
        stage1(a.bank_root, a.historical_root, a.support, a.output)
    else:
        if not a.stage1:
            p.error("--stage1 required")
        stage2(a.bank_root, a.historical_root, a.support, a.stage1, a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
