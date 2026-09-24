# FSEI Information-Fidelity Partition Objective v0

Date: 2026-09-25

Status:
**CANDIDATE ALGORITHM — REFERENCE-ONLY, NOT YET FROZEN FOR D1C**

This document derives a concrete partition mechanism from the exact
finite-sample emergent-identifiability decomposition.

It is intentionally written before the D1R reference bank is inspected.

---

## 1. Safe estimable channel

The full 10x30 binary support vector contains temporal/spatial dependence.

To avoid pretending that the 300 coordinates are independent samples when
measuring information fidelity, define a legal randomized-query channel:

- \(Q\) is a uniformly sampled observation coordinate from the frozen 300
  time-probe coordinates;
- \(H\in\{0,1\}\) is the hit/no-hit value at coordinate \(Q\);
- \(Q\perp S\) by construction.

Then the source-conditioned channel is

\[
p(h\mid s,q).
\]

For a partition \(M=g(S)\), the information discarded by merging source
microcells on this channel is

\[
F_Q(g)
=
I(S;H\mid M,Q).
\]

This is a genuine conditional mutual-information quantity for a finite
discrete channel.

It does not require a fake source transition process.

---

## 2. Explicit fidelity form

Under a uniform microcell prior and uniform query coordinate,

\[
F_Q(g)
=
\frac{1}{NQ}
\sum_m
\sum_{s\in S_m}
\sum_{q=1}^{Q}
D_{\rm KL}
\left[
{\rm Bern}(p_{sq})
\Vert
{\rm Bern}(\bar p_{mq})
\right],
\]

where

\[
\bar p_{mq}
=
\frac1{|S_m|}
\sum_{s\in S_m}p_{sq}.
\]

For the frozen D1R geometry:

- \(N=168\);
- \(Q=300\).

This quantity measures within-macro source information that the encounter
query channel can actually distinguish.

---

## 3. Merge fidelity cost

Suppose neighboring macrostates \(A\) and \(B\) are merged into
\(C=A\cup B\).

The incremental full-vector marginal fidelity cost is

\[
\Delta F_{\Sigma}(A,B)
=
\frac{1}{N}
\sum_{q=1}^{Q}
\left[
|A|D_{\rm KL}
(
{\rm Bern}(\bar p_{Aq})
\Vert
{\rm Bern}(\bar p_{Cq})
)
+
|B|D_{\rm KL}
(
{\rm Bern}(\bar p_{Bq})
\Vert
{\rm Bern}(\bar p_{Cq})
)
\right].
\]

This is a weighted Bernoulli Jensen-Shannon merge cost.

Only four-neighbor-connected source groups are eligible to merge.

---

## 4. Finite-sample complexity reduction

For the factorized Bernoulli working likelihood, every source group carries
\(Q\) Bernoulli parameters.

With \(n\) independent reference realizations per source, a regular
one-parameter Bernoulli predictive model has first-order expected estimation
regret approximately

\[
\frac{1}{2n}
\]

nats per parameter.

For a partition with \(K\) macrostates, pooling all source realizations within
each macro gives the source-prior-averaged first-order estimation regret

\[
R_n(K)
\approx
\frac{QK}{2nN}.
\]

Therefore one merge \(K\to K-1\) has approximate finite-sample complexity
benefit

\[
\Delta R_n
\approx
\frac{Q}{2nN}.
\]

For D1R:

\[
N=168,\quad Q=300.
\]

The value of \(n\) depends on the reference-only training fold.

This asymptotic approximation is not a confirmation endpoint.
It is a theory-derived partition-construction prior.

---

## 5. Parameter-free merge principle

A source merge is favored when

\[
\Delta F_{\Sigma}(A,B)
<
\Delta R_n.
\]

Equivalently:

> merge neighboring source states only when the expected finite-sample
> estimation-risk saved by removing one observation-law parameter block is
> larger than the encounter information lost by treating the two groups as one.

This is the local version of the global FSEI criterion.

A greedy connected algorithm is:

1. begin with 168 singleton source cells;
2. estimate source encounter probabilities from the training references only;
3. compute \(\Delta F_{\Sigma}\) for every four-neighbor-admissible merge;
4. select the smallest-cost merge;
5. accept it only while its cost is below the theory-derived complexity
   benefit;
6. update neighboring group profiles and repeat;
7. stop automatically when no admissible merge passes.

No target data and no hand-selected \(K\) are required.

---

## 6. Why this differs from ordinary connected Ward clustering

Connected Ward minimizes geometric or profile dispersion.

The proposed FSEI merge rule instead compares two quantities with direct
statistical meaning:

- information/fidelity lost by a merge;
- finite-sample estimation complexity removed by a merge.

A geometry-only Ward baseline can create groups without regard to observed
source distinguishability.

A profile-clustering baseline can minimize within-group profile distance but
does not explicitly price that distance against the finite-realization
estimation budget.

The empirical question remains whether this extra theory produces a real
fresh-target advantage.

---

## 7. Reference-only cross-fitting

The D1R bank has 16 independent realizations/source.

Proposed development folds:

- F1: reps 1-4
- F2: reps 5-8
- F3: reps 9-12
- F4: reps 13-16

For each outer fold:

1. learn the partition from the other 12 reps/source only;
2. fit every candidate/baseline observation model on the same 12 reps/source;
3. predict the held-out 4 reps/source;
4. lift every macro model to the same 168-cell support;
5. compute microcell log score.

Across folds report:

- mean paired log-score gain vs identity;
- partition ARI / VI;
- pairwise co-membership frequency;
- group-size/diameter stability;
- query-channel fidelity;
- encounter-profile stability.

The final algorithm family and all tuning rules are selected using reference
data only.

After selection, the chosen algorithm is re-fit on all 16 references/source
and serialized before D1C targets are generated.

---

## 8. Candidate family for fair comparison

The finite pre-registered family should include at least:

### Identity
168 independent source observation models.

### All-in-one
One pooled observation model; negative control.

### Geometry-only connected hierarchy
No plume information.

### Encounter-profile connected clustering
Same connectedness, profile-distance objective, finite \(K\) grid.

### Hierarchical shrinkage
No hard macrostate required; source parameters shrink toward local/global
means, with shrinkage strength selected by reference-only CV.

### MDL / marginal-likelihood pooling
Complexity-regularized statistical baseline.

### FSEI information-fidelity partition
The theory-derived merge criterion in this document.

Random size-matched partitions remain a diagnostic/null, not a serious
predictive competitor.

---

## 9. Honest source posterior

For a learned hard partition \(g\), the group observation law produces

\[
Q_g(m\mid y).
\]

The final PMFS-compatible posterior must be

\[
q_g(s\mid y)
=
Q_g(g(s)\mid y)
\frac{\pi_s}{\Pi_{g(s)}}.
\]

No group centroid is promoted to a precise source estimate.

This preserves the uncertainty that the observation cannot resolve.

---

## 10. Raw concentration safeguard

R0 showed that encounter/support structure is highly reproducible.

However previous S1 evidence showed that absolute concentration can remain
useful in low-variability regimes.

Therefore an encounter-only FSEI model must face a strong raw-concentration
baseline at D1C.

D1R should retain all raw pooled concentrations.

The primary thread will decide, before D1C targets, whether the final candidate
uses:

- encounter only;
- a preregistered hurdle/joint channel;
- or encounter for partition discovery plus a separately frozen raw
  microcell likelihood at inference.

Target results may not decide this choice.

---

## 11. Falsification conditions for the partition idea

The information-fidelity construction loses mainline value if reference-only
analysis shows any of the following:

- partitions are unstable across 12/4 folds;
- the stopping scale collapses to identity or all-in-one;
- ordinary hierarchical shrinkage matches its microcell log score;
- geometry/profile clustering gives the same result under equal search budget;
- fidelity loss is large even where predictive score improves;
- selected groups cross physical barriers without observation evidence;
- raw amplitude baselines dominate because encounter partitioning discards
  stable information.

No final D1C target should be generated until these reference-only questions
are resolved.
