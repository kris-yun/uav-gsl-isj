# R0 Frozen Protocol — Multi-Realization Stochastic Benchmark Calibration

Date: 2026-09-24

Branch:
`research/stochastic-benchmark-refoundation-20260924`

Status:
**EXECUTE BENCHMARK CALIBRATION ONLY**

This is not a new gas-source-localization method and does not rescue PASI.

## 1. Question

Can the current House02/W2 observation operator support reproducible source-conditioned stochastic plume descriptors, or have recent routes been over-interpreting two-seed realization structure?

R0 asks whether stochastic descriptors converge across independent realizations before any new mother theory is selected.

## 2. Frozen environment

House:
`House02`

Wind:
`W2 = 3,5-1_slow`

Use the exact same GADEN, occupancy, wind and extractor contracts as PASI/Gate1A.

Observation operator:
- 10 frozen times: 100,150,...,550;
- 30 frozen pooled probes;
- pooled array shape: 10×30.

Legacy Gate1A C/D:
- C = 2026092401
- D = 2026092402

Legacy C/D are used only to construct the initial stratified source panel and later audit whether a two-seed estimate was representative.

**They are not included in the R0 16-realization estimator.**

## 3. Frozen 18-source panel

Panel file:
`research/stochastic_benchmark_refoundation/R0_SOURCE_PANEL_18.tsv`

Selection is deterministic:

1. remove every candidate within 2.0 m of S1/S2/S3;
2. using legacy C/D only, compute:
   - relative path discrepancy;
   - mean path mass;
3. split each variable into three eligible-source terciles: low/mid/high;
4. form the 3×3 cross-strata;
5. in each stratum choose:
   - one candidate closest to the within-stratum robust metric center;
   - one candidate spatially farthest from that central candidate.

Total:
3 × 3 × 2 = **18 sources**.

The old C/D strata are sampling strata only. R0 explicitly tests whether they remain meaningful under many new realizations.

## 4. Frozen 288 new simulations

Seed matrix:
`research/stochastic_benchmark_refoundation/R0_SEED_MATRIX_18x16.tsv`

Each source receives 16 completely new, unique RNG seeds.

Total:
18 × 16 = **288 new plume realizations**.

Seed range:
`2026093001 ... 2026093288`

No seed is reused between panel sources.

## 5. Frozen stochastic descriptors

For each source and each K in:

`K = 2, 4, 8, 12, 16`

compute:

- median pairwise relative L2 path discrepancy;
- 90th percentile pairwise relative L2;
- median pairwise cosine;
- 10th percentile pairwise cosine;
- median / q10 / q90 total observed plume mass;
- median zero fraction;
- median first-arrival time index.

Primary source-stochasticity descriptor for the R0 decision:

**median pairwise relative L2 path discrepancy**.

For realizations a,b:

[
d(a,b)=
\frac{\|a-b\|_2}
{\left\|\frac{a+b}{2}\right\|_2+10^{-12}}
]

## 6. Frozen reproducibility tests

Two independent 8-vs-8 split structures are required:

### Split A
replicates 1–8 versus 9–16.

### Split B
odd replicates versus even replicates.

For each split report across the 18 sources:

- Spearman correlation of source median pairwise relative-L2 variability;
- Spearman correlation of median total mass;
- exact agreement of low/mid/high variability tercile assignment.

This tests whether “which sources are more stochastic” survives different realization samples.

## 7. Frozen K-convergence tests

For each source compare its primary variability statistic from:

- K=8 versus K=16;
- K=12 versus K=16.

Relative change:

[
\Delta_K(s)=
\frac{|D_K(s)-D_{16}(s)|}{|D_{16}(s)|+10^{-12}}
]

Aggregate:
- median (Delta_K);
- 75th percentile (Delta_K);
- maximum diagnostic.

## 8. Frozen R0 decision

### PASS

Decision:

`R0_PASS_STOCHASTIC_BENCHMARK_USABLE`

All must hold:

1. complete 18×16 data;
2. both 8/8 split variability Spearman ≥ 0.70;
3. both split low/mid/high variability-tercile agreement ≥ 0.50;
4. K8→K16 median relative change ≤ 0.25;
5. K8→K16 q75 relative change ≤ 0.40;
6. K12→K16 median relative change ≤ 0.15;
7. K12→K16 q75 relative change ≤ 0.25.

Interpretation:
16-realization source stochastic summaries are reproducible enough to support a new stochastic benchmark.

PASS does **not** validate PASI, Gaussianity, Onsager–Machlup, or any main innovation.

### HOLD

Decision:

`R0_HOLD_MORE_REALIZATIONS_REQUIRED`

If PASS fails but all hold:

- complete 18×16;
- both variability split Spearman ≥ 0.40;
- K12→K16 median relative change ≤ 0.25;
- K12→K16 q75 relative change ≤ 0.40.

Interpretation:
statistics are partly stabilizing but 16 realizations are not enough. Increase K before searching for the next mainline.

### STOP

Decision:

`R0_STOP_PER_SOURCE_DISTRIBUTION_MAINLINE_UNSTABLE`

If even HOLD fails.

Interpretation:
under the current observation operator, per-source stochastic descriptors remain too unstable for a practical source-conditioned path-distribution mainline.

Do not rescue by changing thresholds after the result.

## 9. Diagnostic outputs that do not control PASS

R0 also reports:

- legacy C/D variability vs 16-realization variability Spearman;
- median total-mass split reproducibility;
- pairwise heavy-tail/intermittency summaries;
- zero-hit and arrival-time statistics.

These diagnose why two-seed routes failed but do not alter the frozen R0 decision.

## 10. After R0

### If PASS
Only then choose the next mother theory based on the observed stochastic object and define separate:
- development sources/seeds;
- locked validation sources/seeds;
- final test sources/seeds.

### If HOLD
Generate more realizations for the same frozen panel. Do not change source panel or theory.

### If STOP
Do not build the next main innovation around per-source stochastic path distributions with this observation operator. Search a different scientific object.

No PMFS closed-loop work is authorized by R0.
