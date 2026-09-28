"""Check opt-in VGR replay against the audited writer map and old-mode parity."""
from __future__ import annotations

import bisect
import csv
import hashlib
from pathlib import Path
import runpy

SOURCES = (
    Path("/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/sim_timebase.py"),
    Path("/home/zyc/brg_closedloop_20260927/vgr_execution_v2/vgr_bridge/sim_timebase.py"),
)
MAP = Path("/home/zyc/brg_v1_recovery_20260928/RESULT_TIME_MAP_300S.tsv")
EXPECTED_MAP_SHA = "a0af8f46ab91fa0e2f46f0af69076a72e5884e7d0ad38858c280e0aa4f38f728"


def main() -> None:
    if hashlib.sha256(MAP.read_bytes()).hexdigest() != EXPECTED_MAP_SHA:
        raise RuntimeError("writer time map changed")
    with MAP.open(newline="") as stream:
        times = [float(row["sim_time_s"]) for row in csv.DictReader(stream, delimiter="\t")]
    if len(times) != 566 or times[-1] < 299.8:
        raise RuntimeError("writer coverage mismatch")
    for source in SOURCES:
        backup = source.with_name(source.name + ".pre_brg_v1_20260928")
        new = runpy.run_path(str(source))["DeterministicTimebase"]
        old = runpy.run_path(str(backup))["DeterministicTimebase"]
        prev = -1
        for step in range(1501):
            t = step * .2
            expected = max(0, bisect.bisect_right(times, t + 1e-12) - 1)
            actual = new(.2, step=step).replay_iteration(565, 47, "physical_time_replay_300s")
            if actual != expected or actual < prev or not 0 <= t - times[actual] < .7:
                raise RuntimeError(f"causal physical-frame mismatch at step {step}: {actual}/{expected}")
            prev = actual
            for mode in ("seeded_time_replay", "fixed_debug"):
                if new(.2, step=step).replay_iteration(565, 47, mode) != old(.2, step=step).replay_iteration(565, 47, mode):
                    raise RuntimeError(f"legacy mode drift: {mode} step {step}")
    print("PASS base and overlay: 1501 causal steps, writer-map parity, 300 s coverage, old-mode parity")


if __name__ == "__main__":
    main()
