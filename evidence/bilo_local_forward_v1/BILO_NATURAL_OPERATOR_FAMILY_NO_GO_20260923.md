# BiLO-style natural forward-operator family pre-audit — authoritative R2

Date: 2026-09-23  
Status: **NO-GO for advancing BiLO-style local forward adaptation as the main innovation from current evidence**

## Mother idea

The 2026 BiLO / Bayesian BiLO line replaces a fixed global forward surrogate with a forward operator that is adapted locally during inverse inference. This is mechanistically relevant to PMFS because the established failure is upstream of the Bayesian score: the fixed candidate forward family often assigns poor identity to the true source.

The PMFS transport kernel has genuine non-source physical nuisance parameters (including `deltaTime`, `noiseSTDev`, and the spatial wind field), so a local-forward-adaptation transfer is semantically possible. This pre-audit asks whether the existing data provide any evidence that **source-conditioned forward-operator variation** actually restores source identity before paying the cost of a new VM transport sweep.

## Frozen pre-audit

Authoritative R2, all six House x seed runs, source updates 1–5.

For each run:

- use the authoritative final-partition leaf candidates;
- restrict scoring to cells with positive measurement confidence in **all five** source updates (126–140 cells depending on run);
- anchor each final source hypothesis by its Native sampled source point;
- at each earlier update, select the finest candidate region containing the same source grid cell;
- compare the final measured field against that candidate's simulated hit field using the unchanged Native PMFS likelihood;
- the five update-specific forward maps are treated as a naturally occurring discrete forward-operator family.

Scores:

1. **current-common** — update 5 only, on the common support;
2. **shared operator** — one update index selected globally for all source hypotheses by source-marginal evidence;
3. **source-conditioned marginal** — uniform log-mean-exp over the five operator states for each source hypothesis;
4. **profile upper bound** — best of the five operator states separately for each source hypothesis.

The profile score is diagnostic only; the marginal score is the predeclared gate score.

### Destructive null

For updates 1–4 independently permute source labels while preserving each update's complete candidate-score distribution and leaving update 5 untouched. This destroys source↔operator consistency without flattening the score distribution. 500 repetitions.

Gate:

- marginal truth rank must beat current-common truth rank;
- marginal truth rank must beat the shared-operator truth rank;
- fraction of null truth ranks as good or better than actual must be <= 0.05;
- scores must remain non-degenerate.

## Results

| run | N leaves | current | shared | marginal | profile | null <= actual |
|---|---:|---:|---:|---:|---:|---:|
| House01 seed0 | 123 | 60.5 | 66.0 | 70.5 | 71.5 | 0.564 |
| House01 seed1 | 121 | 98.0 | 99.5 | 100.0 | 100.0 | 0.760 |
| House02 seed0 | 123 | 84.0 | 84.0 | 97.0 | 97.0 | 0.718 |
| House02 seed1 | 119 | 95.0 | 107.5 | 96.0 | 96.0 | 0.718 |
| House03 seed0 | 160 | 90.0 | 95.0 | 103.0 | 103.0 | 0.566 |
| House03 seed1 | 160 | 92.0 | 97.0 | 103.0 | 103.0 | 0.496 |

Summary:

- marginal beats current: **0/6**;
- marginal beats shared: **1/6**;
- destructive-null significance: **0/6**;
- even the unpenalized per-source profile upper bound does not rescue the truth source.

The marginal scores are non-degenerate, so this is not the constant-collapse artifact seen in the scalar sim-to-observation bridge test.

## Interpretation

The existing online operator variation does not contain a source-consistent correction direction that restores true-source identity. Therefore the data do not justify immediately investing in a 121 x nuisance-grid exact transport sweep or a learned low-rank local operator.

This does **not** claim that BiLO is invalid in general, nor that every possible PMFS nuisance perturbation is impossible. It closes the current evidence-based path from BiLO to the **main innovation**: before reopening it, a new independent mechanism must show that a specific physical nuisance direction improves true-source identity.

Machine-readable results: `BILO_NATURAL_OPERATOR_FAMILY_PREAUDIT_R2.csv`.
