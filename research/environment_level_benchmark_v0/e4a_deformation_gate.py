#!/usr/bin/env python3
"""One-time E4A gate; prepare OPEN subspace before reading H02 DEV data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
E1 = ROOT / "evidence/environment_level_benchmark_v0/e1"
E2 = ROOT / "evidence/environment_level_benchmark_v0/e2"
OUT = ROOT / "evidence/environment_level_benchmark_v0/e4a"
SCRIPT = Path(__file__).resolve()
OPEN = E2 / "E2_OPEN_DISCOVERY_10x30.npy"
LOCK = OUT / "E4A_PREUNSEAL_LOCK.json"
V_PATH = OUT / "E4A_V_OPEN_300x2.npy"
OPEN_SHA = "1dfccccbd6a780e134ce387048730c12ed8f46818820079e5689ea9b1b5bbd42"
E1_PROBE_SHA = "364c7a2f0333c95845cfb7a10dbb96ee8c5f30a47282e508e3961d4eec575812"
E1_SOURCE_SHA = "e38bee4467fb9d98ab5ee48a6115eb1b3306df63cd3da409b9412b3032c4b06e"
THRESHOLDS = {"G1_mean_capture_min": 0.70, "G2_each_capture_min": 0.55,
              "G3_each_top2_energy_min": 0.80}


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


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def center(a: np.ndarray) -> np.ndarray:
    return a - a.mean(axis=0, keepdims=True)


def top2_energy(c: np.ndarray) -> float:
    sv = np.linalg.svd(c, compute_uv=False)
    denominator = float(np.sum(sv ** 2))
    return float(np.sum(sv[:2] ** 2) / denominator) if denominator > 0 else 0.0


def open_inputs() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    need(OPEN, OPEN_SHA)
    need(E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv", E1_PROBE_SHA)
    need(E1 / "E1_HOUSE_SOURCE_PANELS.tsv", E1_SOURCE_SHA)
    a = np.load(OPEN, allow_pickle=False)
    if a.shape != (3, 6, 4, 10, 30) or not np.isfinite(a).all() or (a < 0).any():
        raise RuntimeError("OPEN array contract drift")
    # Environment rows 1 and 2 are H02 slow winds in frozen E2 order.
    return a, np.log1p(a[1].astype(np.float64)).reshape(6, 4, 300), np.log1p(a[2].astype(np.float64)).reshape(6, 4, 300)


def make_open() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    _, x0, x2 = open_inputs()
    m0, m2 = x0.mean(axis=1), x2.mean(axis=1)
    c02 = center(m2 - m0)
    _, sv, vh = np.linalg.svd(c02, full_matrices=False)
    v = np.ascontiguousarray(vh[:2].T)
    # Fix SVD sign convention so the saved basis bytes are reproducible.
    for j in range(2):
        if v[np.argmax(np.abs(v[:, j])), j] < 0:
            v[:, j] *= -1
    same_w0 = center(x0[:, :2].mean(axis=1) - x0[:, 2:].mean(axis=1))
    same_w2 = center(x2[:, :2].mean(axis=1) - x2[:, 2:].mean(axis=1))
    facts = {
        "open_C02_top2_energy": float(np.sum(sv[:2] ** 2) / np.sum(sv ** 2)),
        "open_C02_norm": float(np.linalg.norm(c02)),
        "same_W0_seed_half_norm": float(np.linalg.norm(same_w0)),
        "same_W2_seed_half_norm": float(np.linalg.norm(same_w2)),
    }
    return v, m0, m2, facts


def prepare() -> None:
    if LOCK.exists() or V_PATH.exists():
        raise RuntimeError("pre-unseal lock already exists; refusing overwrite")
    v, _, _, facts = make_open()
    if v.shape != (300, 2) or not np.allclose(v.T @ v, np.eye(2), atol=1e-10):
        raise RuntimeError("OPEN basis invalid")
    OUT.mkdir(parents=True, exist_ok=True)
    with V_PATH.open("wb") as f:
        np.save(f, v, allow_pickle=False)
    lock = {
        "status": "OPEN_SUBSPACE_FROZEN_BEFORE_H02_DEV_UNSEAL",
        "open_array_sha256": OPEN_SHA,
        "e1_probe_sha256": E1_PROBE_SHA,
        "e1_source_sha256": E1_SOURCE_SHA,
        "e3_audit_sha256": sha(ROOT / "research/environment_level_benchmark_v0/E3_OPEN_STRUCTURAL_AUDIT_20260925.md"),
        "e4a_charter_sha256": sha(ROOT / "research/environment_level_benchmark_v0/E4A_H02_DEV_DEFORMATION_SUBSPACE_GATE_20260925.md"),
        "scorer_sha256": sha(SCRIPT),
        "numpy_version": np.__version__,
        "v_open_sha256": sha(V_PATH),
        "thresholds": THRESHOLDS,
        "effect_size_hold_rule": "HOLD if both target norms are below max(same_W0,same_W2) seed-half norm",
        **facts,
    }
    write_json(LOCK, lock)
    print("E4A_OPEN_LOCK_FROZEN", "V_OPEN_SHA256=" + lock["v_open_sha256"],
          "OPEN_TOP2=" + str(facts["open_C02_top2_energy"]), flush=True)


def target_rows() -> list[dict[str, str]]:
    path = E2 / "E2_SEALED_DEV_HASH_MANIFEST.tsv"
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["environment_index"] == "4"]
    rows.sort(key=lambda r: (int(r["source_index"]), int(r["replicate_index"])))
    if len(rows) != 24 or {(int(r["source_index"]), int(r["replicate_index"])) for r in rows} != {(s, rep) for s in range(6) for rep in range(4)}:
        raise RuntimeError("H02 DEV target count/identity drift")
    for r in rows:
        if (r["role"], r["house"], r["wind"]) != ("SEALED_DEV_HOLDOUT", "House02", "3,5-1_fast"):
            raise RuntimeError("forbidden sealed environment in E4A target manifest")
        if int(r["requested_seed"]) != 2026110000 + 4000 + 10 * int(r["source_index"]) + int(r["replicate_index"]):
            raise RuntimeError("H02 DEV seed drift")
    return rows


def unseal_target(rows: list[dict[str, str]]) -> np.ndarray:
    with (E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv").open(newline="", encoding="utf-8") as f:
        probes = [r for r in csv.DictReader(f, delimiter="\t") if r["house"] == "House02"]
    probes.sort(key=lambda r: int(r["probe_rank"]))
    if len(probes) != 30:
        raise RuntimeError("H02 probe count drift")
    target = np.empty((6, 4, 10, 30), dtype=np.float32)
    for r in rows:
        cube_path = Path(r["cube_path"])
        need(cube_path, r["cube_sha256"])
        cube = np.load(cube_path, allow_pickle=False)
        if cube.shape != (10, 83, 119) or not np.isfinite(cube).all() or (cube < 0).any():
            raise RuntimeError(f"H02 DEV cube QC drift: {cube_path}")
        parts = []
        for p in probes:
            x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
            y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
            if (x1 - x0, y1 - y0) != (2, 2):
                raise RuntimeError("H02 probe pooling block drift")
            parts.append(cube[:, x0:x1, y0:y1].mean(axis=(1, 2)))
        target[int(r["source_index"]), int(r["replicate_index"])] = np.stack(parts, axis=1).astype(np.float32)
    return target


def score() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock["status"] != "OPEN_SUBSPACE_FROZEN_BEFORE_H02_DEV_UNSEAL":
        raise RuntimeError("OPEN lock status drift")
    need(SCRIPT, lock["scorer_sha256"])
    need(V_PATH, lock["v_open_sha256"])
    need(ROOT / "research/environment_level_benchmark_v0/E4A_H02_DEV_DEFORMATION_SUBSPACE_GATE_20260925.md", lock["e4a_charter_sha256"])
    if lock["thresholds"] != THRESHOLDS:
        raise RuntimeError("threshold drift")
    v = np.load(V_PATH, allow_pickle=False)
    expected_v, m0, m2, facts = make_open()
    if not np.array_equal(v, expected_v):
        raise RuntimeError("OPEN basis reconstruction drift")
    for key, value in facts.items():
        if lock[key] != value:
            raise RuntimeError(f"OPEN fact drift: {key}")
    # This is the only point at which scientific values from a sealed role are read.
    rows = target_rows()
    target = unseal_target(rows)
    m1 = np.log1p(target.astype(np.float64)).reshape(6, 4, 300).mean(axis=1)
    c01, c21 = center(m1 - m0), center(m1 - m2)
    def capture(c: np.ndarray) -> float:
        denominator = float(np.linalg.norm(c) ** 2)
        return float(np.linalg.norm(c @ v) ** 2 / denominator) if denominator > 0 else 0.0
    cap01, cap21 = capture(c01), capture(c21)
    top01, top21 = top2_energy(c01), top2_energy(c21)
    norm01, norm21 = float(np.linalg.norm(c01)), float(np.linalg.norm(c21))
    noise_max = max(lock["same_W0_seed_half_norm"], lock["same_W2_seed_half_norm"])
    hold = norm01 < noise_max and norm21 < noise_max
    gates = {
        "G1_mean_capture_ge_0p70": (cap01 + cap21) / 2 >= 0.70,
        "G2_each_capture_ge_0p55": cap01 >= 0.55 and cap21 >= 0.55,
        "G3_each_top2_energy_ge_0p80": top01 >= 0.80 and top21 >= 0.80,
        "effect_size_valid": not hold,
    }
    if hold:
        decision = "E4A_HOLD_TARGET_WIND_SHIFT_TOO_SMALL_FOR_SUBSPACE_TEST"
    elif all(gates.values()):
        decision = "E4A_PASS_REUSABLE_ENVIRONMENT_DEFORMATION_SUBSPACE_H02"
    else:
        decision = "E4A_FAIL_STOP_DEFORMATION_SUBSPACE_MAINLINE"
    with (OUT / "E4A_H02_W1_6x4x10x30.npy").open("wb") as f:
        np.save(f, target, allow_pickle=False)
    with (OUT / "E4A_H02_W1_TARGET_CUBE_HASHES.tsv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_index", "source_id", "replicate_index", "requested_seed", "cube_sha256", "cube_path"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    result = {
        "decision": decision,
        "frozen_open_lock_sha256": sha(LOCK),
        "v_open_sha256": sha(V_PATH),
        "open_array_sha256": OPEN_SHA,
        "target_vector_sha256": sha(OUT / "E4A_H02_W1_6x4x10x30.npy"),
        "target_cube_count": 24,
        "capture_C01": cap01,
        "capture_C21": cap21,
        "mean_capture": (cap01 + cap21) / 2,
        "top2_energy_C01": top01,
        "top2_energy_C21": top21,
        "norm_C01": norm01,
        "norm_C21": norm21,
        "same_W0_seed_half_norm": lock["same_W0_seed_half_norm"],
        "same_W2_seed_half_norm": lock["same_W2_seed_half_norm"],
        "same_wind_noise_norm_max": noise_max,
        "thresholds": THRESHOLDS,
        "gates": gates,
        "new_plume_runs": 0,
        "other_sealed_environments_opened": False,
    }
    write_json(OUT / "E4A_RESULT.json", result)
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "E4A_SHA256SUMS.txt")
    (OUT / "E4A_SHA256SUMS.txt").write_text(
        "".join(f"{sha(p)}  {p.name}\n" for p in files), encoding="utf-8")
    print(json.dumps({"decision": decision, "capture_C01": cap01, "capture_C21": cap21,
                      "top2_C01": top01, "top2_C21": top21, "norm_C01": norm01,
                      "norm_C21": norm21, "same_wind_noise_norm_max": noise_max,
                      "gates": gates}, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "score"))
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        score()
