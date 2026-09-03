#!/usr/bin/env python3
"""One-shot fresh-confirm evaluator for frozen CTPI M2 TSDC V0.

No fitting or outcome-dependent tuning is implemented here. The evaluator loads
only the frozen TSDC runtime and compares it against the preregistered raw finite-
8 transport probability on exactly 30 fresh controlled-source worlds.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import binomtest

EPS = 1e-15
EXPECTED_MODULE_SHA256 = "854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7"
EXPECTED_SELECTION_SHA256 = "0d4e6162863ca2a07bf93ef74f178b1d4ad5d058ab787345d291362fd8e9f431"
WORLD_MANIFEST_CONTRACT = "CTPI_M2_TSDC_FRESH_WORLD_MANIFEST_V0"
MATERIALIZER_CONTRACT = "CTPI_M2_TSDC_ONE_WORLD_MATERIALIZER_V0"
PREGEN_CONTRACT = "CTPI_M2_TSDC_PREGEN_AUDIT_V0"
CONTRACT = "CTPI_M2_TSDC_FRESH_CONFIRM_GATE_V0"
HOUSES = ("H01", "H02", "H03")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_frozen(path: Path):
    if sha256_file(path) != EXPECTED_MODULE_SHA256:
        raise RuntimeError("TSDC_FRESH_FROZEN_MODULE_SHA")
    spec = importlib.util.spec_from_file_location("ctpi_m2_tsdc_frozen_confirm", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("TSDC_FRESH_MODULE_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "fit_dev_mle"):
        raise RuntimeError("TSDC_FRESH_FIT_OPERATOR_PRESENT")
    return module


def nll(y: np.ndarray, p: np.ndarray) -> float:
    yy = np.asarray(y, dtype=np.float64)
    pp = np.clip(np.asarray(p, dtype=np.float64), EPS, 1.0 - EPS)
    return float(np.mean(-(yy * np.log(pp) + (1.0 - yy) * np.log1p(-pp))))


def brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((np.asarray(y, dtype=np.float64) - np.asarray(p, dtype=np.float64)) ** 2))


def ece(y: np.ndarray, p: np.ndarray, bins: int = 5) -> float:
    yy = np.asarray(y, dtype=np.float64)
    pp = np.asarray(p, dtype=np.float64)
    edges = np.linspace(0.0, 1.0, bins + 1)
    value = 0.0
    for index in range(bins):
        mask = (pp >= edges[index]) & ((pp < edges[index + 1]) if index < bins - 1 else (pp <= edges[index + 1]))
        if np.any(mask):
            value += float(np.mean(mask)) * abs(float(np.mean(pp[mask]) - np.mean(yy[mask])))
    return value


def exact_sign(rows: list[dict[str, Any]], raw_key: str, tsdc_key: str) -> dict[str, Any]:
    wins = sum(float(row[tsdc_key]) < float(row[raw_key]) - 1e-15 for row in rows)
    losses = sum(float(row[tsdc_key]) > float(row[raw_key]) + 1e-15 for row in rows)
    ties = len(rows) - wins - losses
    p = float(binomtest(wins, wins + losses, 0.5, alternative="greater").pvalue) if wins + losses else 1.0
    return {"wins": int(wins), "losses": int(losses), "ties": int(ties), "p_one_sided": p}


def read_events(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 15:
        raise RuntimeError(f"TSDC_FRESH_EVENT_COUNT:{path}:{len(rows)}")
    return rows


def write_records(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--world-root", type=Path, required=True)
    p.add_argument("--world-manifest", type=Path, required=True)
    p.add_argument("--selection", type=Path, required=True)
    p.add_argument("--stage1-root", type=Path, required=True)
    p.add_argument("--frozen-module", type=Path, required=True)
    p.add_argument("--pregen-authorization", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    if sha256_file(args.selection) != EXPECTED_SELECTION_SHA256:
        raise RuntimeError("TSDC_FRESH_SELECTION_SHA")
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    manifest = json.loads(args.world_manifest.read_text(encoding="utf-8"))
    auth = json.loads(args.pregen_authorization.read_text(encoding="utf-8"))
    if manifest.get("contract") != WORLD_MANIFEST_CONTRACT or not manifest.get("pass"):
        raise RuntimeError("TSDC_FRESH_WORLD_MANIFEST")
    if auth.get("contract") != PREGEN_CONTRACT or auth.get("CTPI_M2_TSDC_PREGEN") != "PASS" or not auth.get("pass"):
        raise RuntimeError("TSDC_FRESH_PREGEN")
    if manifest.get("selection_sha256") != EXPECTED_SELECTION_SHA256:
        raise RuntimeError("TSDC_FRESH_MANIFEST_SELECTION_SHA")
    module = load_frozen(args.frozen_module)

    stage: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for house in HOUSES:
        path = args.stage1_root / f"{house}_FACTORIAL.npz"
        if sha256_file(path) != selection["houses"][house]["input_npz_sha256"]:
            raise RuntimeError(f"TSDC_FRESH_STAGE1_SHA:{house}")
        with np.load(path, allow_pickle=False) as z:
            stage[house] = (np.asarray(z["carrier_ids"]).astype(str), np.asarray(z["q_raw"], dtype=np.float64))

    records: list[dict[str, Any]] = []
    world_metrics: list[dict[str, Any]] = []
    for world in manifest["formal_worlds"]:
        world_id = str(world["world_id"])
        house = str(world["house"])
        root = args.world_root / world_id
        audit = json.loads((root / "WORLD_AUDIT.json").read_text(encoding="utf-8"))
        if audit.get("contract") != MATERIALIZER_CONTRACT or not audit.get("pass"):
            raise RuntimeError(f"TSDC_FRESH_WORLD_AUDIT:{world_id}")
        if audit.get("world_id") != world_id or audit.get("set") != "TSDC_FRESH_CONFIRM":
            raise RuntimeError(f"TSDC_FRESH_WORLD_IDENTITY:{world_id}")
        event_rows = read_events(root / "stop_events.csv")
        measured = np.load(root / "measured_ppm_1502.npy", allow_pickle=False)
        if measured.shape != (1502,) or not np.isfinite(measured).all():
            raise RuntimeError(f"TSDC_FRESH_MEASURED:{world_id}")

        carrier_ids, q_raw = stage[house]
        idx = np.flatnonzero(carrier_ids == str(world["controlled_carrier_id"]))
        if len(idx) != 1:
            raise RuntimeError(f"TSDC_FRESH_CARRIER:{world_id}:{len(idx)}")
        route = int(world["route_index"])
        raw = np.asarray(q_raw[route, int(idx[0]), :], dtype=np.float64)
        if raw.shape != (15,):
            raise RuntimeError(f"TSDC_FRESH_RAW_SHAPE:{world_id}")
        k_float = raw * 9.0 - 0.5
        k = np.rint(k_float).astype(np.int64)
        if np.max(np.abs(k_float - k)) > 1e-9 or np.any(k < 0) or np.any(k > 8):
            raise RuntimeError(f"TSDC_FRESH_K:{world_id}")

        decision = np.zeros(15, dtype=np.float64)
        for stop in range(1, 15):
            previous_end = int(event_rows[stop - 1]["end_index"])
            decision[stop] = float(measured[previous_end])
        observed = np.asarray([int(row["observed_hit"]) for row in event_rows], dtype=np.int64)
        if not np.all((observed == 0) | (observed == 1)):
            raise RuntimeError(f"TSDC_FRESH_OBSERVED:{world_id}")
        tsdc = np.asarray(module.predict_committor(k, decision), dtype=np.float64)
        if tsdc.shape != (15,) or np.any(tsdc <= 0.0) or np.any(tsdc >= 1.0):
            raise RuntimeError(f"TSDC_FRESH_PREDICTION:{world_id}")

        for stop in range(15):
            records.append({
                "world_id": world_id, "house": house, "stop_id": stop + 1,
                "controlled_carrier_id": world["controlled_carrier_id"], "route_index": route,
                "member_hit_count": int(k[stop]), "raw_probability": repr(float(raw[stop])),
                "decision_sensor_state_ppm": repr(float(decision[stop])),
                "tsdc_probability": repr(float(tsdc[stop])), "observed_event": int(observed[stop]),
            })
        world_metrics.append({
            "world_id": world_id, "house": house,
            "raw_nll": nll(observed, raw), "tsdc_nll": nll(observed, tsdc),
            "raw_brier": brier(observed, raw), "tsdc_brier": brier(observed, tsdc),
        })

    if len(records) != 450 or len(world_metrics) != 30:
        raise RuntimeError("TSDC_FRESH_CARDINALITY")
    y = np.asarray([r["observed_event"] for r in records], dtype=np.int64)
    raw = np.asarray([float(r["raw_probability"]) for r in records], dtype=np.float64)
    tsdc = np.asarray([float(r["tsdc_probability"]) for r in records], dtype=np.float64)
    nll_sign = exact_sign(world_metrics, "raw_nll", "tsdc_nll")
    brier_sign = exact_sign(world_metrics, "raw_brier", "tsdc_brier")

    per_house: dict[str, Any] = {}
    for house in HOUSES:
        rows = [r for r in records if r["house"] == house]
        worlds = [w for w in world_metrics if w["house"] == house]
        hy = np.asarray([r["observed_event"] for r in rows], dtype=np.int64)
        hp0 = np.asarray([float(r["raw_probability"]) for r in rows])
        hp1 = np.asarray([float(r["tsdc_probability"]) for r in rows])
        per_house[house] = {
            "raw_nll": nll(hy, hp0), "tsdc_nll": nll(hy, hp1),
            "raw_brier": brier(hy, hp0), "tsdc_brier": brier(hy, hp1),
            "nll_sign": exact_sign(worlds, "raw_nll", "tsdc_nll"),
            "brier_sign": exact_sign(worlds, "raw_brier", "tsdc_brier"),
        }

    metrics = {
        "raw_nll": nll(y, raw), "tsdc_nll": nll(y, tsdc),
        "raw_brier": brier(y, raw), "tsdc_brier": brier(y, tsdc),
        "raw_ece5": ece(y, raw, 5), "tsdc_ece5": ece(y, tsdc, 5),
        "nll_sign": nll_sign, "brier_sign": brier_sign, "per_house": per_house,
    }
    gate = {
        "pooled_nll_lower": metrics["tsdc_nll"] < metrics["raw_nll"],
        "pooled_brier_lower": metrics["tsdc_brier"] < metrics["raw_brier"],
        "ece5_not_worse": metrics["tsdc_ece5"] <= metrics["raw_ece5"] + 1e-15,
        "paired_world_nll_sign_p": nll_sign["p_one_sided"] <= 0.05,
        "paired_world_brier_sign_p": brier_sign["p_one_sided"] <= 0.05,
        "per_house_nll_wins_min_6": all(per_house[h]["nll_sign"]["wins"] >= 6 for h in HOUSES),
        "no_house_mean_nll_and_brier_both_worse": all(not (
            per_house[h]["tsdc_nll"] > per_house[h]["raw_nll"]
            and per_house[h]["tsdc_brier"] > per_house[h]["raw_brier"]
        ) for h in HOUSES),
        "finite_probabilities": bool(np.isfinite(raw).all() and np.isfinite(tsdc).all()),
        "beta_hash_match": sha256_file(args.frozen_module) == EXPECTED_MODULE_SHA256,
        "no_confirm_refit": not hasattr(module, "fit_dev_mle"),
    }
    passed = all(gate.values())
    report = {
        "contract": CONTRACT, "status": "FRESH_CONFIRM_ONE_SHOT",
        "events": len(records), "worlds": len(world_metrics),
        "world_manifest_sha256": sha256_file(args.world_manifest),
        "selection_sha256": sha256_file(args.selection),
        "frozen_module_sha256": sha256_file(args.frozen_module),
        "pregen_authorization_sha256": sha256_file(args.pregen_authorization),
        "metrics": metrics, "gate": gate, "pass": passed,
        "m3_offline_action_gate_authorized": passed,
        "cpp_ros_closed_loop_authorized": False,
        "verdict": "CTPI_M2_TSDC_FRESH_CONFIRM=PASS" if passed else "CTPI_M2_TSDC_FRESH_CONFIRM=NO_GO",
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_records(args.output_dir / "TSDC_FRESH_CONFIRM_RECORDS.csv", records)
    with (args.output_dir / "TSDC_FRESH_WORLD_METRICS.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(world_metrics[0].keys()))
        writer.writeheader(); writer.writerows(world_metrics)
    (args.output_dir / "TSDC_FRESH_CONFIRM_GATE.json").write_bytes(canonical_bytes(report))
    (args.output_dir / ("PASS" if passed else "NO_GO")).write_text(report["verdict"] + "\n", encoding="ascii")
    print(report["verdict"])
    print(json.dumps(metrics, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
