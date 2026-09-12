# Native GMRF input-chain checkpoint

Status: DIAGNOSTIC_COMPLETE, NOT C2_PASS, NOT CLOSED_LOOP_EFFECTIVE.

The active M1 goal remains open. No M2/M3, new seed, new bank, or
controller was run. Isolated VM directory: `/home/zyc/M1_GMRF_SHADOW_20260910`.
The VM's older repository was not overwritten.

## Actual execution

The installed native `libgmrf_wind_core.so` was linked by a small standalone
driver. Inputs are the audited navigation-height occupancy slice and only
`t_sim_s`, `pose_xy`, `wind_uv` from the existing 12 frozen histories.
No gas, candidate-source location, full wind field, or vertical true wind is
passed to the estimator. Source labels remain external file identifiers.

Explicit diagnostic configuration: cell size 0.5 m; advection/mass/diffusion
weights 100/100/100; obstacle weight 10; polar observation variances 0.0001;
one Picard iteration; update after observing each completed 2 s prefix.
These are NOT claimed to match historical ROS launch parameters/timing.
Native node defaults informed parameters; diagnostic cadence is explicit.

All 12 histories reached 240 s and produced 120 finite-valued field snapshots.

| House | Accepted observations per case | Rejected per case | Output rows per case |
|---|---:|---:|---:|
| H01 | 1136 | 64 | 35040 |
| H02 | 1162 | 38 | 38160 |
| H03 | 1132 | 68 | 41640 |

At fixed House/wind, SA and SB output files are byte-identical. This is an
expected no-source-input check, not a ranking or task-benefit result.

## Findings that constrain next execution

1. The native insertion routine rejects out-of-extent/nonfree GMRF cells.
   Map resampling to 0.5 m is a suspected explanation for rejected local
   measurements; exact rejected positions still need auditing against the
   original 0.1 m occupancy. Do not call this hypothesis proven.
2. Every solve prints `did not converge after 1 iterations`. Native source
   checks relative-state convergence only when `iter > 0`; a one-iteration
   run cannot satisfy that check. This warning is not evidence of divergence.
   A bounded multi-iteration diagnostic is required to assess numerical error.
3. Native observations are `time_invariant = true`, and insertion accumulates
   observations. The node update does not clear them. Historical winds can
   therefore remain influential under dynamic transport. This is a candidate
   failure mechanism, not yet evidence that forgetting improves localization.
4. Native GMRF is 2-D. Do not invent a validated 3-D field or inject true W.
   The 3-D filament provider still needs an explicit, testable closure/input
   contract before it can be called deployable.
5. Header/library/binary hashes were captured, but native source-to-installed-
   library identity has not been established; source findings are not binary
   equivalence proof. ROS event/callback parity is also unverified.

## Artifacts and next gate

Inputs and manifest: `evidence/cstar_m1_gmrf_shadow_inputs_20260910/`.
Native outputs, logs and hashes: `evidence/cstar_m1_gmrf_shadow_results_20260910/`.
Driver and producer: `experiments/ctpi_cstar/m1_gmrf_shadow.cpp`,
`prepare_m1_gmrf_shadow.py`, `run_m1_gmrf_shadow.sh`.

Next: audit rejection positions and numerical iteration behavior without
source labels, bind deployed configuration and timing, then test the physical
forward provider against measured concentration. Only after that compare
same-provider ordinary Bayes and robust causal evidence; proceed to frozen
House123 seed12 same-controller paired closed loop when the input and
mechanism gates pass. Do not declare source identifiability from this replay.

## Follow-up: numerical and geometry experiments

Executed native 20-iteration replay for six distinct House/wind histories;
SA/SB are redundant wind inputs, so they were not rerun for this diagnostic.
All outputs are finite. Convergence counts out of 120 snapshots are
H01 fast/slow 120/120, H02 115/116, H03 114/110. No divergence messages.
Twenty iterations therefore do NOT warrant an all-snapshots convergence claim.
Maximum component differences versus one iteration range from 0.0794 to
0.5282 m/s. These compare numerical settings, not accuracy against truth.

Every rejected observation is in a free original 0.1 m map voxel:
H01 64/64, H02 38/38, H03 68/68 per case. This rules out an original-map
obstacle at those measured positions as the rejection explanation.

A generic map adapter was then tested: translate to map-local coordinates,
anchor origin to zero, and set GMRF cell size equal to occupancy resolution.
No observation is snapped or moved physically; weights are unchanged.
All 1200 observations were accepted in each of H01/H02/H03, with zero
rejections. Geometry-only mode intentionally performs no wind solves.
This is a geometry-interface test, not full graph-topology or field accuracy
validation; translation/rotation equivariance remain separate tests.

An aligned full-field run was launched in
`/home/zyc/M1_GMRF_SHADOW_20260910/aligned_field_v4`, six distinct histories,
20-iteration cap, 240 s horizon. At this checkpoint it is still running;
inspect its process/session and outputs before claiming completion. The
goal-turn process handle is unified exec session 32732. Do not restart just
because an observation call times out.

New evidence: `cstar_m1_gmrf_numerical_20260910/`,
`cstar_m1_gmrf_numerical_audit_20260910.json`, and
`cstar_m1_gmrf_geometry_20260910/` under `evidence/`.
The standalone driver has an explicit `aligned-geometry`/`aligned-field`
mode; normal mode preserves the earlier diagnostic configuration.

Do not keep optimizing wind indefinitely: once coordinate/timestamp/input
contracts are satisfied, expose remaining transport uncertainty in the
provider error audit and test source evidence. Numerical/geometry improvements
alone cannot establish the causal M1 contribution.

## Disk-full invalidation and restart

The `aligned_field_v4` run above is INVALIDATED: VM `/dev/sda3` reached
100% use (0 available), causing truncated/empty output files. Advancing to a
later case was NOT completion. The task-owned parent PID 10791 and replay
PID 11013 were explicitly terminated; unified exec session 32732 ended with
exit 1. No old data or banks were removed. Partial files are preserved.

The native driver now throws on output stream failure and flushes both data
and rejection streams before success reporting. A symlink to `/dev/full`
inside the task tmpfs directory verified exit code 1 with an iostream error.

A fresh run uses `/dev/shm/m1_aligned_20260910.43Qpj0` (2.9 GiB available at
preflight, host available RAM 4.8 GiB). It is reconstructible and temporary:
copy and hash-check completed artifacts onto the Windows evidence directory
before considering them preserved. Current unified exec session: 29161.
The old root-disk run is not resumed or used for field validation.

Added `m1_causal/estimated_wind_history.py` with explicit map-centre alignment,
fixed spatial support, finite values, chronological prefix-only lookup,
expected terminal time and refusal of unsupported horizontal cells.
The caller must declare initial constant wind prior and
`planar_extrusion_zero_vertical` closure; neither is inferred from true wind.
Unit checks cover pre-first-field prior, no future-field backfill, unsupported
cells, misaligned maps and truncated horizons. This is an ingress contract,
not proof of the planar model, transport accuracy, or M1 closed-loop benefit.

First recovered case H01_SA_fast completed: 120 snapshots, 1200 accepted
observations, zero rejected, 240 s. Its field was copied to
`evidence/cstar_m1_gmrf_aligned_valid_20260910/H01_SA_fast.txt` and passed the
new reader's alignment/finite/support/terminal checks (6866 free cells).
SHA256: `5cf06e8e895a59046321f03a91e04450523bce5b52e35c99a822032f480b4c16`.
At requested time 239 s the selected field is timestamp 238 s, not 240 s.
The remaining five histories are still running at this checkpoint.
