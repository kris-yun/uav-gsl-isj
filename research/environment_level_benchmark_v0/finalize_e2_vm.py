#!/usr/bin/env python3
"""Finalize E2 without exposing sealed concentration statistics."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from acquire_e2_vm import (DATA, E1, E2, ENVIRONMENTS, EXPECTED, ROOT,
                           build_plan, cube_qc, digest, valid_run, write_json, write_tsv)


def main() -> None:
    plan, _, inputs = build_plan()
    inputs["e2_charter_sha256"] = digest(ROOT / "research/environment_level_benchmark_v0/E2_MINIMAL_FILLIN_CHARTER_20260925.md")
    all_rows, dev_rows, final_rows, open_index = [], [], [], []
    open_array = np.empty((3, 6, 4, 10, 30), dtype=np.float32)
    probes = list(csv.DictReader((E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv").open(newline=""), delimiter="\t"))
    probe_by_house = {h: sorted((p for p in probes if p["house"] == h), key=lambda x: int(x["probe_rank"]))
                      for h in ("House01", "House02", "House03")}
    for item in plan:
        meta = valid_run(item, inputs)
        if meta is None:
            raise RuntimeError(f"E2 acquisition incomplete: {item['run_dir']}")
        cube_path = Path(item["run_dir"]) / "concentration.npy"
        cube_qc(cube_path, item["house"])
        row = {k: item[k] for k in ("environment_index", "role", "house", "wind", "source_index", "source_id", "replicate_index", "requested_seed")}
        row.update(resolved_seed_base_uint32=meta["resolved_seed_base_uint32"],
                   cube_path=str(cube_path), cube_bytes=meta["cube_bytes"],
                   cube_sha256=meta["cube_sha256"], run_metadata_path=str(Path(item["run_dir"]) / "run_metadata.json"),
                   run_metadata_sha256=digest(Path(item["run_dir"]) / "run_metadata.json"), qc="PASS")
        all_rows.append(row)
        if item["role"] == "OPEN_DISCOVERY":
            cube = np.load(cube_path, allow_pickle=False)
            vals = []
            for p in probe_by_house[item["house"]]:
                x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
                y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
                if (x1 - x0, y1 - y0) != (2, 2):
                    raise RuntimeError("E1 pooling block drift")
                vals.append(cube[:, x0:x1, y0:y1].mean(axis=(1, 2)))
            pooled = np.stack(vals, axis=1).astype(np.float32)
            if pooled.shape != (10, 30) or not np.isfinite(pooled).all() or (pooled < 0).any():
                raise RuntimeError("open probe extraction QC failed")
            ei, si, rep = item["environment_index"], item["source_index"], item["replicate_index"]
            open_array[ei, si, rep] = pooled
            open_index.append(dict(environment_index=ei, source_index=si, replicate_index=rep,
                                   house=item["house"], wind=item["wind"], source_id=item["source_id"],
                                   requested_seed=item["requested_seed"], cube_sha256=meta["cube_sha256"]))
        elif item["role"] == "SEALED_DEV_HOLDOUT":
            dev_rows.append(row)
        else:
            final_rows.append(row)
    if len(all_rows) != 168 or len(dev_rows) != 48 or len(final_rows) != 48 or len(open_index) != 72:
        raise RuntimeError("E2 count drift")
    if len({x["requested_seed"] for x in all_rows}) != 168:
        raise RuntimeError("E2 seed collision")
    fields = list(all_rows[0])
    E2.mkdir(parents=True, exist_ok=True)
    write_tsv(E2 / "E2_RUN_MANIFEST.tsv", all_rows, fields)
    write_tsv(E2 / "E2_SEALED_DEV_HASH_MANIFEST.tsv", dev_rows, fields)
    write_tsv(E2 / "E2_SEALED_FINAL_HOUSE_HASH_MANIFEST.tsv", final_rows, fields)
    write_tsv(E2 / "E2_OPEN_DISCOVERY_INDEX.tsv", open_index, list(open_index[0]))
    with (E2 / "E2_OPEN_DISCOVERY_10x30.npy").open("wb") as f:
        np.save(f, open_array, allow_pickle=False)
    env_rows = []
    for ei, (house, wind, role) in enumerate(ENVIRONMENTS):
        env_rows.append(dict(environment_index=ei, role=role, house=house, wind=wind,
                             source_count=6, realization_count_per_source=4, run_count=24, qc="PASS"))
    write_tsv(E2 / "E2_ENVIRONMENT_MANIFEST.tsv", env_rows, list(env_rows[0]))
    write_json(E2 / "E2_QC_SUMMARY.json", {
        "decision": "E2_PASS_BENCHMARK_ACQUIRED_AND_SEALED",
        "completed_new_plume_runs": 168,
        "environment_count": 7,
        "open_run_count": 72,
        "sealed_dev_run_count": 48,
        "sealed_final_house_run_count": 48,
        "full_concentration_cubes_retained": 168,
        "open_vector_shape": [3, 6, 4, 10, 30],
        "open_vector_qc": "PASS",
        "sealed_dev_infrastructure_qc": "PASS",
        "sealed_final_house_infrastructure_qc": "PASS",
        "source_z_m": 0.2,
        "scientific_mechanism_evaluated": False,
    })
    write_json(E2 / "E2_DATA_LOCATION.json", {
        "raw_cube_root": str(DATA),
        "sealed_dev_path": str(DATA / "SEALED_DEV_HOLDOUT"),
        "sealed_final_house_path": str(DATA / "SEALED_FINAL_HOUSE"),
        "sealed_raw_data_in_review_package": False,
    })
    candidates = sorted(p for p in E2.iterdir() if p.is_file() and p.name != "E2_SHA256SUMS.txt")
    (E2 / "E2_SHA256SUMS.txt").write_text(
        "".join(f"{digest(p)}  {p.name}\n" for p in candidates), encoding="utf-8")
    print("E2_PASS_BENCHMARK_ACQUIRED_AND_SEALED", "runs=168", "full_cubes=168", flush=True)


if __name__ == "__main__":
    main()
