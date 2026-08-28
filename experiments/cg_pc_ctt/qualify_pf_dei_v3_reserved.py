#!/usr/bin/env python3
"""Frozen reserved-synthetic qualification for PF-DEI-SR V3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

from pf_dei_v3_causal_tcn import initialize_frozen_model
from pf_dei_v3_features import build_features, load_carriers, read_schedule
from pf_dei_v3_schema import FEATURE_NAMES
from pf_dei_v3_sensor_forward import forward_sensor
from pf_dei_v3_stream_format import read_multistream, read_wind_multistream


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_digest(text: str) -> bytes:
    return hashlib.sha256(text.encode()).digest()


def select_coverage_carriers(carriers, count: int = 32) -> list[int]:
    if len(carriers) < count:
        raise ValueError("PF_DEI_V3_RESERVED_TOO_FEW_CARRIERS")
    x = np.asarray([item.centroid_x for item in carriers], dtype=np.float64)
    y = np.asarray([item.centroid_y for item in carriers], dtype=np.float64)
    scale_x = max(float(np.ptp(x)), 1e-12)
    scale_y = max(float(np.ptp(y)), 1e-12)
    xy = np.column_stack(((x - x.min()) / scale_x, (y - y.min()) / scale_y))
    tie = [stable_digest(f"PFDEI-V3-RESERVED|{item.house}|{item.carrier_id}") for item in carriers]
    selected = [min(range(len(carriers)), key=lambda index: tie[index])]
    remaining = set(range(len(carriers))) - set(selected)
    while len(selected) < count:
        def key(index: int):
            distance = min(float(np.sum((xy[index] - xy[prior]) ** 2)) for prior in selected)
            return (-distance, tie[index])
        chosen = min(remaining, key=key)
        selected.append(chosen)
        remaining.remove(chosen)
    return selected


def reserved_trajectory_index(carrier_id: str, member: int) -> int:
    value = int.from_bytes(stable_digest(f"PFDEI-V3-TRAJECTORY|{carrier_id}|{member}")[:8], "big")
    return value % 5


def midrank_descending(values: np.ndarray, true_index: int) -> float:
    truth = values[true_index]
    greater = int(np.count_nonzero(values > truth))
    equal_other = int(np.count_nonzero(values == truth)) - 1
    return 1.0 + greater + 0.5 * equal_other


def score_candidates(models, schedule, measured, wind, carriers, device, order=None) -> np.ndarray:
    order = list(range(len(carriers))) if order is None else list(order)
    per_model = [[] for _ in models]
    for start in range(0, len(order), 64):
        indices = order[start : start + 64]
        features = np.stack([build_features(schedule, measured, wind, carriers[index]) for index in indices])
        mask = np.ones(features.shape[:2], dtype=np.bool_)
        x = torch.from_numpy(features).to(device)
        m = torch.from_numpy(mask).to(device)
        with torch.no_grad():
            for target, model in zip(per_model, models, strict=True):
                target.extend(model(x, m).detach().cpu().numpy().tolist())
    output = np.empty((len(models), len(carriers)), dtype=np.float64)
    for model_index, scores in enumerate(per_model):
        output[model_index, order] = scores
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--maponly-root", type=Path, required=True)
    parser.add_argument("--wind-root", type=Path, required=True)
    parser.add_argument("--weights-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("PF_DEI_V3_QUALIFICATION_CUDA_REQUIRED")
    if any(token in name for name in FEATURE_NAMES for token in ("truth", "source_z", "latent", "error", "future")):
        raise SystemExit("PF_DEI_V3_QUALIFICATION_FEATURE_LEAKAGE")
    house = args.house
    device = torch.device("cuda")
    carriers = load_carriers(args.support)[house]
    selected = select_coverage_carriers(carriers)
    prior = np.asarray([item.prior_mass for item in carriers], dtype=np.float64)
    models = []
    weight_hashes = {}
    for seed in (1701, 1702, 1703):
        path = args.weights_root / f"{house}_seed{seed}.pt"
        model = initialize_frozen_model(seed)
        model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
        models.append(model.to(device).eval())
        weight_hashes[str(seed)] = sha256_file(path)
    winds = read_wind_multistream(args.wind_root / f"{house}_wind35.bin")
    schedules = [read_schedule(args.maponly_root / house / "reserved" / f"trajectory_seed_{seed}.csv") for seed in range(4001, 4006)]
    rows = []
    permutation_checked = False
    for true_index in selected:
        carrier = carriers[true_index]
        for member in range(4):
            trajectory = reserved_trajectory_index(carrier.carrier_id, member)
            shard = args.bank_root / house / "reserved" / f"member_{member:02d}" / f"{carrier.carrier_id}.bin"
            physical = read_multistream(shard)[10 + trajectory]
            measured = forward_sensor(physical).astype(np.float32)
            wind = winds[30 + trajectory]
            schedule = schedules[trajectory]
            scores = score_candidates(models, schedule, measured, wind, carriers, device)
            if not permutation_checked:
                reversed_scores = score_candidates(models, schedule, measured, wind, carriers, device, reversed(range(len(carriers))))
                if not np.allclose(scores, reversed_scores, rtol=1e-6, atol=1e-7):
                    raise SystemExit("PF_DEI_V3_RESERVED_CANDIDATE_PERMUTATION_FAIL")
                permutation_checked = True
            ensemble = scores.mean(axis=0)
            log_weight = np.log(prior) + ensemble
            log_weight -= float(log_weight.max())
            posterior = np.exp(log_weight)
            posterior /= posterior.sum()
            rank = midrank_descending(posterior, true_index)
            q0_rank = midrank_descending(prior, true_index)
            model_ranks = []
            for model_scores in scores:
                model_log_weight = np.log(prior) + model_scores
                model_log_weight -= float(model_log_weight.max())
                model_ranks.append(midrank_descending(np.exp(model_log_weight), true_index))
            rows.append({
                "house": house, "true_carrier_index": true_index,
                "true_carrier_id": carrier.carrier_id, "reserved_member": member,
                "reserved_trajectory_seed": 4001 + trajectory,
                "rank": rank, "normalized_rank": (rank - 1.0) / (len(carriers) - 1),
                "top5": int(rank <= 5.0),
                "log_posterior_prior_gain": math.log(posterior[true_index] / prior[true_index]),
                "q0_normalized_rank": (q0_rank - 1.0) / (len(carriers) - 1),
                **{f"model_{seed}_normalized_rank": (model_ranks[index] - 1.0) / (len(carriers) - 1)
                   for index, seed in enumerate((1701, 1702, 1703))},
            })
    top5 = float(np.mean([row["top5"] for row in rows]))
    median_rank = float(np.median([row["normalized_rank"] for row in rows]))
    mean_gain = float(np.mean([row["log_posterior_prior_gain"] for row in rows]))
    q0_mean = float(np.mean([row["q0_normalized_rank"] for row in rows]))
    individual = {
        str(seed): float(np.mean([row[f"model_{seed}_normalized_rank"] for row in rows]))
        for seed in (1701, 1702, 1703)
    }
    passed = top5 >= 0.75 and median_rank <= 0.10 and mean_gain > 0 and all(value < q0_mean for value in individual.values())
    args.output_root.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_root / f"{house}_reserved_cases.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as sink:
        writer = csv.DictWriter(sink, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "verdict": "PF_DEI_V3_RESERVED_SYNTHETIC_PASS" if passed else "PF_DEI_INFERENCE_ENGINE_NO_GO",
        "house": house, "case_count": len(rows), "top5_recall": top5,
        "median_normalized_rank": median_rank,
        "mean_log_posterior_prior_gain": mean_gain,
        "q0_mean_normalized_rank": q0_mean,
        "individual_model_mean_normalized_rank": individual,
        "candidate_permutation": "PASS", "forbidden_field_leakage": False,
        "selected_carrier_ids": [carriers[index].carrier_id for index in selected],
        "weights_sha256": weight_hashes, "cases_sha256": sha256_file(csv_path),
    }
    summary_path = args.output_root / f"{house}_reserved_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["verdict"] + " " + json.dumps(summary, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
