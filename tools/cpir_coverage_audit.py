#!/usr/bin/env python3
"""Read-only coverage audit for CPIR historical fixed-trajectory replay.

This intentionally reads only bank metadata and historical pose/timing files;
it never opens world payloads, PMFS truth, or posterior outputs.  It mirrors
the native integer coordinate conversion and the 80-sample completed-stop
contract, and fails closed on unsupported pose cells.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


HOUSES = {"H01": "House01", "H02": "House02", "H03": "House03"}
SEEDS = range(10)
TIME_COUNT = 1500
STOP_SAMPLES = 80
UPDATES = 5


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def audit_case(bank_root: Path, historical_root: Path, short: str, seed: int):
    house = HOUSES[short]
    bank = bank_root / short
    cells = rows(bank / "cell_manifest.csv")
    native = {int(r["native_cell_index"]) for r in cells}
    runtime = (historical_root / house / f"seed{seed}" / "off" / "runtime" /
               f"{house}_seed{seed}_off_off")
    pose = rows(runtime / "sim_pose_trace.csv")
    timing = rows(runtime / "context_bank" / "source_update_timing.csv")
    if len(pose) < TIME_COUNT or len(timing) != UPDATES:
        raise RuntimeError(f"length:{short}:{seed}:{len(pose)}:{len(timing)}")
    t0 = timing[0]
    width = int(t0["grid_width"])
    height = int(t0["grid_height"])
    ox = float(t0["origin_x"])
    oy = float(t0["origin_y"])
    cs = float(t0["cell_size"])
    indices = []
    for r in pose[:TIME_COUNT]:
        ix = int((float(r["x"]) - ox) / cs)
        iy = int((float(r["y"]) - oy) / cs)
        if not (0 <= ix < width and 0 <= iy < height):
            raise RuntimeError(f"bounds:{short}:{seed}:{ix}:{iy}")
        indices.append(ix + iy * width)
    missing = sorted(set(i for i in indices if i not in native))
    moving = [int(r["is_moving"]) for r in pose[:TIME_COUNT]]
    stops = []
    start = None
    for i, value in enumerate(moving):
        if value == 0 and start is None:
            start = i
        if value != 0 and start is not None:
            if i - start >= STOP_SAMPLES:
                stops.append((start, start + STOP_SAMPLES - 1))
            start = None
    if start is not None and len(moving) - start >= STOP_SAMPLES:
        stops.append((start, start + STOP_SAMPLES - 1))
    stop_positions = {i for begin, end in stops for i in range(begin, end + 1)}
    missing_positions = [i for i, cell in enumerate(indices) if cell not in native]
    missing_stop_positions = [i for i in missing_positions if i in stop_positions]
    missing_motion_positions = [i for i in missing_positions if i not in stop_positions]
    update_times = [float(r["sim_time"]) for r in timing]
    sample_times = [float(r["t_sim_s"]) for r in pose[:TIME_COUNT]]
    visible = [sum(1 for _, end in stops if sample_times[end] <= u + 1e-10)
               for u in update_times]
    return {
        "house": short, "seed": seed, "pose_rows": len(pose),
        "width": width, "height": height, "bank_cells": len(native),
        "unique_native_cells": len(set(indices)), "missing_samples": len(missing_positions),
        "missing_unique": len(missing), "missing_indices": missing[:32],
        "missing_stop_samples": len(missing_stop_positions),
        "missing_motion_samples": len(missing_motion_positions),
        "missing_stop_indices": missing_stop_positions[:32],
        "complete_stops": len(stops), "visible_stops": visible,
        "schedule_ok": visible == [3, 6, 9, 12, 15],
        "coverage_ok": not missing,
    }


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--bank-root", type=Path, required=True)
    p.add_argument("--historical-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = []
    for short in HOUSES:
        for seed in SEEDS:
            out.append(audit_case(args.bank_root, args.historical_root, short, seed))
    report = {
        "contract": "CPIR_NESTED_SHADOW_COVERAGE_AUDIT_V1",
        "read_only": True, "world_payloads_opened": False,
        "cases": out,
        "all_coverage_ok": all(r["coverage_ok"] for r in out),
        "all_schedule_ok": all(r["schedule_ok"] for r in out),
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("all_coverage_ok", "all_schedule_ok")}, sort_keys=True))
    for r in out:
        print(f"{r['house']} seed{r['seed']}: missing={r['missing_samples']} unique={r['missing_unique']} stops={r['complete_stops']} visible={r['visible_stops']}")
    return 0 if report["all_coverage_ok"] and report["all_schedule_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
