# CTT-M2: causal burst-phase association gate

Date: 2026-08-26  
Status: superseded on 2026-08-26 by `CTT_EXACT_EVENT_FACTORISATION_V2.md`; retained as an audit record because treating a raw OT distance as likelihood was not sufficiently defined.

## Scientific role

M1 supplies a candidate-conditioned family of causal arrival components

\[
\mathcal H_s=\{h_{sk}(t)\}_{k=1}^{K_s},
\]

where a component represents one physically admissible transport path or delay mode. M2 does not learn a source classifier. It asks whether the observed burst sequence can be assigned coherently to those predicted components, following the travel-time phase-association idea used in seismology.

For a completed observation block, convert threshold crossings to a frozen marked event measure

\[
\mu_B=\sum_{j=1}^{J}w_j\,\delta_{(t_j,m_j)},
\]

where onset time, duration and mark extraction are fixed before the gate. Candidate \(s\) gives the predicted measure

\[
\nu_s=\sum_{k=1}^{K_s}a_{sk}\,h_{sk}(t)\,g_{sk}(m)\,dt\,dm.
\]

The A1 reference treats events independently under the normalized aggregate M1 intensity \(\bar h_s=h_s/\int_Bh_s\):

\[
J_1(s)=\sum_{j=1}^{J}\log \bar h_s(t_j,m_j).
\]

M2 replaces this reference; it is not added to it. Its association cost is

\[
c_{jsk}=-\log\!\left[\int_{B_j}h_{sk}(t)g_{sk}(m_j)\,dt+\epsilon\right],
\]

augmented by a frozen background/dustbin component. A capacity-constrained entropic transport plan

\[
P_s^*=\arg\min_{P\in\Pi(\mu_B,\nu_s)}
\langle P,C_s\rangle+\varepsilon_{OT}\,\mathrm{KL}(P\|ab^\top)
\]

prevents one convenient phase peak from explaining every burst. The structured association defines or variationally approximates the conditional event likelihood given the observed block count:

\[
J_2(s)=\log p_{assoc}(\{t_j,m_j\}_{j=1}^{J}\mid N_B=J,s,h_s).
\]

When Sinkhorn/unbalanced optimal transport is used computationally, its objective must be shown to be the stated variational bound or approximation to \(J_2\); a raw transport distance relabeled as a likelihood is not admissible.

All \(P_{jsk}\), costs and dustbin assignments must be logged. Source truth is evaluator-only and never enters event parsing, the cost matrix or the optimizer.

## Separation from M1 and M3

- M1 is scored on physical first-passage/hazard prediction; A1 uses \(J_1\) only as the coarse independent-event comparator. M2's \(J_2\) replaces \(J_1\) online.
- M2 uses only positive burst events and normalized temporal/path mass. It cannot penalize an interval merely because no event occurred.
- M3 alone owns the survival/no-event integral. This prevents the same miss from being counted twice.
- During online integration, the previous-block posterior is the prior. The native PMFS likelihood and CTT likelihood must never both consume the same completed block.

## Direct incremental information

For synthetic premise atom \(a\), after evaluator-only truth reveal define

\[
\Delta^{(2)}_a=
\operatorname{margin}_a(J_2)-\operatorname{margin}_a(J_1),
\qquad
\operatorname{margin}_a(J)=J(s_a^*)-\max_{s\in\mathcal D_a}J(s).
\]

Also report true-candidate rank, pairwise win rate, dustbin fraction, leave-one-burst-out rank stability and assignment entropy. Final localization error, posterior entropy and path length are forbidden M2 gate metrics.

## Premise atoms

The frozen library must contain at least:

1. equal integrated reachability but different delay ordering;
2. two-path arrival splitting versus a one-path distractor;
3. an extra clutter burst requiring the dustbin;
4. irregular sampling/gaps with identical marginal burst counts.

Every atom has at least two independent realizations and predeclared matched distractors. Coverage failure is `M2_INVALID_COVERAGE`, not a performance result.

## Required controls and ablations

| Arm | Change | Load-bearing claim |
|---|---|---|
| M2-FULL | physical components + global capacity-constrained association | reference |
| TIME-PERMUTE | permute observed burst times, preserve marks/count | real time order is required |
| PATH-SHUFFLE | exchange component identities, preserve marginal hazard | path identity is required |
| INDEPENDENT | score each burst independently without global capacities | association, not peak matching, adds information |
| NO-DUSTBIN | remove background component | robustness is not forced matching |
| REACH-ONLY | preserve total arrival mass, remove delay modes | temporal phases are load-bearing |

M2 is non-trivial only if FULL beats TIME-PERMUTE, PATH-SHUFFLE and INDEPENDENT on the same incremental margin. Time permutation must remove the gain; otherwise the module is a static candidate reweighting mislabeled as temporal inference.

## Pass/fail rule

The scorer, event parser, premise library and all hyperparameter selection rules are hashed before evaluation. M2 passes only if:

1. every valid premise atom has positive median \(\Delta^{(2)}\);
2. the paired bootstrap lower 95% bound over frozen realizations is above zero;
3. no House-independent atom family has a negative median;
4. the time-permutation and path-shuffle controls remove the gain;
5. replay produces bitwise-identical event lists and numerically identical rankings;
6. no change to \(\varepsilon_{OT}\), dustbin cost, burst threshold, candidate set or atom is made after truth reveal.

Failure is `M2_INCREMENTAL_INFO_NO_GO`; it blocks implementation qualification and all new 300-second closed loops. A positive M1 or a positive final error cannot rescue it.

## Minimal evidence package

- `M2_CONTRACT.json` and SHA-256 manifest;
- frozen event lists and predicted phase components;
- candidate cost matrices and transport plans;
- per-atom incremental margins/ranks;
- TIME-PERMUTE, PATH-SHUFFLE and INDEPENDENT controls;
- unique terminal verdict.
