"""Reconstruct the original GADEN writer clock, without reading concentration.

This mirrors RunningSimulation::AdvanceTimestep() using IEEE float32.  It is
only valid for the frozen 300 s / 0.1 s / 0.5 s / 1.0 s configuration.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parent


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def derive() -> list[dict[str, object]]:
    lock = json.loads((ROOT / "FROZEN_RUN_MANIFEST.json").read_text())
    p = lock["simulation_parameters"]
    if (p["sim_time"], p["time_step"], p["results_time_step"],
        p["wind_time_step"], p["loop_from_step"], p["loop_to_step"]) != (
        "300.0", "0.1", "0.5", "1.0", "1", "10"
    ):
        raise RuntimeError("writer clock parameters changed")
    t, dt, duration = f32(0), f32(.1), f32(300)
    last_save = -f32(3.4028234663852886e38)
    last_wind = f32(0)
    save_delta, wind_delta = f32(.5), f32(1)
    wind_index, step = 0, 0
    rows: list[dict[str, object]] = []
    while t < duration:
        # The snapshot is saved before the wind update in this timestep.
        if t > f32(last_save + save_delta):
            rows.append({"frame_id": len(rows), "iteration_file": f"iteration_{len(rows)}",
                         "sim_step": step, "sim_time_s": format(t, ".9f"),
                         "wind_index": wind_index})
            last_save = t
        if t > f32(last_wind + wind_delta):
            wind_index = 1 if wind_index >= 10 else wind_index + 1
            last_wind = t
        t = f32(t + dt)
        step += 1
    if len(rows) != 566 or step != 3000 or rows[-1]["frame_id"] != 565:
        raise RuntimeError("writer time-map parity failed")
    return rows


def main() -> None:
    rows = derive()
    path = ROOT / "RESULT_TIME_MAP_300S.tsv"
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "first": rows[0], "last": rows[-1], "path": str(path)}))


if __name__ == "__main__":
    main()
