# Blackwell / Le Cam Source-Experiment Audit — 2026-09-25

Decision: **HOLD_BLACKWELL_AS_EVALUATION_THEORY_NOT_MAIN_ALGORITHM**

No new simulation or neural model is authorized for this route.

## Mother theory

Treat the stochastic plume observation process as a statistical experiment indexed by source S.

A representation T(Y) is Blackwell sufficient for source inference if every source-decision problem that can be solved from raw observation Y can be reproduced from T(Y) through a source-independent stochastic transformation.

For finite source hypotheses this is stronger than maximizing one classifier's accuracy: it asks for decision-relevant information preservation across a family of losses / source contrasts.

Recent 2025 work has brought Blackwell sufficiency directly into representation-learning analysis, and 2025 transfer work studies sufficient representations under target-domain adaptation.

## GSL motivation from LSC

D1R LSC showed that local neighbor-source stochastic distinguishability predicts fresh binary source confusion and fresh 168-cell posterior NLL.

Therefore a useful representation should preserve the local source statistical experiment, not merely maximize a global average classification objective.

## Zero-simulation linear audit

Data:
- D1R 168 x16 x300 log(1+ppm);
- train-half internal 6/2 fitting/calibration and opposite 8 fresh evaluation;
- 305 frozen spatial neighbor source pairs.

Representations:
- raw standardized 300-D;
- PCA;
- global shrinkage LDA.

Fresh results, direction A:
- raw multiclass log2 score: -3.888;
- PCA: -4.042;
- LDA: -2.737;
- raw mean neighbor-pair AUC: 0.822;
- LDA mean AUC: 0.918;
- raw mean neighbor-pair error: 0.232;
- LDA: 0.126.

Direction B:
- raw multiclass log2: -4.022;
- PCA: -4.067;
- LDA: -2.509;
- raw mean pair AUC: 0.825;
- LDA: 0.916;
- raw pair error: 0.217;
- LDA: 0.132.

Thus ordinary global LDA already preserves/extracts a large amount of source decision information across several metrics.

## Edge-level non-dominance

However LDA does not dominate raw observations for every local pair:
- only ~52-55% of neighbor pairs have lower fresh error;
- ~30-36% are unchanged;
- ~4.6-8.5% are worsened by at least 0.125 absolute error.

This demonstrates the distinction between average discriminant improvement and Blackwell-like all-decision preservation.

## Blackwell-like model-selection screen

Using only the training half, LDA dimension/temperature were selected three ways:

1. maximize multiclass proper score;
2. minimize the 90th percentile local-pair binary log loss;
3. minimize worst-edge local-pair binary log loss.

Fresh direction A:
- global selection: -2.549 bit;
- q90-local-safe selection: -3.046 bit;
- minimax selection: -5.756 bit.

Fresh direction B:
- global: -2.472 bit;
- q90-local-safe: -2.689 bit;
- minimax: -5.705 bit.

The q90-safe rule mainly flattened posterior temperature and did not alter pairwise ranking; strict minimax protection severely damaged global posterior quality.

## Decision

Blackwell/Le Cam theory is scientifically useful for defining information-preservation tests, but this simple route does not yet yield a distinct GSL inference algorithm beyond ordinary discriminant representation + calibration.

Do not claim novelty for:
- Blackwell sufficiency itself;
- sufficient representations;
- global LDA;
- local-risk calibration;
- minimal-sufficient representation learning.

Retain as an evaluation principle:

> a future representation should be judged not only by average source accuracy but by how much local source-decision information it destroys.

## Next mechanism screen

Static LSC remains the strongest validated bottleneck.

The next reference-only question is:

> does temporal/path structure provide additional distinguishability specifically for the locally confusable source pairs?

This will be tested before proposing any path-space model.