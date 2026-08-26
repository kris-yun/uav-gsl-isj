# CTT exact event factorisation V2

Date: 2026-08-26  
Status: superseded on 2026-08-26 by `CTT_EXACT_DISCRETE_EVENT_FACTORISATION_V3.md`; continuous ordered-event normalization was not fully specified. Retained as an audit record.

## Why V1 was revised

V1 described M2 with an unbalanced optimal-transport score but did not specify the probability model for which that score was a likelihood or a proven variational bound. Adding it to M3 survival would therefore recreate the likelihood-contract ambiguity that invalidated earlier PMFS variants. V2 keeps the seismic idea of global phase association but uses an exact normalized latent-phase model; OT remains a diagnostic comparator, not the online likelihood.

## M1 carrier

For candidate \(s\), M1 produces non-negative physically admissible path/delay components

\[
h_{sk}(t),\qquad k=1,\ldots,K_s,
\quad h_s(t)=\sum_k h_{sk}(t).
\]

The component index is not learned from House truth. It is the frozen index of the physical response-bank path/delay modes; a background state \(k=0\) is calibrated from blank-sensor data. For block \(B\), define

\[
H_{sk}(B)=\int_Bh_{sk}(t)dt,
\qquad
\phi_{sk,B}(t)=\frac{h_{sk}(t)}{H_{sk}(B)}
\]

for nonzero exposure. Zero-exposure components are removed before normalization and logged.

## A1: independent-event reference

Let ordered burst onsets in the block be \(E_B=(t_1,\ldots,t_N)\). The coarse M1 comparator assumes independent latent modes:

\[
J_1(s)=\sum_{j=1}^{N}
\log\left[\sum_{k=0}^{K_s}\pi_{sk}\phi_{sk,B}(t_j)\right],
\]

where \(\pi_{sk}\) is the normalized frozen exposure mass including background. This is a proper density conditional on \(N\); it uses temporal shape but not sequence-level path consistency.

## M2: exact latent-phase association

Let \(z_j\in\{0,\ldots,K_s\}\) denote the physical path/delay state assigned to burst \(j\). Candidate \(s\) supplies a row-stochastic transition matrix \(A_s\) computed from overlap of consecutive frozen physical path populations; no event labels or source truth enter it. The conditional event likelihood is

\[
J_2(s)=\log\sum_{z_{1:N}}
\pi_{s,z_1}\phi_{s,z_1,B}(t_1)
\prod_{j=2}^{N}
A_s(z_{j-1},z_j)\phi_{s,z_j,B}(t_j).
\]

It is evaluated exactly by the forward algorithm in \(O(NK_s^2)\). Every forward responsibility and transition contribution is logged. Time permutation changes the sequence likelihood while preserving event count and marginal event values. A1 is recovered by replacing every row of \(A_s\) with \(\pi_s\), making the ablation algebraically exact.

If later evidence shows \(O(NK_s^2)\) is too slow, a sparse transition implementation may be used only if it preserves the exact score within a frozen numerical envelope. Sinkhorn/OT may initialize or visualize association, but cannot replace \(J_2\) without a separately proven bound.

## M3: complementary count and survival likelihood

Carry source strength \(q\) jointly with \(s\) from the previous block; do not fit it on the block being scored. Define

\[
\Lambda_s(B,q)=\Lambda_{bg}(B)+q\sum_kH_{sk}(B).
\]

M3 is

\[
J_3(s,q)=N\log\Lambda_s(B,q)-\Lambda_s(B,q)-\log(N!).
\]

For \(N=0\), this is exactly the survival term \(-\Lambda_s\). The block likelihood factorizes as

\[
\log p(E_B,N\mid s,q)=J_2(s)+J_3(s,q).
\]

The joint update is

\[
p_b(s,q)\propto p_{b-1}(s,q)
\exp\{J_2(s)+J_3(s,q)\},
\qquad
p_b(s)=\int p_b(s,q)dq.
\]

M1 is not added again. Native PMFS may not score the same block.

## Exact ablation ladder

| Arm | Score | Question |
|---|---|---|
| A0 | native PMFS | baseline |
| A1 | \(J_1\) from M1 | does the physical temporal field carry source information? |
| A2 | \(J_2\) | does global phase continuity add information beyond iid events? |
| A3 | \(J_2+J_3\) | does candidate exposure/count survival add conditional information? |
| A2-P | \(J_2\) after time permutation | is order load-bearing? |
| A3-S | \(J_2+J_3\) after shifting physical exposure away from real silent intervals | are timed misses load-bearing? |

Required direct increments are \(margin(J_2)-margin(J_1)>0\) and \(margin(J_2+J_3)-margin(J_2)>0\) under frozen paired-bootstrap rules. A module that only changes entropy, variance or final path is not positive information.

## Degenerate contracts

- \(N=0\): \(J_2=0\), so only M3 carries evidence.
- \(K_s=1\): A2 must equal A1 up to numerical tolerance; no phase-association claim is allowed.
- identical \(h_s,A_s,\Lambda_s\): candidates must tie exactly.
- zero physical exposure with events: the frozen background state keeps the likelihood finite; the case is logged as background-dominated.
- row sums of \(A_s\) and integrals of every \(\phi_{sk,B}\) must equal one within the refinement envelope.

## Identification gate

M2 can be claimed only when at least two candidates have distinct sequence distributions after matching their marginal event densities. M3 can be claimed only when candidates have distinct predeclared exposure in silent windows and the carried nuisance prior does not absorb that contrast. These conditions are checked before truth reveal; their failure is `INVALID_IDENTIFIABILITY`, not a negative performance average.
