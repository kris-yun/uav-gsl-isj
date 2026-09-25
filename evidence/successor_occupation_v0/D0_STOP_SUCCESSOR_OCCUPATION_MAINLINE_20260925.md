# Successor / Occupation World-Model D0 Decision — 2026-09-25

Decision:

**D0_FAIL_STOP_SUCCESSOR_OCCUPATION_MAINLINE**

This STOP applies to the successor/occupation route as the primary source-localization innovation.

## Why it was tested

D1R showed that source-conditioned mean encounter profiles are:

- highly reproducible across independent plume realizations;
- strongly low-dimensional;
- spatially smooth over the dense 168-source panel.

This motivated a far-domain audit of successor representations, successor measures,
occupation/resolvent operators and predictive world models.

Relevant mother-theory anchors include:

- Agarwal et al., ICML 2025, *Proto Successor Measure: Representing the Behavior Space of an RL Agent*;
- 2026 latent-dynamics / successor-measure work such as RLDP;
- Perron-Frobenius / transfer-operator methods for stochastic dynamical systems.

## D1R evidence

Mean encounter matrix shape:

168 sources x 300 registered time-probe queries.

Low-rank structure:

- 90% variance: 5 singular components;
- 95%: 10;
- 99%: 29;
- participation-ratio effective rank about 2.50.

The low rank is not explained only by total hit-rate amplitude:

- removing each source's row mean still gives 90% at 5 components;
- L2-normalizing each source profile still gives 90% at 5;
- per-query standardization gives 90% at about 10 components.

However, the first mode is strongly correlated with source x coordinate
(correlation about -0.89), showing that a substantial part of the structure is
ordinary spatial transport smoothness.

## Source-held-out interpolation

Use independent realization halves:

- source profiles are estimated from one 8-realization half;
- completely unseen source profiles are evaluated on the other 8-realization half.

Checkerboard 84/84 source holdout:

Simple 4-neighbor interpolation gives approximately:

- cosine median: 0.983-0.986;
- relative-L2 median: 0.176-0.195.

The within-source 8/8 stochastic noise floor is:

- cosine median: 0.9886;
- relative-L2 median: 0.1534.

RBF kernel regression and PCA+RBF do not consistently beat the local interpolation
baseline. Thus the low-rank structure itself does not establish a distinct
operator-learning advantage.

Source ranking under interpolated profiles remains far below the source-specific
oracle profile:

- source-specific 8/8 oracle: top-1 about 27%, median rank 3;
- source-held-out interpolated models: top-1 roughly 7-15%, median rank roughly 4-6.

## Shared temporal dynamics signal

A genuine source-independent temporal prediction signal exists.

A shared 30x30 ridge transition model, learned only from training sources,
predicts one-step future mean encounter states on unseen sources with MSE about
0.0089-0.0094, versus:

- persistence: about 0.0168-0.0173;
- per-probe diagonal affine dynamics: about 0.0142-0.0148.

Therefore a shared temporal plume-occupation dynamics object is real.

Multi-step rollout from the true current state also improves over persistence.

## Why that is not enough for the GSL mainline

When the same learned dynamics operator is used to generate the complete
source-conditioned future occupation profile from a spatially interpolated
initial state, performance collapses:

Direct source interpolation:

- MSE about 0.00835-0.00906;
- relative-L2 median about 0.176-0.195.

Source-initial-state + learned temporal-operator rollout:

- MSE about 0.0534-0.0541;
- relative-L2 median about 0.62-0.64.

Thus the shared temporal operator is useful for forecasting from an already
observed plume state, but it does not replace the source-to-observation model.

For the source-localization task, ordinary spatial interpolation of expected
profiles is substantially stronger than the proposed successor/occupation
construction.

## Scientific conclusion

The D1R data support:

- a reusable temporal plume-prediction auxiliary module;
- a smooth low-dimensional expected encounter field.

They do NOT support:

- successor measure as the primary source-localization innovation;
- an occupation/resolvent source model that beats ordinary interpolation;
- a source-to-profile world model worthy of new GADEN runs.

No full concentration cubes or new simulations are authorized for this route.

The route is stopped as the mainline before additional computation.
