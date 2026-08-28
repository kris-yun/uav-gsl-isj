#!/usr/bin/env python3
"""Close PF-DEI synthetic physical/sensor/block parity without development truth."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path("/home/zyc/PF_DEI_FORWARD_CLOSURE_20260828")
REPO_CANDIDATES = [
    Path("/home/zyc/uav-gsl-isj"),
    Path("/home/zyc/pf-dei-forward-closure-work"),
    Path("/home/zyc/uav-gsl-isj-v6-audit-20260828"),
]
REPO = next(
    (candidate for candidate in REPO_CANDIDATES
     if (candidate / "experiments/cg_pc_ctt/pf_dei_observation_contract.py").exists()),
    REPO_CANDIDATES[0],
)
VGR = Path("/home/zyc/ros2_ws/src/vgr_bridge")
sys.path.insert(0, str(REPO / "experiments/cg_pc_ctt"))
sys.path.insert(0, str(VGR))

from pf_dei_observation_contract import validate_forward_payload  # noqa: E402
from vgr_bridge.sensor_model import SensorModel  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    shared = read_rows(ROOT / "shared_query.csv")
    player = read_rows(ROOT / "ros_player_query.csv")
    if len(shared) != 50 or len(player) != 50:
        raise RuntimeError("PF_DEI_SYNTHETIC_SAMPLE_COUNT_MISMATCH")

    integer_fields = ["sample_id", "iteration"]
    numeric_fields = [
        "sample_time_s", "x", "y", "z", "concentration_ppm",
        "wind_u", "wind_v", "wind_w",
    ]
    for field in integer_fields:
        if [int(r[field]) for r in shared] != [int(r[field]) for r in player]:
            raise RuntimeError(f"PF_DEI_SYNTHETIC_ID_MISMATCH={field}")
    max_abs: dict[str, float] = {}
    for field in numeric_fields:
        left = np.asarray([float(r[field]) for r in shared], dtype=np.float64)
        right = np.asarray([float(r[field]) for r in player], dtype=np.float64)
        max_abs[field] = float(np.max(np.abs(left - right)))
        if not np.array_equal(left, right):
            raise RuntimeError(f"PF_DEI_SYNTHETIC_NATIVE_QUERY_PARITY_FAIL={field}:{max_abs[field]}")

    sample_time = np.asarray([float(r["sample_time_s"]) for r in shared], dtype=np.float64)
    physical_shared = np.asarray([float(r["concentration_ppm"]) for r in shared], dtype=np.float64)
    physical_player = np.asarray([float(r["concentration_ppm"]) for r in player], dtype=np.float64)

    sensor_kwargs = {
        "gain": 1.0,
        "baseline": 0.0,
        "tau_rise_s": 1.2,
        "tau_recovery_s": 1.2,
        "dead_time_s": 0.4,
        "noise_std_ppm": 0.0,
        "drift_rate_ppm_s": 0.0,
        "saturation_min_ppm": 0.0,
        "saturation_max_ppm": 1.0e6,
        "initial_state_ppm": 0.0,
        "initial_input_ppm": 0.0,
    }
    seed = 20260828
    sensor_shared = SensorModel(mode="dynamic", seed=seed, **sensor_kwargs)
    sensor_player = SensorModel(mode="dynamic", seed=seed, **sensor_kwargs)
    measured_shared = np.asarray(
        [sensor_shared.process(value, 0.2) for value in physical_shared], dtype=np.float64
    )
    measured_player = np.asarray(
        [sensor_player.process(value, 0.2) for value in physical_player], dtype=np.float64
    )
    if not np.array_equal(measured_shared, measured_player):
        raise RuntimeError("PF_DEI_SYNTHETIC_SENSOR_PARITY_FAIL")

    threshold = 0.1
    block_means_shared = measured_shared.reshape(5, 10).mean(axis=1, dtype=np.float64)
    block_means_player = measured_player.reshape(5, 10).mean(axis=1, dtype=np.float64)
    block_hits_shared = block_means_shared > threshold
    block_hits_player = block_means_player > threshold
    if not np.array_equal(block_means_shared, block_means_player):
        raise RuntimeError("PF_DEI_SYNTHETIC_BLOCK_MEAN_PARITY_FAIL")
    if not np.array_equal(block_hits_shared, block_hits_player):
        raise RuntimeError("PF_DEI_SYNTHETIC_BLOCK_HIT_PARITY_FAIL")

    reset_at_block_2 = SensorModel(mode="dynamic", seed=seed, **sensor_kwargs)
    reset_value = reset_at_block_2.process(float(physical_shared[10]), 0.2)
    persistence_delta = float(abs(measured_shared[10] - reset_value))
    if persistence_delta <= 0.0:
        raise RuntimeError("PF_DEI_SYNTHETIC_PERSISTENT_STATE_NOT_EXERCISED")

    sensor_model_path = VGR / "vgr_bridge/sensor_model.py"
    vgr_node_path = VGR / "vgr_bridge/vgr_sim_node.py"
    sensor_model_hash = sha256_file(sensor_model_path)
    sensor_manifest = sensor_shared.manifest()
    parameter_blob = json.dumps(sensor_manifest, sort_keys=True, separators=(",", ":")).encode()
    sensor_parameter_hash = hashlib.sha256(parameter_blob).hexdigest()

    payload = {
        "sample_time": sample_time,
        "physical_concentration_ppm": physical_shared[None, None, :],
        "simulated_measured_ppm": measured_shared[None, None, :],
        "source_xy": np.asarray([[-2.0, 0.07]], dtype=np.float64),
        "transport_keys": ["synthetic_house02_native_gaden_default_mt19937_5489"],
        "sensor_model_hash": sensor_model_hash,
        "sensor_parameter_hash": sensor_parameter_hash,
        "concentration_origin": "native_gaden_physical_concentration",
        "sensor_state_scope": "run_persistent",
        "context_state_reset": False,
        "source_truth_used": False,
    }
    if validate_forward_payload(payload) is not True:
        raise RuntimeError("PF_DEI_MINIMAL_FORWARD_PAYLOAD_CONTRACT_FAIL")
    np.savez_compressed(
        ROOT / "minimal_forward_payload.npz",
        sample_time=payload["sample_time"],
        physical_concentration_ppm=payload["physical_concentration_ppm"],
        simulated_measured_ppm=payload["simulated_measured_ppm"],
        source_xy=payload["source_xy"],
        transport_keys=np.asarray(payload["transport_keys"]),
        sensor_model_hash=np.asarray(sensor_model_hash),
        sensor_parameter_hash=np.asarray(sensor_parameter_hash),
        concentration_origin=np.asarray(payload["concentration_origin"]),
        sensor_state_scope=np.asarray(payload["sensor_state_scope"]),
        context_state_reset=np.asarray(False),
        source_truth_used=np.asarray(False),
    )

    with (ROOT / "synthetic_parity_samples.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "sample_id", "sample_time_s", "iteration", "x", "y", "z",
            "shared_concentration_ppm", "player_concentration_ppm",
            "shared_measured_ppm", "player_measured_ppm", "block_id",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in enumerate(shared):
            writer.writerow(
                {
                    "sample_id": index,
                    "sample_time_s": sample_time[index],
                    "iteration": int(row["iteration"]),
                    "x": row["x"], "y": row["y"], "z": row["z"],
                    "shared_concentration_ppm": physical_shared[index],
                    "player_concentration_ppm": physical_player[index],
                    "shared_measured_ppm": measured_shared[index],
                    "player_measured_ppm": measured_player[index],
                    "block_id": index // 10,
                }
            )

    provenance = {
        "sensor_model_source": str(sensor_model_path),
        "sensor_model_sha256": sensor_model_hash,
        "vgr_node_source": str(vgr_node_path),
        "vgr_node_sha256": sha256_file(vgr_node_path),
        "sensor_parameter_sha256": sensor_parameter_hash,
        "sensor_manifest": sensor_manifest,
        "sampling_cadence_s": 0.2,
        "sensor_state_scope": "run_persistent",
        "context_state_reset": False,
        "launch_override_observed": "sensor_model_mode=dynamic; remaining sensor fields use VGR declared defaults",
    }
    (ROOT / "sensor_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "verdict": "PF_DEI_SYNTHETIC_END_TO_END_PARITY_PASS",
        "samples": 50,
        "blocks": 5,
        "native_query_max_abs": max_abs,
        "measured_ppm_max_abs": float(np.max(np.abs(measured_shared - measured_player))),
        "block_mean_max_abs": float(np.max(np.abs(block_means_shared - block_means_player))),
        "block_hits": [bool(value) for value in block_hits_shared],
        "block_means_ppm": [float(value) for value in block_means_shared],
        "threshold_ppm": threshold,
        "persistence_delta_at_second_block_first_sample_ppm": persistence_delta,
        "minimal_forward_payload_contract": "PASS",
        "raw_samples_treated_as_independent": False,
    }
    (ROOT / "synthetic_parity_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PF_DEI_SYNTHETIC_END_TO_END_PARITY_PASS")
    print("PF_DEI_MINIMAL_FORWARD_PAYLOAD_CONTRACT=PASS")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
