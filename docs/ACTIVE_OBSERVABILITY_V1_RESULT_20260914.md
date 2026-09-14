# Active observability V1 result

Date: 2026-09-14

Branch: `codex/dual-uav-two-point-premise-20260913`

Starting SHA: `3cf57c079411d03205c820d9cc1f2dc5281083e4`

Pre-response freeze SHA: `6d5ea8fc0e67990f7750c7e86b010368dda88221`

## Decision

```text
TIME_MISMATCH_FORENSIC = MOTION_REVISIT_CONFOUND_SUPPORTED
DESIGN_TRACE_INTEGRITY = PASS
OBSERVABILITY_FIRST_ROUTE_PREMISE = NO_GO
FROZEN_ROUTE_STATUS = NONE_NO_DESIGN_CANDIDATE_PASS
HELD_WIND_SOURCE_IDENTITY = NOT_RUN_W_ALTFAST_UNOPENED
NOVELTY_COLLISION_STATUS = NOT_RUN_MECHANISM_PREMISE_FAILED
```

## Five-second mismatch forensic

The geometry-only lag scan does not support a plume-advection interpretation of the previous 5 s improvement. Across the three winds, the baseline projected along vehicle motion gives a median revisit timescale of 4.04 s and upper quartiles of 5.48 to 5.63 s; the full-baseline reference is `2/0.35 = 5.714 s`. At a +5 s shift, the 10th-percentile plus-to-shifted-minus separation falls from 2 m to 0.47–0.55 m.

The corresponding median `|b|/|u|` wind-advection times are 104.3 s (`W_fast`), 228.9 s (`W_slow`), and 475.3 s (`W_altfast`). The best median-distance geometry lags are 1.8, 1.8, and 2.4 s rather than exactly 5 s, so motion revisit is a supported confound rather than a proof of causation. No lag-based method is authorized.

## Candidate freeze and integrity

Twelve routes were generated without gas values, source identity, or source coordinates. Deterministic farthest-point starts and fixed DFS neighbor orders provide a bounded map-only candidate set. Every candidate preserves 0.4 m altitude, 0.35 m/s speed, 150 s duration, 0.2 s cadence, and a 2 m dual-receiver formation.

Native GADEN validation covered 63,000 center/endpoint positions and 27,000 receiver corridors with zero failures. The candidate set, analysis policy, query code, and score code were pushed before any source response was queried.

The design query used only `W_fast` and `W_slow` from the existing caches. It produced 96 traces and 72,000 rows. Independent verification reproduced every route coordinate and FOPDT value exactly. No `W_altfast` trace was created or read.

## Design-wind observability

None of the 12 routes passed. The old geometry-only route is exactly candidate `AO_00` by SHA-256 and remains the top lexicographic candidate; no redesigned route displaced it.

For `AO_00`:

| Design wind | Rank | sigma3/sigma1 | Maximum corrected Q_energy | Zero-exposure sources |
|---|---:|---:|---:|---|
| W_fast | 3 | 0.0006091 | 6.80e-8 | S_k01, S_k22 |
| W_slow | 2 | 4.42e-17 | 1.78e-16 | S_k01, S_k22 |

The required gates are `rank=3`, `sigma3/sigma1>=0.05`, `Q_energy>=0.01`, no collision, and every source exposed in at least two temporal thirds for both design winds. The observed weakest-direction ratios and energies miss the thresholds by many orders of magnitude, and every candidate has at least one completely unexposed source-wind case. Several candidates produce identically zero four-source responses over an entire wind.

The frozen scorer initially emitted tiny negative `Q_energy` values below `4e-17` for a few zero-information cases because of eigensolver round-off on a theoretically positive-semidefinite matrix. The reporting code was corrected to clamp these values at zero. The formula, threshold, route ranking, zero passing count, and null selection did not change; the correction is recorded separately.

## Scientific interpretation

This bounded experiment does not establish that every possible House02 path is uninformative. It establishes that a precommitted, spatially diverse set of 12 map-only routes cannot repair the source-response rank collapse under the existing 150 s, single-channel sensor and transport conditions. Because no design-wind route passed, selecting one for `W_altfast` would violate the contract. Held-wind evaluation and novelty collision search were therefore not run.

The persistent-excitation route idea is not supported as the next main innovation in its current form. The evidence points to a sensing-support limitation: some source/transport combinations do not reach the admissible route set strongly enough within the fixed horizon. Further posterior, causal-score, differencing, or route-ranking modules cannot create that missing physical exposure. The next scientific decision should concern the sensing modality, response time, horizon, or validation environment, not another inference-layer repair.
