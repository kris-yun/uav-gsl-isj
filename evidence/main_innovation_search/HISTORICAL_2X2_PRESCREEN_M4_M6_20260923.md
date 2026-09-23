# Historical 2×2 Pre-Screen Plan — M4 vs M6

Date: 2026-09-23  
Branch: \`research/main-innovation-search-parallel-v1\`

## Controlled asset now verified

Historical project branch:

\`project/research-master-20260914\`

contains:

\[
3\ \text{Houses}
\times
2\ \text{sources}
\times
2\ \text{transport conditions}
=
12
\]

fixed-route histories.

Within every House:

- all four pose sequences are exactly identical;
- all four timestamps are exactly identical;
- SA_fast and SB_fast use exactly the same recorded wind sequence;
- SA_slow and SB_slow use exactly the same recorded wind sequence.

Fast and slow are not simple constant wind scaling:
- scalar-fit relative vector RMSE is 0.483 / 0.444 / 0.229 for H01/H02/H03.

Thus this is a valid **source × transport intervention-style mechanism asset** for pre-screening.

It is not a replacement for new independent dense-field GADEN data.

## Negative result already obtained

A zero-training additive recombination:

\[
\hat f(S,W)
=
f(S,W')
+
f(S',W)
-
f(S',W')
\]

fails to beat the same-source/opposite-wind baseline in 0/12 held-out combinations at every tested horizon.

Therefore:
- simple additive source+wind decomposition is rejected;
- M4 must use causal **operator composition**:
  \[
  C=\mathcal T_{W,O}(Q_S).
  \]

## Shared historical pre-screen

### M4 arm

Compare matched-capacity:

1. monolithic:
   \[
   F(S,W,O,x)\rightarrow c
   \]

2. operator-compositional:
   \[
   Q_S=f_Q(S),
   \qquad
   c=\mathcal T_{W,O}(Q_S;x).
   \]

Cross-validation:
- hold out one source×wind combination at a time;
- train on the other three;
- repeat across all four combinations × three Houses.

Do not use truth-source endpoint to tune architecture.

### M6 arm

Compare:

1. random-init GeoPT architecture + same small gas/source head;
2. official pretrained GeoPT frozen/partially frozen backbone + same head.

Use:
- House geometry/SDF/boundary direction;
- recorded local wind along the fixed route;
- candidate source-relative injection features.

Same held-out source×wind folds.

## Pre-screen metrics

Before source identity:
- held-out concentration/log-concentration error;
- hit/miss predictive log score if thresholded;
- calibration by wind/source condition.

Then candidate identity:
- for a held-out query, score both source candidates under the held-out wind;
- record correct source rank among SA/SB.

This is a 2-candidate mechanism pre-screen only.

It does not replace full PMFS candidate-rank evaluation.

## Decision

Advance only if:

- M4 factorized operator beats matched-capacity monolithic on multiple held-out combinations; or
- M6 pretrained GeoPT beats random-init under the same low-data protocol.

If neither shows a signal, do not spend resources on dense-field/full PMFS integration.
