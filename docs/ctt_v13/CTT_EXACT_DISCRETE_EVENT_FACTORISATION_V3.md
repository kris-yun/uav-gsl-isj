# CTT exact discrete event factorisation V3

Date: 2026-08-26  
Status: current formula candidate; no implementation or House qualification authorized until the gates pass.

## Observation object

Use the native sensor/PMFS time grid inside a completed block \(B\); no new bin width is tuned. After applying the frozen MOX recovery-time parser, define

\[
y_n=\mathbf 1\{\text{a burst onset occurs in native bin }n\},
\quad n=1,\ldots,T,
\quad N=\sum_n y_n.
\]

The parser's blank-sensor false-alarm rule and refractory/recovery rule are frozen before any premise truth is revealed.

## M1 — physical hidden-phase emissions

M1 maps candidate \(s\), physical response-bank mode \(k\), robot state and wind/map fields to a bin exposure \(h_{skn}\ge0\). The mode set is the immutable response-bank index, not a clustering selected from House outcomes. With source strength nuisance \(q\) carried from block \(b-1\),

\[
r_{skn}(q)=1-\exp[-\{\lambda_{bg,n}+q h_{skn}\}\Delta t_n]
\]

is the probability of a burst onset in bin \(n\) conditional on physical phase \(k\). M1 also provides a row-stochastic, possibly time-inhomogeneous transition \(A_{s,n}(k,k')\) from overlap of the frozen backward path populations at adjacent bins. All row sums and \(0\le r\le1\) are hard numerical contracts.

## A1 — iid physical-field comparator

Propagate the physical state occupancy without looking at \(y\):

\[
\rho_{s,n+1}=\rho_{s,n}A_{s,n}.
\]

The marginal burst probability is

\[
\bar r_{sn}(q)=\sum_k\rho_{skn}r_{skn}(q).
\]

The iid binary-sequence likelihood is

\[
L_1(y\mid s,q)=\prod_n\bar r_{sn}^{y_n}(1-\bar r_{sn})^{1-y_n}.
\]

Let \(C_1(N\mid s,q)\) be the Poisson-binomial probability of total count \(N\), computed exactly by count dynamic programming. A1's conditional timing score is

\[
J_1(s,q)=\log L_1(y\mid s,q)-\log C_1(N\mid s,q).
\]

It uses M1's time-varying physical field but assumes event bins are independent after marginalizing phase.

## M2 — global hidden-phase association

The full hidden-phase likelihood is

\[
L_2(y\mid s,q)=
\sum_{z_{1:T}}\pi_s(z_1)
\prod_{n=1}^{T}
r_{s,z_n,n}^{y_n}(1-r_{s,z_n,n})^{1-y_n}
\prod_{n=2}^{T}A_{s,n-1}(z_{n-1},z_n).
\]

It is computed exactly in log space by the HMM forward algorithm. A count-augmented forward recursion computes

\[
C_2(N\mid s,q)=\Pr_{L_2}\!\left(\sum_n y_n=N\right)
\]

without enumerating binary sequences. M2 is the exact conditional sequence/phase-association likelihood

\[
J_2(s,q)=\log L_2(y\mid s,q)-\log C_2(N\mid s,q).
\]

Time permutation preserves \(N\) but changes \(J_2\) when physical phase continuity is informative. If every row of \(A_s\) equals the predicted marginal occupancy, A2 collapses to A1; this is an algebraic ablation, not a hand-designed baseline.

## M3 — exact count and survival factor

M3 is

\[
J_3(s,q)=\log C_2(N\mid s,q).
\]

Therefore

\[
J_2(s,q)+J_3(s,q)=\log L_2(y\mid s,q)
\]

exactly. When \(N=0\), \(J_3\) is the candidate's no-burst survival probability across the completed block. The full Bayesian update is

\[
p_b(s,q)\propto p_{b-1}(s,q)L_2(y_B\mid s,q),
\qquad p_b(s)=\int p_b(s,q)dq.
\]

The native PMFS likelihood cannot consume \(y_B\) again.

## Exact ablations

| Arm | Score | Information tested |
|---|---|---|
| A0 | native PMFS | frozen baseline |
| A1 | \(J_1\) | M1 temporal physical field without phase dependence |
| A2 | \(J_2\) | M2 phase continuity conditional on the same count |
| A3 | \(J_2+J_3=\log L_2\) | M3 count/non-arrival evidence |
| A2-P | time-permuted \(y\), fixed \(N\) | temporal-order control |
| A3-S | physically shifted \(r_{skn}\), fixed \(y,N\) | timed-survival control |

Module gates use \(margin(J_2)-margin(J_1)\) and \(margin(J_2+J_3)-margin(J_2)\). A3 never contains \(J_1\).

## Exact computation and complexity

- ordinary forward recursion: \(O(TK^2)\);
- count-augmented recursion: \(O(TK^2N)\), bounded by the completed block's observed count;
- all recursions use log-sum-exp and deterministic state ordering;
- sparse transitions are allowed only after equality to dense recursion is verified on the frozen gate library.

No neural network is needed for M2/M3. A neural operator is optional only in M1 and must beat the reference solver on held-out physical prediction.

## Degenerate contracts

- \(N=0\): M2 has no positive placement information; all source evidence comes from M3 survival.
- \(K=1\) or phase-independent transitions: A2 equals A1 within numerical tolerance.
- identical \((r,A,q)\) across candidates: all candidates tie.
- all \(r=0\) with \(N>0\): the background component must keep likelihood finite; otherwise the block is `INVALID_BACKGROUND_SUPPORT`.
- \(C_2(N)=0\): numerical/model support failure, never clipped into a performance value.

## Premise gates before House123

1. M1: held-out physical onset-probability score and source margin beat the fixed analytical field.
2. M2: with candidates matched on \(C_2(N)\), \(J_2\) improves true-versus-best-false margin over \(J_1\); time permutation removes the gain.
3. M3: conditional on frozen M2, \(J_3\) improves the margin; shifted exposure removes the gain.
4. Full: dense/sparse recursion parity, single-use block ledger, and real-stack activation pass before any new 300-second run.

Any failed gate stops the campaign. Final error, posterior variance or one successful trajectory cannot rescue it.

