#!/usr/bin/env python3
"""Frozen JTD-E2 OPEN-only preflight and 108+72 GADEN acquisition."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/jtd_cross_environment_v0"))
import run_jtd_e1_vm as e1  # Exact audited OPEN-only source/probe/wind/simulator helpers.

EVIDENCE = ROOT / "evidence/jtd_e2_20260925"
DATA_ROOT = Path("/home/zyc/JTD_E2_K12_180_RUNS_20260925")
BRANCH = "research/jtd-crossenv-k12-confirmation-v0"
INITIAL_LOCK = EVIDENCE / "JTD_E2_INITIAL_LOCK.json"
PRE_TARGET_LOCK = EVIDENCE / "JTD_E2_PRE_TARGET_LOCK.json"
SOURCE_IDS = 6
REFERENCE_NEW, TARGET_NEW = 6, 4


def sha(path: Path) -> str:
    return e1.sha(path)


def write_json(path: Path, value: object) -> None:
    e1.write_json(path, value)


def write_tsv(path: Path, values: list[dict]) -> None:
    e1.write_tsv(path, values)


def seed_from_key(key: str) -> int:
    # Positive signed-32-bit simulator seed; full tuple is retained for audit.
    return 1 + int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") % 2147483646


def source_groups() -> list[dict]:
    sources, winds = e1.source_rows(), e1.open_winds()
    result = []
    for ei, (house, wind) in enumerate(e1.ENVS):
        for si, row in enumerate(sources[house]):
            result.append({"environment_index": ei, "house": house, "wind": wind, "source_index": si,
                           "source_id": row["source_id"],
                           "source_xyz": [float(row[k]) for k in ("x_m", "y_m", "z_m")],
                           "wind_dir": winds[ei]["wind_dir"],
                           "wind_iteration_hashes": winds[ei]["iteration_hashes"]})
    assert len(result) == 18
    return result


def plan(group: dict, phase: str, index: int) -> dict:
    assert phase in ("REFERENCE", "TARGET")
    key = f"JTD_E2|{phase}|environment_id={group['environment_index']}|source_id={group['source_id']}|{phase.lower()}_new_index={index}"
    seed = seed_from_key(key)
    root = DATA_ROOT / phase.lower() / f"E{group['environment_index']}_{group['house']}" / group["wind"] / group["source_id"]
    run = root / f"{phase.lower()}_{index:02d}_seed_{seed}"
    return {"phase": phase, "environment_index": group["environment_index"], "house": group["house"],
            "wind": group["wind"], "source_index": group["source_index"], "source_id": group["source_id"],
            "source_xyz": group["source_xyz"], "new_index": index, "seed_key": key,
            "requested_seed": seed, "run_dir": str(run)}


def audit_existing(groups: list[dict], probes: dict) -> tuple[np.ndarray, list[dict]]:
    e2_index = e1.rows(e1.E2 / "E2_OPEN_DISCOVERY_INDEX.tsv")
    e1_index = e1.rows(e1.OUT / "JTD_E1_TARGET_MANIFEST.tsv")
    e2_tensor = np.load(e1.E2 / "E2_OPEN_DISCOVERY_10x30.npy", allow_pickle=False)
    e1_tensor = np.load(e1.OUT / "JTD_E1_FRESH_TARGETS_10x30.npy", allow_pickle=False)
    if len(e2_index) != 72 or len(e1_index) != 36 or e2_tensor.shape != (3,6,4,10,30) or e1_tensor.shape != (3,6,2,10,30):
        raise RuntimeError("OPEN E2/E1 historical reference count drift")
    by_e2 = {(int(r["environment_index"]), int(r["source_index"]), int(r["replicate_index"])): r for r in e2_index}
    by_e1 = {(int(r["environment_index"]), int(r["source_index"]), int(r["target_replicate"])): r for r in e1_index}
    if len(by_e2) != 72 or len(by_e1) != 36:
        raise RuntimeError("duplicate historical OPEN run key")
    tensor = np.empty((3,6,6,10,30), dtype=np.float32)
    manifest = []
    for group in groups:
        ei, si, house, wind, sid = (group[k] for k in ("environment_index", "source_index", "house", "wind", "source_id"))
        for r in range(6):
            if r < 4:
                row = by_e2[(ei, si, r)]
                requested = 2026110000 + 1000*ei + 10*si + r
                run = e1.E2_RAW / f"E{ei}_{house}" / wind / sid / f"r{r}_seed{requested}"
                pooled_expected = e2_tensor[ei, si, r]
                origin = "E2_OPEN_REFERENCE"
            else:
                j = r-4
                row = by_e1[(ei, si, j)]
                requested = 2026120000 + 1000*ei + 10*si + j
                run = e1.TARGET_ROOT / f"E{ei}_{house}" / wind / sid / f"t{j}_seed{requested}"
                pooled_expected = e1_tensor[ei, si, j]
                origin = "E1_HISTORICAL_TARGET_RECLASSIFIED_REFERENCE"
            if row["source_id"] != sid or int(row["requested_seed"]) != requested:
                raise RuntimeError("OPEN historical seed/source drift")
            cube_path = run / "concentration.npy"
            pooled_path = run / "pooled.npy"
            meta_path = run / "run_metadata.json"
            if sha(cube_path) != row["cube_sha256"]:
                raise RuntimeError(f"OPEN historical cube hash drift: {cube_path}")
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta["requested_seed"] != requested or meta["cube_sha256"] != row["cube_sha256"]:
                raise RuntimeError("OPEN historical run metadata drift")
            cube = e1.cube_qc(cube_path, house)
            repooled = e1.pool(cube, probes[house])
            # E2 retained raw cubes and the aggregate OPEN tensor; E1 also retained per-run pooled.npy.
            pooled = np.load(pooled_path, allow_pickle=False) if pooled_path.is_file() else repooled
            if not np.array_equal(repooled, pooled) or not np.array_equal(pooled, pooled_expected):
                raise RuntimeError("OPEN historical raw cube/pooled tensor mismatch")
            tensor[ei, si, r] = pooled
            manifest.append({"environment_index": ei, "house": house, "wind": wind,
                             "source_index": si, "source_id": sid, "reference_index": r,
                             "origin": origin, "requested_seed": requested, "cube_sha256": row["cube_sha256"],
                             "pooled_sha256": sha(pooled_path) if pooled_path.is_file() else "",
                             "pooled_value_sha256": hashlib.sha256(pooled.tobytes()).hexdigest(),
                             "run_dir": str(run)})
    assert len(manifest) == 108
    return tensor, manifest


def preflight() -> None:
    if INITIAL_LOCK.exists() or DATA_ROOT.exists():
        raise RuntimeError("refuse to replace existing E2 initial lock/acquisition")
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() != BRANCH:
        raise RuntimeError("wrong JTD E2 branch")
    if sha(e1.BINARY) != e1.BINARY_SHA or sha(e1.EXTRACTOR) != e1.EXTRACTOR_SHA:
        raise RuntimeError("simulator or extractor hash drift")
    for house, expected in e1.OCC_SHA.items():
        if sha(e1.CANONICAL / house / "OccupancyGrid3D.csv") != expected:
            raise RuntimeError("OPEN occupancy hash drift")
    probes = e1.probe_rows()
    groups = source_groups()
    six, historical_manifest = audit_existing(groups, probes)
    full_plan = [plan(g, "REFERENCE", i) for g in groups for i in range(6)] + \
                [plan(g, "TARGET", i) for g in groups for i in range(4)]
    if len(full_plan) != 180 or len({r["requested_seed"] for r in full_plan}) != 180:
        raise RuntimeError("E2 new simulator seed alias")
    old_seeds = {r["requested_seed"] for r in historical_manifest}
    if old_seeds & {r["requested_seed"] for r in full_plan}:
        raise RuntimeError("E2 seed collides with historical OPEN run")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    np.save(EVIDENCE / "JTD_E2_EXISTING_6_REFERENCE_10x30.npy", six, allow_pickle=False)
    write_tsv(EVIDENCE / "JTD_E2_EXISTING_REFERENCE_MANIFEST.tsv", historical_manifest)
    write_tsv(EVIDENCE / "JTD_E2_SEED_PLAN_180.tsv", full_plan)
    charter = ROOT / "research/jtd_crossenv_k12_v0/JTD_E2_K12_CROSSENV_CONFIRMATION_CHARTER_20260925.md"
    prompt = ROOT / "research/jtd_crossenv_k12_v0/CODEX_JTD_E2_EXECUTION_PROMPT_20260925.md"
    lock = {"branch": BRANCH, "phase": "BEFORE_ANY_E2_NEW_PLUME", "source_groups": groups,
            "planned_new_reference_count": 108, "planned_new_target_count": 72,
            "existing_development_reference_count": 108,
            "seed_domain": "SHA256 full key, first eight bytes big-endian modulo 2147483646 plus 1",
            "seed_plan_sha256": sha(EVIDENCE / "JTD_E2_SEED_PLAN_180.tsv"),
            "existing_tensor_sha256": sha(EVIDENCE / "JTD_E2_EXISTING_6_REFERENCE_10x30.npy"),
            "existing_manifest_sha256": sha(EVIDENCE / "JTD_E2_EXISTING_REFERENCE_MANIFEST.tsv"),
            "e2_open_index_sha256": sha(e1.E2 / "E2_OPEN_DISCOVERY_INDEX.tsv"),
            "e1_target_manifest_sha256": sha(e1.OUT / "JTD_E1_TARGET_MANIFEST.tsv"),
            "source_contract_sha256": e1.SOURCE_SHA, "probe_contract_sha256": e1.PROBE_SHA,
            "binary_sha256": e1.BINARY_SHA, "extractor_sha256": e1.EXTRACTOR_SHA,
            "occupancy_sha256": e1.OCC_SHA,
            "winds": e1.open_winds(), "seed_source_sha256": sha(e1.MATHUTILS),
            "simulation_parameters": json.loads((e1.OUT / "JTD_E1_PRE_RUN_LOCK.json").read_text(encoding="utf-8"))["simulation_parameters"],
            "charter_sha256": sha(charter), "execution_prompt_sha256": sha(prompt),
            "runner_sha256": sha(Path(__file__)),
            "no_sealed_input": True, "no_target_data_seen": True}
    write_json(INITIAL_LOCK, lock)
    print("JTD_E2_INITIAL_LOCK_READY", sha(INITIAL_LOCK), "historical_refs", len(historical_manifest),
          "new_references", 108, "fresh_targets", 72, flush=True)


def lock_checked() -> tuple[dict, list[dict]]:
    lock = json.loads(INITIAL_LOCK.read_text(encoding="utf-8"))
    if lock["branch"] != BRANCH or lock["runner_sha256"] != sha(Path(__file__)):
        raise RuntimeError("E2 initial lock/code drift")
    committed = subprocess.check_output(["git", "show", "HEAD:evidence/jtd_e2_20260925/JTD_E2_INITIAL_LOCK.json"], cwd=ROOT)
    if hashlib.sha256(committed).hexdigest() != sha(INITIAL_LOCK):
        raise RuntimeError("initial lock must be committed before any E2 plume")
    seed_path = EVIDENCE / "JTD_E2_SEED_PLAN_180.tsv"
    if sha(seed_path) != lock["seed_plan_sha256"]:
        raise RuntimeError("E2 seed plan drift")
    if sha(e1.BINARY) != lock["binary_sha256"] or sha(e1.EXTRACTOR) != lock["extractor_sha256"]:
        raise RuntimeError("E2 binary/extractor drift")
    plans = e1.rows(seed_path)
    for row in plans:
        row["environment_index"] = int(row["environment_index"])
        row["source_index"] = int(row["source_index"])
        row["new_index"] = int(row["new_index"])
        row["requested_seed"] = int(row["requested_seed"])
        row["source_xyz"] = json.loads(row["source_xyz"].replace("'", '"')) if row["source_xyz"].startswith("[") else row["source_xyz"]
        if row["requested_seed"] != seed_from_key(row["seed_key"]):
            raise RuntimeError("E2 seed resolution drift")
    if len(plans) != 180:
        raise RuntimeError("E2 plan count drift")
    return lock, plans


def existing_run(item: dict, lock: dict, probes: dict) -> dict | None:
    run = Path(item["run_dir"])
    meta_file, cube_file, pooled_file = run / "run_metadata.json", run / "concentration.npy", run / "pooled.npy"
    if not (meta_file.is_file() and cube_file.is_file() and pooled_file.is_file()):
        return None
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    for key in ("phase", "environment_index", "house", "wind", "source_index", "source_id", "source_xyz", "new_index", "seed_key", "requested_seed"):
        if meta[key] != item[key]:
            raise RuntimeError(f"E2 run metadata drift: {run}, {key}")
    if meta["initial_lock_sha256"] != sha(INITIAL_LOCK) or meta["binary_sha256"] != lock["binary_sha256"]:
        raise RuntimeError("E2 run initial lock/binary drift")
    if sha(cube_file) != meta["cube_sha256"] or sha(pooled_file) != meta["pooled_sha256"]:
        raise RuntimeError("E2 cube/pooled hash drift")
    cube = e1.cube_qc(cube_file, item["house"])
    if not np.array_equal(e1.pool(cube, probes[item["house"]]), np.load(pooled_file, allow_pickle=False)):
        raise RuntimeError("E2 raw cube re-pool mismatch")
    return meta


def acquire_one(item: dict, lock: dict, probes: dict) -> dict:
    previous = existing_run(item, lock, probes)
    if previous is not None:
        return previous
    run = Path(item["run_dir"])
    if run.exists() and any(run.iterdir()):
        real = run / "realization"
        log = run / "generation.log"
        resume = real.is_dir() and log.is_file() and "Filament simulator finished correctly!" in log.read_text(errors="replace") and len(list(real.glob("iteration_*"))) == 566 and not (run / "concentration.npy").exists()
        if not resume:
            raise RuntimeError(f"incomplete E2 run requires infrastructure audit: {run}")
    else:
        run.mkdir(parents=True, exist_ok=True)
        real = run / "realization"
        real.mkdir()
        resume = False
    occ = e1.CANONICAL / item["house"] / "OccupancyGrid3D.csv"
    if not resume:
        real.joinpath("OccupancyGrid3D.csv").symlink_to(occ)
        sx, sy, sz = item["source_xyz"]
        wind = lock["winds"][item["environment_index"]]["wind_dir"]
        options = {"verbose": "false", "wait_preprocessing": "false", "sim_time": "300.0", "time_step": "0.1",
                   "num_filaments_sec": "7", "variable_rate": "true", "filament_stop_steps": "0",
                   "ppm_filament_center": "10.0", "filament_initial_std": "10.0", "filament_growth_gamma": "15.0",
                   "filament_noise_std": "0.01", "gas_type": "10", "temperature": "298.0", "pressure": "1.0",
                   "concentration_unit_choice": "1", "occupancy3D_data": str(occ), "fixed_frame": "map",
                   "wind_data": wind, "wind_time_step": "1.0", "allow_looping": "true",
                   "loop_from_step": "1", "loop_to_step": "10",
                   "source_position_x": repr(sx), "source_position_y": repr(sy), "source_position_z": repr(sz),
                   "save_results": "1", "results_time_step": "0.5", "results_min_time": "0.0",
                   "writeConcentrations": "false", "results_location": str(real)}
        cmd = [str(e1.BINARY), "--ros-args"] + [v for k, x in options.items() for v in ("-p", f"{k}:={x}")]
        with (run / "generation.log").open("w", encoding="utf-8") as stream:
            subprocess.run(cmd, env=dict(os.environ, GADEN_RNG_SEED=str(item["requested_seed"])),
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
    if "Filament simulator finished correctly!" not in (run / "generation.log").read_text(errors="replace") or len(list(real.glob("iteration_*"))) != 566:
        raise RuntimeError("E2 simulator completion/iteration count failed")
    if not real.joinpath("OccupancyGrid3D.csv").exists():
        real.joinpath("OccupancyGrid3D.csv").symlink_to(occ)
    header = occ.read_text().splitlines()[:4]
    origin = [float(v) for v in header[0].split()[1:]]
    dims = [int(v) for v in header[2].split()[1:]]
    if dims[:2] != ([87,114] if item["house"] == "House01" else [83,119]):
        raise RuntimeError("OPEN occupancy dimensions drift")
    command = [str(e1.EXTRACTOR), str(real), str(real), str(run / "concentration.npy"),
               str(run / "spatial_metadata.json"), repr(origin[0]), repr(origin[1]), "0.1", "1", "0.20",
               str(dims[0]), str(dims[1]), *[str(t) for t in e1.TIMES]]
    with (run / "extract.log").open("w", encoding="utf-8") as stream:
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
    cube = e1.cube_qc(run / "concentration.npy", item["house"])
    with (run / "pooled.npy").open("wb") as stream:
        np.save(stream, e1.pool(cube, probes[item["house"]]), allow_pickle=False)
    requested = item["requested_seed"]
    resolved = (requested ^ (requested >> 32)) & 0xFFFFFFFF
    meta = dict(item, initial_lock_sha256=sha(INITIAL_LOCK),
                binary_sha256=lock["binary_sha256"], extractor_sha256=lock["extractor_sha256"],
                occupancy_sha256=lock["occupancy_sha256"][item["house"]],
                wind_iteration_hashes=lock["winds"][item["environment_index"]]["iteration_hashes"],
                source_contract_sha256=lock["source_contract_sha256"],
                probe_contract_sha256=lock["probe_contract_sha256"],
                resolved_seed_base_uint32=resolved,
                resolved_seed_gaussian_uint32=(resolved+0x9E3779B9)&0xFFFFFFFF,
                resolved_seed_uniform_uint32=(resolved+0x243F6A88)&0xFFFFFFFF,
                cube_sha256=sha(run / "concentration.npy"), cube_bytes=(run / "concentration.npy").stat().st_size,
                pooled_sha256=sha(run / "pooled.npy"), pooled_bytes=(run / "pooled.npy").stat().st_size,
                spatial_metadata_sha256=sha(run / "spatial_metadata.json"),
                generation_log_sha256=sha(run / "generation.log"), extract_log_sha256=sha(run / "extract.log"))
    write_json(run / "run_metadata.json", meta)
    if real.resolve().is_relative_to(DATA_ROOT.resolve()):
        shutil.rmtree(real)
    else:
        raise RuntimeError("temporary simulator cleanup escaped E2 root")
    return meta


def acquire(phase: str) -> None:
    lock, plans = lock_checked()
    if phase == "TARGET":
        if not PRE_TARGET_LOCK.exists():
            raise RuntimeError("target phase requires frozen pre-target lock")
        pre = json.loads(PRE_TARGET_LOCK.read_text(encoding="utf-8"))
        committed = subprocess.check_output(["git", "show", "HEAD:evidence/jtd_e2_20260925/JTD_E2_PRE_TARGET_LOCK.json"], cwd=ROOT)
        if hashlib.sha256(committed).hexdigest() != sha(PRE_TARGET_LOCK):
            raise RuntimeError("pre-target lock not committed before fresh target")
        if pre["phase"] != "BEFORE_ANY_E2_FRESH_TARGET" or pre["reference_count"] != 216:
            raise RuntimeError("pre-target lock state drift")
        for name, key in (("JTD_E2_REFERENCE_12x10x30.npy", "reference_tensor_sha256"),
                          ("JTD_E2_MODEL_LOCK.npz", "model_lock_sha256"),
                          ("JTD_E2_NULL_MODEL_LOCK.npz", "null_model_lock_sha256")):
            if sha(EVIDENCE / name) != pre[key]:
                raise RuntimeError(f"pre-target fitted artifact drift: {name}")
    chosen = [q for q in plans if q["phase"] == phase]
    expected = 108 if phase == "REFERENCE" else 72
    if len(chosen) != expected:
        raise RuntimeError("E2 phase plan size drift")
    probes = e1.probe_rows()
    for index, item in enumerate(chosen, 1):
        meta = acquire_one(item, lock, probes)
        print(f"JTD_E2_{phase}_QC_PASS", index, expected, item["environment_index"], item["source_id"],
              item["requested_seed"], meta["cube_sha256"], flush=True)
    rows = []
    tensor = np.empty((3,6,6 if phase=="REFERENCE" else 4,10,30), dtype=np.float32)
    for item in chosen:
        meta = existing_run(item, lock, probes)
        if meta is None:
            raise RuntimeError("E2 phase incomplete")
        tensor[item["environment_index"], item["source_index"], item["new_index"]] = np.load(Path(item["run_dir"]) / "pooled.npy", allow_pickle=False)
        rows.append({k: meta[k] for k in ("phase", "environment_index", "house", "wind", "source_index", "source_id",
                                                "new_index", "seed_key", "requested_seed", "resolved_seed_base_uint32",
                                                "cube_sha256", "cube_bytes", "pooled_sha256", "pooled_bytes", "run_dir")})
    if len(rows) != expected or not np.isfinite(tensor).all():
        raise RuntimeError("E2 complete tensor QC fail")
    prefix = "JTD_E2_NEW_REFERENCE" if phase=="REFERENCE" else "JTD_E2_FRESH_TARGET"
    write_tsv(EVIDENCE / f"{prefix}_MANIFEST.tsv", rows)
    np.save(EVIDENCE / f"{prefix}_10x30.npy", tensor, allow_pickle=False)
    if phase == "REFERENCE":
        six = np.load(EVIDENCE / "JTD_E2_EXISTING_6_REFERENCE_10x30.npy", allow_pickle=False)
        full = np.concatenate([six, tensor], axis=2)
        assert full.shape == (3,6,12,10,30)
        np.save(EVIDENCE / "JTD_E2_REFERENCE_12x10x30.npy", full, allow_pickle=False)
        historical = e1.rows(EVIDENCE / "JTD_E2_EXISTING_REFERENCE_MANIFEST.tsv")
        twelve = historical + [dict(r, reference_index=6+int(r["new_index"]), origin="E2_NEW_REFERENCE") for r in rows]
        write_tsv(EVIDENCE / "JTD_E2_REFERENCE_12_MANIFEST.tsv", twelve)
        write_json(EVIDENCE / "JTD_E2_REFERENCE_ACQUISITION.json", {
            "new_reference_runs": 108, "historical_open_development_runs": 108,
            "reference_count": 216, "realizations_per_source": 12,
            "full_concentration_cubes_retained_new": 108,
            "initial_lock_sha256": sha(INITIAL_LOCK),
            "new_manifest_sha256": sha(EVIDENCE / f"{prefix}_MANIFEST.tsv"),
            "reference_12_manifest_sha256": sha(EVIDENCE / "JTD_E2_REFERENCE_12_MANIFEST.tsv"),
            "reference_tensor_sha256": sha(EVIDENCE / "JTD_E2_REFERENCE_12x10x30.npy"),
            "new_reference_root": str(DATA_ROOT / "reference"), "sealed_data_read": False})
    else:
        write_json(EVIDENCE / "JTD_E2_TARGET_ACQUISITION.json", {
            "new_fresh_target_runs": 72, "full_concentration_cubes_retained": 72,
            "pre_target_lock_sha256": sha(PRE_TARGET_LOCK),
            "manifest_sha256": sha(EVIDENCE / f"{prefix}_MANIFEST.tsv"),
            "target_tensor_sha256": sha(EVIDENCE / f"{prefix}_10x30.npy"),
            "target_root": str(DATA_ROOT / "target"), "sealed_data_read": False})
    print(f"JTD_E2_{phase}_ACQUISITION_COMPLETE", expected, flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("preflight", "reference", "target"))
    a = p.parse_args()
    if a.mode == "preflight":
        preflight()
    else:
        acquire("REFERENCE" if a.mode == "reference" else "TARGET")


if __name__ == "__main__":
    main()
