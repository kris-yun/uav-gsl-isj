# CORE-M1-PHIC: proxy-calibrated hierarchical partial-invariance causal evidence

## Decision

The next M1 is not another arithmetic, geometric, or variance pooling rule.
It is a sensor-consistent, hierarchical partial-invariance estimator that
separates stable source evidence from transport/sensor-shift evidence and
keeps an explicit sensitivity interval when the separation is not identified.

The working name is **PHIC**: Proxy-calibrated Hierarchical Invariant Causal
evidence.

This document is a design freeze for the offline attribution replay only. It
does not authorize a new closed-loop run or a new seed.

## Theory anchors

1. **Bayesian Hierarchical Invariant Prediction (BHIP), CLeaR 2026.** BHIP
   reframes invariant causal prediction as hierarchical Bayes and explicitly
   tests causal-mechanism invariance under heterogeneous data. This is the
   primary basis for replacing the false global-invariance assumption with a
   partial-invariance model over transport contexts.
2. **Causal Fine-Tuning under Latent Confounded Shift, ICML 2026.** The paper
   derives identification conditions for decomposing stable and
   environment-specific components under latent confounded shift. This maps to
   separating source-responsive evidence from transport/sensor artifacts.
3. **Proxy-Guided Measurement Calibration, CLeaR 2026.** The method models
   systematic measurement error with latent content and bias variables and
   uses bias-independent proxies to calibrate the observation. This motivates
   using the continuous concentration/FOPDT state as an observation proxy
   instead of treating filament-visit frequency as the event law.
4. **Disentangling Dynamical Systems: Causal Representation Learning Meets
   Local Sparse Attention, CLeaR 2026.** Its identifiability result shows that
   local state-dependent causal structure can be necessary in dynamical
   systems. This supports keeping M1 event-time windows local rather than
   forcing one global transport-invariance relation.
5. **Sharp Bounds for Treatment Effect Generalization under Outcome
   Distribution Shift, CLeaR 2026.** The sensitivity parameter `Lambda` gives a
   principled bound when transportability is violated. PHIC uses this as a
   falsification/safety interval, not as a post-hoc performance knob.

These papers support the design principles. None proves gas-source
localization. The task-specific identification proposition and replay gate
remain ours to establish.

## Causal model for PMFS

For a source candidate `c`, transport context/member `u`, event window `i`,
and observed context proxy `z_i`:

```text
S=c -> T_u -> exposure -> concentration/FOPDT state -> Y_i (block event)
E   -> T_u
E   -> sensor/measurement regime
```

`T_u` is a mediator/mechanism, not a nuisance that can be assumed to cancel
for every candidate. The false assumption exposed by H02/H03 was that the
transport contribution is candidate-independent after centering.

PHIC instead uses the local hierarchical decomposition

```text
eta_{u,i}(c) = tau_i(c) + a_i(z_i) + gamma_i(c)^T z_{u,i} + epsilon_{u,i}(c)
```

where:

- `tau_i(c)` is the source-responsive component that is intended to transfer;
- `a_i(z_i)` is the observation/context component shared across candidates;
- `gamma_i(c)` is an explicit candidate-by-transport interaction, shrunk by a
  hierarchical prior rather than silently discarded;
- `z_{u,i}` contains only observed transport/geometry/sensor-state proxies;
- `epsilon` is residual uncertainty.

The stable evidence is the standardized hierarchical component

```text
tau_i(c) = E_u[ eta_{u,i}(c) | z_{u,i} = z_0 ]
```

where `z_0` is the preregistered reference context, not a House label and not
source truth. The interaction uncertainty is retained in a candidate-level
interval rather than converted into confidence by a member-variance penalty.

## Sensor-consistent event law

The predicted event probability must use the same observation operator as the
runtime sensor:

```text
transport exposure
 -> persistent FOPDT state
 -> native block mean
 -> threshold/event probability
```

The current M1H implementation does not yet satisfy this law: it feeds the
filament hit-map value at the event cell directly into the event likelihood.
Therefore L2 in the attribution plan is a required implementation step, not
an already available result.

For each candidate/member/event, the replay will store:

```text
raw exposure, FOPDT state, block mean, threshold,
predicted event probability, observed event, log likelihood
```

No posterior, planner, House ID, or source truth is used to construct these
quantities.

## Candidate score and sensitivity guard

After sensor calibration, the candidate score is the hierarchical marginal
event likelihood over the frozen event window:

```text
L_PHIC(c) = log integral [ product_i Bernoulli(Y_i; q_{u,i}(c,delta)) ]
                     p(delta | z_{u,i}) d delta
```

The replay must also export a sensitivity interval obtained by bounding the
candidate-specific likelihood ratio by a fixed preregistered `Lambda`.
Candidates whose intervals overlap are not allowed to create a concentrated
posterior update. This is an uncertainty/identifiability guard, not a distance
penalty or planner rescue.

## Falsification and effectiveness gate

Run one read-only frozen-trajectory replay on existing H01/H02/H03 seed4:

1. Native PMFS event likelihood.
2. Frozen M1H likelihood.
3. Sensor-consistent likelihood.
4. PHIC hierarchical partial-invariance likelihood and sensitivity interval.

For each layer report:

- true-source rank;
- false-winner rank;
- true-vs-false likelihood margin;
- false-exclusion ratio after each event;
- NLL/Brier/calibration;
- candidate-dependent residual map by House and geometry class.

The M1 redesign is **not** considered effective unless the sensor-consistent
and PHIC layers improve the frozen margins without reading truth at inference,
and then pass a preregistered one-seed closed-loop screen on all three Houses.
A failure at L2 means observation-operator mismatch was not the only cause; a
failure after PHIC means the candidate-specific transport discrepancy remains
unidentified and the causal claim must be narrowed.

## Explicit non-claims

- BHIP, CFT, and proxy calibration do not prove cross-House gas localization.
- A low transport-member variance is not evidence of correctness; shared model
  bias can still have low variance.
- No new seed or closed-loop claim is authorized before the attribution replay.
- M1H remains a preserved negative result and is not retroactively relabeled.

