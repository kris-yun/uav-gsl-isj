#!/usr/bin/env python3
"""Audit whether historical Classic PMFS has full support on frozen H01 carriers."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_support(path: Path) -> tuple[list[str], dict[tuple[str, str], str]]:
    carriers: dict[int, str] = {}
    coordinate_owner: dict[tuple[str, str], str] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["house"] != "H01":
                continue
            index = int(row["carrier_index"])
            carrier = row["carrier_id"]
            if index in carriers and carriers[index] != carrier:
                raise ValueError("carrier index identity drift")
            carriers[index] = carrier
            key = (format(float(row["pmfs_x"]), ".6f"), format(float(row["pmfs_y"]), ".6f"))
            if key in coordinate_owner and coordinate_owner[key] != carrier:
                raise ValueError(f"PMFS support cell belongs to two carriers: {key}")
            coordinate_owner[key] = carrier
    if sorted(carriers) != list(range(210)) or len(set(carriers.values())) != 210:
        raise ValueError("H01 carrier support is not exactly 210 stable carriers")
    return [carriers[i] for i in range(210)], coordinate_owner


def aggregate_one(path: Path, ids: list[str], coordinate_owner: dict[tuple[str, str], str]):
    mass = defaultdict(float)
    seen: set[tuple[str, str]] = set()
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        key = (format(float(row["x"]), ".6f"), format(float(row["y"]), ".6f"))
        if key in seen:
            raise ValueError(f"duplicate PMFS posterior cell: {key}")
        seen.add(key)
        if key not in coordinate_owner:
            raise ValueError(f"PMFS posterior free cell absent from carrier support: {key}")
        value = float(row["source_probability"])
        if not np.isfinite(value) or value < 0:
            raise ValueError("invalid PMFS source probability")
        mass[coordinate_owner[key]] += value
    if seen != set(coordinate_owner):
        missing = sorted(set(coordinate_owner) - seen)
        raise ValueError(f"carrier support contains {len(missing)} cells absent from PMFS posterior")
    q = np.asarray([mass[sid] for sid in ids], dtype=np.float64)
    total = float(np.sum(q))
    if not np.isclose(total, 1.0, rtol=0.0, atol=1e-9):
        raise ValueError(f"carrier posterior mass does not sum to one: {total}")
    return q, len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical-root", type=Path, required=True)
    ap.add_argument("--support", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    ids, coordinate_owner = load_support(args.support)
    cases = []
    matrices = np.empty((10, 5, 210), dtype=np.float64)
    for seed in range(10):
        runtime = (args.historical_root / "House01" / f"seed{seed}" / "off" / "runtime"
                   / f"House01_seed{seed}_off_off" / "context_bank")
        for update in range(1, 6):
            path = runtime / f"source_update_{update:04d}" / "source_posterior.csv"
            if not path.is_file():
                raise FileNotFoundError(path)
            q, cells = aggregate_one(path, ids, coordinate_owner)
            matrices[seed, update - 1] = q
            cases.append({
                "seed": seed,
                "source_update_id": update,
                "carrier_count": len(q),
                "pmfs_free_cell_count": cells,
                "posterior_sum": float(q.sum()),
                "positive_carriers": int(np.sum(q > 0)),
                "zero_carriers": int(np.sum(q == 0)),
                "min_carrier_mass": float(np.min(q)),
                "median_carrier_mass": float(np.median(q)),
                "max_carrier_mass": float(np.max(q)),
                "effective_support_exp_entropy": float(np.exp(-np.sum(q[q > 0] * np.log(q[q > 0])))),
                "source_posterior_sha256": sha256(path),
            })
    full = all(r["positive_carriers"] == 210 and r["zero_carriers"] == 0 for r in cases)
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "pmfs_carrier_support_cases.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(cases[0]))
        writer.writeheader(); writer.writerows(cases)
    npz_path = args.out / "pmfs_carrier_posteriors.npz"
    np.savez_compressed(npz_path, posterior=matrices, carrier_id=np.asarray(ids))
    summary = {
        "contract": "PF_DEI_SET_NRE_PMFS_CARRIER_SUPPORT_AUDIT_V1",
        "cases": len(cases),
        "carriers": len(ids),
        "free_support_cells": len(coordinate_owner),
        "all_cases_full_support": full,
        "minimum_mass_over_50x210": float(matrices.min()),
        "maximum_mass_over_50x210": float(matrices.max()),
        "minimum_effective_support": float(min(r["effective_support_exp_entropy"] for r in cases)),
        "maximum_effective_support": float(max(r["effective_support_exp_entropy"] for r in cases)),
        "support_manifest_sha256": sha256(args.support),
        "cases_sha256": sha256(csv_path),
        "posterior_npz_sha256": sha256(npz_path),
        "verdict": "PF_DEI_SET_NRE_PMFS_FULL_SUPPORT_PASS" if full else "STOP_PMFS_CARRIER_POSTERIOR_NOT_FULL_SUPPORT",
    }
    (args.out / "pmfs_carrier_support_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["verdict"] + " " + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
