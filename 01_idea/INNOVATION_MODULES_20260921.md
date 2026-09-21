# Innovation Modules — 2026-09-21

This file separates the **current frozen TNQC V5 method** from the
**next-generation research direction**. They must not be mixed in one
scientific result.

## A. Current frozen method: TNQC V5

### A1. Main innovation — Transport-Nuisance Quotient Canonicalization

**Origin field**

- symmetry / invariance;
- canonicalization and quotient representations;
- geometric deep learning;
- nuisance-robust inverse problems.

**Transferred idea**

Observations that differ only by a nuisance transformation should be compared
through a canonical representative of the nuisance-equivalence class.

For the current supported PMFS hit-logit representation, TNQC uses weighted
centering and weighted normalization. Under fixed support/weights,

`x' = a x + b 1, a > 0`

maps to the same canonical representative as `x`.

**GSL-specific innovation**

The canonicalization is not used as a neural-network front end. It is inserted
inside a physics-based PMFS source-hypothesis inference pipeline: measured
hit-logits and candidate simulated hit-logits are compared in quotient space,
while the native PMFS transport simulator and candidate-generation mechanism
remain the physical backbone.

**Claim boundary**

Exact invariance is only claimed for the stated positive-affine transform in
the supported hit-logit coordinates. It is not a claim of exact invariance to
arbitrary wind-field, diffusion, raw concentration, release-rate, saturation,
or sensor-dynamics changes.

### A2. Auxiliary innovation — Local spatial ordinal corroboration

**Origin field**

- ordinal/rank statistics;
- monotone invariance;
- calibration-free sensing.

**Transferred idea**

Strictly monotone pointwise transformations preserve pairwise order.

**GSL-specific role**

TNQC does not replace PMFS by global concentration ranking. It compares local
adjacent-cell order in measured and simulated spatial fields and uses this as
a corroboration channel for the main quotient score.

This is deliberately auxiliary because concentration-ranking GSL already
exists in the literature. The local-order channel is not allowed to become an
independent source estimator or override the main channel.

### A3. Auxiliary innovation — Support/partition-measure safe evidence gate

**Origin field**

- robust evidence aggregation;
- adaptive discretization;
- generalized Bayesian/Gibbs updating.

**Problem addressed**

Two implementation artifacts can otherwise create false confidence:

1. an auxiliary statistic may be perfect on only a tiny informative subset;
2. adaptive quadtree leaves do not represent equal physical source mass.

**GSL-specific construction**

- gate only on terminal active free leaves;
- weight leaves by represented free-cell count;
- compute informative-support coverage `rho`;
- combine conditional concordance with coverage;
- use one shared nonnegative gate;
- apply bounded evidence through an exponential/Gibbs-style posterior tilt.

The auxiliary channel can attenuate or abstain but cannot reverse the ordering
of the main quotient score.

## B. Evidence state of TNQC V5

The method equations are frozen.

Current evidence ladder:

1. algebra/unit tests — passed;
2. concentration-space mechanism evidence — positive;
3. House01/seed0 300-s pipeline validation — passed;
4. House01/seed0 TNQC localization effect — approximately neutral/slightly
   worse in the first valid case;
5. six-case House01/02/03 x seed0/1 verdict — pending;
6. closed-loop TNQC effect — pending and prohibited until the six-case
   offline gate is complete.

Do not tune V5 after observing individual House results.

## C. Next-generation research direction — Active Source–Transport
Deconfounding

This is **not part of TNQC V5** and has no closed-loop result yet.

### C1. Origin field

- active system identification;
- Bayesian optimal experimental design;
- dual control;
- nuisance-hardened inference / Fisher-Schur geometry;
- decision-aware experiment design.

### C2. Scientific object

Let source parameters be `s`, transport/calibration nuisance be `nu`, and
action sequence be `A`.

The central object is no longer only an invariant score. The problem is to
identify when changes in source can be mimicked by changes in transport:

`J_s delta_s in col(J_nu)`.

The source information that cannot be locally explained by nuisance is

`I_eff = A^T (I - P_B) A`

for whitened source and nuisance sensitivities.

### C3. Proposed GSL-specific novelty

The intended new principle is:

**actively choose a short sequence of feasible measurements that breaks
source–transport confounding, rather than greedily moving to the location with
the largest immediate source-information score.**

The potentially novel part is not Fisher information, BOED, dual control, or
joint wind/source estimation by themselves. Those are established tools.

The research contribution would have to be the combination of:

- an explicit GSL source–transport confounding geometry;
- a physically shared nuisance state rather than per-cell nuisance fitting;
- a short-horizon complementary probing rule that can create identifiability
  even when each single action is individually uninformative;
- a finite-budget decision objective tied to the original source-localization
  endpoint;
- evidence against matched-model/inverse-crime baselines.

### C4. Status

Theory/review material exists under:

`01_idea/teacher_reviews/20260921_endpoint_and_closed_loop/`

No production code, frozen algorithm, or House closed-loop result exists for
this next-generation direction yet.

## D. Paper architecture rule

For the current TNQC V5 paper line:

- Main: quotient canonicalization in physics-based GSL inference.
- Auxiliary 1: local ordinal corroboration.
- Auxiliary 2: support/partition-measure safe evidence gate.

For a future active-deconfounding paper line, do not present TNQC auxiliary
modules as the new main contribution. Active deconfounding would be a separate
main innovation, with TNQC only potentially serving as a nuisance-handling
subroutine if justified prospectively.
