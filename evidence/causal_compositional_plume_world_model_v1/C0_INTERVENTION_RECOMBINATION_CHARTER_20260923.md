# C0 Falsification Charter — Causal Compositional Plume World Model

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## Decision target

This experiment decides whether M4 has a genuine **compositional-intervention signal**.

It is not a full model implementation.

The candidate advances only if a mechanism-factorized model predicts an **unseen source × wind recombination** better than a matched-capacity monolithic model and improves downstream source identity.

## 1. Novelty boundary

Generic “causal gas propagation model” language is not new in GSL.

Older Bayesian gas-localization literature already used causal graphical models to describe gas propagation and observation dependence.

Therefore the M4 claim must be specifically about:

- reusable source / wind / geometry mechanisms;
- explicit interventions;
- unseen mechanism recombination;
- world-model generalization.

Do not claim first use of causality in gas localization.

## 2. Minimal 2 × 2 intervention design

Use **one House only** so geometry is frozen.

Select:

- source intervention S1;
- source intervention S2;
- wind intervention W1;
- wind intervention W2.

Generate independent stochastic plume seeds for each available cell.

Full factorial:

| | W1 | W2 |
|---|---|---|
| S1 | train | train |
| S2 | train | **held-out test** |

The key test is:

[
(S2,W2)
]

which must never be used to fit either model.

Then rotate the held-out cell in a second fold:

- hold out S1-W2;
- optionally repeat with other source/wind pairs.

## 3. Source intervention

Hold fixed:

- House geometry;
- wind condition;
- gas type;
- release rate;
- GADEN numerical settings.

Change only source position.

Choose S1/S2 source-blind:
- both free valid locations;
- spatially separated;
- avoid one being trivially adjacent to all sensors;
- predeclare before plume truth evaluation.

## 4. Wind intervention

Preferred order:

### A. Existing independent wind configurations
If the House scenario already contains two physically generated CFD/GADEN wind configurations, use them.

### B. Existing time-indexed wind regimes
If the scenario contains materially distinct wind states/sequences that can be frozen/replayed independently, use two predeclared regimes.

### C. Source-blind speed scaling of one CFD field
Only if A/B are unavailable.

Use a predeclared multiplicative speed intervention while preserving the vector-field topology:

[
W_2(x)=gamma W_1(x)
]

with (gamma) fixed before downstream evaluation.

Do **not** arbitrarily rotate a wind field through indoor obstacles and call it physical.

Record exactly which option is used.

## 5. Stochastic replication

Minimum pilot:

- 2 plume seeds per observed training combination;
- 2 independent plume seeds for the held-out combination.

More seeds are useful only after the first gate passes.

## 6. Two deliberately small model classes

Do not begin with WM3C's full masked-autoencoder/language machinery.

Gas mechanisms are already semantically known.

### Model A — monolithic control

One model:

[
F_{m mono}(O,W,Q_s)ightarrow C.
]

All variables are concatenated/conditioned jointly.

### Model B — compositional mechanism model

Separate:

[
z_E = E_{m env}(O,W)
]

[
z_S = E_{m source}(Q_s)
]

then combine through a fixed shared transport decoder:

[
C = D(z_E,z_S).
]

Parameter count must be matched to Model A within a predeclared tolerance.

No extra capacity for the factorized model.

## 7. Stronger mechanism version

If M6 GeoPT passes its pretrained-weight gate, C0 may use:

[
z_E = E_{m GeoPT}(O,W)
]

as a common environment representation.

But this is a later cross-candidate integration.

For the first M4 test, do not depend on M6 passing.

## 8. Output target

Prefer one physical field:

- concentration at a fixed sensor-height slice; or
- PMFS-compatible hit-probability field generated from concentration.

Do not train directly on source rank.

## 9. Source-blind primary C0 metrics

On the held-out S2-W2 combination:

- relative field error;
- hit/miss predictive log score;
- plume centroid/advection direction diagnostic;
- obstacle-boundary violation;
- source-injection locality.

These are diagnostic only.

## 10. Hard downstream metric

Freeze both models.

Use the predicted candidate forward fields in the same PMFS source-inference replay.

Primary outcome:

**truth-containing source-candidate rank.**

The factorized model must improve source rank on the held-out intervention combination.

Field MSE alone cannot pass M4.

## 11. Causal/compositional mechanism tests

### C0-M1 — source swap
Hold (W,O) fixed and swap only the source module.

Required:
- plume origin/injection follows source intervention;
- environment representation remains fixed.

### C0-M2 — wind swap
Hold source module fixed and swap environment/wind module.

Required:
- transport pattern changes consistently;
- source injection stays localized at the same source.

### C0-M3 — held-out recombination
Compose the S2 source module with W2 environment module even though this pair was never trained together.

This is the central M4 test.

### C0-M4 — label destructive null
Shuffle source/wind intervention labels in training while preserving sample counts and marginals.

The held-out recombination advantage must disappear.

## 12. Representation-invariance diagnostics

Do not use invariance alone as proof of causality.

But report:

- environment embedding variation when only source changes;
- source embedding variation when only wind changes.

Desired:

[
E_{m env}(O,W)
]

is unchanged by source intervention by construction/data path.

[
E_{m source}(Q_s)
]

is unchanged by wind intervention.

If implementation leaks the other variable into each encoder, M4's mechanism interpretation weakens.

## 13. Hard kill conditions

M4 is NO-GO as the main idea if:

1. monolithic model matches or beats compositional model on held-out recombination;
2. only field reconstruction improves but truth-source rank does not;
3. intervention-label shuffle preserves the gain;
4. physically valid wind intervention cannot be constructed;
5. the factorized model requires materially more parameters;
6. the result appears only for one held-out pair/seed;
7. “causal” benefit disappears when capacity/data are controlled.

## 14. Minimum conclusion vocabulary

If C0 passes:

`POSITIVE COMPOSITIONAL-INTERVENTION SIGNAL`

Do not yet write:

`causal mechanism discovered`

or:

`causal identifiability proven`.

Those require stronger intervention coverage and final literature/theory audit.

## 15. Current status

`READY FOR DATA-GENERATION COST AUDIT + 2×2 INTERVENTION PILOT`.
