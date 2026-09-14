# Codex continuation — sensing-support upper-bound diagnostic

Date: 2026-09-14

Branch: `codex/dual-uav-two-point-premise-20260913`

Start from audited HEAD: `1be4363959fcf7909e935568bb74d0a0dbd4328b` (`record observability-first route premise no-go`).

## 0. Frozen conclusion from the previous stage

Treat the following as final and do not rescue or reinterpret them:

```text
TIME_MISMATCH_FORENSIC = MOTION_REVISIT_CONFOUND_SUPPORTED
DESIGN_TRACE_INTEGRITY = PASS
OBSERVABILITY_FIRST_ROUTE_PREMISE = NO_GO
DESIGN_WIND_OBSERVABILITY = NO_GO_0_OF_12
FROZEN_ROUTE_STATUS = NONE_NO_DESIGN_CANDIDATE_PASS
HELD_WIND_SOURCE_IDENTITY = NOT_RUN_W_ALTFAST_UNOPENED
CAUSAL_LOCALIZATION_CLAIM = NOT_AUTHORIZED
CROSS_DATASET_CLAIM = NOT_AUTHORIZED
```

The best route remained `AO_00`, exactly equal to the old route by SHA-256. On `W_fast`, rank was 3 but `sigma3/sigma1=6.0906e-4`, maximum corrected `Q_energy=6.7995e-8`, and `S_k01/S_k22` had zero exposure. On `W_slow`, rank fell to 2, `sigma3/sigma1=4.4223e-17`, maximum corrected `Q_energy=1.7835e-16`, one exact source-response collision occurred, and `S_k01/S_k22` again had zero exposure.

The previous stage therefore points to a sensing-support limitation, not an inference-layer failure. Do not tune route ranking, posterior, likelihood, thresholds, lag, or causal score to rescue it.

## 1. New scientific question

Run a **sensing-support upper-bound（感知支撑上界） diagnostic** on the already frozen 12 map-only routes to determine which physical measurement restriction is responsible for the observability collapse:

1. finite sensor response dynamics (FOPDT),
2. single-channel center sensing,
3. or neither of the above within the fixed 150 s horizon.

This is a diagnostic/falsification stage, not yet a main-innovation claim.

## 2. Hard invariants

Keep unchanged:

- House02 map and all existing raw caches;
- four frozen source interventions: `S_truth`, `S_k01`, `S_k10`, `S_k22`;
- DESIGN winds only: `W_fast`, `W_slow`;
- candidate routes exactly `AO_00` ... `AO_11` from the pre-response freeze SHA `6d5ea8fc0e67990f7750c7e86b010368dda88221`;
- 0.4 m altitude, 0.35 m/s speed, 150 s duration, 0.2 s cadence;
- 2 m plus/minus formation geometry and the native geometry audit;
- original FOPDT parameters `dead_s=0.4`, `rise_s=1.2`, `recovery_s=1.2`, `dt_s=0.2`;
- source-response centering convention and the historical rank / conditioning / energy gates.

Forbidden during this stage:

- `W_altfast` concentration/source-response query or read;
- new GADEN simulation;
- new routes or source-aware route design;
- new source coordinates used for design;
- threshold relaxation;
- posterior tuning, new likelihood, neural network, closed loop, lag-based localization;
- causal-localization or cross-dataset claims.

`W_altfast` may remain visible only in the already-frozen Phase-A geometry/wind forensic artifacts. Do not read or generate any held-wind gas/source-response trace.

## 3. Pre-response audit first

Before computing the new source-response scores:

1. Verify that all 12 candidate center routes and their plus/minus endpoint trajectories are byte/coordinate identical to the pre-response frozen candidates.
2. Re-run or independently verify native GADEN geometry feasibility for center, endpoints, and receiver corridors; report maximum coordinate discrepancy and failure counts.
3. Verify the raw-cache query path can return center / plus / minus concentration at the frozen coordinates without using source identity except as the intervention file selector.
4. Write and push a measurement-policy freeze file **before inspecting aggregate source-separation scores**.

Required file:

`experiments/sensing_support_upper_bound_v1/MEASUREMENT_POLICY_FREEZE.json`

It must contain hashes of the candidate manifest, code used to query/process traces, definitions below, all gates, and the current commit SHA.

## 4. Measurement configurations

Evaluate the same 12 routes under four precommitted configurations. Do not invent additional configurations after looking at results.

### C0 — center + FOPDT (reference only)

`S1_CENTER_PROCESSED_FOPDT`

Reproduce the already-frozen baseline result. This is an integrity comparator, not a new experiment.

### C1 — center + raw instantaneous concentration

`S1_CENTER_RAW_ORACLE`

Use the simulator concentration at the center before FOPDT. This is an **oracle upper bound（理想上界）** used only to test whether sensor response dynamics destroy source information. It is never eligible for a deployment/novelty claim and never opens `W_altfast`.

### C2 — plus/minus two-channel + FOPDT

`D2_TWO_CHANNEL_PROCESSED_FOPDT`

At every frozen timestamp form the measurement feature as the ordered pair

```text
y(t) = [c_plus_FOPDT(t), c_minus_FOPDT(t)]
```

Do **not** subtract the channels and do not compress them to a signed increment. Preserve both channels as independent measurements. This is the only new configuration in this stage that is eligible to become a deployable candidate.

### C3 — plus/minus two-channel + raw instantaneous concentration

`D2_TWO_CHANNEL_RAW_ORACLE`

Use

```text
y(t) = [c_plus_raw(t), c_minus_raw(t)]
```

This is an oracle upper bound for the combined effect of spatial measurement geometry + zero sensor lag. It is diagnostic only and never opens `W_altfast`.

## 5. Source-response operator and gates

For every configuration, route, and design wind, construct the four-source response feature matrix using the exact same source ordering. For C2/C3, concatenate the two ordered receiver channels in feature space; do not average or difference them.

Center across the four source interventions and compute the singular values `sigma1 >= sigma2 >= sigma3` of the source-response operator. Maximum relevant rank remains 3 after source-centering.

Reuse the previous gates **without relaxation** for both design winds:

```text
rank = 3
sigma3/sigma1 >= 0.05
Q_energy >= 0.01
no exact source-pair collision
every source exposed in at least two temporal thirds
```

For C2/C3 exposure, a source is exposed at a timestamp if **either** physical receiver exceeds the frozen `0.1 ppm` hit floor. Report plus-only, minus-only, union, and overlap counts so this union rule cannot hide a dead channel.

For C2/C3 exact collision, compare the full ordered two-channel source-response feature vectors.

For C2/C3 `Q_energy`, use the same source-centering projection and accumulated moment definition as the frozen scorer after concatenating the two receiver channels. Use only the frozen 5 s and 10 s windows and require the maximum corrected value to meet the same `0.01` gate.

Do not change numerical rank tolerance. Any PSD round-off correction must use the already-recorded clamp-to-zero rule only.

## 6. Required attribution logic

The purpose is mechanism attribution, not winner fishing. Report the following exactly from the design-wind results:

### Case A — C1 passes but C2 fails

Interpretation:

`SENSOR_RESPONSE_DYNAMICS_IS_PRIMARY_BOTTLENECK_SUPPORTED`

Raw center sensing contains enough information, while deployable two-channel FOPDT does not. Stop. Do not open `W_altfast`.

### Case B — C2 passes on at least one frozen route

Interpretation:

`MULTICHANNEL_MEASUREMENT_GEOMETRY_IS_LOAD_BEARING_CANDIDATE`

Freeze exactly one C2 route using the same lexicographic route ranking as before and push its route/config manifest + hashes **before** any held-wind response is read. Only then may a later stage test `W_altfast`; do not run held wind in this commit unless the freeze is separately committed first.

### Case C — only C3 passes

Interpretation:

`JOINT_GEOMETRY_AND_SENSOR_DYNAMICS_LIMITATION_SUPPORTED`

The deployable FOPDT configuration still fails. Stop. Do not open `W_altfast`.

### Case D — C1, C2, and C3 all fail

Interpretation:

`SENSING_SUPPORT_150S_PREMISE = NO_GO`

The 150 s support limitation survives removal of sensor lag and addition of two-channel geometry. Stop. The next experiment may investigate horizon/support extension, but do not redesign the horizon in the same response-aware commit.

If multiple diagnostic configurations pass, report all of them. Do not suppress evidence to force a single narrative. C2 is the only deployable candidate in this stage.

## 7. Required outputs

Create under:

`experiments/sensing_support_upper_bound_v1/`

At minimum:

- `MEASUREMENT_POLICY_FREEZE.json`
- `TRACE_INTEGRITY_AUDIT.json`
- `C0_REFERENCE_REPRODUCTION.json`
- `C1_CENTER_RAW_ORACLE.json`
- `C2_D2_PROCESSED_FOPDT.json`
- `C3_D2_RAW_ORACLE.json`
- `CONFIGURATION_COMPARISON.json`
- `FINAL_GATE.json`
- `PRE_RESPONSE_SHA256SUMS`
- `FINAL_SHA256SUMS`

Also add a concise result note under `docs/` with the exact scientific interpretation and no novelty inflation.

Required final fields:

```text
branch
starting_SHA
pre_response_freeze_SHA
final_SHA
TRACE_INTEGRITY
C0_REFERENCE_REPRODUCTION
C1_CENTER_RAW_ORACLE
C2_D2_PROCESSED_FOPDT
C3_D2_RAW_ORACLE
PRIMARY_BOTTLENECK_ATTRIBUTION
DEPLOYABLE_C2_ROUTE_STATUS
HELD_WIND_STATUS
FINAL_VERDICT
```

## 8. Stop conditions

Stop immediately and return to GPT after the design-wind diagnostic and committed artifacts.

Do not run `W_altfast` in the same stage. Even if C2 passes, first freeze/push exactly one route/config and return.

Do not claim a main innovation yet. A successful C2 result would establish only that preserving two spatial channels is load-bearing under the frozen design winds; novelty and held-wind generalization remain separate gates.
