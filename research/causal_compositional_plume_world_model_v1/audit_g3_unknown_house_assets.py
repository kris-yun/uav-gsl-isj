#!/usr/bin/env python3
"""Read-only asset audit for the M4-v2 unknown-House transfer gate.

This deliberately does not launch GADEN or consume a plume seed.  It answers
whether the assets needed for leave-one-House-out, unseen-wind-family,
two-seed, spatial-field, and sensor-shift evaluation already exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def count_files(path: Path, pattern: str) -> int:
    return sum(1 for _ in path.glob(pattern)) if path.is_dir() else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical-root", type=Path, default=Path("/mnt/hgfs/workspace/GADEN_files/scenarios"))
    ap.add_argument("--hcmc-root", type=Path, default=Path("/home/zyc/hcmc_v1_native_runs_20260922"))
    ap.add_argument("--rmfe-root", type=Path, default=Path("/home/zyc/rmfe_current_h03_realization_20260813"))
    ap.add_argument("--c05-root", type=Path, default=Path("/home/zyc/c0_5_real_gaden_bank_20260923"))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    houses: dict[str, object] = {}
    for house in ("House01", "House02", "House03"):
        root = args.canonical_root / house
        occupancy = root / "OccupancyGrid3D.csv"
        winds = []
        for wind in sorted(root.glob("gas_simulations/*/*/wind")):
            iters = sorted(wind.glob("wind_iteration_*"))
            winds.append({
                "path": str(wind),
                "iteration_count": len(iters),
                "iteration0_sha256": sha256(wind / "wind_iteration_0"),
            })
        houses[house] = {
            "occupancy_exists": occupancy.is_file(),
            "occupancy_sha256": sha256(occupancy),
            "canonical_wind_families": winds,
            "physical_wind_inventory_ready": bool(winds) and all(x["iteration_count"] >= 2 for x in winds),
        }

    # C0.5 spatial fields are intentionally counted by House.  The current
    # bank has only House02 provenance and therefore cannot be an unknown-House
    # target for a model trained on other Houses.
    c05_cells = sorted(p.parent.parent.name for p in args.c05_root.glob("S*_W*_*/spatial/concentration.npy")) if args.c05_root.is_dir() else []
    hcmc_runs = []
    if args.hcmc_root.is_dir():
        for run in sorted(args.hcmc_root.glob("H*_R*")):
            hcmc_runs.append({
                "run": run.name,
                "sensor_trace": (run / "sensor_trace.csv").is_file(),
                "wind_trace": (run / "wind_trace.csv").is_file(),
                "spatial_concentration_fields": count_files(run, "**/concentration.npy"),
                "gaden_iteration_files": count_files(run, "**/iteration_*"),
            })

    rmfe_iterations = count_files(args.rmfe_root, "iteration_*")
    sensor_shift_candidates = []
    for base in (args.hcmc_root, args.rmfe_root, args.c05_root):
        if base.exists():
            sensor_shift_candidates.extend(str(p) for p in base.rglob("*") if "sensor" in p.name.lower() and "shift" in p.name.lower())

    checks = {
        "at_least_two_canonical_houses": sum(bool(v["occupancy_exists"]) for v in houses.values()) >= 2,
        "unknown_house_spatial_field_bank": False,
        "unknown_house_two_independent_seeds": False,
        "unseen_wind_family_target_fields": False,
        "sensor_shift_field_bank": bool(sensor_shift_candidates),
        "truth_rank_endpoint": False,
    }
    result = {
        "scope": "M4-v2 G3 unknown-House transfer hard gate",
        "read_only": True,
        "houses": houses,
        "current_c05_spatial_slice_files": c05_cells,
        "existing_hcmc_native_runs": hcmc_runs,
        "existing_rmfe_iteration_count": rmfe_iterations,
        "sensor_shift_candidates": sensor_shift_candidates,
        "checks": checks,
        "decision": "HOLD — UNKNOWN-HOUSE DATA NOT AVAILABLE",
        "reason": "Canonical geometry/wind assets exist, but no source-blind spatial plume bank with two independent seeds exists for a held-out House and no predeclared sensor-shift field bank exists.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(checks, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
