# D1R Reference-Only Selection Contract v0

Date: 2026-09-25

Status:
**PRE-D1R ANALYSIS PLAN — TO BE FINALIZED AFTER AUXILIARY-PRO REVIEW, BEFORE READING D1R OUTCOMES**

## Primary development objective

All candidate methods remain on the original 168-cell source task.

For validation target \((s,y)\), score

\[
\ell(q;s,y)=\log_2 q(s\mid y).
\]

For candidate c versus identity:

\[
d_c(s,y)=\ell(q_c;s,y)-\ell(q_{\rm id};s,y).
\]

Reference cross-fitting estimates

\[
\widehat\Delta_{\rm ref}(c)
=
\frac{1}{168}
\sum_s
\frac{1}{16}
\sum_r d_c(s,y_{sr})
\]

using only predictions from folds in which realization r was held out.

No macro accuracy is used for model selection.

## Four-fold source-stratified realization CV

Use the same replicate indices for every source:

- fold 1: 1-4
- fold 2: 5-8
- fold 3: 9-12
- fold 4: 13-16.

Every candidate uses exactly 12 training realizations/source and four held-out
realizations/source per fold.

Hyperparameter searches must have a finite frozen grid and equalized budget
where meaningful.

## Required model-selection report

Before a method can be frozen for D1C, report:

1. paired microcell log-score gain vs identity;
2. paired gain vs strongest ordinary pooling/shrinkage baseline;
3. fold-to-fold score dispersion;
4. partition ARI and VI;
5. source-pair co-membership stability;
6. group cell-count / area / diameter;
7. query-channel fidelity loss;
8. exact-cell rank / MAP error / 0.5 m / 1.0 m mass as diagnostics;
9. raw-concentration baseline results;
10. computational/model-selection budget.

## Firewall

D1R may choose the final algorithm.

D1C may only evaluate it.

No D1C target can alter:

- observation channel;
- partition family;
- K/stopping rule;
- shrinkage strength;
- priors;
- smoothing;
- calibration;
- probability floor;
- baseline set;
- primary endpoint;
- target sample size;
- PASS threshold.
