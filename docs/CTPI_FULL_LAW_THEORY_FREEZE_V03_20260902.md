# CTPI-FL V0.3 — theory freeze

**Framework:** Causal Transport Partial Identification from Full Route-Encounter Laws  
**Status:** oracle falsification candidate; runtime / closed loop / neural training not authorized.

## One mother problem

Given an already executed sensing route and deployable context `C_t`, the source response is a controlled interventional query in which both the candidate source and the already executed sensing design are clamped:

\[
P(K_t\mid do(S=s),do(X_{1:t}=x^{obs}_{1:t}),C_t).
\]

The framework asks three sequential questions:

1. what stochastic route response can `do(S=s)` cause? — M1;
2. which source interventions are distinguishable before looking at the realized gas count? — M2;
3. after observing the realized count, which distinctions remain robust to finite transport-ensemble uncertainty? — M3.

## M1 — CREL

For source `s`, transport member `m`, and visible stops `V_t`,

\[
K_{sm,t}=\sum_{j\in V_t} E_{smj},
\qquad E_{smj}\in\{0,1\}.
\]

Output:

\[
\widehat P_{s,t}(K)=M^{-1}\sum_m\delta_{K_{sm,t}}.
\]

M1 does not read measured gas.

## Proposition 1 — exact F00 mean-projection limit

Frozen F00 forms

\[
q_{sj}=\frac{\sum_m E_{smj}+1/2}{M+1},
\]

and then

\[
\bar q_s=\frac1N\sum_j q_{sj}
=\frac{\sum_mK_{sm}+N/2}{N(M+1)}.
\]

Therefore its count-only physical likelihood

\[
\ell_{F00}(s)=H\log\bar q_s+(N-H)\log(1-\bar q_s)
\]

factors through the scalar

\[
T_s=\sum_mK_{sm}.
\]

If `T_i=T_j`, F00 gives the two sources exactly the same physical likelihood for every `H`. Any later difference comes from prior/context outside this physical statistic.

This is an expressivity theorem, not by itself proof that the lost information matters for the true source in the current development tapes. The Oracle Gate therefore separately checks whether the true source ever belongs to such an exact-mean alias class and, when it does, whether the full-law persistence breaks the physical-likelihood tie in the truth direction. If no true-source hard-alias context exists, the direct task relevance of Proposition 1 is marked `NOT_IDENTIFIED` rather than claimed.

## M2 — CDIG

Let `n_s(k)` be the empirical histogram and

\[
C_s(k)=\sum_{u\le k}n_s(u).
\]

Output 1 — theorem-linked CDF geometry:

\[
G_{ij}=\sum_{k=0}^{N-1}[C_i(k)-C_j(k)]^2.
\]

`G_ij=0` iff the empirical laws are identical.

Output 2 — interpretable empirical transport radius:

\[
R^T_{ij}=\frac12\sum_k|n_i(k)-n_j(k)|.
\]

This is the number of ensemble outcomes outside the two histograms' maximal common overlap, and the minimum number of outcomes in one empirical law that must be changed to transform it into the other.

M2 reads only M1 output. It does not read measured gas or source truth.

## M3 — APRS

For observed route hit count `H`, use the discrete Ranked Probability Score:

\[
RPS(P,H)=\sum_{k=0}^{N-1}[F_P(k)-\mathbf1(H\le k)]^2.
\]

### Proposition 2 — strict full-law separation

For true law `P` and candidate law `Q`,

\[
\mathbb E_{H\sim P}[RPS(Q,H)]-\mathbb E_{H\sim P}[RPS(P,H)]
=\sum_{k=0}^{N-1}[F_Q(k)-F_P(k)]^2.
\]

Thus if `P != Q`, the expected regret is strictly positive. In particular, if `P` and `Q` have equal mean but different shape, F00's physical statistic can tie while RPS can strictly distinguish the laws in expectation.

### Exact finite-ensemble robustness without a fixed q

For every deletion level `q=0,...,M-1`, retain `r=M-q` members. The implementation computes exact RPS numerator bounds over all such retained sub-multisets by dynamic programming on the discrete histogram; no member-label enumeration or approximation is required.

Source `a` robustly fits the observation better than `b` through depth `R^O_ab` when, for every deletion level up to that depth,

\[
\max RPS_a(q)<\min RPS_b(q).
\]

No single deletion level is selected.

## Two-axis partial-identification output

For all intrinsic integer levels `r_T,r_O=1,...,M`,

\[
\mathcal S_t(r_T,r_O)
=
\{b:\nexists a\;R^T_{ab}\ge r_T\;\land\;R^O_{ab}\ge r_O\}.
\]

The complete surface is the primary output. A persistence score obtained by averaging membership over the intrinsic `M x M` grid is descriptive support only, not a calibrated posterior.

## Adaptive meaning

No tuned `alpha`, deletion depth, margin, kernel bandwidth, temperature, or candidate-specific gain is used. Resolution is determined by the empirical law separation and the observation-conditioned proper-score robustness spectrum.

## Interpretation boundaries

- This oracle construction is trajectory-conditioned: `P(K | do(S=s), do(X=x_observed), context)`.
- It does not yet prove a bank-free unknown-site M1.
- It does not solve unknown source strength; later `Q` must be a source-shared nuisance, never a per-candidate fitted gain.
- Historical H01/H02/H03 assets are development data, not independent confirmation.
- Old persistent-sensor and stop-resolved modules remain NO-GO and are not reused.
