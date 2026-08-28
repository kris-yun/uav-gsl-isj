#!/usr/bin/env python3
"""Truth-blind historical PF-DEI sensor deconvolution and block counterfactual.

Reads only the archived measured sensor stream plus the already validated block
consumption manifest.  It never materializes true_gas_ppm, true source, final
localization error or ON/OFF performance.

This diagnostic is valid only for the source-proven frozen zero-noise symmetric
sensor configuration.  It quantifies how often native sensor dynamics changes
PMFS's block HIT/NOTHING decision relative to an ideal instantaneous sensor on
the reconstructed same physical concentration sequence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np

from pf_dei_inverse_sensor_reference import (
    FrozenSensorInverseConfig,
    forward_frozen_sensor,
    invert_frozen_sensor,
    inverse_quantization_bound_ppm,
)


HOUSES = ("House01", "House02", "House03")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_runtime(archive: Path, house: str, seed: int) -> Path:
    paths = sorted((archive / house / f"seed{seed}" / "off" / "runtime").glob(
        f"{house}_seed{seed}_off_off"
    ))
    if len(paths) != 1:
        raise ValueError(f"{house}/seed{seed}: expected one OFF runtime, got {len(paths)}")
    return paths[0]


def read_measured_trace(path: Path) -> tuple[np.ndarray, np.ndarray, str]:
    """Read only timestamp + measured ppm; forbidden columns are never copied."""
    times: list[float] = []
    measured: list[float] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        index = {name: i for i, name in enumerate(header)}
        required = ("t_sim_s", "measured_gas_ppm")
        if any(name not in index for name in required):
            raise ValueError(f"{path}: missing required measured fields")
        for row in reader:
            times.append(float(row[index["t_sim_s"]]))
            measured.append(float(row[index["measured_gas_ppm"]]))
    t = np.asarray(times, dtype=np.float64)
    m = np.asarray(measured, dtype=np.float64)
    if t.size < 3 or t.shape != m.shape or not np.all(np.diff(t) > 0.0):
        raise ValueError(f"{path}: invalid measured trace")
    return t, m, sha256(path)


def read_block_manifest(path: Path) -> dict[tuple[str, int], list[dict[str, str]]]:
    grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Manifest was produced by the closure provenance code and contains
            # no source truth/performance fields.  Still keep only what we need.
            key = (row["house"], int(row["seed"]))
            grouped[key].append({
                "house": row["house"],
                "seed": row["seed"],
                "block_id": row["block_id"],
                "physical_stop_id": row["physical_stop_id"],
                "block_within_stop": row["block_within_stop"],
                "sample_row_indices": row["sample_row_indices"],
                "reconstructed_mean_ppm": row["reconstructed_mean_ppm"],
                "gas_threshold_ppm": row["gas_threshold_ppm"],
                "archived_hit": row["archived_hit"],
                "sensor_trace_sha256": row.get("sensor_trace_sha256", ""),
            })
    return grouped


def parse_indices(text: str) -> list[int]:
    values = [int(token) for token in text.split(";") if token != ""]
    if len(values) != 10 or len(set(values)) != 10:
        raise ValueError(f"expected ten unique consumed indices, got {text!r}")
    if values != sorted(values):
        raise ValueError("consumed sample indices are not time ordered")
    return values


def classify_block(native_hit: bool, ideal_mean: float, threshold: float, eps: float) -> tuple[str, bool | None]:
    if abs(ideal_mean - threshold) <= eps:
        return "AMBIGUOUS_SERIALIZATION_MARGIN", None
    ideal_hit = bool(ideal_mean > threshold)
    if native_hit and not ideal_hit:
        return "NATIVE_HIT_IDEAL_NOTHING", ideal_hit
    if (not native_hit) and ideal_hit:
        return "NATIVE_NOTHING_IDEAL_HIT", ideal_hit
    if native_hit and ideal_hit:
        return "SAME_HIT", ideal_hit
    return "SAME_NOTHING", ideal_hit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive-root", type=Path, required=True)
    ap.add_argument("--block-manifest", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--decimal-places", type=int, default=6)
    args = ap.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    cfg = FrozenSensorInverseConfig()
    blocks_by_run = read_block_manifest(args.block_manifest)

    all_block_rows: list[dict[str, object]] = []
    run_summaries: list[dict[str, object]] = []
    trace_manifest_rows: list[dict[str, object]] = []

    for house in HOUSES:
        for seed in range(10):
            runtime = discover_runtime(args.archive_root, house, seed)
            sensor_path = runtime / "sensor_trace.csv"
            t, m, trace_hash = read_measured_trace(sensor_path)
            expected_rows = blocks_by_run.get((house, seed))
            if not expected_rows:
                raise ValueError(f"missing block manifest rows for {house}/seed{seed}")
            expected_hashes = {row["sensor_trace_sha256"] for row in expected_rows if row["sensor_trace_sha256"]}
            if expected_hashes and expected_hashes != {trace_hash}:
                raise ValueError(f"sensor trace hash mismatch for {house}/seed{seed}")

            inv = invert_frozen_sensor(t, m, cfg)
            eps_c = inverse_quantization_bound_ppm(args.decimal_places, inv.alpha, cfg.gain)

            # The inversion is algebraic on the serialized measured stream.  A
            # round-trip must reproduce that stream to floating precision for
            # all rows represented by the recovered physical input + delay.
            m_roundtrip = forward_frozen_sensor(inv.physical_ppm, cfg, inv.sample_dt_s)
            if m_roundtrip.shape != m.shape:
                raise ValueError("round-trip measured length mismatch")
            roundtrip_max_abs = float(np.max(np.abs(m_roundtrip - m)))
            if roundtrip_max_abs > 1e-10:
                raise ValueError(
                    f"{house}/seed{seed}: inverse/forward round-trip mismatch {roundtrip_max_abs}"
                )

            # Values slightly below zero can be caused by six-decimal output
            # quantization.  Do not clip them.  Report values beyond the
            # source-proven worst-case inverse serialization bound.
            below_bound_count = int(np.sum(inv.physical_ppm < -eps_c))
            if below_bound_count:
                raise ValueError(
                    f"{house}/seed{seed}: {below_bound_count} reconstructed physical samples below -serialization bound"
                )

            trace_out = args.output_root / f"recovered_physical_trace_{house}_seed{seed}.csv"
            with trace_out.open("w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "house", "seed", "physical_row_index", "physical_time_s",
                    "recovered_physical_ppm", "source_measured_row_index",
                    "serialization_bound_ppm", "truth_fields_used",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for i, (time_s, value) in enumerate(zip(inv.physical_time_s, inv.physical_ppm)):
                    writer.writerow({
                        "house": house,
                        "seed": seed,
                        "physical_row_index": i,
                        "physical_time_s": f"{time_s:.12g}",
                        "recovered_physical_ppm": f"{float(value):.17g}",
                        "source_measured_row_index": i + inv.delay_steps,
                        "serialization_bound_ppm": f"{eps_c:.17g}",
                        "truth_fields_used": "false",
                    })

            counts = Counter()
            transition_counts = Counter()
            recoverable_blocks = 0
            for row in expected_rows:
                indices = parse_indices(row["sample_row_indices"])
                native_hit = bool(int(row["archived_hit"]))
                native_mean = float(row["reconstructed_mean_ppm"])
                threshold = float(row["gas_threshold_ppm"])
                stop_id = int(row["physical_stop_id"])
                block_within_stop = int(row["block_within_stop"])
                first_after_transition = stop_id > 1 and block_within_stop == 1

                if any(index >= inv.physical_ppm.size for index in indices):
                    label = "UNRECOVERABLE_END_OF_RUN"
                    ideal_mean = math.nan
                    ideal_hit = None
                else:
                    ideal_values = inv.physical_ppm[np.asarray(indices, dtype=np.int64)]
                    ideal_mean = float(np.mean(ideal_values, dtype=np.float64))
                    label, ideal_hit = classify_block(native_hit, ideal_mean, threshold, eps_c)
                    recoverable_blocks += 1

                counts[label] += 1
                if first_after_transition:
                    transition_counts[label] += 1

                all_block_rows.append({
                    "house": house,
                    "seed": seed,
                    "block_id": int(row["block_id"]),
                    "physical_stop_id": stop_id,
                    "block_within_stop": block_within_stop,
                    "first_block_after_transition": int(first_after_transition),
                    "native_mean_ppm": f"{native_mean:.17g}",
                    "native_hit": int(native_hit),
                    "ideal_mean_ppm": "" if not math.isfinite(ideal_mean) else f"{ideal_mean:.17g}",
                    "ideal_hit": "" if ideal_hit is None else int(bool(ideal_hit)),
                    "classification": label,
                    "threshold_ppm": f"{threshold:.17g}",
                    "serialization_bound_ppm": f"{eps_c:.17g}",
                    "sample_row_indices": row["sample_row_indices"],
                    "truth_fields_used": "false",
                })

            run_summary = {
                "house": house,
                "seed": seed,
                "sensor_rows": int(t.size),
                "recoverable_physical_samples": int(inv.physical_ppm.size),
                "delay_steps": int(inv.delay_steps),
                "sample_dt_s": float(inv.sample_dt_s),
                "alpha": float(inv.alpha),
                "serialization_bound_ppm": float(eps_c),
                "roundtrip_max_abs_ppm": roundtrip_max_abs,
                "reconstructed_physical_min_ppm": float(np.min(inv.physical_ppm)),
                "reconstructed_physical_max_ppm": float(np.max(inv.physical_ppm)),
                "blocks": len(expected_rows),
                "recoverable_blocks": recoverable_blocks,
                "classification_counts": dict(counts),
                "first_block_after_transition_counts": dict(transition_counts),
                "sensor_trace_sha256": trace_hash,
                "recovered_trace_sha256": sha256(trace_out),
                "truth_fields_used": False,
            }
            run_summaries.append(run_summary)
            trace_manifest_rows.append({
                "house": house,
                "seed": seed,
                "sensor_trace_sha256": trace_hash,
                "recovered_trace": str(trace_out),
                "recovered_trace_sha256": sha256(trace_out),
            })
            print(json.dumps(run_summary, sort_keys=True), flush=True)

    block_csv = args.output_root / "block_counterfactual.csv"
    with block_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_block_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_block_rows)

    trace_manifest = args.output_root / "recovered_trace_manifest.csv"
    with trace_manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(trace_manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(trace_manifest_rows)

    total_counts = Counter(row["classification"] for row in all_block_rows)
    transition_total = Counter(
        row["classification"] for row in all_block_rows if int(row["first_block_after_transition"]) == 1
    )
    by_house: dict[str, dict[str, object]] = {}
    for house in HOUSES:
        rows = [row for row in all_block_rows if row["house"] == house]
        by_house[house] = {
            "blocks": len(rows),
            "counts": dict(Counter(row["classification"] for row in rows)),
            "first_block_after_transition_counts": dict(Counter(
                row["classification"] for row in rows if int(row["first_block_after_transition"]) == 1
            )),
        }

    summary = {
        "contract": "PF_DEI_EXACT_SENSOR_DECONVOLUTION_COUNTERFACTUAL_V1",
        "runs": len(run_summaries),
        "blocks": len(all_block_rows),
        "truth_fields_used": False,
        "sensor_inverse_scope": "frozen_zero_noise_symmetric_unsaturated_regular_0p2s_only",
        "total_counts": dict(total_counts),
        "first_block_after_transition_counts": dict(transition_total),
        "by_house": by_house,
        "run_summaries": run_summaries,
        "block_csv": str(block_csv),
        "block_csv_sha256": sha256(block_csv),
        "trace_manifest": str(trace_manifest),
        "trace_manifest_sha256": sha256(trace_manifest),
    }
    summary_path = args.output_root / "block_counterfactual_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("PF_DEI_EXACT_SENSOR_DECONVOLUTION_COUNTERFACTUAL PASS")
    print(json.dumps({k: v for k, v in summary.items() if k != "run_summaries"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
