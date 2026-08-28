#!/usr/bin/env python3
"""Materialize the frozen PF-DEI V3 training tensors from native shards."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from pf_dei_v3_features import load_carriers, read_schedule
from pf_dei_v3_sensor_forward import forward_sensor_batch, parameter_sha256
from pf_dei_v3_stream_format import read_multistream, read_wind_multistream


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def historical_paths(root: Path, house: str) -> list[Path]:
    h = f"House{house[-2:]}"
    return [
        root / h / f"seed{seed}" / "off" / "runtime" / f"{h}_seed{seed}_off_off"
        / "sim_pose_trace.csv"
        for seed in range(10)
    ]


def training_paths(historical_root: Path, maponly_root: Path, house: str) -> list[Path]:
    paths = historical_paths(historical_root, house)
    paths.extend(maponly_root / house / "train" / f"trajectory_seed_{seed}.csv" for seed in range(3001, 3021))
    return paths


def split_is_validation(house: str, carrier_id: str, member: int, trajectory: int) -> bool:
    text = f"PFDEI-V3|{house}|{carrier_id}|{member}|{trajectory}".encode()
    return int.from_bytes(hashlib.sha256(text).digest()[:8], "big") % 10 == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--house", choices=("H01", "H02", "H03"), required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--bank-root", type=Path, required=True)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--maponly-root", type=Path, required=True)
    parser.add_argument("--wind-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    house = args.house
    carriers = load_carriers(args.support)[house]
    schedules = [read_schedule(path) for path in training_paths(args.historical_root, args.maponly_root, house)]
    lengths = np.asarray([schedule["x"].size for schedule in schedules], dtype=np.int32)
    if lengths.size != 30:
        raise SystemExit("PF_DEI_V3_TRAINING_TRAJECTORY_COUNT_FAIL")
    max_length = int(lengths.max())
    winds = read_wind_multistream(args.wind_root / f"{house}_wind35.bin")[:30]
    if [item.shape[0] for item in winds] != lengths.tolist():
        raise SystemExit("PF_DEI_V3_TRAINING_WIND_LENGTH_FAIL")

    source_count, members, trajectories = len(carriers), 8, 30
    physical = np.full((source_count, members, trajectories, max_length), np.nan, dtype=np.float32)
    for source_index, carrier in enumerate(carriers):
        for member in range(members):
            shard = args.bank_root / house / "train" / f"member_{member:02d}" / f"{carrier.carrier_id}.bin"
            values = read_multistream(shard)
            if len(values) != trajectories:
                raise ValueError(f"PF_DEI_V3_TRAINING_SHARD_COUNT_FAIL:{shard}")
            for trajectory, ppm in enumerate(values):
                if ppm.size != lengths[trajectory]:
                    raise ValueError(f"PF_DEI_V3_TRAINING_SHARD_LENGTH_FAIL:{shard}:{trajectory}")
                physical[source_index, member, trajectory, : ppm.size] = ppm
        if (source_index + 1) % 25 == 0 or source_index + 1 == source_count:
            print(f"PF_DEI_V3_DATASET_LOAD={source_index + 1}/{source_count}", flush=True)

    args.output_root.mkdir(parents=True, exist_ok=True)
    measured_path = args.output_root / f"{house}_measured_train.npy"
    measured = np.lib.format.open_memmap(
        measured_path, mode="w+", dtype=np.float32,
        shape=(source_count, members, trajectories, max_length),
    )
    measured[:] = np.nan
    for trajectory, length in enumerate(lengths):
        batch = physical[:, :, trajectory, :length].reshape(source_count * members, int(length))
        if not np.isfinite(batch).all():
            raise ValueError("PF_DEI_V3_TRAINING_PHYSICAL_NONFINITE")
        transformed = forward_sensor_batch(batch).astype(np.float32)
        measured[:, :, trajectory, :length] = transformed.reshape(source_count, members, int(length))
    measured.flush()
    del measured, physical

    schedule_path = args.output_root / f"{house}_schedule_train.npz"
    def padded(field: str, width: int = 1) -> np.ndarray:
        shape = (trajectories, max_length) if width == 1 else (trajectories, max_length, width)
        output = np.zeros(shape, dtype=np.float32)
        for index, schedule in enumerate(schedules):
            output[index, : lengths[index]] = schedule[field]
        return output
    wind_padded = np.zeros((trajectories, max_length, 3), dtype=np.float32)
    for index, wind in enumerate(winds):
        wind_padded[index, : lengths[index]] = wind
    np.savez_compressed(
        schedule_path,
        lengths=lengths,
        x=padded("x"), y=padded("y"), dt=padded("dt"),
        stop_start=padded("stop_start"), block_boundary=padded("block_boundary"),
        wind=wind_padded,
    )

    carriers_path = args.output_root / f"{house}_carriers.json"
    carriers_path.write_text(json.dumps([carrier.__dict__ for carrier in carriers], indent=2) + "\n", encoding="utf-8")
    validation = np.zeros((source_count, members, trajectories), dtype=np.bool_)
    for source_index, carrier in enumerate(carriers):
        for member in range(members):
            for trajectory in range(trajectories):
                validation[source_index, member, trajectory] = split_is_validation(
                    house, carrier.carrier_id, member, trajectory,
                )
    split_path = args.output_root / f"{house}_validation_split.npy"
    np.save(split_path, validation)
    summary = {
        "contract": "PF_DEI_V3_TRAINING_DATASET_V1",
        "house": house, "source_count": source_count, "member_count": members,
        "trajectory_count": trajectories, "max_length": max_length,
        "training_trace_count": int((~validation).sum()),
        "validation_trace_count": int(validation.sum()),
        "sensor_parameter_sha256": parameter_sha256(),
        "measured_sha256": sha256_file(measured_path),
        "schedule_sha256": sha256_file(schedule_path),
        "carriers_sha256": sha256_file(carriers_path),
        "split_sha256": sha256_file(split_path),
    }
    summary_path = args.output_root / f"{house}_training_dataset_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PF_DEI_V3_TRAINING_DATASET=PASS house={house} summary_sha256={sha256_file(summary_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
