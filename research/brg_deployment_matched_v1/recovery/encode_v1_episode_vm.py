"""Encode one real VGR event history for source-held-out V1 training.

The same V0 candidate templates and first three observation channels are used.
The added timing channels come from recorded measurement window bounds.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

V0 = Path("/home/zyc/brg_closedloop_20260927/PMFS_BRG_CLOSED_LOOP_STARTER_20260927")
sys.path.insert(0, str(V0))
from pmfs_brg.bank import TemplateBank
from pmfs_brg.features import FeatureConfig, encode
from sample_time_contract import verify_distinct_vgr_samples


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-file", required=True)
    parser.add_argument("--raw-run", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    case = json.loads(Path(args.case_file).read_text())
    if case["split"] not in ("train", "dev"):
        raise RuntimeError("evaluation plume cannot become training/dev episode")
    raw = Path(args.raw_run)
    blocks = rows(raw / "measurement_blocks.csv")
    events = rows(raw / "measurement_events.csv")
    samples = rows(raw / "measurement_samples.csv")
    sensor_trace = rows(raw / "sensor_trace.csv")
    if not blocks or len(blocks) != len(events):
        raise RuntimeError("event/block count mismatch")
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for sample in samples:
        grouped[int(sample["measurement_cycle_id"])].append(sample)
    windows, concentrations, xy, event_ids = [], [], [], []
    clock_collisions = 0
    max_clock_lag = 0.
    last_end = 0.0
    for n, (block, event) in enumerate(zip(blocks, events), 1):
        if int(block["measurement_cycle_id"]) != n or int(event["event_id"]) != n:
            raise RuntimeError("noncontiguous event/cycle identity")
        group = grouped[n]
        sample_times = [float(sample["sim_time"]) for sample in group]
        if len(group) != 10 or [int(sample["sample_index"]) for sample in group] != list(range(10)):
            raise RuntimeError("not exactly ten deployment readings per event")
        start, end = float(block["sim_time_start"]), float(block["sim_time_end"])
        if not (start >= last_end - 1e-6 and end > start and
                start <= sample_times[0] + 1e-6 and sample_times[-1] <= end + 1e-6 and
                end <= 300.0 + 1e-6):
            raise RuntimeError("window bounds do not bracket causal raw readings")
        last_end = end
        concentration = float(block["gas_value_used_by_algorithm"])
        observed = float(event["concentration"])
        mean = sum(float(sample["measured_gas_ppm"]) for sample in group) / 10
        tolerance = 2e-5 + 5e-6 * max(1.0, abs(observed))
        if abs(concentration - observed) > tolerance or abs(concentration - mean) > tolerance:
            raise RuntimeError("deployed gas average/parity mismatch")
        px, py = float(block["pose_x"]), float(block["pose_y"])
        if abs(px - float(event["robot_x"])) > .01 or abs(py - float(event["robot_y"])) > .01:
            raise RuntimeError("deployed pose/event mismatch")
        publication = verify_distinct_vgr_samples(group, sensor_trace, start, end, (px, py))
        clock_collisions += publication['clock_collision_count']
        max_clock_lag = max(max_clock_lag, publication['max_clock_lag_s'])
        windows.append((start, end))
        # The native event audit preserves full precision; the window CSV is
        # rounded for logging.  Train on the exact value sent to the sidecar.
        concentrations.append(observed)
        xy.append((px, py))
        event_ids.append(n)
    bank_path = V0 / f"legal_support_v2/env_{case['environment_index']}_bank.npz"
    bank = TemplateBank.load(bank_path)
    if bank.fingerprint != case["candidate_support_id"] or len(bank.ids) != case["candidate_support_count"]:
        raise RuntimeError("Native legal candidate support mismatch")
    if case["source_id"] not in bank.ids:
        raise RuntimeError("training/development truth outside legal support")
    position = np.asarray(xy, dtype=np.float64)
    p, rawu = bank.project(position, (.2, .2))
    obs3, cues = encode(np.asarray(concentrations), position, bank.xy, p, rawu, FeatureConfig())
    previous_end = 0.0
    previous_xy = np.asarray(case["start_xy"], dtype=np.float64)
    timing = []
    for (start, end), current_xy in zip(windows, position):
        dt = end - previous_end
        duration = end - start
        displacement = float(np.linalg.norm(current_xy - previous_xy))
        if min(dt, duration) <= 0 or not np.isfinite(displacement):
            raise RuntimeError("invalid event timing/motion feature")
        timing.append(np.log1p([dt, duration, displacement / .30]) / 8.)
        previous_end, previous_xy = end, current_xy
    obs = np.concatenate((obs3, np.asarray(timing, dtype=np.float32)), axis=1)
    if not np.isfinite(obs).all() or not np.isfinite(cues).all():
        raise RuntimeError("nonfinite training features")
    output = Path(args.output)
    if output.exists() or output.with_suffix(".json").exists():
        raise RuntimeError("refuse to overwrite encoded episode")
    output.parent.mkdir(parents=True, exist_ok=True)
    # A source update is due after stop 4,7,10,... with the frozen PMFS
    # initialExplorationMoves=2 and stepsSourceUpdate=3, five events/stop.
    source_update_mask = np.asarray([n % 5 == 0 and (n // 5 - 1) >= 2 and
                                     (n // 5 - 1) % 3 == 0 for n in event_ids], dtype=bool)
    np.savez_compressed(output, obs=obs, cues=cues, event_ids=np.asarray(event_ids),
                        windows=np.asarray(windows), positions=position.astype(np.float32),
                        source_update_mask=source_update_mask,
                        label_index=np.asarray(bank.ids.index(case["source_id"]), dtype=np.int64))
    metadata = {"case_id": case["case_id"], "house": case["house"],
                "wind": case["wind"], "split": case["split"],
                "source_group": f"{case['house']}/{case['source_id']}",
                "plume_group": case["plume_id"], "policy": args.policy,
                "events": len(event_ids), "source_update_prefixes": int(source_update_mask.sum()),
                "obs_dim": obs.shape[1], "cue_dim": cues.shape[-1],
                "candidate_count": len(bank.ids), "bank_fingerprint": bank.fingerprint,
                "bank_file_sha256": sha(bank_path),
                "raw_files_sha256": {name: sha(raw / name) for name in
                                     ("measurement_blocks.csv", "measurement_events.csv", "measurement_samples.csv", "sensor_trace.csv")},
                "features_sha256": sha(output), "same_sensor_pipeline": True,
                "pmfs_clock_collision_count": clock_collisions,
                "max_pmfs_to_vgr_clock_lag_s": max_clock_lag,
                "vgr_publications_verified_distinct": True,
                "future_gas_used": False, "labels_used_for_policy": False}
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata))


if __name__ == "__main__":
    main()
