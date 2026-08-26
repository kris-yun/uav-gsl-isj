# CTT-M3: prequential causal miss-survival gate

Date: 2026-08-26  
Status: superseded on 2026-08-26 by `CTT_EXACT_EVENT_FACTORISATION_V2.md`; retained as an audit record.

## Scientific role

M3 turns a physically predicted arrival that fails to occur into explicit falsification evidence. It is a survival-process term, not variance inflation, posterior widening or a generic confidence gate.

For candidate \(s\), M1 provides a non-negative arrival hazard shape \(h_s(t)\). Let the event rate be

\[
\lambda_s(t\mid q)=\lambda_{bg}(t)+q h_s(t).
\]

The source-strength nuisance \(q\) may not be fitted on the same no-hit interval it is used to score. At the start of block \(b\), a frozen common prior or the posterior based only on earlier blocks is used:

\[
q\mid\mathcal H_{b-1}\sim\mathrm{Gamma}(a_{b-1},b_{b-1}).
\]

Conditional on candidate and carried nuisance \(q\), the marked point-process likelihood factorizes into an event-time/mark term conditional on count (owned by M2) and a count term (owned by M3):

\[
\log p(E_b,N_b\mid s,q)=
\underbrace{\log p(E_b\mid N_b,s)}_{J_2(s)}+
\underbrace{\log p(N_b\mid s,q)}_{J_3(s,q)}.
\]

For the complete block, let \(\Lambda_s(B)=\int_B\lambda_s(t\mid q)dt\). Then

\[
J_3(s,q)=N_b\log\Lambda_s(B)-\Lambda_s(B)-\log(N_b!).
\]

For a predeclared no-event window \(W\) in block \(b\), this reduces to the survival contribution. Define

\[
H_s(W)=\int_W h_s(t)\,dt,
\]

and the posterior-predictive survival probability is

\[
P\{N(W)=0\mid s,\mathcal H_{b-1}\}
=e^{-\int_W\lambda_{bg}(t)dt}
\left(\frac{b_{b-1}}{b_{b-1}+H_s(W)}\right)^{a_{b-1}}.
\]

Thus

\[
J_{3,0}(s)=\sum_{W\in\mathcal W_b}
\log P\{N(W)=0\mid s,\mathcal H_{b-1}\}.
\]

Windows are generated from M1 hazard support before current-block observations are inspected. M2 conditions on \(N_b\) and owns event times/marks; M3 owns \(p(N_b\mid s,q)\). This conditional/count factorization, rather than merely deleting overlapping timestamps, is the formal guarantee against double counting.

## Required causal contract

1. `predict -> freeze window -> observe -> score`; no retrospective placement of miss windows.
2. \(q\), background hazard and window rule cannot be candidate-wise profiled on the scored interval.
3. The posterior entering block \(b\) is based on blocks \(<b\). Native PMFS and CTT cannot both update from block \(b\).
4. Every contribution is logged by candidate, block and window as \(H_s(W)\), background exposure and log survival.

## Direct conditional increment

After evaluator-only truth reveal, define the full-versus-M1+M2 increment

\[
\Delta^{(3)}_a=
\operatorname{margin}_{a}(J_2+J_3)
-\operatorname{margin}_{a}(J_2),
\]

where

\[
\operatorname{margin}_{a}(J)=J(s_a^*)-
\max_{s\in\mathcal D_a}J(s).
\]

Also report

\[
\Gamma_a=
\min_{s\in\mathcal D_a}\{-J_{M3}(s)\}
-\{-J_{M3}(s_a^*)\},
\]

the extra survival penalty assigned to the best false candidate relative to truth. M3 provides source information only when both \(\Delta^{(3)}\) and \(\Gamma\) are positive. Lower posterior variance alone is not evidence.

## Premise atoms

The frozen library must include:

1. a false candidate predicting a strong arrival inside a genuine silent window while truth predicts little exposure;
2. matched total hazard with different temporal support, so only correctly timed misses discriminate;
3. intermittent dropout in which occasional true-source misses occur, testing that marginalization over \(q\) prevents over-penalization;
4. background false positives outside predicted windows, ensuring M3 does not steal M2's event evidence.

All windows and nuisance-prior rules are frozen before premise truth reveal.

## Negative controls and ablations

| Arm | Change | Load-bearing claim |
|---|---|---|
| M3-FULL | prequential posterior-predictive survival | reference |
| WINDOW-SHIFT | shift windows outside candidate high-hazard support, preserve duration | timing is required |
| FUTURE-LEAK | diagnostic only: fit \(q\) on the scored interval | exposes leakage sensitivity; never admissible |
| CANDIDATE-CONSTANT | replace \(H_s(W)\) by its candidate mean | candidate-relative falsification is required |
| BINARY-MISS | constant penalty per no-hit window | physical hazard magnitude is required |
| EVENT-OVERLAP | deliberately include M2 event windows | double-count detector; must disagree with FULL |

WINDOW-SHIFT must remove the improvement. CANDIDATE-CONSTANT must give zero relative evidence up to numerical tolerance. EVENT-OVERLAP is expected to fail the factorization audit and cannot be reported as a competing method.

## Pass/fail rule

M3 passes only if:

1. all valid atom families have positive median \(\Delta^{(3)}\) and \(\Gamma\);
2. their paired-bootstrap lower 95% bounds are above zero;
3. WINDOW-SHIFT removes the gain and CANDIDATE-CONSTANT removes relative evidence;
4. prequential timestamps prove nuisance inference predates the scored window;
5. M2 event support and M3 no-event support are disjoint exactly;
6. no nuisance prior, hazard threshold, window length or atom is changed after truth reveal.

Any failure yields `M3_CONDITIONAL_INFO_NO_GO` and blocks House123 closed-loop qualification. The module must be removed or scientifically redesigned under a new version; it cannot be retained as an inactive auxiliary novelty.

## Minimal evidence package

- `M3_CONTRACT.json` with prequential timing rule;
- frozen windows and M2/M3 support-disjointness audit;
- per-window hazard integrals and survival contributions;
- conditional incremental margins and bootstrap report;
- WINDOW-SHIFT/CANDIDATE-CONSTANT controls;
- unique terminal verdict and SHA-256 manifest.
