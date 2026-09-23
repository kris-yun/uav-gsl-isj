#!/usr/bin/env python3
"""Capture the R2 GMRF field as a read-only observer at the Native snapshot.

The PMFS binary remains on /wind_value. This process only reads the frozen
cell list and queries /WindEstimation; it cannot write PMFS algorithm state.
"""

import argparse
import csv
import math
import os
import time
from pathlib import Path

import rclpy
from gmrf_msgs.srv import WindEstimation


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wind-snapshot", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--deadline-s", type=float, default=300)
    args = ap.parse_args()
    deadline = time.monotonic() + args.deadline_s
    while time.monotonic() < deadline:
        if args.wind_snapshot.is_file() and args.wind_snapshot.stat().st_size:
            with args.wind_snapshot.open(newline="") as fh:
                cells = list(csv.DictReader(fh))
            if cells and all(row.get("source_update_id") == "1" for row in cells):
                break
        time.sleep(0.1)
    else:
        raise RuntimeError("R1 wind snapshot missing before deadline")
    if len({int(row["cell_index"]) for row in cells}) != len(cells):
        raise RuntimeError("duplicate R1 wind cell index")
    rclpy.init()
    node = rclpy.create_node("native_r1_gmrf_observer")
    try:
        client = node.create_client(WindEstimation, "/WindEstimation")
        while not client.wait_for_service(timeout_sec=1.0):
            if time.monotonic() >= deadline:
                raise RuntimeError("/WindEstimation unavailable")
        req = WindEstimation.Request()
        req.x = [float(row["x"]) for row in cells]
        req.y = [float(row["y"]) for row in cells]
        query_ns = time.monotonic_ns()
        future = client.call_async(req)
        rclpy.spin_until_future_complete(node, future, timeout_sec=30.0)
        response = future.result()
        if response is None or len(response.u) != len(cells) or len(response.v) != len(cells):
            raise RuntimeError("GMRF response missing or wrong shape")
        tmp = args.output.with_suffix(".partial")
        with tmp.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["source_update_id", "snapshot_steady_ns", "observer_query_steady_ns",
                             "cell_index", "x", "y", "gmrf_u", "gmrf_v"])
            for row, u, v in zip(cells, response.u, response.v):
                if not math.isfinite(u) or not math.isfinite(v):
                    raise RuntimeError("nonfinite GMRF response")
                writer.writerow([1, row["steady_ns"], query_ns,
                                 row["cell_index"], row["x"], row["y"], u, v])
        os.replace(tmp, args.output)
        print(f"R1_GMRF_OBSERVER_CAPTURED cells={len(cells)} query_lag_ns={query_ns-int(cells[0]['steady_ns'])}", flush=True)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
