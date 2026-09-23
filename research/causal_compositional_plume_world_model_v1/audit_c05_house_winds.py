#!/usr/bin/env python3
"""Source-blind audit of canonical same-House GADEN wind interventions.

The audit only reads occupancy and wind files.  It does not inspect source
truth, plume outcomes, or PMFS ranks.  It validates the modern GADEN wind
layout, computes physical-field summary statistics, and hashes every field
file so the selected intervention can be reproduced from an external VM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from pathlib import Path

import numpy as np


WIND_RE = re.compile(r"^wind_iteration_(\d+)$")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def occupancy_metadata(path: Path) -> dict:
    header: dict[str, object] = {"path": str(path), "sha256": sha256(path)}
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines()[:20]:
        if line.startswith("#num_cells"):
            parts = line.split()
            dims = [int(x) for x in parts[1:]]
            header["num_cells"] = dims
            header["cell_count"] = math.prod(dims)
        elif line.startswith("#env_min"):
            header["env_min_m"] = [float(x) for x in line.split()[1:]]
        elif line.startswith("#env_max"):
            header["env_max_m"] = [float(x) for x in line.split()[1:]]
        elif line.startswith("#cell_size"):
            header["cell_size_m"] = [float(x) for x in line.split()[1:]]
    return header


def read_wind(path: Path, cell_count: int) -> np.ndarray:
    raw = path.read_bytes()
    legacy = cell_count * 3 * 8
    modern = 8 + legacy
    if len(raw) == legacy:
        # GADEN's canonical VGR wind files are the legacy layout accepted by
        # WindSequence: one complete double array for U, then V, then W.
        components = np.frombuffer(raw, dtype="<f8").reshape(3, cell_count)
        values = np.column_stack((components[0], components[1], components[2]))
    elif len(raw) == modern:
        major, minor = struct.unpack_from("<ii", raw, 0)
        if major < 2 or major > 999:
            raise ValueError(f"{path}: unexpected version header {(major, minor)}")
        # Modern GADEN Vector3 entries are three little-endian doubles.
        values = np.frombuffer(raw, dtype="<f8", offset=8).reshape(cell_count, 3)
    else:
        raise ValueError(f"{path}: {len(raw)} bytes, expected {legacy} (legacy) or {modern} (modern)")
    if not np.isfinite(values).all():
        raise ValueError(f"{path}: non-finite field value")
    return values


def field_stats(values: np.ndarray) -> dict:
    speed = np.linalg.norm(values, axis=1)
    horizontal = np.linalg.norm(values[:, :2], axis=1)
    nonzero = speed > 1e-12
    mean_vec = values.mean(axis=0)
    angle = np.arctan2(values[:, 1], values[:, 0])
    weighted = speed > 1e-12
    if weighted.any():
        direction_deg = math.degrees(
            math.atan2(
                float(np.sum(speed[weighted] * np.sin(angle[weighted]))),
                float(np.sum(speed[weighted] * np.cos(angle[weighted]))),
            )
        )
    else:
        direction_deg = None
    return {
        "min_mps": float(speed.min()),
        "median_mps": float(np.median(speed)),
        "p95_mps": float(np.quantile(speed, 0.95)),
        "max_mps": float(speed.max()),
        "mean_mps": float(speed.mean()),
        "mean_vector_mps": [float(x) for x in mean_vec],
        "median_horizontal_mps": float(np.median(horizontal)),
        "nonzero_fraction": float(nonzero.mean()),
        "mean_speed_weighted_direction_deg": direction_deg,
    }


def audit_config(wind_dir: Path, cell_count: int) -> dict:
    paths = []
    for p in sorted(wind_dir.iterdir()):
        m = WIND_RE.match(p.name)
        if m and p.is_file():
            paths.append((int(m.group(1)), p))
    paths.sort()
    indices = [i for i, _ in paths]
    if indices != list(range(len(indices))):
        raise ValueError(f"{wind_dir}: non-contiguous iterations {indices}")
    iteration_records = []
    all_speeds = []
    all_vectors = []
    for idx, path in paths:
        values = read_wind(path, cell_count)
        stats = field_stats(values)
        iteration_records.append(
            {
                "iteration": idx,
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "stats": stats,
            }
        )
        all_speeds.append(np.linalg.norm(values, axis=1))
        all_vectors.append(values)
    if not paths:
        raise ValueError(f"{wind_dir}: no modern wind_iteration_* files")
    speeds = np.concatenate(all_speeds)
    vectors = np.concatenate(all_vectors)
    summary = field_stats(vectors)
    return {
        "path": str(wind_dir),
        "iteration_count": len(paths),
        "cell_count": cell_count,
        "all_files_finite": True,
        "layout_bytes_per_iteration": paths[0][1].stat().st_size,
        "summary_over_all_iterations": summary,
        "iteration_records": iteration_records,
    }


def compare(a: dict, b: dict, cell_count: int) -> dict:
    records_a = {x["iteration"]: x for x in a["iteration_records"]}
    records_b = {x["iteration"]: x for x in b["iteration_records"]}
    common = sorted(set(records_a) & set(records_b))
    deltas = []
    flat_a = []
    flat_b = []
    for idx in common:
        va = read_wind(Path(a["path"]) / f"wind_iteration_{idx}", cell_count)
        vb = read_wind(Path(b["path"]) / f"wind_iteration_{idx}", cell_count)
        deltas.append(vb - va)
        flat_a.append(va.reshape(-1))
        flat_b.append(vb.reshape(-1))
    delta = np.concatenate(deltas)
    all_a = np.concatenate(flat_a)
    all_b = np.concatenate(flat_b)
    corr = float(np.corrcoef(all_a, all_b)[0, 1])
    return {
        "common_iteration_count": len(common),
        "equal_iteration_count": sum(
            records_a[i]["sha256"] == records_b[i]["sha256"] for i in common
        ),
        "all_iterations_max_abs_component_delta": float(np.abs(delta).max()),
        "all_iterations_mean_abs_component_delta": float(np.abs(delta).mean()),
        "all_iterations_fraction_components_delta_gt_1e-12": float(
            (np.abs(delta) > 1e-12).mean()
        ),
        "all_iterations_component_correlation": corr,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario-root", type=Path, required=True)
    ap.add_argument("--houses", nargs="+", default=["House01", "House02", "House03"])
    ap.add_argument("--compare", nargs=3, metavar=("HOUSE", "WIND_A", "WIND_B"))
    args = ap.parse_args()

    result: dict[str, object] = {"scenario_root": str(args.scenario_root), "houses": {}}
    for house in args.houses:
        root = args.scenario_root / house
        occ = occupancy_metadata(root / "OccupancyGrid3D.csv")
        cell_count = int(occ["cell_count"])
        configs = {}
        for wind in sorted((root / "gas_simulations").glob("*/FilamentSimulation_*/wind")):
            config = wind.parents[1].name
            configs[config] = audit_config(wind, cell_count)
        result["houses"][house] = {
            "occupancy": occ,
            "wind_configs": configs,
        }
        pairwise: dict[str, object] = {}
        names = sorted(configs)
        for i, first in enumerate(names):
            for second in names[i + 1 :]:
                a = [x["sha256"] for x in configs[first]["iteration_records"]]
                b = [x["sha256"] for x in configs[second]["iteration_records"]]
                pairwise[f"{first}__vs__{second}"] = {
                    "equal_iteration_count": sum(x == y for x, y in zip(a, b)),
                    "iteration_count": min(len(a), len(b)),
                    "iteration0_equal": bool(a and b and a[0] == b[0]),
                    "last_iteration_equal": bool(a and b and a[-1] == b[-1]),
                }
        result["houses"][house]["pairwise_iteration_hash_comparison"] = pairwise
    if args.compare:
        house, wa, wb = args.compare
        configs = result["houses"][house]["wind_configs"]
        result["comparison"] = {
            "house": house,
            "wind_a": wa,
            "wind_b": wb,
            "metrics": compare(
                configs[wa], configs[wb], int(result["houses"][house]["occupancy"]["cell_count"])
            ),
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
