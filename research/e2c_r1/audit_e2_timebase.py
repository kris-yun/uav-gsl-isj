#!/usr/bin/env python3
"""Reconstruct E2 writer records from frozen GADEN clock semantics, no gas reads."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path


RECORD_IDS = tuple(range(100, 551, 50))
E2_BINARY_SHA = "4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1"


def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def reconstruct(sim_time: float) -> list[dict]:
    # RunningSimulation::AdvanceTimestep: add, move, save, wind update, clock update.
    t = last_save = last_wind = f32(0.0)
    dt, save_dt, wind_dt = f32(.1), f32(.5), f32(1.0)
    wind, step = 0, 0
    out = []
    while t < sim_time:
        if step == 0 or t > f32(last_save + save_dt):
            out.append(dict(save_record_id=len(out), clock_before_s=t,
                            active_wind_index=wind, integration_step=step,
                            completed_integration_steps=step + 1,
                            nominal_post_update_time_s=(step + 1) / 10.0))
            last_save = t
        if t > f32(last_wind + wind_dt):
            wind = wind + 1 if wind < 10 else 1
            last_wind = t
        t = f32(t + dt)
        step += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrumented-map", type=Path, required=True)
    ap.add_argument("--writer-source-sha", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    with args.instrumented_map.open(encoding="utf-8", newline="") as f:
        observed = list(csv.DictReader(f, delimiter="\t"))
    predicted = reconstruct(300.0)
    if len(predicted) != 566 or len(observed) < len(predicted):
        raise RuntimeError("writer count inconsistent with E2 566 saved records")
    for i, p in enumerate(predicted):
        row = observed[i]
        got = (int(row["save_record_id"]), float(row["physical_sim_time_s"]),
               int(row["wind_index"]), int(row["integration_step"]))
        exp = (p["save_record_id"], p["clock_before_s"],
               p["active_wind_index"], p["integration_step"])
        if got != exp:
            raise RuntimeError(f"writer replay mismatch at record {i}: {got} != {exp}")
    selected = [predicted[i] for i in RECORD_IDS]
    if any(r["clock_before_s"] >= 300 for r in selected):
        raise RuntimeError("requested record is outside E2 simulation")
    args.out.mkdir(parents=True, exist_ok=True)
    for r in selected:
        r["state_stage"] = "POST_MOVE_PRE_WIND_PRE_CLOCK"
        r["release_enabled"] = True
        r["physical_time_semantics"] = "clock_before_s plus state advanced one integration step"
    fields = list(selected[0])
    with (args.out / "TIMEBASE_MAP.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(selected)
    result = dict(decision="E2C_R1_TIMEBASE_PASS", e2_writer_records=566,
                  source_replay_records_matched=566, record_ids=list(RECORD_IDS),
                  original_e2_binary_sha256=E2_BINARY_SHA,
                  writer_source_sha256=args.writer_source_sha,
                  instrumented_map_sha256=sha(args.instrumented_map),
                  instrumented_binary_is_e2_binary=False,
                  validation="same deterministic save/wind/clock control flow; instrumented AOD map agrees with replay for all 566 E2 records",
                  exact_physical_seconds_claim=False,
                  temporal_label="GADEN float32 clock before write; serialized state is after move and before wind/clock update",
                  scientific_concentration_values_read=False)
    (args.out / "TIMEBASE_PROVENANCE.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
