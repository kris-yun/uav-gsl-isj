# CESS D1A Frozen Gate — 168-Source Dense Emergent-Scale Falsification

Date: 2026-09-25

Branch: `research/causal-emergent-source-scale-v0`

Status: **FROZEN FIRST-KNIFE DESIGN — SUPERSEDES UNEXECUTED 630x8 D1**

## Scientific claim

D1A tests exactly:

> Under fresh stochastic plume realizations, spatially contiguous coarse-graining
> of dense 0.30 m source microstates can yield greater held-out **raw
> interventional effective-information lower bound** than the micro-cell
> representation, at a reproducible intermediate source scale.

## Why the older 630x8 D1 is superseded

Primary-thread audit found that the older unexecuted D1 averaged held-out
samples uniformly over micro source cells when evaluating macro EI, despite
declaring a uniform macro intervention distribution. This is incorrect for
unequal macro sizes.

The corrected 18-source D0 remains positive under proper intervention
weighting, but the first confirmation gate is redesigned to use R0-supported
8/8 validation and a dense >=143-source region before spending 5040 runs.

Do **not** execute `CODEX_CESS_D1_HANDOFF_20260924.md`.

## Frozen source panel

Start from the exact Gate1A House02 630-source bank.

Required SHA256:

- `source_bank.tsv`:
  `0e835c3a3d0f4651f9c4aa87b28a34892589cfb073a73daf6a84896d081824fb`
- `gate1a_contract.json`:
  `68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334`

Panel selection uses geometry only:

1. enumerate every axis-aligned PMFS rectangle whose every cell exists in the
   frozen free-source bank;
2. maximize number of cells;
3. deterministic aspect/lexicographic tie-break.

Frozen result:
- i=1..24
- j=12..18
- 24x7 = **168 equal-area source microstates**
- spacing 0.30 m.

No plume result enters panel selection.

## Frozen environment

- House02
- W2 = `3,5-1_slow`
- same GADEN binary, occupancy, W2, extractor as R0
- 10 frozen times
- 30 frozen pooled probes
- encounter:
  [
  H_{tq}=1[C_{tq}>0].
  ]

The zero threshold is a simulation-mechanism variable only.

## New data

Generate exactly 16 fresh realizations per source:

[
168\times16=2688.
]

No old C/D, R0, S1/S2/S3 target realization enters estimation.

For panel row i=0..167 and replicate r=1..16:

[
seed(i,r)=2026105000+16i+r.
]

## Frozen split

Split A:
- train reps 1..8
- test reps 9..16

Split B:
- train reps 9..16
- test reps 1..8

## Micro likelihood

For source s and observation coordinate tq:

[
hat p_{s,tq}=(k_{s,tq}+1/2)/(8+1).
]

Factorized Bernoulli is only the decoder used to measure held-out information.

## Spatial hierarchy

Use deterministic four-neighbor connectivity-constrained Ward merging based
only on source geometry.

Frozen levels:

[
M\in\{168,126,84,63,42,28,21,14,10,7,5,3,2\}.
]

Every macrostate must remain connected.

## Strict macro intervention

No macro model is fitted.

[
hat p(h|do(M=m))
=
\frac{1}{|S_m|}
\sum_{s\in S_m}
hat p(h|do(S=s)).
]

Macro intervention prior:

[
p(M=m)=1/M.
]

Evaluation must use the same intervention distribution:
equal weight per macrostate, then equal weight per microstate inside the
macrostate.

## Primary metric

[
\underline{EI}(M)=\log M-CE_{do(M)}
]

and

[
\Delta EI(M)=\underline{EI}(M)-\underline{EI}(168).
]

Raw EI is primary. Normalized effectiveness is diagnostic only.

## Realization bootstrap

Uncertainty is over stochastic plume realizations, not over the fixed source
state set.

For every source independently, resample its 8 held-out realizations with
replacement.

- 2000 bootstrap replicates
- RNG seed 2026109001 (+ split offset)

For each bootstrap recompute micro EI, macro EI, and ΔEI using the frozen
intervention weights.

Report q2.5/q50/q97.5.

## Random grouping control

For every M<168:

- keep the exact cluster-size vector from the spatial hierarchy;
- generate 250 non-spatial random partitions;
- no refitting;
- use the identical corrected macro intervention evaluation;
- RNG seed 2026109002+M.

Report spatial EI percentile separately for both splits.

## Supported scale band

A macro level M is supported only if in BOTH splits:

1. ΔEI(M)>0;
2. realization-bootstrap q2.5 of ΔEI(M)>0;
3. spatial EI percentile >0.95 versus size-matched random partitions.

A supported scale **band** requires at least two adjacent frozen M levels.

One lucky M is insufficient.

## Peak reproducibility

Find the raw-EI maximizing M in each split.

The peaks must:
- be adjacent in the frozen M sequence, OR
- both lie inside the same supported band.

## Decision

PASS:

`CESS_D1A_PASS_EMERGENT_SOURCE_SCALE`

Requires:
- all 168×16 realizations valid;
- >=1 supported scale band;
- peak reproducibility passes.

STOP:

`CESS_D1A_FAIL_STOP_CAUSAL_EMERGENT_SCALE_MAINLINE`

Any scientific failure.

There is **no scientific HOLD** at D1A. Sixteen realizations were chosen
specifically to avoid post-result seed rescue.

## Secondary diagnostics

Report without affecting decision:

- micro exact-source top1/top3;
- micro MAP spatial-error median/q90;
- posterior mass within 0.5 m / 1.0 m;
- macro cell counts, area, diameters;
- 0.30 m-neighbor vs >=3 m encounter-profile similarity.

These separate exact-cell identifiability from source-basin identifiability.

## Interpretation

A PASS means only:

> in one dense House02/W2 region, an intermediate spatial source
> coarse-graining reproducibly increases held-out interventional source
> information.

It does not establish cross-House generalization or closed-loop benefit.

After PASS, independent review is mandatory before any full-630,
cross-environment, or PMFS experiment.
