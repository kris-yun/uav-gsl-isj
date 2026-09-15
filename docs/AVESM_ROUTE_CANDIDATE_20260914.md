# AVESM candidate: Anytime-Valid E-process Source Map

Date: 2026-09-14

## Why PE-WHRM stopped

PE-WHRM found positive ordered-history source evidence on the VGR factorial
development set, but its empirical ratio moment missed the calibration gate
(maximum absolute error 0.106). The missing property is not more expressive
representation; it is a sequential evidence object whose meaning survives
adaptive observation and optional stopping.

## Main innovation

**Anytime-Valid E-process Source Map (AVESM)** replaces the PMFS update kernel
with a source-grid map built from candidate-wise test martingales. For source
candidate s, define the null predictive distribution for the next gas
observation, `p_s(y_t | H_{t-1}, c)`, and a predictable alternative mixture
`q_s(y_t | H_{t-1}, c)` over the other source candidates. The update is

`e_{s,t} = q_s(y_t | H_{t-1}, c) / p_s(y_t | H_{t-1}, c)` and
`E_{s,t} = product_{tau<=t} e_{s,tau}`.

Under the null that s generated the history, `E_{s,t}` is a nonnegative
martingale (or supermartingale after safe calibration), so its expectation is
bounded at every stopping time. The probability-map interface is the normalized
test-inversion map

`pi_t(s) proportional to pi_0(s|c) / E_{s,t}`.

The fixed-rival evidence increment is
`delta_t(s*,r) = log E_{r,t} - log E_{s*,t}`. Positive values favor the true
source while retaining a finite-sample, anytime-valid evidence interpretation.

## What makes this a main mechanism

The contribution is not “use e-values” in isolation. It changes the map's
semantic object from an uncalibrated posterior-like score to a source-grid
test-inversion process whose evidence can be audited under arbitrary stopping,
history-dependent sensing, and source/time permutation controls. No online
candidate-response provider or dense field target is required.

## Falsification gate

1. Held-out null e-process expectation must remain at or below 1 under each
   source and under random stopping rules.
2. Intact true-versus-fixed-rival cumulative log-inverse-e-process margin must
   exceed direct pointwise `q0`.
3. Time-position and source-history permutations must collapse the margin and
   must not create false e-process threshold crossings.
4. Candidate-list permutation must exactly reorder the map.

Failure of the null expectation or optional-stopping gate is a hard NO-GO; no
closed-loop claim is opened by a positive rank result alone.

## Scope boundary

This is a development candidate. The existing VGR factorial source evidence is
explicitly diagnostic-only and its nominal seeds are pseudoreplicates. A PMFS
confirmation requires a genuinely independent source-by-transport asset after
the AVESM mechanism gate passes.

## Small transfer audit (2026-09-15)

Two cross-wind fits and one physical-distance fit were tested offline; none
passed the predeclared control/null gates. A route-protocol transfer from VGR
factorial episodes to eight R3C replays was also run. It produced a positive
mean inverse-e margin (`283.82`) and a reduced shuffle control (`3.16`), but
the true source was not reliably top-ranked (mean rank `2.5`) and every
episode crossed the log-20 e-process threshold. The R3C package explicitly
reuses the frozen R3B physical realization, so this is not independent
cross-simulation evidence. AVESM therefore remains an unproven candidate for
cross-data validity; no main-result claim is opened.

## Fresh House123 seed probe (2026-09-15)

With explicit authorization, a bounded new-seed probe generated four fixed
route histories (`H01_SA`, `H01_SB`, `H03_SA`, `H03_SB`), 300 frames each, from
the current GADEN runtime. The contract and hashes passed, but all four
histories contained zero nonzero gas frames. The resulting AVESM transfer
diagnostic is therefore `CROSS_HOUSE_TRANSFER_NO_GO`: any apparent rank signal
is a prior/model artifact, not observed source evidence. The probe is retained
as a data-coverage failure, not counted as a negative scientific result.

The explicit RNG rerun (`GADEN_RNG_SEED=20260915`, H01_SA) also produced 300
frames with zero nonzero gas observations. This closes the bounded probe as a
route-coverage failure: an independent seed exists, but the selected fixed
route never interrogates plume evidence.

## Concentration-chain audit (2026-09-15)

Before changing the estimator, the current-runtime path was checked end-to-end
on a preserved 10.1-s H01_SA_fast simulator output (seed 20260915). The exact
helper used by the extractor returned 9.18, 15.27, and 19.64 ppm at the declared
source for raw iterations 1, 10, and 100, while returning 0 ppm at the frozen
route points for raw iterations 2, 4, and 100. Re-extraction of the first 50
route frames mapped `t=0.2 s -> raw_iteration=2` and produced 0 ppm for every
frame. The raw iteration-file hashes and query values are recorded in
`experiments/avesm_concentration_chain_audit.json`.

This separates two issues: concentration parsing/iteration alignment PASS;
route/plume coverage FAIL. A source-near query is an offline diagnostic only and
is not evidence for a source-blind localization claim. The next valid experiment
must repair or replace the route-coverage premise under a pre-registered,
source-blind design, without changing AVESM or treating the present all-zero run
as a mechanism failure.

## Source-blind coverage control (2026-09-15)

As a bounded control, a deterministic serpentine route was generated from the
House01 occupancy bounds alone (no source coordinates) and run through the same
current-runtime extractor. It produced 36/300 frames above `1e-6 ppm`, 24/300
above `0.1 ppm`, and a peak of `4.466 ppm` at `(0.052, 2.000, 0.3)`. Thus the
concentration path is capable of producing informative observations; the earlier
all-zero result was a route-coverage defect.

Using the existing pooled distance-kernel diagnostic only as a sanity check, the
same 300-frame history gave a true-versus-fixed-wrong log-inverse-e margin of
`202.69` in favor of the declared source. This demonstrates that the recovered
observations carry source-discriminating information, but it is a single-case
diagnostic and not an AVESM confirmation.

However, the measured-history SHA256 is identical for metadata seeds `1234` and
`20260915` under this simulator build. The seed field is therefore not yet
independent-realization evidence (`SEED_SENSITIVITY_UNPROVEN_IDENTICAL_OUTPUT`).
The coverage control is retained as diagnostic evidence only; a genuine seed
separation check is required before any held-out or cross-seed claim.

## Seed-runtime audit (2026-09-15)

The immediate runtime cause was twofold. First, `ldd` had selected the older
closure `libgaden.so` because the generator's `LD_LIBRARY_PATH` omitted
`PF_DEI_V3_GADEN_BUILD_REF/install/lib`. Second, after that library was loaded,
the V3 source had lost the validated VGR legacy wind-layout parser and was
reading the no-header double arrays from the wrong offset, producing `inf`
wind vectors. The generator was corrected and pushed as `ff30740`; the
library and `filament_simulator` were rebuilt as an ABI-consistent pair after
restoring the parser. The same-route raw `iteration_100` hashes now differ
(`1234`: `e4fad6...0a85`; `20260915`: `ae3151...1284`), and the source query
changes from `19.4250` to `18.3227` ppm while the wind query remains finite.
The bounded independent-realization premise is therefore open. The full
runtime evidence is in `experiments/avesm_seed_runtime_audit.json` and
`experiments/avesm_current_runtime_coverage_result.json`.

## Cross-fitted current-runtime mechanism gate (2026-09-15)

To test the actual AVESM object, I used four short current-runtime histories:
candidate A and fixed rival B, each with training seed `1234` and held-out
seed `20260915`, all on the same occupancy-only serpentine route. Each
candidate's distance-stratified Bernoulli predictive model was fitted only on
its training realization, then evaluated on its held-out realization. The
held-out rival-minus-true margins were positive for both A (`142.56`) and B
(`58.01`), but the untempered model did not pass: the A null e-process
crossed `log(20)` and the B permutation did not reduce the margin. A fixed
power-tempered factor was then tested as the single repair: `e'_t=e_t^κ` with
`κ=0.1`. This is not an arbitrary score tweak: for a valid base e-value,
concavity gives `E[e_t^κ] <= E[e_t]^κ <= 1`, so the anytime-valid expectation
bound is preserved. With the predeclared `0.001 ppm` event threshold and 100
deterministic time permutations per held-out realization, the repaired gate
passed every bounded check: A/B margins `23.04/7.51`, permutation mean
absolute margins `4.50/1.73`, permutation threshold-cross rates `0/0.04`, no
held-out null crossing, and exact candidate-list reordering error below
`1e-12`. The machine-readable result is
`experiments/avesm_current_runtime_gate_result.json` and the implementation is
`experiments/avesm_current_runtime_gate.py`.

This establishes a bounded mechanism result for **κ-tempered cross-fitted
AVESM**, not a full PMFS confirmation: it uses one House, two candidates, and
one held-out seed per candidate. The untempered AVESM failure is retained as a
real ablation, and no cross-house or closed-loop claim is opened until this
same repaired mechanism passes a fresh held-out asset.

## Closed-loop action/observation smoke (2026-09-15)

The current ROS workspace has no AVESM call site; its online stop component is
the older `CP_Stopping` path. I therefore ran a transparent physical-runtime
emulator, not a disguised ROS result. The controller selected each next pose
from the current AVESM map, queried the repaired GADEN realization at that
pose, updated the sensor state and e-process, and applied the same stopping
rule.

The result is a hard closed-loop NO-GO. In the A-source realization
`(-0.6,1.95)`, the controller stopped at step 23 with posterior weight 1.0 on
the fixed wrong candidate B and final error `4.854 m`; path length was only
`1.634 m`. It made exactly the same decision in the B-source realization, so
it succeeds only when B is actually true. The trace and combined result are in
`experiments/avesm_closed_loop_evidence/`, and the emulator is
`experiments/avesm_closed_loop_emulator.py`.

Conclusion: the κ-tempered AVESM map gate is positive offline, but its current
action policy does not transfer to closed-loop localization. The main
innovation cannot yet be claimed as a closed-loop performance improvement.
