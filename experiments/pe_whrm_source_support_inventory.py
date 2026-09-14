#!/usr/bin/env python3
"""Inventory source support without opening or mutating any experiment bank."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    groups = defaultdict(lambda: {"sources": set(), "runs": 0, "completed": 0})
    records = []
    for path in root.rglob("*_record.csv"):
        if "results" not in path.parts or "raw" not in path.parts:
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                row = next(csv.DictReader(f), None)
        except (OSError, StopIteration, csv.Error):
            continue
        if not row:
            continue
        required = ("dataset", "config_id", "wind_config", "sensor_config", "ground_truth_x", "ground_truth_y")
        if any(row.get(k) in (None, "") for k in required):
            continue
        key = (row["dataset"], row["config_id"], row["wind_config"], row["sensor_config"])
        src = (float(row["ground_truth_x"]), float(row["ground_truth_y"]))
        g = groups[key]
        g["sources"].add(src)
        g["runs"] += 1
        if str(row.get("declared_success", "")).lower() == "true" or str(row.get("gsl_action_status", "")).lower() in {"completed", "success", "localized"}:
            g["completed"] += 1
    rows = []
    for key, val in sorted(groups.items()):
        rows.append({
            "stratum": {"dataset": key[0], "config_id": key[1], "wind_config": key[2], "sensor_config": key[3]},
            "n_runs": val["runs"],
            "n_completed": val["completed"],
            "unique_source_coordinates": [list(x) for x in sorted(val["sources"])],
            "n_unique_sources": len(val["sources"]),
            "pe_whrm_pair_support": len(val["sources"]) >= 2,
        })
    eligible = [r for r in rows if r["pe_whrm_pair_support"] and r["n_completed"] >= 2]
    result = {
        "mechanism": "PE-WHRM",
        "root": str(root),
        "status": "SOURCE_SUPPORT_NO_GO" if not eligible else "SOURCE_SUPPORT_PRESENT",
        "strata_count": len(rows),
        "eligible_strata_count": len(eligible),
        "criterion": "At least two distinct true-source coordinates and two completed labelled runs within the same dataset/config/wind/sensor stratum.",
        "strata": rows,
        "interpretation": "Do not pool Houses or change the context stratum to manufacture source variation; that would confound geometry/context with source-relative evidence.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "strata_count": len(rows), "eligible_strata_count": len(eligible), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
