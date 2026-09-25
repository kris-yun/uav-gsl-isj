#!/usr/bin/env python3
"""JTD-E1 pre-run lock and exact 36-target GADEN acquisition on the VM."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from itertools import islice
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
E1 = ROOT / "evidence/environment_level_benchmark_v0/e1"
E2 = ROOT / "evidence/environment_level_benchmark_v0/e2"
OUT = ROOT / "evidence/jtd_e1_20260925"
E2_RAW = Path("/home/zyc/E2_CROSS_ENVIRONMENT_168_RUNS_20260925/OPEN_DISCOVERY")
TARGET_ROOT = Path("/home/zyc/JTD_E1_FRESH_TARGETS_20260925")
CANONICAL = Path("/mnt/hgfs/workspace/GADEN_files/scenarios")
BUILD = Path("/home/zyc/hcmc_gaden_seed_build_20260922")
BINARY = BUILD / "install/gaden_filament_simulator/lib/gaden_filament_simulator/filament_simulator"
EXTRACTOR = Path("/home/zyc/rmfe_filament_extractor_omp")
MATHUTILS = BUILD / "src/GADEN/gaden_common/third_party/gaden_core/include/gaden/internal/MathUtils.hpp"
TIMES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550)
ENVS = (("House01", "1,3-2,4_fast"), ("House02", "3,5-1_slow"),
        ("House02", "4,5-3_slow"))
SOURCE_SHA = "e38bee4467fb9d98ab5ee48a6115eb1b3306df63cd3da409b9412b3032c4b06e"
PROBE_SHA = "364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812"
BINARY_SHA = "4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"
EXTRACTOR_SHA = "206cc92384866dcb7d966c6f8f9ec87862e15c7fee460a43c04014b58e3cae91"
OCC_SHA = {"House01": "846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb",
           "House02": "9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d"}
CODE = ("run_jtd_e1_vm.py", "run_jtd_e1_vm.sh", "score_jtd_e1.py", "verify_jtd_e1.py")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True)+"\n").encode("utf-8"))


def write_tsv(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def probe_rows() -> dict[str, list[dict[str, str]]]:
    if sha(E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv") != PROBE_SHA:
        raise RuntimeError("E1 probe contract hash drift")
    found = {}
    for house, _ in ENVS:
        found[house] = sorted((r for r in rows(E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv")
                               if r["house"] == house), key=lambda r: int(r["probe_rank"]))
        if len(found[house]) != 30 or [int(r["probe_rank"]) for r in found[house]] != list(range(1, 31)):
            raise RuntimeError("E1 probe ordering drift")
    return found


def pool(cube: np.ndarray, probes: list[dict[str, str]]) -> np.ndarray:
    values = []
    for p in probes:
        x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
        y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
        if x1-x0 != 2 or y1-y0 != 2:
            raise RuntimeError("probe 2x2 pooling drift")
        values.append(cube[:, x0:x1, y0:y1].mean(axis=(1, 2)))
    pooled = np.stack(values, axis=1).astype(np.float32)
    if pooled.shape != (10, 30) or not np.isfinite(pooled).all() or (pooled < 0).any():
        raise RuntimeError("invalid pooled target/reference")
    return pooled


def source_rows() -> dict[str, list[dict[str, str]]]:
    if sha(E1 / "E1_HOUSE_SOURCE_PANELS.tsv") != SOURCE_SHA:
        raise RuntimeError("E1 source panel hash drift")
    all_rows = rows(E1 / "E1_HOUSE_SOURCE_PANELS.tsv")
    found = {house: [r for r in all_rows if r["house"] == house] for house, _ in ENVS}
    for house, panel in found.items():
        if len(panel) != 6 or any(float(r["z_m"]) != 0.2 for r in panel):
            raise RuntimeError(f"six-source z=0.2 contract drift: {house}")
    return found


def open_winds() -> list[dict]:
    # Read only the 33 OPEN wind rows; do not parse any sealed row.
    with (E2 / "E2_WIND_FILE_HASHES.tsv").open(newline="", encoding="utf-8") as stream:
        records = list(islice(csv.DictReader(stream, delimiter="\t"), 33))
    if len(records) != 33:
        raise RuntimeError("OPEN wind file count drift")
    winds = []
    for ei, (house, wind) in enumerate(ENVS):
        group = [r for r in records if int(r["environment_index"]) == ei]
        if len(group) != 11 or any((r["house"], r["wind"]) != (house, wind) for r in group):
            raise RuntimeError("OPEN wind identity drift")
        by_name = {r["file"]: r for r in group}
        if set(by_name) != {f"wind_iteration_{i}" for i in range(11)}:
            raise RuntimeError("OPEN wind iteration drift")
        for row in group:
            path = Path(row["path"])
            if path.stat().st_size != int(row["bytes"]) or sha(path) != row["sha256"]:
                raise RuntimeError(f"OPEN wind hash drift: {path}")
        winds.append({"environment_index": ei, "house": house, "wind": wind,
                      "wind_dir": str(Path(group[0]["path"]).parent),
                      "iteration_hashes": {name: by_name[name]["sha256"] for name in sorted(by_name)}})
    return winds


def null_permutations() -> tuple[np.ndarray, list[dict]]:
    matrix = np.empty((3, 200, 6, 4, 4), dtype=np.uint8)
    bases = []
    for ei in range(3):
        for null_id in range(200):
            base = f"JTD-E1|environment={ei}|null={null_id}"
            bases.append({"environment_index": ei, "null_id": null_id, "base_key": base})
            for source in range(6):
                for block in range(1, 5):
                    key = f"{base}|source={source}|block={block}"
                    seed = int.from_bytes(hashlib.sha256(key.encode("ascii")).digest()[:8], "little")
                    rng = np.random.default_rng(seed)
                    for _ in range(1000):
                        perm = rng.permutation(4)
                        if np.all(perm != np.arange(4)):
                            matrix[ei, null_id, source, block-1] = perm
                            break
                    else:
                        raise RuntimeError("null derangement generation failure")
    return matrix, bases


def build_pre_run_lock() -> dict:
    if OUT.joinpath("JTD_E1_PRE_RUN_LOCK.json").exists():
        raise RuntimeError("refuse to replace frozen E1 pre-run lock")
    if TARGET_ROOT.exists() and any(TARGET_ROOT.iterdir()):
        raise RuntimeError("fresh target root already contains runs before lock")
    if sha(BINARY) != BINARY_SHA or sha(EXTRACTOR) != EXTRACTOR_SHA:
        raise RuntimeError("E2 simulator/extractor binary drift")
    for house, expected in OCC_SHA.items():
        if sha(CANONICAL / house / "OccupancyGrid3D.csv") != expected:
            raise RuntimeError("OPEN occupancy hash drift")
    sources, probes, winds = source_rows(), probe_rows(), open_winds()
    open_index = rows(E2 / "E2_OPEN_DISCOVERY_INDEX.tsv")
    if len(open_index) != 72:
        raise RuntimeError("E2 OPEN index count drift")
    reference = np.load(E2 / "E2_OPEN_DISCOVERY_10x30.npy", allow_pickle=False).copy()
    if reference.shape != (3, 6, 4, 10, 30) or reference.dtype != np.float32:
        raise RuntimeError("E2 OPEN reference vector shape/dtype drift")
    reference_groups = []
    by_key = {(int(r["environment_index"]), int(r["source_index"]), int(r["replicate_index"])): r
              for r in open_index}
    if len(by_key) != 72:
        raise RuntimeError("duplicate E2 OPEN reference")
    for ei, (house, wind) in enumerate(ENVS):
        for si, source in enumerate(sources[house]):
            runs = []
            for rep in range(4):
                row = by_key[(ei, si, rep)]
                seed = 2026110000 + 1000*ei + 10*si + rep
                if (row["house"], row["wind"], row["source_id"], int(row["requested_seed"])) != (
                        house, wind, source["source_id"], seed):
                    raise RuntimeError("E2 OPEN reference identity/seed drift")
                run = E2_RAW / f"E{ei}_{house}" / wind / source["source_id"] / f"r{rep}_seed{seed}"
                cube_path, meta_path = run / "concentration.npy", run / "run_metadata.json"
                if sha(cube_path) != row["cube_sha256"]:
                    raise RuntimeError(f"E2 OPEN reference cube hash drift: {cube_path}")
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta["requested_seed"] != seed or meta["cube_sha256"] != row["cube_sha256"]:
                    raise RuntimeError("E2 OPEN run provenance drift")
                cube = np.load(cube_path, allow_pickle=False)
                if cube.shape != (10, *((87, 114) if house == "House01" else (83, 119))):
                    raise RuntimeError("E2 OPEN cube shape drift")
                if not np.array_equal(pool(cube, probes[house]), reference[ei, si, rep]):
                    raise RuntimeError("E2 OPEN exact pooled reference mismatch")
                runs.append({"replicate_index": rep, "requested_seed": seed,
                             "resolved_seed_base_uint32": meta["resolved_seed_base_uint32"],
                             "cube_sha256": row["cube_sha256"], "cube_path": str(cube_path)})
            reference_groups.append({"environment_index": ei, "house": house, "wind": wind,
                                     "source_index": si, "source_id": source["source_id"],
                                     "source_xyz": [float(source[k]) for k in ("x_m", "y_m", "z_m")],
                                     "reference_runs": runs})
    plan = []
    for group in reference_groups:
        ei, si = group["environment_index"], group["source_index"]
        for target in range(2):
            seed = 2026120000 + 1000*ei + 10*si + target
            run = TARGET_ROOT / f"E{ei}_{group['house']}" / group["wind"] / group["source_id"] / f"t{target}_seed{seed}"
            plan.append({"environment_index": ei, "house": group["house"], "wind": group["wind"],
                         "source_index": si, "source_id": group["source_id"],
                         "source_xyz": group["source_xyz"], "target_replicate": target,
                         "requested_seed": seed, "run_dir": str(run)})
    if len(plan) != 36 or len({p["requested_seed"] for p in plan}) != 36:
        raise RuntimeError("E1 target seed count/uniqueness drift")
    matrix, keys = null_permutations()
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(E2 / "E2_OPEN_DISCOVERY_10x30.npy", OUT / "JTD_E1_REFERENCE_10x30.npy")
    with (OUT / "JTD_E1_NULL_DERANGEMENTS.npy").open("wb") as stream:
        np.save(stream, matrix, allow_pickle=False)
    code_hashes = {name: sha(ROOT / "research/jtd_cross_environment_v0" / name) for name in CODE}
    code_hashes["JTD_E1_CROSS_ENVIRONMENT_GATE_20260925.md"] = sha(ROOT / "research/jtd_cross_environment_v0/JTD_E1_CROSS_ENVIRONMENT_GATE_20260925.md")
    code_hashes["CODEX_JTD_E1_EXECUTION_PROMPT_20260925.md"] = sha(ROOT / "research/jtd_cross_environment_v0/CODEX_JTD_E1_EXECUTION_PROMPT_20260925.md")
    lock = {"branch": "research/jtd-cross-environment-v0", "source_commit_at_lock":
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "reference_groups": reference_groups, "fresh_target_plan": plan,
            "source_contract_sha256": SOURCE_SHA, "probe_contract_sha256": PROBE_SHA,
            "e2_open_index_sha256": sha(E2 / "E2_OPEN_DISCOVERY_INDEX.tsv"),
            "e2_open_vector_sha256": sha(E2 / "E2_OPEN_DISCOVERY_10x30.npy"),
            "reference_snapshot_sha256": sha(OUT / "JTD_E1_REFERENCE_10x30.npy"),
            "winds": winds, "occupancy_sha256": OCC_SHA,
            "binary_sha256": BINARY_SHA, "extractor_sha256": EXTRACTOR_SHA,
            "seed_source_sha256": sha(MATHUTILS),
            "simulation_parameters": {"sim_time": 300.0, "time_step": 0.1, "num_filaments_sec": 7,
                                      "variable_rate": True, "filament_stop_steps": 0,
                                      "ppm_filament_center": 10.0, "filament_initial_std": 10.0,
                                      "filament_growth_gamma": 15.0, "filament_noise_std": 0.01,
                                      "gas_type": 10, "temperature": 298.0, "pressure": 1.0,
                                      "concentration_unit_choice": 1, "wind_time_step": 1.0,
                                      "allow_looping": True, "loop_from_step": 1, "loop_to_step": 10,
                                      "save_results": 1, "results_time_step": 0.5,
                                      "results_min_time": 0.0, "writeConcentrations": False,
                                      "fixed_frame": "map", "extract_times": list(TIMES), "extract_z_m": 0.2},
            "feature_contract": {"observable": "raw ppm 2x2 pooled mean, float32 as in E2 OPEN",
                                 "shape": [10, 30], "blocks": [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]],
                                 "per_block": "reference-only StandardScaler then PCA(n_components=2,svd_solver=full)",
                                 "density": "six source-specific sklearn OAS Gaussian 10D, G0 jitter, uniform prior"},
            "null_base_keys": keys, "null_derangements_sha256": sha(OUT / "JTD_E1_NULL_DERANGEMENTS.npy"),
            "null_key_rule": "JTD-E1|environment={0..2}|null={0..199}|source={0..5}|block={1..4}; first 8 SHA256 bytes little-endian PCG64 seed; rejection-sample derangement of 4",
            "bootstrap": {"draws": 5000, "seed": 2026092502,
                          "unit": "environment x source; resample six source units within each environment, keeping both targets together"},
            "gate_thresholds": {"G1": "all three environment mean deltas >0",
                                "G2": "cluster bootstrap 95% CI lower >0",
                                "G3": "positive source units >=13/18 and >=4/6 in each environment",
                                "G4": "pooled 20% trimmed mean delta >0",
                                "G5": "remove two largest positive target deltas; remaining mean >0",
                                "G6": "pooled relative mean NLL improvement >=0.10",
                                "G7": "FULL mean NLL <=1.10*SHUFFLED mean NLL in each environment"},
            "hold_rule": "G2,G4,G5,G7 pass; exactly one environment fails its local G1 or local G3; otherwise STOP",
            "code_sha256": code_hashes,
            "no_sealed_input": True, "planned_new_plume_runs": 36}
    write_json(OUT / "JTD_E1_PRE_RUN_LOCK.json", lock)
    return lock


def validate_lock(lock: dict) -> None:
    if lock["branch"] != "research/jtd-cross-environment-v0" or lock["planned_new_plume_runs"] != 36:
        raise RuntimeError("E1 lock identity drift")
    attestation_path = OUT / "JTD_E1_INFRA_PATCH_ATTESTATION.json"
    attestation = json.loads(attestation_path.read_text(encoding="utf-8")) if attestation_path.exists() else None
    if attestation is not None and attestation.get("pre_run_lock_sha256") != sha(OUT / "JTD_E1_PRE_RUN_LOCK.json"):
        raise RuntimeError("infrastructure attestation references a different lock")
    for name, expected in lock["code_sha256"].items():
        actual = sha(ROOT / "research/jtd_cross_environment_v0" / name)
        if actual != expected and not (attestation is not None and
                                       name in ("run_jtd_e1_vm.py", "score_jtd_e1.py") and
                                       attestation.get("original_code_sha256", {}).get(name) == expected and
                                       attestation.get("patched_code_sha256", {}).get(name) == actual):
            raise RuntimeError(f"pre-run code hash drift: {name}")
    if sha(OUT / "JTD_E1_NULL_DERANGEMENTS.npy") != lock["null_derangements_sha256"]:
        raise RuntimeError("null derangement matrix drift")
    if sha(OUT / "JTD_E1_REFERENCE_10x30.npy") != lock["reference_snapshot_sha256"]:
        raise RuntimeError("reference snapshot drift")
    if len(lock["fresh_target_plan"]) != 36 or len(lock["reference_groups"]) != 18:
        raise RuntimeError("E1 lock cardinality drift")
    if sha(BINARY) != lock["binary_sha256"] or sha(EXTRACTOR) != lock["extractor_sha256"]:
        raise RuntimeError("simulator/extractor drift after lock")


def cube_qc(cube_path: Path, house: str) -> np.ndarray:
    cube = np.load(cube_path, allow_pickle=False)
    shape = (10, 87, 114) if house == "House01" else (10, 83, 119)
    if cube.shape != shape or not np.isfinite(cube).all() or (cube < 0).any():
        raise RuntimeError(f"fresh target cube QC fail: {cube_path}")
    return cube


def validate_existing(item: dict, lock: dict) -> dict | None:
    run = Path(item["run_dir"])
    meta_path, cube_path, pooled_path = run / "run_metadata.json", run / "concentration.npy", run / "pooled.npy"
    if not (meta_path.is_file() and cube_path.is_file() and pooled_path.is_file()):
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    for key in ("environment_index", "house", "wind", "source_index", "source_id", "source_xyz",
                "target_replicate", "requested_seed"):
        if meta.get(key) != item[key]:
            raise RuntimeError(f"fresh target metadata drift: {run}, {key}")
    if meta["binary_sha256"] != lock["binary_sha256"] or meta["cube_sha256"] != sha(cube_path):
        raise RuntimeError(f"fresh target code/cube hash drift: {run}")
    if meta["pooled_sha256"] != sha(pooled_path):
        raise RuntimeError(f"fresh target pooled hash drift: {run}")
    cube = cube_qc(cube_path, item["house"])
    pooled = np.load(pooled_path, allow_pickle=False)
    probes = probe_rows()[item["house"]]
    if not np.array_equal(pool(cube, probes), pooled):
        raise RuntimeError(f"fresh target pooled extraction drift: {run}")
    return meta


def acquire_one(item: dict, lock: dict, probes: dict[str, list[dict]]) -> dict:
    existing = validate_existing(item, lock)
    if existing is not None:
        return existing
    run = Path(item["run_dir"])
    resume_extraction = False
    if run.exists() and any(run.iterdir()):
        real_existing = run / "realization"
        log_existing = run / "generation.log"
        resume_extraction = (real_existing.is_dir() and log_existing.is_file() and
                             "Filament simulator finished correctly!" in log_existing.read_text(errors="replace") and
                             len(list(real_existing.glob("iteration_*"))) == 566 and
                             not (run / "concentration.npy").exists())
        if not resume_extraction:
            raise RuntimeError(f"incomplete target run; infrastructure repair required: {run}")
    else:
        run.mkdir(parents=True)
    real = run / "realization"
    occ = CANONICAL / item["house"] / "OccupancyGrid3D.csv"
    if not resume_extraction:
        real.mkdir()
        real.joinpath("OccupancyGrid3D.csv").symlink_to(occ)
    wind = lock["winds"][item["environment_index"]]["wind_dir"]
    sx, sy, sz = item["source_xyz"]
    options = {
        "verbose": "false", "wait_preprocessing": "false", "sim_time": "300.0", "time_step": "0.1",
        "num_filaments_sec": "7", "variable_rate": "true", "filament_stop_steps": "0",
        "ppm_filament_center": "10.0", "filament_initial_std": "10.0",
        "filament_growth_gamma": "15.0", "filament_noise_std": "0.01",
        "gas_type": "10", "temperature": "298.0", "pressure": "1.0",
        "concentration_unit_choice": "1", "occupancy3D_data": str(occ), "fixed_frame": "map",
        "wind_data": wind, "wind_time_step": "1.0", "allow_looping": "true",
        "loop_from_step": "1", "loop_to_step": "10",
        "source_position_x": repr(sx), "source_position_y": repr(sy), "source_position_z": repr(sz),
        "save_results": "1", "results_time_step": "0.5", "results_min_time": "0.0",
        "writeConcentrations": "false", "results_location": str(real),
    }
    cmd = [str(BINARY), "--ros-args"] + [token for k, v in options.items() for token in ("-p", f"{k}:={v}")]
    env = dict(os.environ, GADEN_RNG_SEED=str(item["requested_seed"]))
    if not resume_extraction:
        with (run / "generation.log").open("w", encoding="utf-8") as stream:
            subprocess.run(cmd, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
    if "Filament simulator finished correctly!" not in (run / "generation.log").read_text(errors="replace"):
        raise RuntimeError(f"fresh target simulator completion missing: {run}")
    if len(list(real.glob("iteration_*"))) != 566:
        raise RuntimeError(f"fresh target iteration count drift: {run}")
    # The simulator removes the pre-run occupancy symlink from its results directory;
    # the extractor requires it. This matches the frozen E2 acquisition behavior.
    if not real.joinpath("OccupancyGrid3D.csv").exists():
        real.joinpath("OccupancyGrid3D.csv").symlink_to(occ)
    header = occ.read_text().splitlines()[:4]
    origin = [float(v) for v in header[0].split()[1:]]
    dims = [int(v) for v in header[2].split()[1:]]
    if dims[:2] != ([87, 114] if item["house"] == "House01" else [83, 119]):
        raise RuntimeError("OPEN occupancy dimensions drift")
    extractor_cmd = [str(EXTRACTOR), str(real), str(real), str(run / "concentration.npy"),
                     str(run / "spatial_metadata.json"), repr(origin[0]), repr(origin[1]),
                     "0.1", "1", "0.20", str(dims[0]), str(dims[1]), *[str(t) for t in TIMES]]
    with (run / "extract.log").open("w", encoding="utf-8") as stream:
        subprocess.run(extractor_cmd, stdout=stream, stderr=subprocess.STDOUT, check=True)
    cube_path = run / "concentration.npy"
    cube = cube_qc(cube_path, item["house"])
    pooled = pool(cube, probes[item["house"]])
    pooled_path = run / "pooled.npy"
    with pooled_path.open("wb") as stream:
        np.save(stream, pooled, allow_pickle=False)
    resolved = (item["requested_seed"] ^ (item["requested_seed"] >> 32)) & 0xFFFFFFFF
    meta = dict(item, resolved_seed_base_uint32=resolved,
                resolved_seed_gaussian_uint32=(resolved + 0x9E3779B9) & 0xFFFFFFFF,
                resolved_seed_uniform_uint32=(resolved + 0x243F6A88) & 0xFFFFFFFF,
                seed_source_sha256=lock["seed_source_sha256"],
                binary_sha256=lock["binary_sha256"], extractor_sha256=lock["extractor_sha256"],
                occupancy_sha256=lock["occupancy_sha256"][item["house"]],
                wind_iteration_hashes=lock["winds"][item["environment_index"]]["iteration_hashes"],
                source_contract_sha256=lock["source_contract_sha256"],
                probe_contract_sha256=lock["probe_contract_sha256"],
                pre_run_lock_sha256=sha(OUT / "JTD_E1_PRE_RUN_LOCK.json"),
                cube_sha256=sha(cube_path), cube_bytes=cube_path.stat().st_size,
                pooled_sha256=sha(pooled_path), pooled_bytes=pooled_path.stat().st_size,
                spatial_metadata_sha256=sha(run / "spatial_metadata.json"),
                generation_log_sha256=sha(run / "generation.log"),
                extraction_log_sha256=sha(run / "extract.log"))
    write_json(run / "run_metadata.json", meta)
    # E2 parity: keep the full concentration cube, remove only this run's temporary simulator iterations.
    if real.resolve().is_relative_to(TARGET_ROOT.resolve()):
        shutil.rmtree(real)
    else:
        raise RuntimeError("scratch cleanup path escaped fresh-target root")
    return meta


def acquire(lock: dict) -> None:
    validate_lock(lock)
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != lock["branch"]:
        raise RuntimeError("VM JTD branch drift")
    # Require the lock to be committed before the first plume.
    rel = "evidence/jtd_e1_20260925/JTD_E1_PRE_RUN_LOCK.json"
    committed = subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=ROOT)
    if hashlib.sha256(committed).hexdigest() != sha(OUT / "JTD_E1_PRE_RUN_LOCK.json"):
        raise RuntimeError("pre-run lock is not committed at HEAD")
    patch_path = OUT / "JTD_E1_INFRA_PATCH_ATTESTATION.json"
    if patch_path.exists():
        patch_rel = "evidence/jtd_e1_20260925/JTD_E1_INFRA_PATCH_ATTESTATION.json"
        committed_patch = subprocess.check_output(["git", "show", f"HEAD:{patch_rel}"], cwd=ROOT)
        if hashlib.sha256(committed_patch).hexdigest() != sha(patch_path):
            raise RuntimeError("infrastructure patch attestation is not committed")
    probes = probe_rows()
    for index, item in enumerate(lock["fresh_target_plan"], 1):
        meta = acquire_one(item, lock, probes)
        print("JTD_E1_TARGET_QC_PASS", index, item["environment_index"], item["source_id"],
              item["requested_seed"], meta["cube_sha256"], flush=True)
    manifest, vector = [], np.empty((3, 6, 2, 10, 30), dtype=np.float32)
    for item in lock["fresh_target_plan"]:
        meta = validate_existing(item, lock)
        if meta is None:
            raise RuntimeError("fresh target acquisition incomplete")
        ei, si, target = item["environment_index"], item["source_index"], item["target_replicate"]
        vector[ei, si, target] = np.load(Path(item["run_dir"]) / "pooled.npy", allow_pickle=False)
        manifest.append({k: meta[k] for k in ("environment_index", "house", "wind", "source_index",
                                                   "source_id", "target_replicate", "requested_seed",
                                                   "resolved_seed_base_uint32", "cube_sha256", "cube_bytes",
                                                   "pooled_sha256", "pooled_bytes", "run_dir")})
    if len(manifest) != 36 or not np.isfinite(vector).all():
        raise RuntimeError("fresh target final count/QC drift")
    write_tsv(OUT / "JTD_E1_TARGET_MANIFEST.tsv", manifest)
    with (OUT / "JTD_E1_FRESH_TARGETS_10x30.npy").open("wb") as stream:
        np.save(stream, vector, allow_pickle=False)
    write_json(OUT / "JTD_E1_TARGET_ACQUISITION.json", {
        "completed_new_plume_runs": 36, "full_concentration_cubes_retained": 36,
        "manifest_sha256": sha(OUT / "JTD_E1_TARGET_MANIFEST.tsv"),
        "target_vector_sha256": sha(OUT / "JTD_E1_FRESH_TARGETS_10x30.npy"),
        "pre_run_lock_sha256": sha(OUT / "JTD_E1_PRE_RUN_LOCK.json"),
        "target_root": str(TARGET_ROOT), "only_open_environments": True,
        "sealed_data_read": False})
    print("JTD_E1_36_FRESH_TARGETS_ACQUIRED", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "acquire"))
    args = parser.parse_args()
    if args.mode == "preflight":
        lock = build_pre_run_lock()
        print("JTD_E1_PRE_RUN_LOCK_READY", sha(OUT / "JTD_E1_PRE_RUN_LOCK.json"),
              len(lock["reference_groups"]), len(lock["fresh_target_plan"]), flush=True)
    else:
        lock = json.loads((OUT / "JTD_E1_PRE_RUN_LOCK.json").read_text(encoding="utf-8"))
        acquire(lock)


if __name__ == "__main__":
    main()
