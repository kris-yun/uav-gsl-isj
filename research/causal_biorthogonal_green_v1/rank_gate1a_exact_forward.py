#!/usr/bin/env python3
"""Rank the frozen Gate-1A arbitrary-source bank against S2-W2 A/B targets."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_target(root: Path, cell: str) -> Path:
    choices = [
        root / cell / "spatial" / "concentration.npy",
        root / cell / "concentration.npy",
        root / "realizations" / cell / "concentration.npy",
    ]
    for p in choices:
        if p.is_file():
            return p
    raise FileNotFoundError(f"target concentration not found for {cell}: {choices}")


def load_bank(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not rows:
        raise ValueError("empty source bank")
    return rows


def pooled_probe_vector(a: np.ndarray, points: list[dict]) -> np.ndarray:
    vals = []
    for p in points:
        x0, x1 = int(p["native_x0"]), int(p["native_x1_exclusive"])
        y0, y1 = int(p["native_y0"]), int(p["native_y1_exclusive"])
        vals.append(a[:, x0:x1, y0:y1].mean(axis=(1, 2)))
    return np.stack(vals, axis=1).astype(np.float64).reshape(-1)


def target_vector(path: Path, contract: dict) -> np.ndarray:
    a = np.load(path, allow_pickle=False)
    if a.shape != (10, 83, 119):
        raise ValueError(f"{path}: target shape drift {a.shape}")
    if contract.get("probe_operator", {}).get("type") != "avg_pool_2x2_then_sample":
        raise ValueError("probe operator contract drift")
    v = pooled_probe_vector(a, contract["probe_points"])
    if v.size != 300 or not np.isfinite(v).all():
        raise ValueError(f"{path}: invalid target vector")
    return v


def normalized_sse(pred: np.ndarray, target: np.ndarray) -> float:
    den = float(np.dot(target, target)) + 1e-12
    d = pred - target
    return float(np.dot(d, d) / den)


def log1p_normalized_sse(pred: np.ndarray, target: np.ndarray) -> float:
    p = np.log1p(np.clip(pred, 0.0, None))
    y = np.log1p(np.clip(target, 0.0, None))
    return normalized_sse(p, y)


def rank_of(scores: dict[str, float], source_id: str) -> int:
    ordered = sorted(scores.items(), key=lambda kv: (kv[1], kv[0]))
    return 1 + next(i for i, (sid, _) in enumerate(ordered) if sid == source_id)


def top_rows(scores: dict[str, float], bank_by_id: dict[str, dict], n: int = 10):
    out = []
    for rank, (sid, score) in enumerate(
        sorted(scores.items(), key=lambda kv: (kv[1], kv[0]))[:n], start=1
    ):
        r = bank_by_id[sid]
        out.append({
            "rank": rank,
            "source_id": sid,
            "score": float(score),
            "pmfs_i": int(r["pmfs_i"]),
            "pmfs_j": int(r["pmfs_j"]),
            "x_m": float(r["x_m"]),
            "y_m": float(r["y_m"]),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--target-root", type=Path, required=True)
    ap.add_argument("--prediction-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    bank_path = args.contract.parent / "source_bank.tsv"
    bank = load_bank(bank_path)
    bank_by_id = {r["source_id"]: r for r in bank}
    if len(bank_by_id) != len(bank):
        raise ValueError("duplicate source_id in source bank")

    truth_id = str(contract["truth_source_id"])
    if truth_id not in bank_by_id:
        raise ValueError("truth source missing from bank")

    seeds = [int(x) for x in contract["prediction_seeds"]]
    if seeds != [2026092401, 2026092402]:
        raise ValueError(f"prediction seed drift: {seeds}")

    predictions: dict[int, dict[str, np.ndarray]] = {}
    for seed in seeds:
        predictions[seed] = {}
        root = args.prediction_root / f"seed_{seed}"
        for r in bank:
            sid = r["source_id"]
            p = root / f"{sid}.npy"
            if not p.is_file():
                raise FileNotFoundError(p)
            v = np.load(p, allow_pickle=False).astype(np.float64).reshape(-1)
            if v.size != 300 or not np.isfinite(v).all():
                raise ValueError(f"{p}: expected 300 finite values, got {v.shape}")
            predictions[seed][sid] = v

    target_cells = list(contract["target_cells"])
    result = {
        "mode": "BIGREEN_GATE1A_EXACT_FORWARD_ORACLE",
        "contract_sha256": sha256(args.contract),
        "source_bank_sha256": sha256(bank_path),
        "source_count": len(bank),
        "truth_source_id": truth_id,
        "prediction_seeds": seeds,
        "probe_operator": contract["probe_operator"],
        "targets": {},
    }

    all_gate = len(bank) >= int(contract["gate"]["min_free_sources"])
    mean_rank_max = int(contract["gate"]["mean_prediction_truth_rank_max"])
    seed_rank_max = int(contract["gate"]["per_seed_truth_rank_max"])

    for cell in target_cells:
        target_path = find_target(args.target_root, cell)
        y = target_vector(target_path, contract)
        raw_scores: dict[str, float] = {}
        log_scores: dict[str, float] = {}
        seed_scores: dict[int, dict[str, float]] = {s: {} for s in seeds}

        for r in bank:
            sid = r["source_id"]
            stack = np.stack([predictions[s][sid] for s in seeds], axis=0)
            mean_pred = stack.mean(axis=0)
            raw_scores[sid] = normalized_sse(mean_pred, y)
            log_scores[sid] = log1p_normalized_sse(mean_pred, y)
            for s in seeds:
                seed_scores[s][sid] = normalized_sse(predictions[s][sid], y)

        mean_rank = rank_of(raw_scores, truth_id)
        log_rank = rank_of(log_scores, truth_id)
        per_seed_ranks = {str(s): rank_of(seed_scores[s], truth_id) for s in seeds}
        cell_pass = (
            mean_rank <= mean_rank_max
            and all(r <= seed_rank_max for r in per_seed_ranks.values())
        )
        all_gate = all_gate and cell_pass

        result["targets"][cell] = {
            "target_path": str(target_path),
            "target_sha256": sha256(target_path),
            "target_energy": float(np.dot(y, y)),
            "target_nonzero_count": int(np.count_nonzero(y > 0)),
            "truth_primary_score": float(raw_scores[truth_id]),
            "truth_primary_rank": int(mean_rank),
            "truth_log1p_rank_secondary": int(log_rank),
            "truth_per_prediction_seed_rank": per_seed_ranks,
            "gate_pass": bool(cell_pass),
            "top10_primary": top_rows(raw_scores, bank_by_id, 10),
        }

        score_path = args.out.parent / f"{cell}_all_source_scores.csv"
        with score_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "source_id", "pmfs_i", "pmfs_j", "x_m", "y_m",
                "primary_raw_nss", "secondary_log1p_nss",
                *[f"raw_nss_seed_{s}" for s in seeds],
            ])
            for sid, score in sorted(raw_scores.items(), key=lambda kv: (kv[1], kv[0])):
                r = bank_by_id[sid]
                w.writerow([
                    sid, r["pmfs_i"], r["pmfs_j"], r["x_m"], r["y_m"],
                    f"{score:.17g}", f"{log_scores[sid]:.17g}",
                    *[f"{seed_scores[s][sid]:.17g}" for s in seeds],
                ])

    result["decision"] = (
        "GATE1A_PASS_EXACT_PHYSICS_SOURCE_IDENTIFIABLE"
        if all_gate
        else "GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY"
    )
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "source_count": result["source_count"],
        "truth_source_id": truth_id,
        "ranks": {
            c: {
                "mean": result["targets"][c]["truth_primary_rank"],
                "per_seed": result["targets"][c]["truth_per_prediction_seed_rank"],
            }
            for c in target_cells
        },
        "out": str(args.out),
    }, indent=2))
    return 0 if all_gate else 10


if __name__ == "__main__":
    raise SystemExit(main())
