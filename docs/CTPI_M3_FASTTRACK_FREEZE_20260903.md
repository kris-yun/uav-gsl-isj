# CTPI M3 Fast-Track Freeze — 2026-09-03

## Scientific status at entry

- M1 CREL/F00: PASS. The passing runtime identity is the raw route-event/count-only F00 path formerly represented by `cpir_a1`; the CTPI runtime exposes the same frozen source-inference operator as `ctpi_f00`, `ctpi_f10`, and `ctpi_f11`.
- M2 TSDC V0: fresh-confirm PASS on 30 new worlds / 450 events. Frozen TSDC source file SHA-256: `854a2fc8513201cdb2ae497a62c0cd3c5fa09fdae2f1bc309ad594a8b1aaacf7`.
- M3 PIP: this document freezes the first true-closed-loop implementation and Gate. No new M2/M3 training data are authorized.

## M3 — Predictive Information Planning (PIP)

At decision time t, M1 supplies the current source posterior `pi_t(s)`. For each candidate action `a`, the frozen full-grid transport bank provides 8 source-conditioned future raw physical dwell-reach events, summarized by `K_t(s,a) in {0,...,8}`. This is the same raw-physical-event object used to construct `q_raw` in the confirmed M2 experiment; the TSDC sensor-memory coordinate is added afterwards rather than running a second FOPDT member model.

F10 raw forecast:

`q10(s,a) = (K_t(s,a)+0.5)/9`.

F11 TSDC forecast:

`q11(s,a) = TSDC_V0(K_t(s,a), M_t)`,

where `M_t` is the measured detector state at the end of the most recently completed sensing dwell and TSDC V0 is frozen from the already-passed M2 confirmatory Gate.

The M3 score is

`J(a) = H(sum_s pi_t(s) q(s,a)) - sum_s pi_t(s) H(q(s,a)) = I(S;Y_next | a,M_t)`.

No source truth, localization error, future measured gas, posterior temperature, planner weight, or outcome-tuned coefficient enters `J`.

## Action domain

The action domain is the union of PMFS's existing `openMoveSet` and the native PMFS goal for the same decision. Including the native goal creates an exact truth-blind sanity contract: whenever the native goal is forecastable, the selected M3 action must have `J(selected) >= J(native)`.

Tie-break only: if information scores are equal within `1e-12`, choose smaller existing PMFS `distanceFromRobot`, then lexicographic grid index. Travel cost never trades against information with a tuned weight.

## Forecast horizon

- bank time step: 0.2 s;
- dwell: 80 samples = 16 s;
- horizontal speed used only to map existing `distanceFromRobot` to a future bank time: frozen 0.4 m/s;
- prediction start index: `last_observed_time_index + 1 + ceil(distance/0.4/0.2)`;
- a candidate whose full 80-sample dwell exceeds the 1500-sample bank is not forecastable;
- closed-loop evaluation horizon is frozen to 240 s for every arm, leaving bank headroom rather than extrapolating beyond support.

TSDC V0 itself remains unchanged and does not acquire travel time as a new feature. If transfer later fails because candidate transit changes sensor memory in a way not represented by V0, that is a failure mechanism to report, not a parameter to add after seeing the closed-loop result.

## Factorial arms

- A0: authoritative native PMFS.
- F00: frozen M1 CREL/F00 + native planner.
- F10: frozen M1 + raw finite-8 forecast + M3 PIP.
- F11: frozen M1 + frozen M2 TSDC + exactly the same M3 PIP.

Increment claims:

- M1: F00 vs A0.
- M3: F10 vs F00.
- M2 downstream robot-task increment: F11 vs F10.

## Fast-track sequence

1. VM materialization, patch application, compile/runtime parity.
2. H01 seed0 F00/F10/F11 true-closed-loop smoke.
3. If smoke causal chain and both M3 action sanity checks PASS, run H01 seeds0-2 A0/F00/F10/F11 (12-run screening set).
4. If the frozen H01 screen PASS, run new seeds3-5 on H01/H02/H03 x A0/F00/F10/F11 = 36-run confirmatory set.
5. Do not start a larger run if any preceding Gate is NO-GO.

## Non-negotiable runtime evidence

For F10/F11 each decision logs current causal detector state, candidate count, native goal and native information, selected goal and selected information, travel distance, prediction start index, and whether the action changed.

The smoke must establish:

- navigation command exists;
- motion feedback exceeds 0.05 m;
- fresh sensor stream exists;
- posterior trace contains at least two states and changes;
- M3 selected goal appears in navigation command trace;
- F10 and F11 trajectories each differ from F00 at least once;
- no fixed historical trajectory replay is used.

## Performance boundary

All task metrics are evaluated at a common 240 s horizon from `source_estimate_trace.csv` using the logged `POSTERIOR_MAP` estimate. This is a closed-loop robot-task endpoint and must not be silently described as the earlier offline top-set endpoint.

The 36-run paired confirmation uses nine House/seed pairs and an exact 2^9 sign-flip randomization test on the continuous paired improvement. No asymptotic p-value and no post-outcome Gate change are allowed.

## Current limitations

This is a prepared-site, frozen-bank closed-loop test. It does not establish bank-free deployment on an unseen site. The bank-free CREL provider remains a separate deployment Gate.
