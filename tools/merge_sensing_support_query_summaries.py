#!/usr/bin/env python3
"""Merge the eight precommitted source/wind query-batch manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summaries = sorted(args.summary_dir.glob("ENDPOINT_QUERY_*.json"))
    if len(summaries) != 8:
        raise RuntimeError(f"expected 8 batch summaries, found {len(summaries)}")
    loaded = [json.loads(path.read_text(encoding="utf-8")) for path in summaries]
    keys = []
    manifest = []
    for summary in loaded:
        if summary["status"] != "PASS" or summary["raw_cache_only"] is not True or summary["new_gaden_dataset_generated"] is not False or summary["non_design_wind_queried"] is not False:
            raise RuntimeError(f"batch failed policy: {summary}")
        manifest.extend(summary["manifest"])
        keys.extend((item["route_id"], item["source"], item["wind"]) for item in summary["manifest"])
    if len(manifest) != 96 or len(set(keys)) != 96:
        raise RuntimeError(f"merged trace cardinality/key failure: {len(manifest)} {len(set(keys))}")
    result = {
        "schema": "SENSING_SUPPORT_ENDPOINT_DESIGN_QUERY_V1",
        "mode": "EXISTING_RAW_CACHE_ONLY_NO_SIMULATION",
        "winds_queried": ["W_fast", "W_slow"],
        "non_design_wind_queried": False,
        "sources": ["S_truth", "S_k01", "S_k10", "S_k22"],
        "candidate_count": 12,
        "trace_count": len(manifest),
        "total_rows": sum(item["rows"] for item in manifest),
        "receiver_channels": ["plus", "minus"],
        "channel_compression": "NONE_ORDERED_CHANNELS_PRESERVED",
        "fopdt": {"dead_s": 0.4, "rise_s": 1.2, "recovery_s": 1.2, "dt_s": 0.2, "independent_receiver_states": True},
        "raw_cache_only": True,
        "filament_simulator_started": False,
        "new_gaden_dataset_generated": False,
        "batch_summary_paths": [path.name for path in summaries],
        "manifest": sorted(manifest, key=lambda item: (item["route_id"], item["source"], item["wind"])),
        "status": "PASS" if all(item["rows"] == 750 for item in manifest) else "FAIL",
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("trace_count", "total_rows", "status")}))


if __name__ == "__main__":
    main()
