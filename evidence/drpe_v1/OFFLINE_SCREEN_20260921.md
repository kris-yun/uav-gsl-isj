# DRPE V1 offline screen — 2026-09-21

Status: **POSITIVE DEVELOPMENT SIGNAL / CLOSED-LOOP PILOT AUTHORIZED**.

This is not a final publication result. The same six seeds used here are
development data and cannot serve as the confirmatory closed-loop test.

## Data and endpoint

Input: the frozen TNQC R2 House01/02/03 x seed0/1 300-s native trajectories.

The source endpoint is the original PMFS top-5% probability-weighted
ExpectedValue. A local C++ clone of the frozen `std::sort` endpoint semantics
reproduced all six native errors within approximately 2e-7 m before any new
screen was evaluated.

The DRPE screen uses leave-one-House-out supervised candidate scoring and maps
the score back to the original native posterior by a bounded exponential tilt.

## Primary comparison

| Case | Native m | Exponential-onset m | DRPE onset m | Native -> DRPE |
|---|---:|---:|---:|---:|
| H01/s0 | 5.527347155 | 5.483334089 | 5.441234760 | +1.5580% |
| H01/s1 | 4.001642364 | 3.968738734 | 3.956581813 | +1.1261% |
| H02/s0 | 4.107022746 | 4.045324958 | 4.034832886 | +1.7578% |
| H02/s1 | 3.700743269 | 3.683478151 | 3.689225686 | +0.3111% |
| H03/s0 | 7.782054929 | 7.767597737 | 7.747248202 | +0.4472% |
| H03/s1 | 8.211551290 | 8.200428760 | 8.146145112 | +0.7965% |

Pooled means:

- native: 5.555060292 m
- matched exponential-onset: 5.524817071 m
- DRPE onset: **5.502544743 m**

DRPE vs native pooled reduction: **0.94536%**.

DRPE improves all 6/6 development cases relative to native.

DRPE is better than the matched exponential-onset representation in 5/6
cases and improves its pooled mean by approximately 0.403%.

## Ablations supporting the secondary innovations

### WOST: onset-only sparse transduction

DRPE using hit + onset + blank resonant channels:

`5.522770875 m`

DRPE using only whiff-onset resonant channels:

`5.502544743 m`

The onset-only representation is therefore retained. Dense hit/blank neural
channels are rejected.

### WRRR: wind-relative resonant readout

Onset DRPE with distance-only candidate geometry:

`5.528133385 m`

Onset DRPE with the full wind-relative candidate geometry:

`5.502544743 m`

The wind-relative projection is retained.

## Rejected additions

The following were screened and are **not** part of DRPE V1:

- Fractional-order plume memory: candidate-ranking signal did not translate
  into superiority over ordinary exponential memory on the native endpoint.
- Difference predictive coding: improved some H01/H02 true-source ranks but
  failed badly on H03.
- Multi-order fractional bank: no consistent endpoint advantage.
- Resonant branch pruning: all three fixed branches performed best.
- Refractory whiff consolidation: no improvement.
- Adaptive resonance threshold/spiking: no improvement.

These negative screens are important: DRPE V1 is intentionally small.

## Important limitation

The observed effect is consistent but small (~0.95% pooled). One previously
measured H01 native repeat differed by about 0.062 m, comparable to the scale
of the expected DRPE gain.

Therefore this screen authorizes only a **new-seed closed-loop pilot**, not a
claim that DRPE is already effective online.

## Promotion rule

Closed-loop confirmation must:

- train/freeze each held-out-House readout before test runs;
- use new seeds/realizations, not seed0/1;
- preserve the R2 300-s endpoint;
- include native and DRPE arms;
- make no parameter changes after new-seed results are observed.

See `docs/DRPE_V1_CLOSED_LOOP_PILOT_20260921.md`.
