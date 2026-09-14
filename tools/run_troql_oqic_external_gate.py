#!/usr/bin/env python3
"""Run the frozen two-stage TROQL/OQIC external real-data gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "experiments/troql_oqic_external_v1/POLICY_FREEZE.json"
DEVELOPMENT_PATH = ROOT / "experiments/troql_oqic_external_v1/DEVELOPMENT_GATE.json"
CONFIRMATION_PATH = ROOT / "experiments/troql_oqic_external_v1/CONFIRMATION_GATE.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalized(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 0.0:
        raise ValueError("TROQL_ZERO_OR_NONFINITE_NORM")
    return vector / norm


def midranks(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        stop = start + 1
        while stop < values.size and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def load_features(csv_path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    with csv_path.open("r", encoding="mac_roman") as handle:
        header = handle.readline().strip().split(",")
    concentration_indices = [i for i, name in enumerate(header) if name.startswith("C_")]
    if len(concentration_indices) != 27:
        raise ValueError(f"TROQL_EXPECTED_27_CONCENTRATION_COLUMNS:{csv_path}")
    data = np.loadtxt(csv_path, delimiter=",", skiprows=1, dtype=float)
    if data.ndim != 2 or data.shape[1] != len(header) or not np.isfinite(data).all():
        raise ValueError(f"TROQL_INVALID_RAW_MATRIX:{csv_path}")
    trim = float(policy["representation"]["trim_fraction_each_end"])
    blocks = int(policy["representation"]["contiguous_blocks"])
    start = int(math.floor(trim * data.shape[0]))
    stop = int(math.ceil((1.0 - trim) * data.shape[0]))
    indices = np.arange(start, stop, dtype=int)
    split = np.array_split(indices, blocks)
    if len(split) != blocks or any(part.size == 0 for part in split):
        raise ValueError(f"TROQL_EMPTY_BLOCK:{csv_path}")
    concentration = data[:, concentration_indices]
    features = []
    spans = []
    for part in split:
        summary = np.median(concentration[part, :], axis=0)
        rank_vector = midranks(summary)
        features.append(normalized(rank_vector - np.mean(rank_vector)))
        spans.append(
            {
                "row_start_zero_based": int(part[0]),
                "row_stop_exclusive": int(part[-1] + 1),
                "time_start_s": float(data[part[0], 0]),
                "time_stop_s": float(data[part[-1], 0]),
            }
        )
    return {
        "features": np.asarray(features),
        "rows": int(data.shape[0]),
        "columns": int(data.shape[1]),
        "block_spans": spans,
    }


def prototype(features: np.ndarray) -> np.ndarray:
    return normalized(np.median(features[0::2, :], axis=0))


def directional_margins(
    own_features: np.ndarray, own_prototype: np.ndarray, other_prototype: np.ndarray
) -> np.ndarray:
    targets = own_features[1::2, :]
    own_distance = 1.0 - targets @ own_prototype
    other_distance = 1.0 - targets @ other_prototype
    return other_distance - own_distance


def pair_margins(features_a: np.ndarray, features_b: np.ndarray) -> dict[str, np.ndarray]:
    proto_a = prototype(features_a)
    proto_b = prototype(features_b)
    return {
        "a_to_b": directional_margins(features_a, proto_a, proto_b),
        "b_to_a": directional_margins(features_b, proto_b, proto_a),
    }


def conformal_threshold(null_margins: dict[str, np.ndarray], alpha: float) -> dict[str, Any]:
    scores = np.sort(
        np.abs(np.concatenate([null_margins["a_to_b"], null_margins["b_to_a"]]))
    )
    rank_one_based = min(scores.size, int(math.ceil((scores.size + 1) * (1.0 - alpha))))
    return {
        "value": float(scores[rank_one_based - 1]),
        "rank_one_based": rank_one_based,
        "calibration_scores": int(scores.size),
        "alpha": alpha,
    }


def summarize_pair(
    pair: tuple[str, str], margins: dict[str, np.ndarray], threshold: float, required: int
) -> dict[str, Any]:
    directions: dict[str, Any] = {}
    for name, values in margins.items():
        directions[name] = {
            "count_above_threshold": int(np.sum(values > threshold)),
            "target_blocks": int(values.size),
            "median_margin": float(np.median(values)),
            "minimum_margin": float(np.min(values)),
            "maximum_margin": float(np.max(values)),
            "margins": [float(value) for value in values],
        }
    resolved = all(
        item["count_above_threshold"] >= required for item in directions.values()
    )
    return {
        "pair": list(pair),
        "threshold": threshold,
        "required_count_per_direction": required,
        "directions": directions,
        "resolved": resolved,
    }


def verify_policy(policy: dict[str, Any], stage: str) -> dict[str, Any]:
    dataset = policy["external_dataset"]
    data_root = ROOT / dataset["local_root"]
    commit = (
        __import__("subprocess")
        .check_output(["git", "-C", str(data_root), "rev-parse", "HEAD"], text=True)
        .strip()
    )
    if commit != dataset["upstream_commit"]:
        raise ValueError("TROQL_UPSTREAM_COMMIT_MISMATCH")
    opened = set(policy["stages"][stage]["open_only"])
    verified: dict[str, str] = {}
    for relative, expected in policy["raw_inputs"].items():
        experiment = Path(relative).stem
        if relative.startswith("logs/") and experiment not in opened:
            continue
        actual = sha256(data_root / relative)
        if actual != expected:
            raise ValueError(f"TROQL_RAW_HASH_MISMATCH:{relative}")
        verified[relative] = actual
    return {"upstream_commit": commit, "verified_raw_inputs": verified}


def load_stage_features(policy: dict[str, Any], stage: str) -> dict[str, dict[str, Any]]:
    data_root = ROOT / policy["external_dataset"]["local_root"] / "logs"
    return {
        experiment: load_features(data_root / f"{experiment}.csv", policy)
        for experiment in policy["stages"][stage]["open_only"]
    }


def run_development(policy: dict[str, Any]) -> dict[str, Any]:
    provenance = verify_policy(policy, "development")
    loaded = load_stage_features(policy, "development")
    null_pair = tuple(policy["stages"]["development"]["null_pair"])
    source_pair = tuple(policy["stages"]["development"]["source_pair"])
    null_margins = pair_margins(
        loaded[null_pair[0]]["features"], loaded[null_pair[1]]["features"]
    )
    calibration = conformal_threshold(null_margins, float(policy["calibration"]["alpha"]))
    required = int(policy["calibration"]["required_target_blocks_above_threshold_per_direction"])
    null_summary = summarize_pair(null_pair, null_margins, calibration["value"], required)
    source_summary = summarize_pair(
        source_pair,
        pair_margins(
            loaded[source_pair[0]]["features"], loaded[source_pair[1]]["features"]
        ),
        calibration["value"],
        required,
    )
    passed = source_summary["resolved"] and not null_summary["resolved"]
    return {
        "schema": "TROQL_OQIC_EXTERNAL_DEVELOPMENT_GATE_V1",
        "stage": "development",
        "policy_sha256": sha256(POLICY_PATH),
        "scorer_sha256": sha256(Path(__file__).resolve()),
        "provenance": provenance,
        "calibration": calibration,
        "null_edge": null_summary,
        "source_edge": source_summary,
        "input_shapes": {
            name: {key: value for key, value in item.items() if key != "features"}
            for name, item in loaded.items()
        },
        "gate_pass": passed,
        "verdict": (
            "TROQL_OQIC_EXTERNAL_DEVELOPMENT_PASS_TO_CONFIRMATION"
            if passed
            else "TROQL_OQIC_EXTERNAL_DEVELOPMENT_NO_GO"
        ),
        "confirmation_opened": False,
    }


def run_confirmation(policy: dict[str, Any]) -> dict[str, Any]:
    if not DEVELOPMENT_PATH.exists():
        raise ValueError("TROQL_DEVELOPMENT_GATE_MISSING")
    development = json.loads(DEVELOPMENT_PATH.read_text(encoding="utf-8"))
    if not development.get("gate_pass"):
        raise ValueError("TROQL_DEVELOPMENT_NO_GO_CONFIRMATION_FORBIDDEN")
    if development["policy_sha256"] != sha256(POLICY_PATH):
        raise ValueError("TROQL_POLICY_CHANGED_AFTER_DEVELOPMENT")
    if development["scorer_sha256"] != sha256(Path(__file__).resolve()):
        raise ValueError("TROQL_SCORER_CHANGED_AFTER_DEVELOPMENT")
    provenance = verify_policy(policy, "confirmation")
    loaded = load_stage_features(policy, "confirmation")
    null_pair = tuple(policy["stages"]["confirmation"]["null_pair"])
    source_pair = tuple(policy["stages"]["confirmation"]["source_pair"])
    threshold = float(development["calibration"]["value"])
    required = int(policy["calibration"]["required_target_blocks_above_threshold_per_direction"])
    null_summary = summarize_pair(
        null_pair,
        pair_margins(
            loaded[null_pair[0]]["features"], loaded[null_pair[1]]["features"]
        ),
        threshold,
        required,
    )
    source_summary = summarize_pair(
        source_pair,
        pair_margins(
            loaded[source_pair[0]]["features"], loaded[source_pair[1]]["features"]
        ),
        threshold,
        required,
    )
    passed = source_summary["resolved"] and not null_summary["resolved"]
    return {
        "schema": "TROQL_OQIC_EXTERNAL_CONFIRMATION_GATE_V1",
        "stage": "untouched_confirmation",
        "policy_sha256": sha256(POLICY_PATH),
        "scorer_sha256": sha256(Path(__file__).resolve()),
        "development_gate_sha256": sha256(DEVELOPMENT_PATH),
        "provenance": provenance,
        "frozen_threshold_from_development": threshold,
        "null_edge": null_summary,
        "source_edge": source_summary,
        "input_shapes": {
            name: {key: value for key, value in item.items() if key != "features"}
            for name, item in loaded.items()
        },
        "gate_pass": passed,
        "verdict": (
            "TROQL_OQIC_MAIN_INNOVATION_PREMISE_PASS"
            if passed
            else "TROQL_OQIC_EXTERNAL_CONFIRMATION_NO_GO"
        ),
        "claim_boundary": {
            "bounded_cross_dataset_identifiability_mechanism": (
                "AUTHORIZED" if passed else "NOT_AUTHORIZED"
            ),
            "closed_loop_localization_improvement": "NOT_AUTHORIZED",
            "online_pmfs_deployment": "NOT_AUTHORIZED",
        },
    }


def selftest() -> None:
    rng = np.random.default_rng(20260914)
    base_a = normalized(np.linspace(-1.0, 1.0, 27))
    base_b = normalized(np.r_[np.linspace(1.0, -0.2, 13), np.linspace(-0.1, 0.9, 14)])
    null_a = np.asarray([normalized(base_a + 0.01 * rng.normal(size=27)) for _ in range(40)])
    null_b = np.asarray([normalized(base_a + 0.01 * rng.normal(size=27)) for _ in range(40)])
    different_a = np.asarray([normalized(base_a + 0.01 * rng.normal(size=27)) for _ in range(40)])
    different_b = np.asarray([normalized(base_b + 0.01 * rng.normal(size=27)) for _ in range(40)])
    threshold = conformal_threshold(pair_margins(null_a, null_b), 0.05)["value"]
    summary = summarize_pair(
        ("synthetic_a", "synthetic_b"),
        pair_margins(different_a, different_b),
        threshold,
        18,
    )
    if not summary["resolved"]:
        raise AssertionError("TROQL_SYNTHETIC_RESOLUTION_SELFTEST_FAILED")
    print("TROQL_OQIC_SELFTEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["development", "confirmation"])
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.stage:
        parser.error("--stage is required unless --selftest is used")
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    payload = run_development(policy) if args.stage == "development" else run_confirmation(policy)
    output = args.out or (DEVELOPMENT_PATH if args.stage == "development" else CONFIRMATION_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "gate_pass": payload["gate_pass"]}))


if __name__ == "__main__":
    main()
