#!/usr/bin/env python3
"""Acquire exactly the 24 preregistered H02/W3 factorial-corner runs."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
E1 = ROOT / "evidence/environment_level_benchmark_v0/e1"
OUT = ROOT / "evidence/environment_level_benchmark_v0/e4b"
DATA = Path("/home/zyc/E4B_H02_W3_24_RUNS_20260925")
OCC = Path("/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv")
INVENTORY = ROOT / "evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json"
BUILD = Path("/home/zyc/hcmc_gaden_seed_build_20260922")
BINARY = BUILD / "install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
EXTRACTOR = Path("/home/zyc/rmfe_filament_extractor_omp")
TIMES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550)
E1_SOURCE_SHA = "e38bee4467fb9d98ab5ee48a6115eb1b3306df63cd3da409b9412b3032c4b06e"
E1_PROBE_SHA = "364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812"
BINARY_SHA = "4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXTRACTOR_SHA = "206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"
OCC_SHA = "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"
ENV_INDEX = 7
HOUSE, WIND = "House02", "4,5-3_fast"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def need(path: Path, expected: str) -> None:
    actual = sha(path)
    if actual != expected:
        raise RuntimeError(f"hash drift: {path}: {actual} != {expected}")


def json_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def plan() -> tuple[list[dict], dict]:
    need(E1 / "E1_HOUSE_SOURCE_PANELS.tsv", E1_SOURCE_SHA)
    need(E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv", E1_PROBE_SHA)
    need(BINARY, BINARY_SHA)
    need(EXTRACTOR, EXTRACTOR_SHA)
    need(OCC, OCC_SHA)
    with (E1 / "E1_HOUSE_SOURCE_PANELS.tsv").open(newline="", encoding="utf-8") as f:
        sources = [r for r in csv.DictReader(f, delimiter="\t") if r["house"] == HOUSE]
    if len(sources) != 6 or any(float(s["z_m"]) != 0.2 for s in sources):
        raise RuntimeError("E1 H02 source panel drift")
    record = json.loads(INVENTORY.read_text(encoding="utf-8"))["houses"][HOUSE]["wind_configs"][WIND]
    wind_dir = Path(record["path"])
    winds = record["iteration_records"]
    if len(winds) != 11 or {w["name"] for w in winds} != {f"wind_iteration_{i}" for i in range(11)}:
        raise RuntimeError("W3 wind iteration contract drift")
    for w in winds:
        p = wind_dir / w["name"]
        if p.stat().st_size != w["size_bytes"]:
            raise RuntimeError(f"W3 wind size drift: {p}")
        need(p, w["sha256"])
    rows = []
    for si, s in enumerate(sources):
        for rep in range(4):
            seed = 2026110000 + 1000 * ENV_INDEX + 10 * si + rep
            run_dir = DATA / s["source_id"] / f"r{rep}_seed{seed}"
            rows.append(dict(environment_index=ENV_INDEX, house=HOUSE, wind=WIND,
                             source_index=si, source_id=s["source_id"],
                             source_xyz=[float(s[k]) for k in ("x_m", "y_m", "z_m")],
                             replicate_index=rep, requested_seed=seed, run_dir=str(run_dir)))
    if len(rows) != 24 or len({r["requested_seed"] for r in rows}) != 24:
        raise RuntimeError("W3 seed collision or run count drift")
    return rows, dict(wind_path=str(wind_dir),
                      wind_hashes={w["name"]: w["sha256"] for w in winds},
                      wind_inventory_sha256=sha(INVENTORY), occupancy_sha256=OCC_SHA,
                      binary_sha256=BINARY_SHA, extractor_sha256=EXTRACTOR_SHA)


def cube_qc(path: Path) -> None:
    c = np.load(path, allow_pickle=False)
    if c.shape != (10, 83, 119) or not np.isfinite(c).all() or (c < 0).any():
        raise RuntimeError(f"W3 cube QC failed: {path}")


def one_run(item: dict, wind: dict, lock_sha: str) -> dict:
    work = Path(item["run_dir"])
    meta_path, cube = work / "run_metadata.json", work / "concentration.npy"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if {k: meta[k] for k in item} != item or meta["pre_run_lock_sha256"] != lock_sha:
            raise RuntimeError(f"existing run provenance drift: {work}")
        need(cube, meta["cube_sha256"])
        cube_qc(cube)
        return meta
    if work.exists() and any(work.iterdir()):
        raise RuntimeError(f"incomplete W3 run needs documented infrastructure repair: {work}")
    work.mkdir(parents=True)
    real = work / "realization"
    real.mkdir()
    (real / "OccupancyGrid3D.csv").symlink_to(OCC)
    sx, sy, sz = item["source_xyz"]
    options = {
        "verbose": "false", "wait_preprocessing": "false", "sim_time": "300.0", "time_step": "0.1",
        "num_filaments_sec": "7", "variable_rate": "true", "filament_stop_steps": "0",
        "ppm_filament_center": "10.0", "filament_initial_std": "10.0",
        "filament_growth_gamma": "15.0", "filament_noise_std": "0.01",
        "gas_type": "10", "temperature": "298.0", "pressure": "1.0",
        "concentration_unit_choice": "1", "occupancy3D_data": str(OCC),
        "fixed_frame": "map", "wind_data": wind["wind_path"], "wind_time_step": "1.0",
        "allow_looping": "true", "loop_from_step": "1", "loop_to_step": "10",
        "source_position_x": repr(sx), "source_position_y": repr(sy), "source_position_z": repr(sz),
        "save_results": "1", "results_time_step": "0.5", "results_min_time": "0.0",
        "writeConcentrations": "false", "results_location": str(real),
    }
    cmd = [str(BINARY), "--ros-args"] + [x for k, v in options.items() for x in ("-p", f"{k}:={v}")]
    with (work / "generation.log").open("w", encoding="utf-8") as f:
        subprocess.run(cmd, env=dict(os.environ, GADEN_RNG_SEED=str(item["requested_seed"])),
                       stdout=f, stderr=subprocess.STDOUT, check=True)
    if "Filament simulator finished correctly!" not in (work / "generation.log").read_text(errors="replace"):
        raise RuntimeError(f"W3 simulator did not finish correctly: {work}")
    if len(list(real.glob("iteration_*"))) != 566:
        raise RuntimeError(f"W3 filament iteration count drift: {work}")
    if not (real / "OccupancyGrid3D.csv").exists():
        (real / "OccupancyGrid3D.csv").symlink_to(OCC)
    cmd = [str(EXTRACTOR), str(real), str(real), str(cube),
           str(work / "spatial_metadata.json"), "-5.39273", "-7.45088", "0.1", "1", "0.20",
           "83", "119", *[str(t) for t in TIMES]]
    with (work / "extract.log").open("w", encoding="utf-8") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
    cube_qc(cube)
    base = (item["requested_seed"] ^ (item["requested_seed"] >> 32)) & 0xFFFFFFFF
    meta = dict(item, pre_run_lock_sha256=lock_sha, wind_path=wind["wind_path"],
                wind_hashes=wind["wind_hashes"], wind_inventory_sha256=wind["wind_inventory_sha256"],
                binary_sha256=BINARY_SHA, extractor_sha256=EXTRACTOR_SHA, occupancy_sha256=OCC_SHA,
                e1_source_sha256=E1_SOURCE_SHA, e1_probe_sha256=E1_PROBE_SHA,
                resolved_seed_base_uint32=base,
                resolved_seed_gaussian_uint32=(base + 0x9E3779B9) & 0xFFFFFFFF,
                resolved_seed_uniform_uint32=(base + 0x243F6A88) & 0xFFFFFFFF,
                cube_sha256=sha(cube), cube_bytes=cube.stat().st_size,
                spatial_metadata_sha256=sha(work / "spatial_metadata.json"),
                generation_log_sha256=sha(work / "generation.log"),
                extraction_log_sha256=sha(work / "extract.log"))
    json_write(meta_path, meta)
    shutil.rmtree(real)
    return meta


def acquire() -> None:
    lock_path = OUT / "E4B_PRE_RUN_LOCK.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    need(Path(__file__), lock["acquisition_script_sha256"])
    if lock["environment_index"] != ENV_INDEX or lock["status"] != "E4B_PRE_RUN_LOCKED":
        raise RuntimeError("E4B pre-run lock drift")
    rows, wind = plan()
    if wind["wind_hashes"] != lock["w3_wind_hashes"]:
        raise RuntimeError("E4B W3 wind hash lock drift")
    manifest = []
    for n, row in enumerate(rows, 1):
        meta = one_run(row, wind, sha(lock_path))
        print("E4B_W3_QC_PASS", n, row["source_id"], row["requested_seed"], meta["cube_sha256"], flush=True)
        manifest.append({k: row[k] for k in ("source_index", "source_id", "replicate_index", "requested_seed", "run_dir")}
                        | {"cube_path": str(Path(row["run_dir"]) / "concentration.npy"),
                           "cube_sha256": meta["cube_sha256"], "cube_bytes": meta["cube_bytes"],
                           "run_metadata_sha256": sha(Path(row["run_dir"]) / "run_metadata.json"), "qc": "PASS"})
    fields = list(manifest[0])
    with (OUT / "E4B_W3_RUN_MANIFEST.tsv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(manifest)
    print("E4B_W3_ACQUISITION_COMPLETE", "runs=24", flush=True)


if __name__ == "__main__":
    acquire()
