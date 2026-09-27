#!/usr/bin/env python3
"""Frozen E2 acquisition; sealed environments expose infrastructure metadata only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
E1 = ROOT / "evidence/environment_level_benchmark_v0/e1"
E2 = ROOT / "evidence/environment_level_benchmark_v0/e2"
DATA = Path("/home/zyc/E2_CROSS_ENVIRONMENT_168_RUNS_20260925")
CANONICAL = Path("/mnt/hgfs/workspace/GADEN_files/scenarios")
INVENTORY = ROOT / "evidence/causal_compositional_plume_world_model_v1/C0_5_HOUSE_WIND_INVENTORY_20260923.json"
BUILD = Path("/home/zyc/hcmc_gaden_seed_build_20260922")
BINARY = BUILD / "install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
EXTRACTOR = Path("/home/zyc/rmfe_filament_extractor_omp")
MATHUTILS = BUILD / "src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp"
TIMES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550)
ENVIRONMENTS = (
    ("House01", "1,3-2,4_fast", "OPEN_DISCOVERY"),
    ("House02", "3,5-1_slow", "OPEN_DISCOVERY"),
    ("House02", "4,5-3_slow", "OPEN_DISCOVERY"),
    ("House01", "2,4-1_fast", "SEALED_DEV_HOLDOUT"),
    ("House02", "3,5-1_fast", "SEALED_DEV_HOLDOUT"),
    ("House03", "1-2,5_fast", "SEALED_FINAL_HOUSE"),
    ("House03", "5-3_fast", "SEALED_FINAL_HOUSE"),
)
EXPECTED = {
    "E1_HOUSE_PROBE_CONTRACTS.tsv": "364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812",
    "E1_HOUSE_SOURCE_PANELS.tsv": "e38bee4467fb9d98ab5ee48a6115eb1b3306df63cd3da409b9412b3032c4b06e",
    "E1_RESULT.json": "ca9fa1b7d3961565d8636c179e848ae20de94fdf5b00cde65a471b44ea74c384",
}
EXPECTED_BINARY = "4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXPECTED_EXTRACTOR = "206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"
EXPECTED_OCC = {
    "House01": "846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb",
    "House02": "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d",
    "House03": "ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_hash(path: Path, expected: str) -> None:
    got = digest(path)
    if got != expected:
        raise RuntimeError(f"input hash drift: {path}: {got} != {expected}")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def build_plan() -> tuple[list[dict], list[dict], dict]:
    for name, expected in EXPECTED.items():
        require_hash(E1 / name, expected)
    result = json.loads((E1 / "E1_RESULT.json").read_text())
    if result["decision"] != "E1_PASS_CROSS_HOUSE_CONTRACT_READY_FOR_FILLIN_DESIGN" or result["source_z_m"] != 0.2:
        raise RuntimeError("E1 gate or source height drift")
    require_hash(BINARY, EXPECTED_BINARY)
    require_hash(EXTRACTOR, EXPECTED_EXTRACTOR)
    panels = read_tsv(E1 / "E1_HOUSE_SOURCE_PANELS.tsv")
    probes = read_tsv(E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv")
    source_by_house = {h: [x for x in panels if x["house"] == h] for h in EXPECTED_OCC}
    probe_by_house = {h: [x for x in probes if x["house"] == h] for h in EXPECTED_OCC}
    for house in EXPECTED_OCC:
        require_hash(CANONICAL / house / "OccupancyGrid3D.csv", EXPECTED_OCC[house])
        if len(source_by_house[house]) != 6 or len(probe_by_house[house]) != 30:
            raise RuntimeError(f"E1 panel size drift: {house}")
        if any(float(x["z_m"]) != 0.2 for x in source_by_house[house] + probe_by_house[house]):
            raise RuntimeError(f"E1 z drift: {house}")
        if len({x["source_id"] for x in source_by_house[house]}) != 6:
            raise RuntimeError(f"duplicate source: {house}")
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    wind_rows, wind_meta = [], {}
    for ei, (house, wind, role) in enumerate(ENVIRONMENTS):
        rec = inv["houses"][house]["wind_configs"][wind]
        wind_dir = Path(rec["path"])
        records = rec["iteration_records"]
        if len(records) != 11 or {r["name"] for r in records} != {f"wind_iteration_{i}" for i in range(11)}:
            raise RuntimeError(f"wind iteration contract drift: {house}/{wind}")
        for r in records:
            path = wind_dir / r["name"]
            if path.stat().st_size != r["size_bytes"]:
                raise RuntimeError(f"wind size drift: {path}")
            require_hash(path, r["sha256"])
            wind_rows.append(dict(environment_index=ei, house=house, wind=wind, path=str(path),
                                  file=r["name"], bytes=r["size_bytes"], sha256=r["sha256"]))
        wind_meta[ei] = {"path": str(wind_dir), "iteration_hashes": {r["name"]: r["sha256"] for r in records}}
    plan = []
    for ei, (house, wind, role) in enumerate(ENVIRONMENTS):
        for si, source in enumerate(source_by_house[house]):
            for rep in range(4):
                seed = 2026110000 + 1000 * ei + 10 * si + rep
                run_dir = DATA / role / f"E{ei}_{house}" / wind / source["source_id"] / f"r{rep}_seed{seed}"
                plan.append(dict(environment_index=ei, role=role, house=house, wind=wind,
                                 source_index=si, source_id=source["source_id"],
                                 source_xyz=[float(source[k]) for k in ("x_m", "y_m", "z_m")],
                                 replicate_index=rep, requested_seed=seed, run_dir=str(run_dir)))
    if len(plan) != 168 or len({x["requested_seed"] for x in plan}) != 168:
        raise RuntimeError("seed uniqueness or run count drift")
    for ei in range(7):
        if sum(x["environment_index"] == ei for x in plan) != 24:
            raise RuntimeError("environment count drift")
    inputs = {
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "pre_run_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "e1_sha256": EXPECTED,
        "binary_path": str(BINARY), "binary_sha256": EXPECTED_BINARY,
        "extractor_path": str(EXTRACTOR), "extractor_sha256": EXPECTED_EXTRACTOR,
        "seed_source_path": str(MATHUTILS), "seed_source_sha256": digest(MATHUTILS),
        "occupancy_sha256": EXPECTED_OCC,
        "wind_inventory_sha256": digest(INVENTORY),
        "wind_meta": wind_meta,
        "simulation_parameters": {
            "sim_time": 300.0, "time_step": 0.1, "num_filaments_sec": 7,
            "variable_rate": True, "filament_stop_steps": 0,
            "ppm_filament_center": 10.0, "filament_initial_std": 10.0,
            "filament_growth_gamma": 15.0, "filament_noise_std": 0.01,
            "gas_type": 10, "temperature": 298.0, "pressure": 1.0,
            "concentration_unit_choice": 1, "wind_time_step": 1.0,
            "allow_looping": True, "loop_from_step": 1, "loop_to_step": 10,
            "save_results": 1, "results_time_step": 0.5, "results_min_time": 0.0,
            "writeConcentrations": False, "fixed_frame": "map",
            "extract_times": TIMES, "extract_z_m": 0.2,
        },
    }
    return plan, wind_rows, inputs


def cube_qc(path: Path, house: str) -> None:
    dims = {"House01": (87, 114), "House02": (83, 119), "House03": (138, 83)}
    cube = np.load(path, allow_pickle=False)
    if cube.shape != (10, *dims[house]) or not np.isfinite(cube).all() or (cube < 0).any():
        raise RuntimeError(f"cube infrastructure QC failed: {path}")


def valid_run(item: dict, inputs: dict) -> dict | None:
    run = Path(item["run_dir"])
    meta_path = run / "run_metadata.json"
    cube = run / "concentration.npy"
    spatial = run / "spatial_metadata.json"
    if not (meta_path.is_file() and cube.is_file() and spatial.is_file()):
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    for key in ("environment_index", "role", "house", "wind", "source_index", "source_id",
                "source_xyz", "replicate_index", "requested_seed"):
        if meta.get(key) != item[key]:
            raise RuntimeError(f"run metadata drift: {run} {key}")
    if meta.get("binary_sha256") != EXPECTED_BINARY or meta.get("wind_iteration_hashes") != inputs["wind_meta"][item["environment_index"]]["iteration_hashes"]:
        raise RuntimeError(f"run provenance drift: {run}")
    if meta.get("cube_sha256") != digest(cube) or meta.get("spatial_metadata_sha256") != digest(spatial):
        raise RuntimeError(f"run artifact hash drift: {run}")
    cube_qc(cube, item["house"])
    return meta


def run_one(item: dict, inputs: dict) -> dict:
    existing = valid_run(item, inputs)
    if existing is not None:
        return existing
    run = Path(item["run_dir"])
    if run.exists() and any(run.iterdir()):
        raise RuntimeError(f"incomplete run requires documented infrastructure repair: {run}")
    run.mkdir(parents=True)
    real = run / "realization"
    real.mkdir()
    occ = CANONICAL / item["house"] / "OccupancyGrid3D.csv"
    (real / "OccupancyGrid3D.csv").symlink_to(occ)
    wind = inputs["wind_meta"][item["environment_index"]]["path"]
    sx, sy, sz = item["source_xyz"]
    options = {
        "verbose": "false", "wait_preprocessing": "false", "sim_time": "300.0",
        "time_step": "0.1", "num_filaments_sec": "7", "variable_rate": "true",
        "filament_stop_steps": "0", "ppm_filament_center": "10.0",
        "filament_initial_std": "10.0", "filament_growth_gamma": "15.0",
        "filament_noise_std": "0.01", "gas_type": "10", "temperature": "298.0",
        "pressure": "1.0", "concentration_unit_choice": "1", "occupancy3D_data": str(occ),
        "fixed_frame": "map", "wind_data": wind, "wind_time_step": "1.0",
        "allow_looping": "true", "loop_from_step": "1", "loop_to_step": "10",
        "source_position_x": repr(sx), "source_position_y": repr(sy), "source_position_z": repr(sz),
        "save_results": "1", "results_time_step": "0.5", "results_min_time": "0.0",
        "writeConcentrations": "false", "results_location": str(real),
    }
    cmd = [str(BINARY), "--ros-args"] + [t for k, v in options.items() for t in ("-p", f"{k}:={v}")]
    env = dict(os.environ, GADEN_RNG_SEED=str(item["requested_seed"]))
    with (run / "generation.log").open("w", encoding="utf-8") as f:
        subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
    log = (run / "generation.log").read_text(errors="replace")
    if "Filament simulator finished correctly!" not in log:
        raise RuntimeError(f"simulator did not finish correctly: {run}")
    iterations = list(real.glob("iteration_*"))
    if len(iterations) != 566:
        raise RuntimeError(f"iteration count {len(iterations)} != 566: {run}")
    if not (real / "OccupancyGrid3D.csv").exists():
        (real / "OccupancyGrid3D.csv").symlink_to(occ)
    header = (occ.read_text().splitlines()[:4])
    origin = [float(x) for x in header[0].split()[1:]]
    dims = [int(x) for x in header[2].split()[1:]]
    if dims[:2] != {"House01": [87, 114], "House02": [83, 119], "House03": [138, 83]}[item["house"]]:
        raise RuntimeError("occupancy header dimensions drift")
    if float(header[3].split()[-1]) != 0.1:
        raise RuntimeError("occupancy resolution drift")
    extractor_cmd = [str(EXTRACTOR), str(real), str(real), str(run / "concentration.npy"),
                     str(run / "spatial_metadata.json"), repr(origin[0]), repr(origin[1]),
                     "0.1", "1", "0.20", str(dims[0]), str(dims[1]),
                     *[str(x) for x in TIMES]]
    with (run / "extract.log").open("w", encoding="utf-8") as f:
        subprocess.run(extractor_cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
    cube = run / "concentration.npy"
    cube_qc(cube, item["house"])
    resolved_base = (item["requested_seed"] ^ (item["requested_seed"] >> 32)) & 0xFFFFFFFF
    meta = dict(item, resolved_seed_base_uint32=resolved_base,
                resolved_seed_gaussian_uint32=(resolved_base + 0x9E3779B9) & 0xFFFFFFFF,
                resolved_seed_uniform_uint32=(resolved_base + 0x243F6A88) & 0xFFFFFFFF,
                seed_source_sha256=inputs["seed_source_sha256"],
                binary_sha256=EXPECTED_BINARY, extractor_sha256=EXPECTED_EXTRACTOR,
                occupancy_sha256=EXPECTED_OCC[item["house"]],
                wind_path=wind, wind_iteration_hashes=inputs["wind_meta"][item["environment_index"]]["iteration_hashes"],
                e1_probe_contract_sha256=EXPECTED["E1_HOUSE_PROBE_CONTRACTS.tsv"],
                e1_source_contract_sha256=EXPECTED["E1_HOUSE_SOURCE_PANELS.tsv"],
                e2_charter_sha256=inputs["e2_charter_sha256"],
                cube_sha256=digest(cube), cube_bytes=cube.stat().st_size,
                spatial_metadata_sha256=digest(run / "spatial_metadata.json"),
                generation_log_sha256=digest(run / "generation.log"),
                extraction_log_sha256=digest(run / "extract.log"))
    write_json(run / "run_metadata.json", meta)
    shutil.rmtree(real)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("preflight", "run"))
    args = ap.parse_args()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != "research/generalization-refoundation-v0":
        raise RuntimeError(f"wrong branch: {branch}")
    if subprocess.run(["git", "merge-base", "--is-ancestor", "b3be882043fee8b2a6becb56507433cdcf2d111b", "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("E1 final commit absent")
    plan, wind_rows, inputs = build_plan()
    inputs["e2_charter_sha256"] = digest(ROOT / "research/environment_level_benchmark_v0/E2_MINIMAL_FILLIN_CHARTER_20260925.md")
    E2.mkdir(parents=True, exist_ok=True)
    write_json(E2 / "E2_INPUT_PROVENANCE.json", inputs)
    write_tsv(E2 / "E2_WIND_FILE_HASHES.tsv", wind_rows,
              ["environment_index", "house", "wind", "path", "file", "bytes", "sha256"])
    write_json(E2 / "E2_ACQUISITION_PLAN.json", {"runs": plan})
    print("E2_PREFLIGHT_PASS", "environments=7", "runs=168", "seeds_unique=168", flush=True)
    if args.mode == "preflight":
        return 0
    for n, item in enumerate(plan, 1):
        meta = run_one(item, inputs)
        print("E2_QC_PASS", n, item["role"], item["house"], item["wind"],
              item["source_id"], item["requested_seed"], meta["cube_sha256"], flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"E2_INFRASTRUCTURE_STOP: {exc}", file=sys.stderr)
        raise
