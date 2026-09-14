# Source-response support extension mechanism v1

Date: 2026-09-14  
Branch: `codex/dual-uav-two-point-premise-20260913`

Status: **FROZEN BEFORE EXTENDED RESPONSE QUERY**

## 1. Purpose

The frozen 150 s sensing-support upper bound failed for all four measurement
configurations, including raw dual-channel measurements. The subsequent
observability-aware student also failed on held `W_slow` and on the development
split. This contract tests one upstream physical mechanism only:

> Does extending the same deployable two-channel route beyond 150 s create
> enough source-response support to distinguish the four source interventions?

This is a mechanism test, not a claim that a longer route is the final main
innovation. No learning model, posterior repair, extra receiver, route scoring
or held-wind rescue is introduced here.

## 2. Frozen data and measurement conditions

- House: `House02`.
- Sources: `S_truth`, `S_k01`, `S_k10`, `S_k22`.
- Design winds: `W_fast`, `W_slow` only.
- Forbidden in this stage: `W_altfast`, any other wind, any source not listed
  above, and any source-dependent route selection.
- Route: deterministic map-only dual-UAV route, 2 m plus/minus aperture,
  altitude 0.4 m, speed 0.35 m/s, cadence 0.2 s.
- Measurement: ordered plus/minus channels retained separately; independent
  FOPDT states with dead time 0.4 s, rise 1.2 s, recovery 1.2 s; no differencing.
- Raw cache: the pre-existing immutable cache is used read-only. The route may
  query only frames `iteration_0` through `iteration_445`.
- Extended route horizon: `222.8 s`, giving exactly `1115` route samples at
  times `0.0, 0.2, ..., 222.8 s`; the last query maps to frame 445 under the
  frozen 0.5 s frame clock.
- No new GADEN simulation is run in this stage. This is an upper-bound reuse of
  already available source responses, not a new stochastic realization.

## 3. Route freeze rule

The candidate set is generated before any extended source response is read.
Candidate selection may use only:

1. the committed House02 occupancy grid;
2. map connectivity and collision-free edges;
3. 2 m endpoint feasibility;
4. the recorded deployable design-wind vectors only to choose the fixed
   cross-wind aperture angle;
5. the fixed duration, speed, altitude and cadence above.

It must not read gas data, source identities/coordinates, raw-cache frame
contents, previous response scores, or learning outputs. Twelve candidates are
required, with the same deterministic farthest-point starts and DFS neighbor
orders as the 150 s candidate generator. Candidate IDs are `AO_00` through
`AO_11`.

The route generator and all candidate bytes are hashed and committed before
the first extended response query.

## 4. Pre-registered response score

For each route and wind, form the ordered two-channel processed response vector
at each time by concatenating the plus and minus values for each of the four
source interventions. Let `Y` be the resulting time-window by source matrix.
For each endpoint window and for the full horizon, compute:

- numerical rank using the frozen rank tolerance from the 150 s score;
- `sigma3/sigma1` (zero when `sigma1` is zero);
- `Q_energy` using the same centered response-operator definition;
- minimum pairwise source-response distance;
- per-source exposure support and temporal-third coverage.

The implementation must reuse the frozen scoring definitions and record the
exact code hashes. It may not change thresholds after seeing the extended
responses.

## 5. Gate

The mechanism passes only if at least one of the twelve routes satisfies all
of the following on **both** `W_fast` and `W_slow` at the extended horizon:

- rank is at least 3;
- `sigma3/sigma1 >= 0.05`;
- `Q_energy >= 0.01`;
- no exact source-response collision;
- every source has nonzero exposure in at least two of the three equal time
  thirds.

The route must also show a strictly positive full-horizon rich score relative
  to its own 150 s prefix under the same definitions. This prevents a nominal
  pass caused only by numerical recomputation of the old prefix.

If no route passes, the result is
`SUPPORT_EXTENSION_MECHANISM_NO_GO` and the candidate main innovation remains
unconfirmed. If a route passes, this establishes only that the longer physical
support is load-bearing; a separate, frozen held-condition learning/planning
test is still required before any main-innovation claim.

## 6. Integrity and stopping rules

- No response query occurs before route and policy hashes are committed.
- No held wind is read.
- No new GADEN data is generated.
- No post-hoc route, window, threshold, FOPDT, or source selection is allowed.
- A failure is recorded as evidence, not repaired by tuning.
