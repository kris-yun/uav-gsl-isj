# L1 cumulative repair 3: STOP

This single authorized extra repair stopped on a VM SciPy API incompatibility before the first CG solution. The executed code called `cg(..., rtol=...)`; the VM loaded SciPy 1.8.0 with `(A, b, x0=None, tol=1e-05, maxiter=None, M=None, callback=None, atol=None)`. The attempt was not rerun, patched after execution, or renamed. This is an engineering failure, not a scientific rejection of the prior.

The frozen amendment is `2576f444f8172b09291f0c15832409fe10d757294672a2b1640add68fa1fae3f` at anchor `cc2cd7711bd5c2aeb3c10cb56d9d5af4b6b3b41f`. The counter advanced from 2 to 3, and the permitted cumulative limit is 3. Original source, CFD/wind/plant history, generation seeds, route rules, frame500, source support and success criteria were not modified. All 447 public candidates still have legal heights.

## Executed change and limits

`repair_boundary.py` implements closed OOB/Obstacle normal flux with only original Outlet faces open, nested re-projection of the saved 24-mode public basis, direct-raw comparison under the same discrete edge metric, float32 divergence/continuity checks and fail-closed null-mode handling. Original conditioned paths are never loaded. The computation was supervised for time, RSS, disk capacity and free space. The saved `flow_faces.f32` is an unqualified zero-filled output allocated before the solver exception; it is excluded from GitHub and cannot be consumed.

The prescribed Laplace/Rao–Blackwell importance proposal and explicit libbsc/ROS binding remain prospective in the frozen contract. Neither was implemented/executed after the boundary dependency stopped. Build logs explicitly record NOT_STARTED. No exact likelihood, prior, seed or ESS threshold was changed by execution.

## Measured outcome

Boundary stage wall: 4.237070 s; conservative host-stage charge: 4.672000 s. Peak RSS: 403988480 bytes (385.273 MiB). Gas forwards started/completed: 0/0; native goals: 0. All monitored resource limits passed. No new CFD or true-plant batch was started.

Boundary/numerical/importance/native-link qualification therefore remains incomplete. The six-forward batch was not admitted. The 447-source sequential filter, finite-reference calibration/convergence, state-aware likelihood and native `sourceProbability` plus `varianceOfHitProb` consumers remain unqualified/unconnected. No full-447 cost was measured, and it cannot be extrapolated from this failed initialization attempt. R4 ordinary-baseline sufficiency and R5 STOP are preserved.

## Budget and engineering timing

Conservative starting balance: 5537.991 s. This repair reserves 900 s; another independent interface-only task reserves 120 s. Safely unreserved project balance: 4517.991 s. This repair's conservative actual charge is 4.672000 s, with 895.328000 s unused reservation retained for parent reconciliation. If the parent releases only this repair's unused reservation while keeping the other full120 s, the provisional balance is 5413.319000 s. The other task's final actual cost is not silently assumed.

Recorded preparation wall after amendment freeze and before computation: 222.834712 s. The earlier read-only discovery/planning start was not instrumented, so a complete pre-freeze engineering wall is unavailable. Post-stop read-only environment verification took 0.969000 s on the host. These are separate from the scientific stage.

## Required disposition

STOP this candidate. No fourth repair or retry is inferred. No 447/native closed loop is authorized. Preserve the original STOP history and all executed evidence. The runtime API prerequisite must be resolved only within a separately authorized future scope; this record does not request or grant that scope.
