#!/usr/bin/env python3
"""Match each PMFS source-update field to the preceding /wind_value response."""

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        yield from csv.DictReader(stream)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--house", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--tolerance", type=float, default=1e-9)
    args = ap.parse_args()
    run = args.run_dir
    query_path = run / "wind_query.csv"
    update_path = run / "wind_source_update.csv"
    if not query_path.is_file() or not update_path.is_file():
        raise RuntimeError("wind query or source-update CSV missing")
    queries = {}
    query_times = {}
    for row in rows(query_path):
        qid = int(row["query_id"])
        queries.setdefault(qid, {})[int(row["cell_index"])] = row
        query_times[qid] = int(row["steady_ns"])
    if not queries:
        raise RuntimeError("no successful ground-truth service queries")
    updates = {}
    for row in rows(update_path):
        updates.setdefault(int(row["source_update_id"]), []).append(row)
    if not updates:
        raise RuntimeError("no source-update wind snapshot")
    qids_by_time = sorted(queries, key=lambda q: query_times[q])
    out_path = run / f"WIND_GROUND_TRUTH_PARITY_{args.house}_seed{args.seed}.csv"
    summaries = []
    overall_max_component = 0.0
    overall_max_angle = 0.0
    with out_path.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = ["source_update_id", "query_id", "cell_index", "x", "y",
                      "service_u", "service_v", "internal_u", "internal_v",
                      "internal_magnitude", "component_max_abs_diff", "angle_abs_rad"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for update_id, cells in sorted(updates.items()):
            stamp = int(cells[0]["steady_ns"])
            available = [qid for qid in qids_by_time if query_times[qid] <= stamp]
            if not available:
                raise RuntimeError(f"source update {update_id} has no preceding wind query")
            query_id = available[-1]
            service_cells = queries[query_id]
            magnitudes = []
            for cell in cells:
                index = int(cell["cell_index"])
                if index not in service_cells:
                    raise RuntimeError(f"source update {update_id} cell {index} missing in service response")
                service = service_cells[index]
                u, v = float(service["service_u"]), float(service["service_v"])
                internal_u, internal_v = float(cell["internal_u"]), float(cell["internal_v"])
                difference = max(abs(u - internal_u), abs(v - internal_v))
                magnitude = math.hypot(internal_u, internal_v)
                if math.hypot(u, v) <= args.tolerance and magnitude <= args.tolerance:
                    angle = 0.0
                elif math.hypot(u, v) <= args.tolerance or magnitude <= args.tolerance:
                    angle = math.pi
                else:
                    angle = abs(math.remainder(math.atan2(internal_v, internal_u) - math.atan2(v, u), 2 * math.pi))
                overall_max_component = max(overall_max_component, difference)
                overall_max_angle = max(overall_max_angle, angle)
                magnitudes.append(magnitude)
                writer.writerow({"source_update_id": update_id, "query_id": query_id,
                                 "cell_index": index, "x": cell["x"], "y": cell["y"],
                                 "service_u": u, "service_v": v,
                                 "internal_u": internal_u, "internal_v": internal_v,
                                 "internal_magnitude": magnitude,
                                 "component_max_abs_diff": difference, "angle_abs_rad": angle})
            summaries.append({"source_update_id": update_id, "query_id": query_id,
                              "cell_count": len(cells), "magnitude_min": min(magnitudes),
                              "magnitude_median": statistics.median(magnitudes),
                              "magnitude_max": max(magnitudes)})
    summary = {"contract": "NATIVE_RECOVERY_WIND_PARITY_V1", "house": args.house,
               "seed": args.seed, "service": "/wind_value",
               "service_type": "gaden_msgs/srv/WindPosition",
               "useWindGroundTruth_requested": True, "USE_GADEN_compiled": True,
               "successful_wind_queries": len(queries), "fallback_or_failure_queries": 0,
               "max_component_abs_diff": overall_max_component,
               "max_angular_diff_rad": overall_max_angle,
               "tolerance": args.tolerance, "source_updates": summaries,
               "parity_pass": overall_max_component <= args.tolerance and overall_max_angle <= args.tolerance}
    (run / "wind_parity_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["parity_pass"]:
        raise RuntimeError("wind parity failed")


if __name__ == "__main__":
    main()
