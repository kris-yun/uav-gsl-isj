#!/usr/bin/env python3
"""Frozen 2x2 factorial E4B gate with explicit pre-run lock."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import numpy as np

import acquire_e4b_w3_vm as acq


ROOT, OUT = acq.ROOT, acq.OUT
E1 = acq.E1
E2 = ROOT / "evidence/environment_level_benchmark_v0/e2"
E4A = ROOT / "evidence/environment_level_benchmark_v0/e4a"
OPEN = E2 / "E2_OPEN_DISCOVERY_10x30.npy"
W1 = E4A / "E4A_H02_W1_6x4x10x30.npy"
LOCK = OUT / "E4B_PRE_RUN_LOCK.json"
V_SPEED = OUT / "E4B_V_SPEED_300x2.npy"
V_FAMILY = OUT / "E4B_V_FAMILY_300x2.npy"
SCRIPT = Path(__file__).resolve()
OPEN_SHA = "1dfccccbd6a780e134ce387048730c12ed8f46818820079e5689ea9b1b5bbd42"
W1_SHA = "ce47f637af9c26ff6ec9b6274b23e2fc7d54b2053646186852bfecec655bfddc"
THRESHOLDS = {
    "G1_speed_capture_min": 0.55,
    "G2_family_capture_min": 0.55,
    "G3_mean_capture_min": 0.70,
    "G4_each_top2_energy_min": 0.80,
    "G5_interaction_noise_multiplier": 2.0,
}


def center(x: np.ndarray) -> np.ndarray:
    return x - x.mean(axis=0, keepdims=True)


def load_discovery() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    acq.need(OPEN, OPEN_SHA)
    acq.need(W1, W1_SHA)
    a = np.load(OPEN, allow_pickle=False)
    b = np.load(W1, allow_pickle=False)
    if a.shape != (3, 6, 4, 10, 30) or b.shape != (6, 4, 10, 30):
        raise RuntimeError("W0/W1/W2 shape drift")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or (a < 0).any() or (b < 0).any():
        raise RuntimeError("W0/W1/W2 QC drift")
    w0 = np.log1p(a[1].astype(np.float64)).reshape(6, 4, 300)
    w1 = np.log1p(b.astype(np.float64)).reshape(6, 4, 300)
    w2 = np.log1p(a[2].astype(np.float64)).reshape(6, 4, 300)
    return w0, w1, w2, b


def basis(c: np.ndarray) -> tuple[np.ndarray, float]:
    _, singular, vh = np.linalg.svd(c, full_matrices=False)
    v = np.ascontiguousarray(vh[:2].T)
    for j in range(2):
        if v[np.argmax(np.abs(v[:, j])), j] < 0:
            v[:, j] *= -1
    energy = float(np.sum(singular[:2] ** 2) / np.sum(singular ** 2))
    return v, energy


def noise_norm(w: np.ndarray) -> float:
    half = center(w[:, :2].mean(axis=1) - w[:, 2:].mean(axis=1))
    return float(np.linalg.norm(half))


def all_wind_hashes() -> dict:
    inventory = json.loads(acq.INVENTORY.read_text(encoding="utf-8"))
    result = {}
    for label, wind in (("W0", "3,5-1_slow"), ("W1", "3,5-1_fast"),
                        ("W2", "4,5-3_slow"), ("W3", "4,5-3_fast")):
        record = inventory["houses"]["House02"]["wind_configs"][wind]
        path = Path(record["path"])
        rows = record["iteration_records"]
        if len(rows) != 11:
            raise RuntimeError(f"wind count drift: {label}")
        for r in rows:
            if (path / r["name"]).stat().st_size != r["size_bytes"]:
                raise RuntimeError(f"wind size drift: {label}/{r['name']}")
            acq.need(path / r["name"], r["sha256"])
        result[label] = {"wind": wind, "path": str(path),
                         "sha256": {r["name"]: r["sha256"] for r in rows}}
    return result


def prepare() -> None:
    if LOCK.exists() or V_SPEED.exists() or V_FAMILY.exists():
        raise RuntimeError("E4B pre-run artifacts already exist; refusing overwrite")
    rows, wind = acq.plan()
    w0, w1, w2, _ = load_discovery()
    m0, m1, m2 = (w.mean(axis=1) for w in (w0, w1, w2))
    cs = center(m1 - m0)
    cf = center(m2 - m0)
    vs, speed_energy = basis(cs)
    vf, family_energy = basis(cf)
    if not np.allclose(vs.T @ vs, np.eye(2), atol=1e-10) or not np.allclose(vf.T @ vf, np.eye(2), atol=1e-10):
        raise RuntimeError("factor basis orthonormality failed")
    winds = all_wind_hashes()
    if winds["W3"]["sha256"] != wind["wind_hashes"]:
        raise RuntimeError("W3 wind plan mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    with V_SPEED.open("wb") as f:
        np.save(f, vs, allow_pickle=False)
    with V_FAMILY.open("wb") as f:
        np.save(f, vf, allow_pickle=False)
    lock = {
        "status": "E4B_PRE_RUN_LOCKED",
        "environment_index": acq.ENV_INDEX,
        "run_count": 24,
        "seed_formula": "2026110000 + 1000*7 + 10*source_index + replicate_index",
        "first_seed": rows[0]["requested_seed"],
        "last_seed": rows[-1]["requested_seed"],
        "source_order": [rows[4 * s]["source_id"] for s in range(6)],
        "source_xyz": [rows[4 * s]["source_xyz"] for s in range(6)],
        "open_array_sha256": OPEN_SHA,
        "w1_array_sha256": W1_SHA,
        "e1_source_sha256": acq.E1_SOURCE_SHA,
        "e1_probe_sha256": acq.E1_PROBE_SHA,
        "occupancy_sha256": acq.OCC_SHA,
        "binary_sha256": acq.BINARY_SHA,
        "extractor_sha256": acq.EXTRACTOR_SHA,
        "wind_inventory_sha256": acq.sha(acq.INVENTORY),
        "wind_file_hashes": winds,
        "w3_wind_hashes": wind["wind_hashes"],
        "scorer_sha256": acq.sha(SCRIPT),
        "acquisition_script_sha256": acq.sha(Path(acq.__file__)),
        "charter_sha256": acq.sha(ROOT / "research/environment_level_benchmark_v0/E4B_H02_FACTORIAL_CORNER_GATE_20260925.md"),
        "thresholds": THRESHOLDS,
        "effect_size_hold_rule": "HOLD if either target factor norm <= Nmax",
        "representation": "300-D log1p(ppm), source-centered mean difference",
        "v_speed_sha256": acq.sha(V_SPEED),
        "v_family_sha256": acq.sha(V_FAMILY),
        "C_speed_A_norm": float(np.linalg.norm(cs)),
        "C_family_slow_norm": float(np.linalg.norm(cf)),
        "C_speed_A_top2_energy": speed_energy,
        "C_family_slow_top2_energy": family_energy,
        "same_W0_seed_half_norm": noise_norm(w0),
        "same_W1_seed_half_norm": noise_norm(w1),
        "same_W2_seed_half_norm": noise_norm(w2),
        "numpy_version": np.__version__,
    }
    acq.json_write(LOCK, lock)
    print("E4B_PRE_RUN_LOCKED", "V_SPEED_SHA256=" + lock["v_speed_sha256"],
          "V_FAMILY_SHA256=" + lock["v_family_sha256"], "seeds=2026117000..2026117053", flush=True)


def target_data(lock: dict) -> tuple[np.ndarray, list[dict]]:
    manifest_path = OUT / "E4B_W3_RUN_MANIFEST.tsv"
    with manifest_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    rows.sort(key=lambda r: (int(r["source_index"]), int(r["replicate_index"])))
    if len(rows) != 24 or {(int(r["source_index"]), int(r["replicate_index"])) for r in rows} != {(s, rep) for s in range(6) for rep in range(4)}:
        raise RuntimeError("W3 run manifest count/identity drift")
    with (E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv").open(newline="", encoding="utf-8") as f:
        probes = [r for r in csv.DictReader(f, delimiter="\t") if r["house"] == "House02"]
    probes.sort(key=lambda r: int(r["probe_rank"]))
    if len(probes) != 30:
        raise RuntimeError("H02 probe count drift")
    target = np.empty((6, 4, 10, 30), dtype=np.float32)
    for row in rows:
        si, rep = int(row["source_index"]), int(row["replicate_index"])
        if row["source_id"] != lock["source_order"][si] or int(row["requested_seed"]) != 2026110000 + 7000 + 10 * si + rep:
            raise RuntimeError("W3 source/seed drift")
        p = Path(row["cube_path"])
        if not str(p).startswith(str(acq.DATA) + os.sep):
            raise RuntimeError("W3 cube outside dedicated acquisition root")
        acq.need(p, row["cube_sha256"])
        acq.cube_qc(p)
        c = np.load(p, allow_pickle=False)
        values = []
        for point in probes:
            x0, x1 = int(point["native_x0"]), int(point["native_x1_exclusive"])
            y0, y1 = int(point["native_y0"]), int(point["native_y1_exclusive"])
            if (x1 - x0, y1 - y0) != (2, 2):
                raise RuntimeError("H02 probe block drift")
            values.append(c[:, x0:x1, y0:y1].mean(axis=(1, 2)))
        target[si, rep] = np.stack(values, axis=1).astype(np.float32)
    return target, rows


def top2(c: np.ndarray) -> float:
    sv = np.linalg.svd(c, compute_uv=False)
    denom = float(np.sum(sv ** 2))
    return float(np.sum(sv[:2] ** 2) / denom) if denom > 0 else 0.0


def capture(c: np.ndarray, v: np.ndarray) -> float:
    denom = float(np.linalg.norm(c) ** 2)
    return float(np.linalg.norm(c @ v) ** 2 / denom) if denom > 0 else 0.0


def score() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock["status"] != "E4B_PRE_RUN_LOCKED" or lock["thresholds"] != THRESHOLDS:
        raise RuntimeError("E4B pre-run lock drift")
    acq.need(SCRIPT, lock["scorer_sha256"])
    acq.need(Path(acq.__file__), lock["acquisition_script_sha256"])
    acq.need(V_SPEED, lock["v_speed_sha256"])
    acq.need(V_FAMILY, lock["v_family_sha256"])
    acq.need(ROOT / "research/environment_level_benchmark_v0/E4B_H02_FACTORIAL_CORNER_GATE_20260925.md", lock["charter_sha256"])
    acq.need(E1 / "E1_HOUSE_PROBE_CONTRACTS.tsv", lock["e1_probe_sha256"])
    acq.need(E1 / "E1_HOUSE_SOURCE_PANELS.tsv", lock["e1_source_sha256"])
    _, wind = acq.plan()
    if wind["wind_hashes"] != lock["w3_wind_hashes"]:
        raise RuntimeError("W3 wind lock drift")
    w0, w1, w2, _ = load_discovery()
    vs, vf = np.load(V_SPEED, allow_pickle=False), np.load(V_FAMILY, allow_pickle=False)
    cs, cf = center(w1.mean(axis=1) - w0.mean(axis=1)), center(w2.mean(axis=1) - w0.mean(axis=1))
    if not np.array_equal(vs, basis(cs)[0]) or not np.array_equal(vf, basis(cf)[0]):
        raise RuntimeError("factor basis reconstruction drift")
    target, rows = target_data(lock)
    w3 = np.log1p(target.astype(np.float64)).reshape(6, 4, 300)
    m0, m1, m2, m3 = (w.mean(axis=1) for w in (w0, w1, w2, w3))
    c_speed_b = center(m3 - m2)
    c_family_fast = center(m3 - m1)
    q = center(m3 - m2 - m1 + m0)
    cap_speed, cap_family = capture(c_speed_b, vs), capture(c_family_fast, vf)
    energy_speed, energy_family = top2(c_speed_b), top2(c_family_fast)
    norm_speed, norm_family, norm_q = map(lambda c: float(np.linalg.norm(c)),
                                          (c_speed_b, c_family_fast, q))
    noise = {label: noise_norm(w) for label, w in (("W0", w0), ("W1", w1), ("W2", w2), ("W3", w3))}
    for label in ("W0", "W1", "W2"):
        if noise[label] != lock[f"same_{label}_seed_half_norm"]:
            raise RuntimeError(f"same-wind frozen noise drift: {label}")
    nmax = max(noise.values())
    gates = {
        "G1_speed_capture_ge_0p55": cap_speed >= 0.55,
        "G2_family_capture_ge_0p55": cap_family >= 0.55,
        "G3_mean_capture_ge_0p70": (cap_speed + cap_family) / 2 >= 0.70,
        "G4_both_top2_energy_ge_0p80": energy_speed >= 0.80 and energy_family >= 0.80,
        "G5_interaction_norm_le_2Nmax": norm_q <= 2 * nmax,
    }
    effect_valid = norm_speed > nmax and norm_family > nmax
    if not effect_valid:
        decision = "E4B_HOLD_TARGET_FACTOR_EFFECT_TOO_SMALL"
    elif all(gates.values()):
        decision = "E4B_PASS_FACTORIZED_ENVIRONMENT_DEFORMATION_H02"
    else:
        decision = "E4B_FAIL_STOP_FACTORIZED_DEFORMATION_MAINLINE"
    with (OUT / "E4B_H02_W3_6x4x10x30.npy").open("wb") as f:
        np.save(f, target, allow_pickle=False)
    result = {
        "decision": decision, "capture_speed": cap_speed, "capture_family": cap_family,
        "mean_capture": (cap_speed + cap_family) / 2,
        "top2_energy_speed_B": energy_speed, "top2_energy_family_fast": energy_family,
        "norm_speed_B": norm_speed, "norm_family_fast": norm_family,
        "same_wind_seed_half_noise_norms": noise, "Nmax": nmax,
        "interaction_Q_norm": norm_q, "interaction_threshold_2Nmax": 2 * nmax,
        "effect_size_valid": effect_valid, "gates": gates, "thresholds": THRESHOLDS,
        "pre_run_lock_sha256": acq.sha(LOCK), "v_speed_sha256": acq.sha(V_SPEED),
        "v_family_sha256": acq.sha(V_FAMILY), "w3_vector_sha256": acq.sha(OUT / "E4B_H02_W3_6x4x10x30.npy"),
        "w3_run_manifest_sha256": acq.sha(OUT / "E4B_W3_RUN_MANIFEST.tsv"),
        "new_plume_runs": len(rows), "other_sealed_environments_opened": False,
    }
    acq.json_write(OUT / "E4B_RESULT.json", result)
    files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "E4B_SHA256SUMS.txt")
    (OUT / "E4B_SHA256SUMS.txt").write_text(
        "".join(f"{acq.sha(p)}  {p.name}\n" for p in files), encoding="utf-8")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("prepare", "score"))
    args = ap.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        score()
