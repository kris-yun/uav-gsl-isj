# R1 A↔B transport-only source-blind diagnostic

Date: 2026-09-23  
Innovation branch: \`research/maximin-transport-design-v1\`  
Baseline source: corrected R1 on \`research/native-pmfs-baseline-recovery-v1\`

## Scope

This diagnostic uses only Arms A and B because they keep:

- the frozen R2 PMFS source;
- the same R2 PMFS forward/hit-map parameters;
- the same 20 observations;
- the same 87 source candidates;
- the same deterministic candidate replay machinery.

The declared difference is the forward wind:

- A: observed GMRF field;
- B: GADEN ground-truth field.

Therefore A↔B is the cleanest available first probe of transport sensitivity in the recovered snapshot.

This is still a **large wind-contract intervention**, not a local differential perturbation, and not a final proof of transport-tangent confounding.

## Source-blind candidate-ranking results

Average-rank Spearman correlation:

\[
\rho_{A,B}=0.74264.
\]

Top-set overlap:

| k | common candidates | fraction |
|---:|---:|---:|
| 5 | 0 | 0% |
| 10 | 4 | 40% |
| 20 | 12 | 60% |

Absolute A↔B rank displacement across all 87 candidates:

- median: 2.5;
- 75th percentile: 11.5;
- 90th percentile: 28.9;
- maximum: 59.

Counts:

- 23/87 candidates move by at least 10 average-rank positions;
- 15/87 move by at least 20;
- 12 cross the top-10 boundary;
- 16 cross the top-20 boundary;
- 8 improve by at least 20;
- 7 worsen by at least 20.

Thus the wind-path intervention does not merely perturb one truth candidate. It materially reorders a nontrivial subset of the entire source hypothesis set.

## Post-freeze truth check

The known truth-containing candidate is \`quadtree_23_14_1_3\`.

Under the average-rank treatment of tied scores:

- A ≈ 40;
- B = 18;
- shift ≈ -22 positions.

The official truth evaluator reports A=48/87 and B=18/87 because A has a large exact-score plateau and uses its own deterministic ranking convention. The source-blind statistics above therefore use average ranks for tie-aware arm-to-arm comparison and must not replace the official truth-rank values.

## Important tie structure

A/B use the same R2 scoring contract but have large score plateaus:

- A: 48 unique score values; one exact tie group contains 40 candidates;
- B: 52 unique score values; one exact tie group contains 36 candidates.

Therefore:
- exact rank positions inside the plateau are not intrinsically meaningful;
- Spearman with average ties and top-set crossing should be interpreted together;
- future differential transport tests should also inspect continuous candidate-map responses, not only final PMFS source scores.

## Why C is excluded from the transport-only claim

Arm C restores the full official PMFS source/forward/hit-map contract.

C has 87/87 unique candidate scores, unlike A/B.

Therefore the large B→C reordering mixes:
- transport-model changes;
- blur;
- sourceDiscriminationPower;
- hit-map prior/kernel/confidence settings;
- warmup/delta-time/refinement changes;
- official-vs-R2 source implementation differences.

A/B/C proves **forward-contract sensitivity**.

A/B alone is the current evidence for **transport sensitivity**.

Do not call B→C transport confounding.

## Scientific implication

Supported hypothesis:

> A nontrivial subset of PMFS source hypotheses changes strongly when the transport environment is changed while observations, candidate geometry, PMFS scoring parameters, and source implementation are fixed.

Not yet supported:

> the changed component is exactly the local transport-nuisance tangent predicted by the V5 theory.

That requires controlled small perturbations and shared-environment sensitivity analysis.

## Next hard gate

On a repaired Native / hit-bearing snapshot:

1. hold the complete Native PMFS contract fixed;
2. perturb only the ground-truth forward wind by predeclared small common fields;
3. use common random numbers;
4. estimate candidate hit-map transport derivatives \(g_s(x)\);
5. measure source-vs-transport tangent confounding source-blind;
6. only then test truth-source-rank interventions.

Status:

\`POSITIVE MOTIVATION SIGNAL — NOT METHOD VALIDATION\`.
