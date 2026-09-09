"""Structural gate for the M1F one-physical-stop evidence windows."""

from pathlib import Path
import json


repo = Path(__file__).resolve().parents[2]
pmfs = (repo / "ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp").read_text(
    encoding="utf-8"
)
launch = (repo / "closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py").read_text(
    encoding="utf-8"
)
runner = (repo / "closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh").read_text(
    encoding="utf-8"
)

# Mirror the PMFS ordering: record the stop, optionally update, then increment
# iterationsCounter.  Warm-up stops must never enter the causal event carrier.
initial_exploration_moves = 2
steps_between_updates = 1
blocks_per_stop = 8
committed = 0
recorded = 0
windows = []
for iterations_counter in range(7):
    if iterations_counter >= initial_exploration_moves:
        recorded += blocks_per_stop
    time_to_simulate = (
        iterations_counter >= initial_exploration_moves
        and iterations_counter % steps_between_updates == 0
    )
    if time_to_simulate:
        windows.append(recorded - committed)
        committed = recorded

checks = {
    "mode_is_explicit": 'pfdiMode == "cer_core_eventtime_m1"' in pmfs,
    "cadence_is_enforced_in_core":
        "CER_CORE_EVENTTIME_REQUIRES_STEPS_SOURCE_UPDATE_1" in pmfs,
    "warmup_events_are_excluded": "eventEvidenceAfterWarmupOnly" in pmfs,
    "launch_identity_is_explicit": "'cer_core_eventtime_m1': 'M1F'" in launch,
    "runner_identity_is_explicit": 'M1F) PFDI_MODE="cer_core_eventtime_m1"' in runner,
    "event_time_is_recorded": "double simTime = 0.0" in pmfs or "double simTime = 0.0" in (repo / "ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.hpp").read_text(encoding="utf-8"),
    "every_scored_window_is_one_stop": windows == [blocks_per_stop] * len(windows),
}
report = {
    "contract": "CSTAR_CORE_M1_EVENTTIME_WINDOW_V1",
    "initial_exploration_moves": initial_exploration_moves,
    "steps_between_source_updates": steps_between_updates,
    "blocks_per_physical_stop": blocks_per_stop,
    "scored_window_block_counts": windows,
    "checks": checks,
    "pass": all(checks.values()),
    "limits": [
        "structural source-and-schedule test only",
        "one-stop windows assume transport nuisance is locally stable during a stop",
        "closed-loop utility requires paired execution",
    ],
}
print(json.dumps(report, indent=2))
if not report["pass"]:
    raise SystemExit(1)
