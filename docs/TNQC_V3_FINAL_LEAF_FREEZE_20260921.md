# TNQC V3 quotient foundation and claim boundary
Date: 2026-09-21

> **Foundation retained; gate superseded:** V3 established the correct online
> variable, quotient theorem, final-leaf hypothesis scope, and C++ endpoint
> audit. V4 added the terminal-leaf free-cell measure, and V5 added
> support-coverage attenuation. The authoritative gate is:
> `docs/TNQC_V5_SUPPORT_COVERAGE_GATE_20260921.md`.

V3 code/evaluator correction checkpoint:
`3024ff349c37105aee1816f6648db3e81c178202`

## 1. Exact online variable

Online TNQC does **not** operate directly on raw concentration.

For a PMFS source update:

- observed field: `x_i = logit(p_i)`, where `p_i` is the accumulated PMFS
  measured hit probability at free cell `i`;
- candidate field: `y_s,i = logit(p_hat_i(s))`, where `p_hat_i(s)` is the
  PMFS transport simulation hit probability for candidate source `s`;
- weight: `w_i` is native PMFS confidence;
- support: free cells with positive confidence and finite values.

The implementation requires at least four supported cells.

The archived 240-s probe instead bins `gas_ppm` spatially. It is therefore
concentration-space mechanism evidence, not direct validation of the online
hit-logit score.

## 2. Main quotient canonicalization

Consider positive-affine actions on a non-constant supported hit-logit field:

`x -> a*x + b*1, with a > 0`.

Define:

`mu_w(x) = sum_i w_i x_i / sum_i w_i`

`pi_w(x) = (x - mu_w(x)*1) / ||x - mu_w(x)*1||_w`

with weighted norm

`||z||_w^2 = sum_i w_i z_i^2`.

For fixed support and weights:

`pi_w(a*x + b*1) = pi_w(x)` for every `a > 0`.

For non-degenerate fields the representative is complete for this action:

`pi_w(x) = pi_w(y)` iff `y = a*x + b*1` for some `a > 0`.

The continuous TNQC score is

`q_aff(x,y_s) = <pi_w(x), pi_w(y_s)>_w`.

Equivalently, a chordal distance on the quotient representation is

`d_Q^2([x],[y_s]) = 2*(1 - q_aff(x,y_s))`.

The scientific idea is therefore **source inference after quotienting
positive-affine nuisance coordinates of the PMFS hit-logit representation**.
The novelty is not Pearson correlation itself.

## 3. Claim boundary

The exact theorem is conditional on:

- the supported **hit-logit** representation;
- fixed support;
- fixed positive weights;
- positive-affine actions in that representation.

PMFS first thresholds raw concentration and propagates a Bayesian/spatial hit
map. Therefore a raw concentration transform `c -> a*c+b` does not
automatically imply a positive-affine transform of the resulting PMFS logits.

Do not claim unconditional exact invariance to arbitrary:

- sensor calibration curves;
- background concentration shifts;
- source release-rate changes.

Allowed claims are:

- exact positive-affine invariance in the supported PMFS hit-logit space;
- empirical robustness to the source-blind concentration interventions that
  were actually tested in the 240-s auxiliary asset;
- a physical hypothesis that PMFS may compress some nuisance variation into
  approximately affine hit-logit coordinates, to be tested rather than
  assumed.

## 4. Local spatial-order auxiliary

For adjacent supported grid-cell edges, the auxiliary channel compares the
sign of local differences between observed and candidate fields. It is
invariant to strictly increasing pointwise transforms of the fields.

A 2026 GSL method already uses concentration measurement ranking for
calibration-free source localization:

Wanting Jin et al.,
"Calibration-Free Gas Source Localization with Mobile Robots: Source Term
Estimation Based on Concentration Measurement Ranking," 2026.
https://arxiv.org/abs/2605.13208

Therefore rank/monotone invariance itself is not TNQC's main novelty. Local
order is only a corroboration/abstention channel.

## 5. Final-leaf hypothesis correction

Native PMFS alone controls quadtree refinement.

After refinement, a coarse candidate that was subdivided is search history,
not a terminal source hypothesis. V3 therefore removed evaluated ancestors
from the authoritative gate and used only terminal active free leaves.

The replay reconstructs the same final partition by assigning every free cell
to the smallest evaluated candidate rectangle covering it.

V4 keeps this final-leaf restriction and additionally fixes the measure over
those leaves.

## 6. Exponential tilt interpretation

The fused score is

`L_fused(s_i) = L_PMFS(s_i) * exp(e_i)`.

This has the form of a bounded Gibbs/exponential tilt. A useful reference for
loss-based exponential updating is:

P. G. Bissiri, C. C. Holmes, S. G. Walker,
"A General Framework for Updating Belief Distributions," JRSS-B, 2016.
https://doi.org/10.1111/rssb.12158

Do **not** describe `L_PMFS` and `exp(e_i)` as conditionally independent
physical likelihoods: both reuse the accumulated PMFS observation map.
Describe TNQC as a bounded quotient-space exponential tilt / generalized-loss
correction.

Do not scale the evidence by raw cell count or `sqrt(N_eff)`; PMFS map cells
are spatially propagated and are not iid replications.

## 7. 300-s endpoint audit

The authoritative House endpoint remains the original PMFS:

`ExpectedValue(sourceProbability, 0.05)`

at the full 300-s budget.

The V3 replay added two integrity anchors before any TNQC gain can be used:

1. reconstruct the native posterior from exported candidate fields and match
   `source_posterior.csv`;
2. match the Python native top-5% error to the C++ terminal
   `RESULT IS: Error=` within 0.011 m, reflecting the C++ two-decimal log.

V4 inherits both.

## 8. Scientific lineage

Canonicalization as projection to a reduced/canonical space:
Behrooz Tahmasebi & Stefanie Jegelka, ICLR 2025.
https://proceedings.iclr.cc/paper_files/paper/2025/hash/b36dc39b319ba6ba2a0fd7601951efb4-Abstract-Conference.html

Continuous/non-compact symmetry canonicalization:
Zakhar Shumaylov et al., ICLR 2025.
https://openreview.net/pdf?id=7PLpiVdnUC

Adaptive canonicalization as a future direction if fixed affine
canonicalization proves too rigid:
Ya-Wei Eileen Lin & Ron Levie, ICLR 2026.
https://proceedings.iclr.cc/paper_files/paper/2026/hash/2774a3b52d436b5930da660dd2b32b3a-Abstract-Conference.html

## 9. Status

**V3 FOUNDATION RETAINED / V5 GATE AUTHORITATIVE /
VGR 300-S ONLINE-REPRESENTATION TEST PENDING / CLOSED LOOP HOLD.**
