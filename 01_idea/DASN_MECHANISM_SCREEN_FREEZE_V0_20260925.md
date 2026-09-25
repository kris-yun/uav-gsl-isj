# DASN v0 — Displacement-Aligned Shared Noise Mechanism Screen

Date: 2026-09-25

Status: **APPROVED REFERENCE-ONLY MECHANISM SCREEN; NO NEW MODEL / NO NEW SIMULATION / NO FINAL TARGET**

## Why this screen exists

After repeated route failures, the mainline adopts a mechanism-first rule:

> before promoting another far-domain mother theory, identify a reproducible localization mechanism that the strongest ordinary explanations cannot absorb.

The current question is not how large plume stochasticity is, but whether same-source realization variability falls preferentially along observation directions that mimic changing source position.

## Core scientific object

Let source coordinate be theta=(x,y), mean observation f(theta), and local source-sensitivity Jacobian J(theta)=df/dtheta.

A residual component aligned with span(J) can mimic source displacement and directly corrupt localization; equally large residual variance orthogonal to span(J) may be much less harmful.

The first screen therefore asks:

> Does source-conditioned shared decoder error contain a reproducible source-displacement-aligned component beyond ordinary gain, generic low-rank correlation, decoder bias, boundary effects, and finite-reference error?

## Data contract

Use only the completed D1R House02/W2 reference bank:
- 168 source cells;
- 16 independent realizations/source;
- frozen 10 times x30 pooled probes;
- raw concentration retained;
- no new GADEN run.

Primary probe split:
- odd probe indices: 15 probes x10 times;
- even probe indices: 15 probes x10 times.

All ten frozen times are retained in each view.

## Discovery split

Primary direction:
- reps 1..8: decoder fitting / source-response estimation;
- reps 9..16: mechanism diagnostic.

Reverse 8/8 direction is a dependent robustness check only, not a fresh confirmation.

## Ordinary readouts

The mechanism must survive at least two ordinary readout families under the same probe split:

1. regularized coordinate regression on log(1+ppm);
2. calibrated source-class decoder with posterior-mean position readout.

Hyperparameters are training-half only.

If either probe half lacks basic 2D localization sensitivity, the mechanism screen is invalid rather than replaced by another post-hoc probe partition.

## Primary observed mechanism statistic

For each source s and diagnostic realization r, let e_A(s,r) and e_B(s,r) be the 2D localization errors from the two disjoint probe views.

Center errors within source and estimate the source-conditioned cross-view error covariance C_AB(s).

Primary descriptive statistic:

T = (1/168) sum_s tr(sym(C_AB(s))).

T is shared localization error in m^2. It is not mutual information, not a physical Q estimate, and not a method proper-score gain.

## Required falsification controls

1. Within-source pairing destruction:
   permute whole B-view realizations within source, preserving each view's own amplitude/time structure while breaking same-realization pairing.

2. Common-gain model:
   test whether a source-conditioned shared amplitude/gain latent explains the observed cross-view error.

3. Generic low-rank factor model:
   equal latent dimension and selection budget; if generic correlation explains the effect, displacement-specific interpretation does not advance.

4. Decoder-bias control:
   repeat with the second ordinary readout; source-center diagnostic errors; do not interpret common decoder bias as plume information limitation.

5. Geometry/boundary audit:
   report internal vs boundary sources under frozen labels; never delete boundary sources post hoc.

6. Sensitivity alignment:
   estimate local source-response sensitivity J using training references and frozen source geometry only; test whether shared error directions systematically align with local source-displacement sensitivity rather than arbitrary observation variance.

## Non-identifiability boundary

A covariance decomposition of the form Sigma = J Q J^T + D is not identifiable without additional constraints on D.

Therefore:
- nonzero fitted Q is not proof of a physical displacement-noise latent;
- positive cross-view covariance is not an information limit;
- PSD projection/clipping cannot be used as evidence;
- if ordinary residual structure cannot be bounded, report only reproducible shared decoder error.

## Decision logic

STOP:
- no reproducible paired shared error;
- reverse split changes sign/direction materially;
- common gain or generic factor model explains the effect;
- effect is readout-specific or dominated by boundary/decoder bias.

HOLD:
- reproducible shared error exists but displacement alignment or residual non-identifiability cannot be separated.

ADVANCE_MECHANISM_ONLY:
- shared error is reproducible across split directions;
- paired-realization destruction removes it;
- source-conditioned displacement alignment survives gain/factor/readout/boundary controls;
- effect is not reducible to a generic covariance fit.

ADVANCE_MECHANISM_ONLY does NOT authorize final targets or a new likelihood. It only earns the right to formulate one candidate inference method and one fresh confirmation contract.

## Relationship to IPTO

IPTO remains a theory/prior-art reserve only.

No IPTO simulation is authorized until this mechanism screen is resolved.

If DASN advances, IPTO may later be reconsidered only if in-context operator identification gives a unique way to predict the same displacement/noise geometry across House/wind regimes.

If DASN fails, IPTO must return through its own mechanism card; the operator name alone is not sufficient justification.