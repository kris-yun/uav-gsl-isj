# Physical-hypothesis source inference V1: stochastic-ensemble pre-screen

Date: 2026-09-23

## Motivation

Repeated R2 falsification shows that changing the PMFS comparison rule does not repair source identity when the fixed candidate forward family is wrong. The new hypothesis is therefore upstream: infer source jointly with a transport hypothesis rather than treating PMFS's single online plume simulator as the unique forward law.

Recent anchors:
- PhysPDE, ICLR 2025: interpret experimental data by selecting among prior physical hypotheses instead of treating one fixed PDE expression as unquestioned truth.
- PIED, ICLR 2025: inverse-problem performance is limited by identifiability and experimental design, not merely by the final estimator.

This branch tests the mother mechanism before designing a method.

## Stage A0: is stochastic realization diversity enough?

Before changing transport physics, use the cheapest available falsification. For each House, the two authoritative R2 seeds provide independent candidate-forward realizations. Candidate leaves are matched source-blind by identical/nearest quadtree center. For a target run, Native PMFS evidence is recomputed on the support common to both seeds, then two alternatives are evaluated:

1. profile evidence: best log evidence across the two independent forward realizations;
2. equal-weight marginal evidence: log-mean-exp across the two realizations.

No truth coordinate enters the score; truth is used only after score freeze to identify the truth-containing quadtree leaf.

| case | Native/full truth-owner rank | own/common | other-seed/common | profile 2-seed | marginal 2-seed |
|---|---:|---:|---:|---:|---:|
| H01 seed0 | 110/152 | 110 | 111 | 110 | 111 |
| H01 seed1 | 117/148 | 118 | 117 | 117 | 118 |
| H02 seed0 | 134.5/148 | 134.5 | 134.5 | 135 | 135 |
| H02 seed1 | 132.5/144 | 132.5 | 132.5 | 133 | 133 |
| H03 seed0 | 149/197 | 149 | 149 | 149 | 149 |
| H03 seed1 | 148/199 | 148 | 149 | 149 | 149 |

The matched candidate-center distance is zero for the median candidate and for every truth-containing leaf. Common support is 221 cells (H01), 268 (H02), and 250 (H03).

## Decision

**NO-GO for “more stochastic replicas of the same PMFS transport law” as the main innovation.**

Independent realization diversity does not recover truth-source identity. This also strengthens the interpretation of the earlier distributional-forward H01 kill: the problem is not simply that PMFS averages away stochastic plume samples.

This does **not** kill physical-hypothesis inference. It sharpens the next test: the hypothesis bank must change the effective transport law itself (e.g. dispersion / wind coupling / transport closure), not merely add random seeds under the same law.

## Frozen next gate

Run only a small, predeclared transport-law grid on one hit-bearing case first. Do not touch posterior temperature, source-discrimination power, scoring rule, endpoint, or use truth to select a transport setting.

For every source candidate, evaluate the same transport-hypothesis bank and score by source-blind profile and equal-prior marginal evidence. Advance only if the truth-containing candidate rank improves materially relative to Native and the selected transport regime is not candidate-specific geometry leakage.
