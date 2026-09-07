# CSTAR current-runtime M1 screen — 2026-09-07

## Decision

`M1_CONTROLLED_SCREEN_NO_GO` remains the honest result after repairing the
environment contract. This is not a simulator crash or a missing-output result.

## What was repaired

- The old frozen raw realization was not mixed with the VM's current GADEN 3.x
  runtime. A one-second reproduction smoke documented the nonidentity.
- A new self-consistent dataset was generated with one current runtime,
  `GADEN_RNG_SEED=1234`, gas type 10, the fixed sensor contract, and the same
  source-blind map-derived route rule.
- Each House has two source positions crossed with two transport conditions
  (fast/slow), giving 12 cases. Source coordinates are evaluator-only.
- The 60 s route was found to be plume-observability limited. A preregistered
  240 s map-cover route was therefore used to remove the all-zero-history
  artifact. The 240 s histories have nonzero observations in all 12 cases.

## Results

| screen | H01 | H02 | H03 | verdict |
|---|---:|---:|---:|---|
| 60 s, current runtime | fail | fail | fail | `M1_CONTROLLED_SCREEN_NO_GO` |
| 240 s, current runtime | partial | fail | fail | `M1_CONTROLLED_SCREEN_NO_GO` |

The 240 s screen used the fixed geometry-normalized, coordinate-equivariant,
paired-posterior-consistency and radial-score configuration. It was run once
with the frozen seed 12. No additional seeds, outcome-driven thresholds,
planner weights, or rescue tuning were used.

## Interpretation

The new evidence supports a narrower claim only: M1 can change source
representations and improve localization in some held-out conditions. It does
not yet establish a cross-House causal source-inference gain. In particular,
the required combination of proper-score improvement, source invariance,
intervention destruction, and uncertainty control is not stable across H02/H03.

M2 was not inferred from this bundle: it contains M1 crossed source/transport
histories but no route-outcome cases. `M2_BASELINE_SCREEN.json` is therefore
explicitly marked `NOT_RUN`.

## M1-v2 architecture audit

The follow-up implementation added a strict source stream: `zS` receives only
measured response, response EMA, and sampling position; wind, time, and the
measurement flag are excluded from the source stream. A fixed event-weighted
pooling variant was then evaluated to avoid diluting sparse plume responses in
the 240 s history.

This repaired the intended representation boundary and improved held-out
NLL/XY error in H01/H02, but the full causal gate still failed:

| variant | H01 | H02 | H03 | verdict |
|---|---:|---:|---:|---|
| strict source stream | fail | fail | fail | `M1_CONTROLLED_SCREEN_NO_GO` |
| strict + event-weighted | fail | fail | fail | `M1_CONTROLLED_SCREEN_NO_GO` |

The result is a useful negative mechanism finding: source-stream separation can
improve prediction without establishing cross-House causal invariance. The
implementation should not be promoted to a main-innovation PASS.

## Evidence

- `evidence/cstar_crossed_generator_smoke_20260907/REPORT.json`
- `evidence/cstar_current_runtime_screen_20260907_v3/M1_SCREEN.json`
- `evidence/cstar_current_runtime_screen240_20260907/M1_SCREEN.json`
- `evidence/cstar_current_runtime_screen240_strict_20260907/M1_SCREEN.json`
- `evidence/cstar_current_runtime_screen240_strict_event_20260907/M1_SCREEN.json`
- `evidence/cstar_current_runtime_assets240_20260907/MANIFEST.json`
- `evidence/cstar_current_runtime_routes_cover240_20260907/ROUTE_RULE.json`
