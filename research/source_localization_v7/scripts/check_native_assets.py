#!/usr/bin/env python3
"""Verify OCB provenance and run a fixed, source-blind two-probe data pilot.

This is an ingestion/readout pilot, not a localization score or Level-2 test.
Probe ranks 1 and 2 and all ten native frames are fixed before reading values.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gsl_discrimination.data import OCBDataset, QualificationError, SynchronousBlock


def check(root, pilot_dir=None):
    dataset = OCBDataset(root)
    result = dataset.audit()
    entries = []
    for world in dataset.worlds:
        block = dataset.to_block(world, range(10), ["1", "2"])
        refused = []
        for label, call in [
            ("continuous_dynamic", block.require_dynamic),
            ("local_wind", lambda: dataset.local_wind(world, 0)),
            ("temporal_interpolation", lambda: dataset.query_time(world, 60.0)),
            ("source_occupancy", lambda: block.qualification.require("source_occupancy_validated")),
        ]:
            try:
                call()
            except QualificationError:
                refused.append(label)
            else:
                raise AssertionError(f"unqualified operation was admitted: {label}")
        exact = None
        if pilot_dir:
            target = Path(pilot_dir)
            target.mkdir(parents=True, exist_ok=True)
            npz = target / f"{world.run_id}.block.npz"
            csv = target / f"{world.run_id}.block.csv"
            block.save_npz(npz); block.save_csv(csv)
            npz_back = SynchronousBlock.load_npz(npz)
            csv_back = SynchronousBlock.load_csv(csv)
            exact = all(np.array_equal(other.values, block.values)
                        and np.array_equal(other.times_s, block.times_s)
                        and np.array_equal(other.positions_m, block.positions_m)
                        for other in (npz_back, csv_back))
            if not exact:
                raise AssertionError("CSV/NPZ changed native values, positions or clocks")
        entries.append({
            "run_id": world.run_id, "master_seed": world.master_seed, "split": world.split,
            "frames": 10, "probe_ranks": ["1", "2"], "observations": int(block.values.size),
            "same_frame_sync": True, "block_sha256": hashlib.sha256(block.values.tobytes()).hexdigest(),
            "ppm_min": float(block.values.min()), "ppm_max": float(block.values.max()),
            "csv_npz_bit_exact": exact, "unqualified_operations_refused": refused,
        })
    result["fixed_replay_pilot"] = {
        "scope": "data path only; no policy, no prediction, no source inference",
        "selection": "original source-blind probe ranks 1 and 2; all ten native frames",
        "worlds": entries, "total_scalar_readouts": sum(x["observations"] for x in entries),
        "no_new_physics": True,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--pilot-dir", type=Path,
                        help="optional local-only CSV/NPZ exports; never package these raw readouts")
    args = parser.parse_args()
    result = check(args.root, args.pilot_dir)
    body = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body)
    print(json.dumps({k: v for k, v in result.items() if k != "fixed_replay_pilot"}, indent=2))


if __name__ == "__main__":
    main()
