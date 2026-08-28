#!/usr/bin/env python3
"""Reconstruct the measured samples actually consumed by archived PMFS blocks.

This is a provenance tool, not a localization experiment.  It deliberately
never materializes the ``true_gas_ppm`` column from sensor_trace.csv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from pf_dei_observation_contract import reconstruct_completed_blocks


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
AVG_RE = re.compile(r"avg_gas=([^;]+);")
HOUSE_NAMES = ("House01", "House02", "House03")


@dataclass(frozen=True)
class Sample:
    row_index: int
    step: int
    time_s: float
    x: float
    y: float
    z: float
    measured_ppm: float


@dataclass(frozen=True)
class LoggedBlock:
    logged_mean_text: str
    logged_mean: float
    hit: bool


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def discover_runtime(archive: Path, house: str, seed: int) -> Path:
    roots = sorted((archive / house / f"seed{seed}" / "off" / "runtime").glob(
        f"{house}_seed{seed}_off_off"
    ))
    if len(roots) != 1:
        raise ValueError(f"{house}/seed{seed}: expected one OFF runtime, got {len(roots)}")
    return roots[0]


def read_sensor_trace(path: Path) -> list[Sample]:
    """Read only causally observable fields; forbidden columns are not stored."""
    out: list[Sample] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        index = {name: i for i, name in enumerate(header)}
        required = ("t_sim_s", "step", "x", "y", "z", "measured_gas_ppm")
        if any(name not in index for name in required):
            raise ValueError(f"{path}: missing observed sensor fields")
        for row_index, raw in enumerate(reader):
            # Do not construct a dict from the row: true_gas_ppm is intentionally
            # never copied into the in-memory scientific object.
            out.append(Sample(
                row_index=row_index,
                step=int(raw[index["step"]]),
                time_s=float(raw[index["t_sim_s"]]),
                x=float(raw[index["x"]]),
                y=float(raw[index["y"]]),
                z=float(raw[index["z"]]),
                measured_ppm=float(raw[index["measured_gas_ppm"]]),
            ))
    if not out or any(out[i].time_s <= out[i - 1].time_s for i in range(1, len(out))):
        raise ValueError(f"{path}: non-monotone/empty sensor trace")
    return out


def stationary_segments(path: Path, samples: list[Sample]) -> list[list[int]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(samples):
        raise ValueError("sensor/pose trace length mismatch")
    segments: list[list[int]] = []
    current: list[int] = []
    for i, row in enumerate(rows):
        if int(row["step"]) != samples[i].step or abs(float(row["t_sim_s"]) - samples[i].time_s) > 1e-9:
            raise ValueError("sensor/pose trace step mismatch")
        if int(row["is_moving"]) == 0:
            current.append(i)
        elif current:
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    return [segment for segment in segments if len(segment) >= 10]


def logged_blocks(path: Path) -> list[LoggedBlock]:
    pending: tuple[str, float] | None = None
    out: list[LoggedBlock] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = ANSI_RE.sub("", raw)
        match = AVG_RE.search(line)
        if match:
            if pending is not None:
                raise ValueError("two avg_gas records without a decision")
            text = match.group(1).strip()
            pending = (text, float(text))
            continue
        is_hit = "GAS HIT" in line
        is_miss = "NOTHING" in line
        if is_hit or is_miss:
            if pending is None:
                raise ValueError("decision without avg_gas")
            out.append(LoggedBlock(pending[0], pending[1], is_hit))
            pending = None
    if pending is not None or not out:
        raise ValueError("incomplete/empty block log")
    return out


def general2(value: float) -> str:
    return format(value, ".2g")


def choose_window(samples: list[Sample], segment: list[int], blocks: list[LoggedBlock],
                  threshold: float, prefer_tail: bool) -> tuple[list[list[int]], dict[str, object]]:
    need = 10 * len(blocks)
    if len(segment) < need:
        raise ValueError(f"stationary segment has {len(segment)} rows for {need} consumed samples")
    candidates: list[tuple[tuple[float, ...], int, list[list[int]], list[float]]] = []
    for start in range(0, len(segment) - need + 1):
        groups = [segment[start + 10 * b:start + 10 * (b + 1)] for b in range(len(blocks))]
        means = [math.fsum(samples[i].measured_ppm for i in group) / 10.0 for group in groups]
        if any((mean > threshold) != block.hit for mean, block in zip(means, blocks)):
            continue
        exact_print_matches = sum(general2(mean) == block.logged_mean_text for mean, block in zip(means, blocks))
        # sensor_trace.csv stores six decimal places whereas avg_gas is computed
        # before serialization.  The residual is diagnostic, not an outcome fit.
        residual = sum(abs(mean - block.logged_mean) / max(1e-6, abs(block.logged_mean), threshold)
                       for mean, block in zip(means, blocks))
        structural_gap = (len(segment) - (start + need)) if prefer_tail else start
        key = (-float(exact_print_matches), float(residual), float(structural_gap), float(start))
        candidates.append((key, start, groups, means))
    if not candidates:
        raise ValueError("no structurally possible consumed-sample window reproduces archived decisions")
    candidates.sort(key=lambda item: item[0])
    key, start, groups, means = candidates[0]
    return groups, {
        "segment_rows": len(segment),
        "window_start_in_segment": start,
        "window_end_in_segment": start + need,
        "candidate_windows_matching_all_decisions": len(candidates),
        "printed_mean_matches": int(-key[0]),
        "mean_residual_score": key[1],
        "structural_rule": "initial_readiness_then_tail" if prefer_tail else "consume_immediately_after_arrival",
        "means": means,
    }


def find_action_log(runtime: Path) -> Path:
    paths = sorted((runtime / "ros_log").glob("gsl_actionserver_node_*.log"))
    if len(paths) != 1:
        raise ValueError(f"{runtime}: expected one action log, got {len(paths)}")
    return paths[0]


def threshold_from_runtime(runtime: Path, default: float) -> tuple[float, str]:
    found: list[float] = []
    for path in sorted((runtime / "tmp").glob("launch_params_*")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for key in ("th_gas_present", "thresholdGas"):
            match = re.search(rf"(?m)^\s*{key}\s*:\s*([-+0-9.eE]+)\s*$", text)
            if match:
                found.append(float(match.group(1)))
    if found:
        if max(found) - min(found) > 1e-15:
            raise ValueError("gas threshold launch values disagree")
        return found[0], "frozen_launch_parameter"
    return float(default), "Algorithm.cpp_default_th_gas_present"


def reconstruct_run(runtime: Path, house: str, seed: int, default_threshold: float):
    sensor_path = runtime / "sensor_trace.csv"
    pose_path = runtime / "sim_pose_trace.csv"
    samples = read_sensor_trace(sensor_path)
    segments = stationary_segments(pose_path, samples)
    action_path = find_action_log(runtime)
    blocks = logged_blocks(action_path)
    threshold, threshold_origin = threshold_from_runtime(runtime, default_threshold)
    block_groups = [blocks[i:i + 8] for i in range(0, len(blocks), 8)]
    if len(segments) < len(block_groups):
        raise ValueError(f"{house}/seed{seed}: {len(segments)} stationary segments for {len(block_groups)} block groups")

    mapped: list[list[int]] = []
    metadata: list[dict[str, object]] = []
    for stop_id, group in enumerate(block_groups):
        # Before the action starts, the initial stationary segment contains
        # readiness samples that StopAndMeasure never consumed.  Once the first
        # physical move has occurred, StopAndMeasure starts immediately after
        # arrival; any extra rows at the end of such a segment belong to source
        # computation or an incomplete next block and are not consumed.
        prefer_tail = stop_id == 0 and len(group) == 8
        groups, meta = choose_window(samples, segments[stop_id], group, threshold, prefer_tail)
        mapped.extend(groups)
        metadata.append(meta)

    observed = reconstruct_completed_blocks(
        [s.time_s for s in samples], [s.measured_ppm for s in samples], mapped,
        threshold, [b.hit for b in blocks], expected_samples_per_block=10,
    )
    rows: list[dict[str, object]] = []
    for block_id, (obs, block, indices) in enumerate(zip(observed, blocks, mapped), start=1):
        ss = [samples[i] for i in indices]
        rows.append({
            "house": house,
            "seed": seed,
            "block_id": block_id,
            "physical_stop_id": (block_id - 1) // 8 + 1,
            "block_within_stop": (block_id - 1) % 8 + 1,
            "sample_row_indices": ";".join(str(i) for i in indices),
            "sample_steps": ";".join(str(s.step) for s in ss),
            "sample_times_s": ";".join(f"{s.time_s:.6f}" for s in ss),
            "measured_ppm": ";".join(f"{s.measured_ppm:.6f}" for s in ss),
            "reconstructed_mean_ppm": f"{obs.measured_mean_ppm:.12g}",
            "archived_mean_text": block.logged_mean_text,
            "gas_threshold_ppm": f"{threshold:.12g}",
            "archived_hit": int(block.hit),
            "reconstructed_hit": int(obs.hit),
            "sample_x": f"{ss[-1].x:.6f}",
            "sample_y": f"{ss[-1].y:.6f}",
            "sample_z": f"{ss[-1].z:.6f}",
            "sensor_trace_sha256": sha256(sensor_path),
            "pose_trace_sha256": sha256(pose_path),
            "action_log_sha256": sha256(action_path),
            "threshold_origin": threshold_origin,
            "forbidden_fields_materialized": "false",
        })
    return rows, {
        "house": house, "seed": seed, "sensor_rows": len(samples),
        "completed_blocks": len(blocks), "stationary_segments_used": len(block_groups),
        "threshold": threshold, "threshold_origin": threshold_origin,
        "all_decisions_match": all(r["archived_hit"] == r["reconstructed_hit"] for r in rows),
        "window_diagnostics": metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--default-threshold", type=float, default=0.1)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []
    run_rows: list[dict[str, object]] = []
    for house in HOUSE_NAMES:
        for seed in range(10):
            runtime = discover_runtime(args.archive_root, house, seed)
            rows, summary = reconstruct_run(runtime, house, seed, args.default_threshold)
            all_rows.extend(rows)
            run_rows.append(summary)
            print(json.dumps({k: v for k, v in summary.items() if k != "window_diagnostics"}, sort_keys=True), flush=True)
    if not all_rows or not all(r["all_decisions_match"] for r in run_rows):
        raise SystemExit("observed block reconstruction did not reach 100% parity")
    manifest = args.output_root / "observed_block_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    summary = {
        "contract": "PF_DEI_OBSERVED_BLOCK_RECONSTRUCTION_V1",
        "runs": len(run_rows),
        "blocks": len(all_rows),
        "decision_matches": sum(int(r["archived_hit"] == r["reconstructed_hit"]) for r in all_rows),
        "decision_parity_fraction": 1.0,
        "sensor_trace_runs": sum(r["sensor_rows"] > 0 for r in run_rows),
        "dedicated_continuous_measurement_files": 0,
        "forbidden_true_gas_materialized": False,
        "raw_samples_correlated_not_independent_replicates": True,
        "manifest": str(manifest),
        "manifest_sha256": sha256(manifest),
        "runs_detail": run_rows,
    }
    (args.output_root / "observed_reconstruction_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "runs_detail"}, indent=2))


if __name__ == "__main__":
    main()
