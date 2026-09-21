# House01 seed0 pipeline repair — scientific status PENDING

Authorized scope: native PMFS, one House01 seed0 case, 300 simulation seconds,
then unchanged V7 CSV replay and linked-native endpoint. No six-case batch.

Baseline: 24f55b95d57dc51b4c0b85e20384b00b1e8cc873 on
codex/tnqc-v5-300s-offline-20260921. The original method manifest is retained
unchanged. Its full ros2_package tree hash intentionally describes the baseline,
not this explicitly authorized terminal-lifecycle patch. Do not claim that the
patched tree passes that original full-tree identity gate.

Only Algorithm.cpp/.hpp and gsl_server.cpp change within ros2_package. PMFS
likelihood, posterior, planner, cadence, TNQC equations/gates, candidate definition,
and ExpectedValue implementation remain byte-identical to the baseline.

Root causes: a second server deadline can break before PMFS terminal saving;
the external launch did not enable simulation time; the wall-time benchmark
could time out before receiving the action result. The case wrapper later sent
SIGINT and SIGKILL after run_status appeared, not at its 900 s outer deadline.

Lifecycle repair: after paused PMFS initialization, the supervisor starts the
simulation at zero. The isolated VGR overlay hard-freezes all scientific tick
work at 300 s. PMFS budget handling calls the existing virtual saveResultsToFile
once, with no later state update. The benchmark's 900 s wall watchdog is only an
infrastructure deadline; the simulator still stops at 300 s. A native terminal
line enables the existing case runner's 3+5 s process flush/cleanup.

The overlay changes only _simulation_tick's terminal guard and the benchmark
watchdog. External baseline file hashes are checked before creating the overlay.
Original external files are never overwritten.

V7 loads simulated_hit_probability from candidate_support_alignment.csv.
Missing .f32 files do not require an exporter change. Support completeness is
audited independently by support_audit.py.

Run with a fresh absolute output root:

    TNQC_SINGLE_ROOT=/home/zyc/ros2_ws/tnqc_h01_pipeline_20260921/verified_native_v1 bash codex/h01_pipeline/run_single.sh

The script stops after native terminal and support auditing. Replay is a separate
step; inspect native reconstruction and endpoint parity before exposing any TNQC
counterfactual. Single-case success is pipeline validation only, not TNQC GO.
