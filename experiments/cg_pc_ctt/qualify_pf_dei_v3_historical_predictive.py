#!/usr/bin/env python3
"""Truth-blind future-predictive qualification for frozen PF-DEI-SR V3.

Weights must already be frozen before this program is invoked.  The program
reads only historical pose/time, measured ppm, and measured wind.  It never
reads source truth, localization error, or ON/OFF performance.  Each native
physical trace is passed through the persistent sensor once from run start;
future segments are slices of that stateful result, never sensor-state resets.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from pf_dei_v3_causal_tcn import initialize_frozen_model
from pf_dei_v3_features import build_features, load_carriers, read_schedule
from pf_dei_v3_schema import FEATURE_NAMES
from pf_dei_v3_sensor_forward import forward_sensor_batch
from pf_dei_v3_stream_format import read_multistream, read_wind_multistream


HOUSES = ("H01", "H02", "H03")
MODEL_SEEDS = (1701, 1702, 1703)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runtime_dir(root: Path, house: str, seed: int) -> Path:
    long_house = f"House{house[-2:]}"
    path = (
        root / long_house / f"seed{seed}" / "off" / "runtime"
        / f"{long_house}_seed{seed}_off_off"
    )
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def read_measured_only(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read exactly time and measured ppm; ignore all other serialized fields."""
    times: list[float] = []
    measured: list[float] = []
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.reader(source)
        header = next(reader)
        index = {name: offset for offset, name in enumerate(header)}
        for required in ("t_sim_s", "measured_gas_ppm"):
            if required not in index:
                raise ValueError(f"PF_DEI_V3_HISTORICAL_MISSING_FIELD:{required}:{path}")
        for row in reader:
            times.append(float(row[index["t_sim_s"]]))
            measured.append(float(row[index["measured_gas_ppm"]]))
    t = np.asarray(times, dtype=np.float64)
    y = np.asarray(measured, dtype=np.float64)
    if t.size < 20 or t.shape != y.shape or np.any(np.diff(t) <= 0.0):
        raise ValueError(f"PF_DEI_V3_HISTORICAL_BAD_MEASURED_TRACE:{path}")
    if not np.isfinite(y).all() or (y < 0.0).any():
        raise ValueError(f"PF_DEI_V3_HISTORICAL_NONPHYSICAL_MEASURED_TRACE:{path}")
    return t, y


def forward_boundaries(length: int) -> np.ndarray:
    """Five disjoint chronological segments yield four prefix/future tests."""
    if length < 20:
        raise ValueError("PF_DEI_V3_HISTORICAL_TRACE_TOO_SHORT")
    boundaries = np.rint(np.linspace(0, length, 6)).astype(np.int64)
    boundaries[0], boundaries[-1] = 0, length
    if np.any(np.diff(boundaries) <= 0):
        raise ValueError("PF_DEI_V3_HISTORICAL_DEGENERATE_BOUNDARIES")
    return boundaries


def normalized_posterior(prior: np.ndarray, logits: np.ndarray) -> np.ndarray:
    q0 = np.asarray(prior, dtype=np.float64)
    f = np.asarray(logits, dtype=np.float64)
    if q0.ndim != 1 or f.shape != q0.shape or np.any(q0 <= 0.0):
        raise ValueError("PF_DEI_V3_HISTORICAL_BAD_POSTERIOR_INPUT")
    log_weight = np.log(q0) + f
    log_weight -= float(np.max(log_weight))
    weight = np.exp(log_weight)
    return weight / float(weight.sum())


def weighted_energy_score(
    observed: np.ndarray,
    ensemble: np.ndarray,
    weights: np.ndarray,
    device: torch.device,
) -> float:
    """Exact finite-mixture multivariate energy score (lower is better)."""
    y = np.asarray(observed, dtype=np.float32)
    x = np.asarray(ensemble, dtype=np.float32)
    w = np.asarray(weights, dtype=np.float64)
    if y.ndim != 1 or x.ndim != 2 or x.shape[1] != y.size or x.shape[0] != w.size:
        raise ValueError("PF_DEI_V3_HISTORICAL_ENERGY_SHAPE_FAIL")
    if not np.isfinite(x).all() or not np.isfinite(y).all() or np.any(w < 0.0) or w.sum() <= 0.0:
        raise ValueError("PF_DEI_V3_HISTORICAL_ENERGY_VALUE_FAIL")
    w = w / w.sum()
    # RMS-L2 is Euclidean distance divided by sqrt(T).  torch.cdist computes
    # the exact finite empirical mixture terms without assuming independent
    # time samples.
    xt = torch.from_numpy(x).to(device)
    yt = torch.from_numpy(y[None, :]).to(device)
    wt = torch.from_numpy(w).to(device=device, dtype=torch.float64)
    scale = float(np.sqrt(y.size))
    first = torch.cdist(xt, yt).squeeze(1).to(torch.float64) / scale
    pairwise = torch.cdist(xt, xt).to(torch.float64) / scale
    score = torch.dot(wt, first) - 0.5 * torch.dot(wt, pairwise @ wt)
    return float(score.cpu())


def load_models(weights_root: Path, house: str, device: torch.device):
    models = []
    hashes = {}
    for seed in MODEL_SEEDS:
        path = weights_root / f"{house}_seed{seed}.pt"
        model = initialize_frozen_model(seed)
        model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
        models.append(model.to(device).eval())
        hashes[str(seed)] = sha256_file(path)
    return models, hashes


def score_prefix(models, schedule, measured, wind, carriers, end: int, device: torch.device) -> np.ndarray:
    truncated = {key: values[:end] for key, values in schedule.items()}
    totals = np.zeros(len(carriers), dtype=np.float64)
    for start in range(0, len(carriers), 64):
        batch_carriers = carriers[start : start + 64]
        features = np.stack([
            build_features(truncated, measured[:end], wind[:end], carrier)
            for carrier in batch_carriers
        ])
        mask = np.ones(features.shape[:2], dtype=np.bool_)
        x = torch.from_numpy(features).to(device)
        m = torch.from_numpy(mask).to(device)
        with torch.no_grad():
            logits = torch.stack([model(x, m) for model in models]).mean(dim=0)
        totals[start : start + len(batch_carriers)] = logits.detach().cpu().numpy()
    return totals


def load_historical_predictive_ensemble(
    bank_root: Path,
    house: str,
    carriers,
    seed: int,
    expected_length: int,
) -> np.ndarray:
    """Return [carrier,reserved_member,time] with persistent sensor state."""
    physical = np.empty((len(carriers), 4, expected_length), dtype=np.float32)
    for source_index, carrier in enumerate(carriers):
        for member in range(4):
            shard = bank_root / house / "reserved" / f"member_{member:02d}" / f"{carrier.carrier_id}.bin"
            streams = read_multistream(shard)
            if len(streams) != 15 or streams[seed].size != expected_length:
                raise ValueError(f"PF_DEI_V3_HISTORICAL_RESERVED_SHARD_FAIL:{shard}:{seed}")
            physical[source_index, member] = streams[seed]
    flat = physical.reshape(len(carriers) * 4, expected_length)
    measured = forward_sensor_batch(flat).astype(np.float32)
    return measured.reshape(len(carriers), 4, expected_length)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--wind-root", type=Path, required=True)
    parser.add_argument("--weights-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("PF_DEI_V3_HISTORICAL_PREDICTIVE_CUDA_REQUIRED")
    forbidden = ("truth", "source_z", "latent", "error", "future")
    if any(token in name for name in FEATURE_NAMES for token in forbidden):
        raise SystemExit("PF_DEI_V3_HISTORICAL_PREDICTIVE_FEATURE_LEAKAGE")

    device = torch.device("cuda")
    carriers_by_house = load_carriers(args.support)
    winds_by_house = {
        house: read_wind_multistream(args.wind_root / f"{house}_wind35.bin")[:10]
        for house in HOUSES
    }
    rows: list[dict[str, object]] = []
    run_rows: list[dict[str, object]] = []
    weight_hashes: dict[str, dict[str, str]] = {}
    measured_hashes: dict[str, str] = {}

    for house in HOUSES:
        carriers = carriers_by_house[house]
        prior = np.asarray([carrier.prior_mass for carrier in carriers], dtype=np.float64)
        models, weight_hashes[house] = load_models(args.weights_root, house, device)
        for seed in range(10):
            runtime = runtime_dir(args.archive_root, house, seed)
            schedule_path = runtime / "sim_pose_trace.csv"
            measured_path = runtime / "sensor_trace.csv"
            schedule = read_schedule(schedule_path)
            measured_time, observed = read_measured_only(measured_path)
            if schedule["time"].shape != measured_time.shape or not np.allclose(
                schedule["time"], measured_time, rtol=0.0, atol=1e-9
            ):
                raise ValueError(f"PF_DEI_V3_HISTORICAL_TIME_PARITY_FAIL:{house}:{seed}")
            wind = winds_by_house[house][seed]
            if wind.shape != (observed.size, 3):
                raise ValueError(f"PF_DEI_V3_HISTORICAL_WIND_LENGTH_FAIL:{house}:{seed}")
            predictive = load_historical_predictive_ensemble(
                args.bank_root, house, carriers, seed, observed.size,
            )
            measured_hashes[f"{house}_seed{seed}"] = sha256_file(measured_path)
            boundaries = forward_boundaries(observed.size)
            positive = 0
            gains = []
            for split in range(1, 5):
                prefix_end = int(boundaries[split])
                future_end = int(boundaries[split + 1])
                logits = score_prefix(models, schedule, observed, wind, carriers, prefix_end, device)
                posterior = normalized_posterior(prior, logits)
                future = predictive[:, :, prefix_end:future_end].reshape(
                    len(carriers) * 4, future_end - prefix_end,
                )
                posterior_weights = np.repeat(posterior / 4.0, 4)
                prior_weights = np.repeat(prior / 4.0, 4)
                posterior_score = weighted_energy_score(
                    observed[prefix_end:future_end], future, posterior_weights, device,
                )
                prior_score = weighted_energy_score(
                    observed[prefix_end:future_end], future, prior_weights, device,
                )
                gain = prior_score - posterior_score
                gains.append(gain)
                positive += int(gain > 0.0)
                rows.append({
                    "house": house, "seed": seed, "split": split,
                    "prefix_end": prefix_end, "future_end": future_end,
                    "posterior_energy_score": f"{posterior_score:.17g}",
                    "prior_energy_score": f"{prior_score:.17g}",
                    "future_predictive_gain": f"{gain:.17g}",
                    "posterior_beats_prior": int(gain > 0.0),
                    "truth_fields_used": "false",
                })
            mean_gain = float(np.mean(gains))
            passed = mean_gain > 0.0 and positive >= 3
            run_rows.append({
                "house": house, "seed": seed, "mean_future_predictive_gain": mean_gain,
                "positive_segments": positive, "segments": 4, "run_pass": int(passed),
            })
            print(
                f"PF_DEI_V3_HISTORICAL_RUN house={house} seed={seed} "
                f"pass={int(passed)} mean_gain={mean_gain:.9g} positive={positive}/4",
                flush=True,
            )

    args.output_root.mkdir(parents=True, exist_ok=True)
    split_csv = args.output_root / "historical_future_predictive_splits.csv"
    with split_csv.open("w", newline="", encoding="utf-8") as sink:
        writer = csv.DictWriter(sink, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    run_csv = args.output_root / "historical_future_predictive_runs.csv"
    with run_csv.open("w", newline="", encoding="utf-8") as sink:
        writer = csv.DictWriter(sink, fieldnames=list(run_rows[0]))
        writer.writeheader(); writer.writerows(run_rows)

    house_pass = {
        house: sum(int(row["run_pass"]) for row in run_rows if row["house"] == house)
        for house in HOUSES
    }
    total_pass = sum(int(row["run_pass"]) for row in run_rows)
    passed = total_pass >= 20 and all(value >= 5 for value in house_pass.values())
    summary = {
        "contract": "PF_DEI_V3_HISTORICAL_FUTURE_PREDICTIVE_V1",
        "verdict": (
            "PF_DEI_V3_HISTORICAL_PREDICTIVE_PASS"
            if passed else "PF_DEI_HISTORICAL_PREDICTIVE_NO_GO"
        ),
        "run_count": len(run_rows), "pass_count": total_pass,
        "house_pass_count": house_pass, "required_total_pass": 20,
        "required_per_house_pass": 5, "future_segments_per_run": 4,
        "weights_sha256": weight_hashes,
        "measured_trace_sha256": measured_hashes,
        "split_csv_sha256": sha256_file(split_csv),
        "run_csv_sha256": sha256_file(run_csv),
        "truth_fields_used": False,
    }
    summary_path = args.output_root / "historical_future_predictive_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["verdict"] + " " + json.dumps(summary, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
