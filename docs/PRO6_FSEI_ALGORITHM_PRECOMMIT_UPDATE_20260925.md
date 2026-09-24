# PRO6 UPDATE — Concrete FSEI Partition Candidate + Precommit Margins

Date: 2026-09-25

Primary thread has now converted the FSEI theory into a pre-data candidate
partition algorithm.

Main branch files:

- 01_idea/FSEI_INFORMATION_FIDELITY_PARTITION_V0_20260925.md
- research/causal_emergent_source_scale_v0/fsei_partition.py
- research/causal_emergent_source_scale_v0/D1R_REFERENCE_SELECTION_CONTRACT_V0_20260925.md
- research/causal_emergent_source_scale_v0/D1C_EFFECT_POWER_PRECOMMIT_V0_20260925.md

## Candidate merge rule

For adjacent source groups A,B, estimate the encounter-channel fidelity loss as
a weighted Bernoulli Jensen-Shannon merge cost:

Delta F_sum(A,B).

Compare it against the first-order finite-sample estimation-regret reduction
from removing one Q-parameter block:

Delta R_n approximately Q / (2 n N).

Accept a connected merge only when:

Delta F_sum(A,B) < Delta R_n.

This gives an automatic stopping scale with no manually selected K.

The algorithm is a candidate only. It must be beaten by ordinary baselines or
discarded.

## Reference CV

Pre-data plan:

- 4 folds of 4 realizations/source;
- train on 12, validate on 4;
- every model predicts the original 168-cell posterior;
- primary reference score is held-out microcell log score;
- partition stability/fidelity are mandatory diagnostics.

## Proposed D1C minimum effects

Written before D1R outcomes:

- candidate vs identity:
  delta_id = log2(1.15) ~= 0.2016 bits/target;
- candidate vs strongest ordinary pooling/shrinkage baseline:
  delta_ordinary = log2(1.05) ~= 0.0704 bits/target.

Target count J is selected from {2,4,8} using only D1R OOF variance components,
not the D1R mean effect.

These numerical margins are not final until your red-team and primary-thread
review, but they must be discussed now, before D1R/final targets.

## What I need from you

In your current D1R->D1C deliverables, directly attack:

1. whether Q/(2nN) is a defensible first-order complexity benefit for the
   factorized Bernoulli predictive family;
2. whether weighted Bernoulli JS is the right estimable fidelity surrogate;
3. whether another ordinary MDL/Bayesian pooling rule is mathematically
   equivalent to this FSEI merge rule;
4. whether 15% and 5% multiplicative true-source-probability margins are too
   weak/strong and why;
5. whether the 4x(12/4) reference CV structure is statistically sound;
6. what stronger ordinary shrinkage baseline could make the FSEI partition
   unnecessary.

Do not run targets or change D1R.
