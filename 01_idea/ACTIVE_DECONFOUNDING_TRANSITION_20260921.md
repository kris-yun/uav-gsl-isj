# Transition Decision: TNQC V5 -> Active Source–Transport Deconfounding

Date: 2026-09-21

## Why V5 is closed

TNQC V5 successfully established an algebraically valid nuisance
canonicalization mechanism, but the authoritative six-case online
hit-logit localization gate is HOLD.

The negative result is scientifically informative:

1. removing a positive-affine observation nuisance does not guarantee that
   source identity remains discriminative under transport mismatch;
2. an internally consistent quotient/order ranking can still rank the wrong
   source region;
3. bounded reweighting cannot manufacture information that the executed
   trajectory did not acquire;
4. the native PMFS posterior can become sharply concentrated far from the true
   source, so posterior-confidence reduction and source identifiability must
   be treated explicitly.

Therefore the next method must not be "TNQC with a stronger weight".

## Next main hypothesis

**Actively acquire measurements that break source–transport confounding.**

Let source state be s and shared transport/calibration nuisance be nu. The
core question is not only which candidate best matches the current field, but
whether source-induced variation is distinguishable from nuisance-induced
variation under the currently executed measurements.

Locally, with whitened sensitivities A for source and B for nuisance:

`I_eff = A^T (I - P_B) A`.

If a source direction lies in the nuisance span, another score on the same
measurements cannot recover it. The robot should instead execute a short
sequence of feasible measurements whose joint response makes source
variation independent of the nuisance span.

## Required novelty boundary

The new contribution cannot be claimed as any of the following by itself:

- Fisher information;
- Bayesian optimal experimental design;
- dual control;
- joint source/wind estimation;
- nuisance projection;
- a transport template bank.

Those ideas already exist.

The intended GSL-specific contribution must combine:

1. an explicit source–transport confounding representation;
2. physically shared nuisance variables across observations;
3. complementary multi-action probing rather than single-step greedy
   information gain;
4. a finite remaining-budget objective tied to final source localization;
5. robust evaluation against transport/model mismatch rather than only a
   matched forward model.

## Fastest validation sequence

Before any ROS closed loop:

### Stage A — reuse the frozen six native histories

Use the already acquired House01/02/03 x seed0/1 histories only for
diagnostics and candidate construction.

Measure:

- source/transport sensitivity alignment;
- whether wrong source hypotheses can be explained by plausible shared
  transport variations;
- which pairs of spatial observations would most reduce this confounding.

Do not claim closed-loop improvement from these histories.

### Stage B — counterfactual physics screen

For a small pre-registered source x transport bank, simulate candidate future
measurements at feasible action locations.

Compare prospectively fixed strategies:

- native PMFS acquisition heuristic;
- one-step source information;
- one-step joint source+nuisance information;
- two-step active-deconfounding criterion.

The goal is to see whether the two-step criterion can make the true source
more identifiable under held-out transport perturbations.

### Stage C — independent closed-loop pilot

Only if Stage B has a clear positive signal, implement the lightweight
planner and run a small independent House pilot with new seeds/realizations.

Do not tune on the six V5 HOLD cases and then call those same six an unseen
test.

## Success signal before production implementation

Promote the idea to production code only if the offline/counterfactual screen
shows all of the following:

- measurable source–transport confounding in the current failure cases;
- the proposed multi-action criterion selects different actions for a
  principled reason;
- those actions increase source identifiability under held-out transport
  conditions;
- benefit is not reproduced by a simpler one-step source-MI baseline;
- compute cost is compatible with the remaining 300-s budget.

Otherwise reject or reformulate the next-generation idea before another large
ROS implementation cycle.
