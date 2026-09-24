# D1R Exploratory Successor/Occupation Signal — 2026-09-25

Status: **EXPLORATORY POSITIVE SIGNAL — NOT A MAINLINE GO**

This analysis uses only the completed D1R 168x16 reference tensor.
No new simulation and no final target are used.

## Encounter matrix

For each source, average the binary encounter support over all 16
realizations, producing a 168 x 300 source-to-encounter matrix.

After centering across sources:

- 90% of source-profile variance is captured by 5 singular components;
- 95% by 10;
- 99% by 29;
- participation-ratio effective rank is approximately 2.50.

Thus the stable source-conditioned encounter object is strongly
low-dimensional.

## Split subspace stability

Construct independent mean encounter matrices from reps 1..8 and 9..16.

Principal angles between their right-singular subspaces:

- top-2: about 2.72 and 1.26 degrees;
- top-3: maximum about 4.84 degrees;
- top-5: maximum about 10.16 degrees.

Each split independently needs about 6 dimensions for 90% variance and 11 for
95%.

Therefore the low-dimensional encounter subspace itself is reproducible across
independent plume realizations.

## Unseen-source interpolation diagnostic

Use a checkerboard source split on the complete 24x7 panel.

For every held-out source, predict its 300-D mean encounter profile using only
the mean profile of its available four-neighbor training sources.

Two complementary checkerboard holdouts each contain 84 unseen sources.

Results:

- parity-0 holdout:
  - cosine median 0.98949;
  - cosine q10 0.96662;
  - relative-L2 median 0.14962;
  - relative-L2 q90 0.26464.
- parity-1 holdout:
  - cosine median 0.98898;
  - cosine q10 0.97389;
  - relative-L2 median 0.15751;
  - relative-L2 q90 0.24828.

For comparison, the source-wise first8-vs-last8 encounter-profile relative-L2
has median about 0.15343 and q90 about 0.23409.

Hence the simplest local interpolation predicts unseen source encounter
profiles at approximately the stochastic split-noise floor.

## Interpretation

This signal argues against exhaustive per-source equivalence banking as the
main scientific object.

A more promising object is a transferable low-dimensional
source-to-expected-encounter / occupation operator.

Candidate far-domain theory families for audit:

- successor representations / successor measures;
- occupation and resolvent operators of Markov transport;
- Perron-Frobenius / transfer-operator representations;
- latent predictive world models that preserve successor measures.

This is only a direction-selection signal.

The route must be rejected if:

- ordinary spatial interpolation already explains all localization benefit;
- the operator cannot be defined without fake RL policy semantics;
- direct GSL prior art already contains the same source-to-occupation object;
- cross-environment use still requires exhaustive repeated releases for every
  candidate source.
