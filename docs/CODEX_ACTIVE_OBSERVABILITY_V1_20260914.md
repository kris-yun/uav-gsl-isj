# Codex continuation — observability-first route premise

Start from branch `codex/dual-uav-two-point-premise-20260913`
HEAD `3cf57c079411d03205c820d9cc1f2dc5281083e4`.

## Frozen facts
- SAME_FRAME_DUAL_TRACE = PASS
- SIGNED_TWO_POINT_INCREMENT = NO_GO_AS_MAIN_INNOVATION
- PER_WIND_SIGMA3_SIGMA1 ≈ 6.8e-4 … 1.4e-3 << 0.05
- HELD_WIND_SIGNED_SOURCE_IDENTITY = 2/4
- ORDINARY_D2_SOURCE_IDENTITY = 1/4
- TIME_MISMATCH_5S = 3/4
- CAUSAL_LOCALIZATION_CLAIM = NOT_AUTHORIZED

Do not rescue the signed-increment method.

## Phase A — explain the 5 s mismatch without gas

Using only frozen plus/minus trajectories and recorded local wind:

1. Scan geometry-only lags from -10 s to +10 s and compute
   `median ||x_plus(t)-x_minus(t+lag)||` plus 10/90 percentiles.
2. Report the best geometry-only lag, distance at 0 s, distance at 5 s.
3. Compute the motion revisit timescale from the 2 m baseline projected along robot motion and route speed. Explicitly report the reference `2.0/0.35 ≈ 5.71 s`.
4. Compute wind-advection timescales from frozen baseline and deployable local wind: median/IQR/10/90 percentile of `|b|/|u|`, plus signed projected timescale where valid.
5. Classify the previous 5 s improvement only as:
   `MOTION_REVISIT_CONFOUND_SUPPORTED`, `ADVECTIVE_TIMESCALE_COMPATIBLE`, or `UNRESOLVED`.

No lag-based localization algorithm is authorized.

## Phase B — persistent-excitation source observability

Hypothesis: the dominant failure is insufficient physical excitation of source directions. Test whether sensing-trajectory design can restore a well-conditioned source-response operator before any posterior assimilation.

Use only the existing four source interventions on DESIGN winds `W_fast + W_slow`.
`W_altfast` is forbidden until exactly one route is frozen and pushed.

Keep House02 map, raw caches, source coordinates, altitude, FOPDT, 150 s duration, 0.2 s cadence, kinematic limits, and 2 m dual-UAV separation unchanged. No new GADEN.

Generate a bounded deterministic route-candidate set using only map and kinematic constraints. Freeze/push the candidate manifest before source-response scoring.

For each route and design wind, form the four-source processed-response matrix, center across sources, and compute `sigma1 >= sigma2 >= sigma3`.

Rank routes lexicographically:
1. number of design winds with rank 3;
2. worst-design-wind `sigma3/sigma1`;
3. weakest-mode physical energy / existing `Q_energy`;
4. minimum source exposure and temporal coverage;
5. path cost as final tie-breaker.

Reuse historical gates without relaxation:
- rank 3 in each design wind;
- `sigma3/sigma1 >= 0.05`;
- `Q_energy >= 0.01`;
- no exact source-pair collision;
- every source exposed in at least two temporal thirds.

If none passes within the frozen budget:
`OBSERVABILITY_FIRST_ROUTE_PREMISE = NO_GO`.

If one passes, freeze exactly one route and push its manifest/hash before opening `W_altfast`.

Held-wind gate: all four source identities must be rank-1 on `W_altfast` using the same simple evaluator as before. Do not invent a new likelihood.

Compare the old geometry-only route and the new route with the same S1-center and ordinary-D2 inference.

If the same inference succeeds only after measurement redesign, conclude only:
`MEASUREMENT_GEOMETRY_PERSISTENT_EXCITATION_IS_LOAD_BEARING`.

Do not yet call it novel. First perform a collision audit against infotaxis/informative path planning, model-based adaptive exploration/OED in GSL, multi-robot formation search, NeurIPS 2025 PhySense, and 2026 sensor-placement/OED work.

Potential novelty claim to test, not assume:
“worst-case source-intervention observability / persistent-excitation design that prevents rank collapse of the source-response operator across transport regimes before Bayesian assimilation.”

## Prohibited
No network, posterior tuning, closed loop, new GADEN, new thresholds, online source truth, causal-localization claim, or cross-dataset claim.

## Final fields
branch
starting SHA
final SHA
TIME_MISMATCH_FORENSIC
DESIGN_WIND_OBSERVABILITY
FROZEN_ROUTE_STATUS
HELD_WIND_SOURCE_IDENTITY
BASELINE_COMPARATOR
NOVELTY_COLLISION_STATUS
FINAL_VERDICT

Then stop and return to GPT.
