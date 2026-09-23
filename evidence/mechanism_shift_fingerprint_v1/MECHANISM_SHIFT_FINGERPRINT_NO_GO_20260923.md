# Mechanism-shift fingerprint pre-audit — authoritative R2

Date: 2026-09-23  
Status: **NO-GO despite 5/6 apparent rank improvements**

## Mother idea

Recent world-model / causal-representation work emphasizes that under changing latent environments the useful object may be the **transformation rule of the mechanism across environments**, not a single static input-output map. This is relevant to PMFS because absolute candidate hit maps repeatedly fail source identity under model mismatch.

We therefore test a deliberately simple, training-free necessary condition: does a candidate source have a source-specific **operator response fingerprint** across the five online PMFS source updates?

## Frozen test

All six authoritative R2 House x seed runs, source updates 1–5.

- use authoritative final-partition leaf candidates;
- use only measurement cells supported in all five updates (126–140 cells/run);
- anchor each final candidate by its Native sampled source point and map that point to the finest candidate region at every earlier update;
- assemble observed and simulated 5 x cell matrices;
- subtract each cell's five-update mean, so the score sees only the way the field changes across update/environment state;
- primary fingerprint score: confidence-weighted normalized Frobenius/cosine agreement between the observed and candidate response matrices;
- controls: current-update Native likelihood on the same common support and a static five-update mean-field cosine score.

No coefficients, windows, or thresholds are fitted.

### Exact destructive null

Enumerate all 5! = 120 update-label permutations of the simulated response matrix. Each permutation preserves every candidate/update/cell value and therefore all marginal variation magnitudes, but breaks the alignment between the observed environment sequence and the simulated environment sequence.

A mechanism-shift interpretation requires the identity alignment to give a truth-source rank that is unusually good under this exact null (p <= 0.05).

## Results

| run | N | current | static mean | mechanism fingerprint | exact permutation p |
|---|---:|---:|---:|---:|---:|
| House01 seed0 | 123 | 60.5 | 88.5 | 59.5 | 0.4667 |
| House01 seed1 | 121 | 98.0 | 100.0 | 57.0 | 0.4000 |
| House02 seed0 | 123 | 84.0 | 100.0 | 80.0 | 0.8500 |
| House02 seed1 | 119 | 95.0 | 93.0 | 91.0 | 1.0000 |
| House03 seed0 | 160 | 90.0 | 95.0 | 61.0 | 0.3000 |
| House03 seed1 | 160 | 92.0 | 81.0 | 105.0 | 0.8083 |

Surface result:
- fingerprint beats current: **5/6**;
- fingerprint beats static mean: **5/6**.

Load-bearing test:
- exact update-alignment permutation gate: **0/6**.

Most score-vs-negative-truth-distance correlations are also weak or negative, so the rank changes do not form a robust spatial source-identity signal.

## Verdict

The 5/6 apparent improvement is **not evidence for a source-specific mechanism-shift law**. The correct environment/update alignment is not special; arbitrary permutations frequently do as well or better. The score is exploiting generic variation magnitude/geometry rather than a source-specific transformation rule.

Do not tune centering, weighting, similarity metric, or choose a favorable subset of updates to rescue this test. A future mechanism-shift route would require a new observable in which the environment state itself is physically identified rather than using update index as a proxy.

Machine-readable results: `MECHANISM_SHIFT_FINGERPRINT_PREAUDIT_R2.csv`.
