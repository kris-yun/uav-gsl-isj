#!/usr/bin/env python3
"""Build the frozen privileged-label dataset from committed C2 traces only."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np


SOURCES = ("S_truth", "S_k01", "S_k10", "S_k22")
WINDS = ("W_fast", "W_slow")
ROUTES = tuple(f"AO_{index:02d}" for index in range(12))
WINDOW = 26
START_INDEX = WINDOW - 1
HIT_FLOOR = 0.1
CENTER = np.eye(4) - np.ones((4, 4)) / 4.0


def read_gzip_csv(path: Path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_route(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint-trace-dir", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    feature_rows, target_rows, metadata = [], [], []
    feature_slices = {"gas_plus": [0, WINDOW], "gas_minus": [WINDOW, 2 * WINDOW]}
    feature_slices["wind"] = [2 * WINDOW, 5 * WINDOW]
    feature_slices["position"] = [5 * WINDOW, 8 * WINDOW]
    feature_slices["velocity"] = [8 * WINDOW, 11 * WINDOW]

    for route_id in ROUTES:
        route = read_route(args.candidate_root / route_id / "CENTER.csv")
        if len(route) != 750:
            raise RuntimeError(f"route cardinality {route_id}: {len(route)}")
        position = np.asarray([[float(row[key]) for key in ("x", "y", "z")] for row in route], dtype=np.float64)
        velocity = np.asarray([[float(row[key]) for key in ("vx", "vy", "vz")] for row in route], dtype=np.float64)
        for wind in WINDS:
            traces = {}
            for source in SOURCES:
                rows = read_gzip_csv(args.endpoint_trace_dir / f"{route_id}__{source}__{wind}.csv.gz")
                if len(rows) != 750 or any((row["route_id"], row["source_id"], row["wind_id"]) != (route_id, source, wind) for row in rows):
                    raise RuntimeError(f"trace identity/cardinality failure {route_id} {source} {wind}")
                traces[source] = {
                    "plus": np.asarray([float(row["processed_c_plus_ppm"]) for row in rows], dtype=np.float64),
                    "minus": np.asarray([float(row["processed_c_minus_ppm"]) for row in rows], dtype=np.float64),
                    "wind": np.asarray([[float(row[key]) for key in ("wind_plus_u", "wind_plus_v", "wind_plus_w")] for row in rows], dtype=np.float64),
                    "wind_minus": np.asarray([[float(row[key]) for key in ("wind_minus_u", "wind_minus_v", "wind_minus_w")] for row in rows], dtype=np.float64),
                }
            for end in range(START_INDEX, 750):
                first = end - WINDOW + 1
                vectors = []
                for source in SOURCES:
                    plus = traces[source]["plus"][first:end + 1]
                    minus = traces[source]["minus"][first:end + 1]
                    vectors.append(np.concatenate((plus, minus)))
                y_matrix = np.stack(vectors)
                residual = CENTER @ y_matrix
                singular = np.linalg.svd(residual, compute_uv=False)
                sigma_ratio = float(singular[2] / singular[0]) if singular[0] > 0 else 0.0
                moment = residual @ residual.T
                eigenvalues = np.sort(np.linalg.eigvalsh(0.5 * (moment + moment.T)))[::-1]
                q_energy = float(eigenvalues[2] / eigenvalues[0]) if eigenvalues[0] > 0 else 0.0
                q_energy = max(0.0, q_energy)
                pair_distances = [float(np.linalg.norm(y_matrix[i] - y_matrix[j])) for i in range(4) for j in range(i + 1, 4)]
                min_distance = min(pair_distances)
                support = min(int(np.any(vector > HIT_FLOOR)) for vector in vectors)
                target = np.asarray([sigma_ratio, q_energy, math.log1p(min_distance), float(support)], dtype=np.float64)
                for source in SOURCES:
                    trace = traces[source]
                    mean_wind = 0.5 * (trace["wind"] + trace["wind_minus"])
                    features = np.concatenate((
                        trace["plus"][first:end + 1],
                        trace["minus"][first:end + 1],
                        mean_wind[first:end + 1].reshape(-1),
                        position[first:end + 1].reshape(-1),
                        velocity[first:end + 1].reshape(-1),
                    ))
                    feature_rows.append(features)
                    target_rows.append(target)
                    metadata.append((route_id, wind, source, end))

    x = np.asarray(feature_rows, dtype=np.float64)
    y = np.asarray(target_rows, dtype=np.float64)
    meta = np.asarray(metadata, dtype="U16")
    np.savez_compressed(args.out_dir / "dataset.npz", X=x, y=y, metadata=meta)
    result = {
        "schema": "OBSERVABILITY_LEARNING_PRIVILEGED_DATASET_V1",
        "source_trace_mode": "COMMITTED_C2_ORDERED_PLUS_MINUS_PROCESSED",
        "example_count": int(x.shape[0]),
        "feature_count": int(x.shape[1]),
        "target_count": int(y.shape[1]),
        "window_samples": WINDOW,
        "window_seconds": 5.0,
        "start_index": START_INDEX,
        "routes": list(ROUTES),
        "winds": list(WINDS),
        "sources": list(SOURCES),
        "feature_slices": feature_slices,
        "student_input_excludes": ["source_id", "route_id", "source_coordinate", "future_sample", "privileged_label"],
        "target_names": ["sigma3_sigma1", "q_energy", "log1p_min_pair_distance", "min_source_hit_support"],
        "train_split": {"wind": "W_fast", "routes": list(ROUTES[:8])},
        "development_split": {"wind": "W_fast", "routes": list(ROUTES[8:])},
        "held_split": {"wind": "W_slow", "routes": list(ROUTES[8:])},
        "target_mean": y.mean(axis=0).tolist(),
        "target_std": y.std(axis=0).tolist(),
        "status": "PASS",
    }
    (args.out_dir / "DATASET_INTEGRITY.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    distribution = {
        "schema": "OBSERVABILITY_LEARNING_LABEL_DISTRIBUTION_V1",
        "target_names": result["target_names"],
        "mean": y.mean(axis=0).tolist(),
        "std": y.std(axis=0).tolist(),
        "minimum": y.min(axis=0).tolist(),
        "maximum": y.max(axis=0).tolist(),
        "nonzero_counts": np.count_nonzero(y, axis=0).tolist(),
        "support_one_count": int(np.count_nonzero(y[:, 3])),
        "status": "PASS" if np.all(y[:, :3].std(axis=0) > 0.0) else "FAIL_LABEL_RICHNESS",
    }
    (args.out_dir / "LABEL_DISTRIBUTION.json").write_text(json.dumps(distribution, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"examples": int(x.shape[0]), "features": int(x.shape[1]), "target_std": distribution["std"], "status": distribution["status"]}))


if __name__ == "__main__":
    main()
