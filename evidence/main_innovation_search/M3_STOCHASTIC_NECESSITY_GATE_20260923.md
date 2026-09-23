# M3 W1 — Stochastic-Necessity Gate Before Any Generative Model

Date: 2026-09-23  
Status: **required before OFM / stochastic world-model training**

## Purpose

Do not assume turbulent stochasticity needs a generative field model.

Use the shared 4-source × 2-wind × 2-seed pilot to measure whether within-condition plume randomness is large enough, structured enough, and source-relevant enough to justify M3.

## 1. Field notation

For source (s), wind condition (w), plume seed (r):

[
H_{s,w,r}(x)
]

is the frozen sensor-height concentration or hit-probability field.

For two seeds:

[
ar H_{s,w}
=
rac12
left(
H_{s,w,1}
+
H_{s,w,2}
ight).
]

## 2. Within-condition stochastic variation

Define:

[
V_{m seed}
=
rac{1}{|S||W|}
sum_{s,w}
rac12
left|
H_{s,w,1}
-
H_{s,w,2}
ight|_M^2
]

where (|cdot|_M) is a fixed free-space masked norm.

This quantifies plume-realization variability with source and wind frozen.

## 3. Between-source signal

For each wind:

[
ar H_{cdot,w}
=
rac1{|S|}
sum_s
ar H_{s,w}.
]

Define:

[
V_{m source}
=
rac{1}{|W||S|}
sum_{w,s}
left|
ar H_{s,w}
-
ar H_{cdot,w}
ight|_M^2.
]

This is the field-scale source-discriminative signal.

## 4. Stochastic-necessity ratio

[
oxed{
R_{m stochastic}
=
rac{V_{m seed}}
{V_{m source}+epsilon}
}
]

Interpretation:

- (Rll1): stochastic variation is small relative to source signal;
- (Rsim1): stochastic plume variability is comparable to source discrimination;
- (R>1): realization uncertainty can dominate source differences.

Do not set an arbitrary pass threshold before seeing the actual distribution.

Report the continuous ratio.

## 5. Spatial/local version

For every free cell (x):

[
R_{m stochastic}(x)
=
rac{
V_{m seed}(x)
}{
V_{m source}(x)+epsilon
}.
]

Map where stochasticity matters.

Important question:

> Are the high-stochasticity regions also the cells PMFS visits or considers source-informative?

If stochasticity only dominates irrelevant remote cells, M3 is unnecessary for localization.

## 6. Source-rank necessity test

The strongest gate is not field variance.

For each source/wind pair:

1. use seed 1 as the candidate-forward realization/mean estimate;
2. evaluate source ranking on seed 2 observations;
3. repeat swapping seeds.

Compare:
- deterministic mean/one-realization forward;
- oracle two-seed empirical distribution.

If a simple deterministic mean gives essentially the same truth-source ranking as the empirical stochastic representation, a generative world model has no source-localization justification.

## 7. Structured stochasticity test

M3 requires learnable stochastic structure, not merely noise.

Compute source-blind diagnostics:

- spatial covariance of seed residuals;
- wind-aligned correlation;
- obstacle-conditioned covariance;
- low-rank/PCA energy;
- multimodality/intermittency of hit events.

Destructive null:
spatially permute seed residuals within free cells while preserving their marginal histogram.

A useful stochastic model requires real residual structure stronger than the null.

## 8. Decision

### M3 advances as auxiliary only if

- within-condition stochasticity is non-negligible relative to source signal;
- it occurs in localization-relevant cells;
- it changes source ranking under independent plume realizations;
- the stochastic residual has spatial/physical structure;
- a stochastic empirical/oracle representation beats deterministic mean forward.

### M3 no-go if

- seed variability is small;
- variability is effectively unstructured;
- deterministic source rank is unaffected;
- stochastic field metrics improve without source-rank gain.

## 9. Consequence for architecture

If M3 fails:
- keep M6 deterministic CF-PFM;
- do not add OFM.

If M3 passes:
- stochastic residual modeling becomes a justified auxiliary;
- only then compare deterministic residual vs Operator Flow Matching.

Status:

`WAIT FOR SHARED PILOT; NO STOCHASTIC MODEL TRAINING YET`.
