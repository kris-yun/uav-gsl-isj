# Candidate Search After TNQC HOLD + Active-Deconfounding V1 NO-GO

Date: 2026-09-21

## What has now been falsified

Two distinct ideas have failed the authoritative/project screens:

1. **TNQC V5 quotient canonicalization**
   - algebraically correct;
   - mechanism-positive in concentration space;
   - 300-s online hit-logit localization HOLD.

2. **Active source–transport deconfounding V1**
   - mathematically coherent;
   - projection/short-horizon screen implemented with shared nuisance state;
   - 0/6 promotion cases in the frozen offline screen.

Therefore the next main idea must not be:

- a stronger TNQC weight;
- another affine/ordinal invariant;
- Fisher/Schur projection presented as new;
- a larger transport bank by itself;
- ordinary source MI / joint MI / BOED by itself;
- another gate layered on the same static response representation.

## Candidate A — Dynamics-Conformance / Unknown-Unknown-Aware GSL

### Cross-domain source

ICLR 2026:
**Detection of unknown unknowns in autonomous systems**.

The transferable scientific idea is that deployment failures can arise from
a change in the underlying system dynamics even when marginal observations do
not look OOD. The proposed remedy in that domain is online model recovery and
**dynamics conformance**, rather than ordinary distribution-shift detection.

### Why it is materially different from TNQC and deconfounding V1

TNQC asks whether two accumulated fields are equivalent after a nuisance
transform.

Deconfounding V1 asks whether selected future measurements separate source
from a finite nuisance bank.

Dynamics-conformance instead asks a prior question:

> is the forward dynamical law currently assumed by the source inference
> actually consistent with the observed temporal evolution?

This attacks **model validity**, not score invariance or nuisance projection.

### GSL hypothesis

PMFS may become sharply confident while the assumed source-to-observation
transport dynamics are locally inconsistent with the actual gas/wind/time
sequence.

A candidate-specific source score should therefore be trusted only to the
extent that its predicted temporal dynamics conform to the observed dynamics.

The main innovation would have to be GSL-specific, for example:

- recover a lightweight local gas/wind response model online;
- compare candidate-source forward dynamics against the recovered dynamics;
- separate observation-fit from dynamics-conformance;
- suppress or broaden source belief when the candidate model is
  dynamically unsupported.

This is not the same as generic anomaly detection: the end product must be a
source-localization inference rule and must improve source ranking/endpoint,
not merely flag a bad run.

### Cheapest falsification screen

Before ROS changes, reuse the six frozen trajectories.

For each trajectory:

1. preserve temporal order instead of only the final accumulated hit map;
2. construct source-blind temporal features from gas/hit, wind and robot
   motion;
3. generate candidate-source temporal responses along the exact same path;
4. compute a pre-registered dynamics-conformance score;
5. evaluate truth only after scores are frozen.

Compare:

- native PMFS candidate ranking;
- static quotient ranking;
- temporal likelihood baseline;
- dynamics-conformance ranking.

Promotion requires a consistent improvement in true-source neighborhood rank
or calibrated uncertainty across multiple Houses/seeds, with held-out
temporal windows and no truth-conditioned fitting.

If the temporal/dynamics score does not expose information absent from the
static map, reject this candidate immediately.

## Candidate B — Horizon-Calibrated Transport Uncertainty

### Cross-domain source

ICLR 2026:
**Learning to Be Uncertain: Pre-training World Models with
Horizon-Calibrated Uncertainty**.

The transferable principle is that a stochastic world model should not
pretend all rollout horizons are equally certain; predictive uncertainty
should increase in a structured way with prediction horizon.

### Possible GSL mapping

Online dispersion simulations are used as if candidate responses had uniform
reliability. A GSL-specific method could attach horizon/distance/transport
uncertainty to simulated evidence so long or poorly constrained transport
rollouts cannot create an overconfident source posterior.

### Risk

This is attractive as an auxiliary idea, but by itself it may only soften
confidence rather than improve localization. It should not be promoted to the
main innovation unless an offline screen shows that horizon-calibrated
transport uncertainty materially changes true-vs-false source discrimination.

## Candidate C — Decision-Aware Set-Valued Source Inference

### Cross-domain source

ICLR 2025:
**Utility-Directed Conformal Prediction: A Decision-Aware Framework for
Actionable Uncertainty Quantification**.

The transferable idea is to represent uncertainty as a calibrated prediction
set designed for downstream utility, rather than as a single overconfident
point prediction.

### Possible GSL mapping

The six TNQC cases show severe false confidence. Instead of forcing PMFS to
collapse to one source mode, maintain an actionable source set/region and let
the downstream planner act on that set.

### Risk

Conformal/set-valued inference does not create missing source information.
It is more naturally an auxiliary reliability mechanism unless it changes the
planning objective in a way that produces better localization.

## Candidate D — Multi-Environment Robust Belief Control

### Cross-domain source

NeurIPS 2025:
**Multi-Environment POMDPs: Discrete Model Uncertainty Under Partial
Observability**.

The transferable principle is a single policy robust across a finite family
of environment models that share state/action/observation spaces but differ
in transition/observation/reward models.

### Possible GSL mapping

Treat plausible transport regimes as environment models and plan a policy
that does not depend on one fragile dispersion model being correct.

### Risk

Robust POMDPs are an established control concept. A direct application to a
transport bank is unlikely to meet the desired novelty bar unless a distinctly
GSL-specific structural result or lightweight reduction is found.

## Current search priority

Do **not** implement all four.

The first candidate worth a cheap screen is **Dynamics-Conformance /
Unknown-Unknown-Aware GSL**, because it changes the scientific question from
"how should we score an assumed forward model?" to "when is that forward
model trustworthy enough to support source inference?"

Only after that screen should a main innovation be selected.

The remaining candidates are retained as alternatives/auxiliary mechanisms,
not accepted innovations.
