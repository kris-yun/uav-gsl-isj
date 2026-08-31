# CTT dynamic-transport two-module V4 preregistration

Status: `FROZEN_BEFORE_V4_PREDICTIVE_OR_MEASURED_RESULT_READ`

This is the one final permitted internal correction of M2. It preserves the
frozen causal M1 and the complete V3 NO-GO evidence. It neither adds a third
module nor changes PMFS, the planner, the physical bank, the four-state
emission matrix, source support, projection, thresholds, or evaluation metric.

## Scientific correction

V3 assumed one transport realization for the whole run. An earlier ablation
allowed independent member selection at every block. V4 places the frozen
eight-member transport ensemble between those two endpoints:

\[
 Z_j\in\{0,\ldots,7\},\qquad
 A_{mm'}=\rho\,\mathbf 1[m=m']+\frac{1-\rho}{M}.
\]

The states are exchangeable Monte Carlo realizations, not named weather
regimes. The stay-or-redraw transition is therefore the maximum-entropy
one-parameter family that remains invariant to any member-label permutation.
There is no fitted House, seed, source, outcome, or localization parameter.

The persistence is estimated once from frozen simulation statistics:

\[
 \hat\rho=\operatorname{clip}\left(
 \frac{\hat p_{same}-\hat p_{cross}}{1-\hat p_{cross}},0,1\right),
\]

where the two probabilities are Jeffreys-smoothed adjacent-block count
agreements for the same realization and for different realizations under the
same House/source/route/block-pair design. This is excess same-realization
agreement over the cross-realization chance baseline. No measured tape,
posterior, truth, or error may be opened to estimate it.

## Exact inference

With the frozen V3 emission table `Q`, the evidence is computed by exact
finite-state filtering:

\[
 \alpha_1(s,m)=q_0(s)Q[K_{sm1},k_1]/M,
\]

\[
 \alpha_j(s,m')=Q[K_{sm'j},k_j]
 \sum_m\alpha_{j-1}(s,m)A_{mm'},
 \qquad q_j(s)\propto\sum_m\alpha_j(s,m).
\]

No particle approximation, selected latent path, transition learning, or
posterior tuning is allowed. `rho=0` must equal the IID arm and `rho=1` must
equal the V3 fixed-member arm exactly.

## Required comparison and terminal decision

The six arms are native PMFS, frozen M1 causal-only, dynamic M1+M2,
time-shuffled dynamic M1+M2, IID transport, and fixed transport. Before truth,
the dynamic arm must beat all four scientific comparators in strict
member-LOO source-ranking tests on 30 House-route units. After Stage 1 is
externally hashed, the 30 measured fixed-trajectory runs must retain at least
10% pooled improvement and 20/30 wins, introduce no catastrophe, and beat
every comparator by both total error and the frozen paired exact sign test in
each primary tie mode.

Failure at either Gate retires M2 permanently and preserves M1. Passing both
Gates freezes the two-module method and authorizes exactly nine paired 300 s
closed-loop experiments: H01/H02/H03, seeds 1--3, PMFS OFF versus frozen ON.
The 49.4% V3 replay is development evidence, not closed-loop proof.

The machine-readable JSON beside this file is the controlling contract.
