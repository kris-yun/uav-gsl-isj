# Score contract and frozen decisions

## Why the V1 Energy Score is changed before execution

V1 used the V-statistic empirical Energy Score:

`ES_V = K^-1 sum_i ||X_i-y|| - (2 K^2)^-1 sum_{i,j} ||X_i-X_j||`.

For K independent ensemble members from an underlying law P:

`E[ES_V] = ES(P,y) + (2K)^-1 E||X-X'||`.

The extra term depends on source dispersion. Since V2 is explicitly testing
dependence/dispersion structure, that finite-K term is a confound if the target
of inference is the underlying source-conditioned law.

Because V1 has NOT been scientifically executed, V2 predeclares the fair
U-statistic estimator as the PRIMARY score:

`ES_U = K^-1 sum_i ||X_i-y||
        - [2 K (K-1)]^-1 sum_{i != j} ||X_i-X_j||`.

Lower is better.

`ES_V` is still reported as a diagnostic only and never changes the decision.

## Full mean-field context baseline

Using the full held-out binary target `Y(t,q)`, also rank sources by marginal
Brier loss:

`MB_s(Y) = mean_{t,q} (Y(t,q) - p_hat_s(t,q))^2`.

This uses all 300 mean encounter probabilities and no joint dependence.
It is a context comparator, not part of the dependence randomization gate.

The old 10-D count-mean Euclidean prototype is also reported as `COUNT_MEAN`
for continuity only.

## Splits

Primary:
- A: reference reps 1..8, targets 9..16
- B: reference reps 9..16, targets 1..8

Robustness:
- C: odd reps reference, even reps target
- D: even reps reference, odd reps target

A/B/C/D reuse the same 288 OPEN realizations; they are cross-fit directions,
not four independent confirmations.

## Surrogate repetitions

Exactly 500 surrogate repetitions, seed `2026092603`.

For every directed split and every repetition:
- generate C1 permutations independently within each source, `(t,q)`;
- generate C2 permutations independently within each source, `t`;
- verify all preservation assertions before scoring.

No target value or source-ranking metric enters permutation construction.

## Metrics

Primary ranking metric:
- mean true-source rank across held-out targets; lower is better.

Also report:
- median true-source rank;
- mean reciprocal rank;
- top1 with explicit name `unique_top1_fraction`;
- top3;
- tie frequency.

For each layer/control report empirical "as-good-or-better" surrogate fraction:
- rank: fraction surrogate mean-rank <= RAW mean-rank;
- unique-top1: fraction surrogate unique-top1 >= RAW unique-top1.

These are reported as frozen reference randomization fractions. Do not call
them universally valid p-values.

## Decision labels

### `DEPENDENCE_D0_CROSS_TIME_SIGNAL`
All:
1. RAW mean true rank is strictly better than the C2 median in primary A and B.
2. Pooled A+B C2 rank as-good-or-better fraction <= 0.05.
3. RAW pooled A+B mean rank is also strictly better than C1 median.
4. In pooled robustness C+D, RAW mean rank is better than C2 median.
5. Robustness C2 rank as-good-or-better fraction <= 0.10.
6. RAW does not have lower pooled MRR than C2 median in either primary or
   robustness pools.

Interpretation:
within this 10-D count representation and K=8 reference budget, cross-time
realization pairing carries development-set source identity beyond complete
each-time snapshot/count marginals. This authorizes only a fresh confirmation
design for the dependence object.

### `DEPENDENCE_D0_INSTANTANEOUS_JOINT_ONLY`
All:
1. CROSS_TIME_SIGNAL conditions fail.
2. Pooled A+B C1 rank as-good-or-better fraction <= 0.05.
3. Pooled A+B C2 median mean-rank is better than C1 median mean-rank.
4. RAW is not materially worse than C2: RAW mean rank <= C2 median + 0.25 rank.
5. Robustness C1 rank as-good-or-better fraction <= 0.10.

Interpretation:
information beyond complete binary marginals exists, but it is adequately
explained by each-time spatial snapshot/count structure; no evidence that
cross-time pairing is required.

### `DEPENDENCE_D0_MEAN_FIELD_ONLY`
If pooled primary C1 rank as-good-or-better fraction > 0.05 and no stronger
layer gate passes.

Interpretation:
this representation provides no development evidence that joint dependence
adds source identity beyond the complete `p_s(t,q)` mean encounter field.

### `DEPENDENCE_D0_INCONSISTENT_HOLD`
Use when effects are directionally inconsistent across A/B or the preservation
assertions pass but none of the above scientific interpretations is stable
enough to assign.

### `DEPENDENCE_D0_HOLD_DATA_CONTRACT`
Only for missing/corrupt R0 assets, invalid 18x16 contract, bad array schema,
or failed preservation assertions.

## Important non-claims

Even `CROSS_TIME_SIGNAL` does NOT establish:
- multimodality;
- a hidden branching state;
- a learned world model;
- cross-House generalization;
- online source posterior calibration;
- real-flight deployability.

It only identifies which dependence layer deserves the next fresh test.
