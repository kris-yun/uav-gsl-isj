# R1 Diagnostic — Per-Source World Shopping Rescues False Source Hypotheses

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`  
Evidence source: corrected R1 A/B candidate-score replay.

## 1. Purpose

Test the M7 v2 principle:

> all source candidates should be evaluated under one shared environment world.

Arms A and B are useful for a weak diagnostic because they have:
- identical observations;
- identical 87 source candidates;
- identical frozen R2 source-scoring contract;
- different forward wind environment.

This is not a learned-operator experiment.

It only tests what happens if source candidates are allowed to select their own favorable forward world.

## 2. Truth candidate score is essentially unchanged

Truth-containing candidate:

\`quadtree_23_14_1_3\`

PMFS source score:

- A: 0.031391846840682185
- B: 0.03139184685277734

Relative change:

\[
3.85\times10^{-10}.
\]

Thus the large truth-rank change A→B is **not caused by increasing the truth candidate's own score**.

The environment intervention mainly changes the competing false candidates.

## 3. False candidates above the truth

Count of false candidates with score strictly above the truth score:

- A: **20**
- B: **17**

B suppresses multiple false-source explanations while leaving the truth score effectively fixed.

The official corrected truth ranks are:
- A: 48/87 because A also contains a large exact-score plateau/tie convention;
- B: 18/87.

The strict-above counts and average-tie ranks are used here only for mechanism diagnosis.

## 4. Per-source world shopping

Construct an intentionally unphysical negative control:

\[
S_{\rm shop}(s)
=
\max\{
S_A(s),S_B(s)
\}.
\]

This means every candidate source is allowed to choose whichever wind world makes itself look better.

This is exactly what M7 forbids physically.

Result:

- truth average-tie rank under B: **18**
- truth average-tie rank under per-source shopping: **25**
- false candidates above truth under shopping: **24**

Therefore source-specific world selection rescues false hypotheses.

## 5. Seven false candidates are specifically rescued above the truth

Seven candidates satisfy:

\[
S_B(s)<S_B(s^\star)
\]

but

\[
\max(S_A(s),S_B(s))
>
\max(S_A(s^\star),S_B(s^\star)).
\]

Examples:

| candidate | A score | B score | best/truth |
|---|---:|---:|---:|
| quadtree_2_32_4_4 | 0.045660 | 0.010549 | 1.455 |
| quadtree_2_31_3_1 | 0.040599 | 0.003151 | 1.293 |
| quadtree_8_14_5_2 | 0.039994 | 0.004432 | 1.274 |
| quadtree_6_31_1_5 | 0.036623 | 0.005034 | 1.167 |
| quadtree_22_27_4_2 | 0.033803 | 0.031392 | 1.077 |
| quadtree_28_27_1_1 | 0.031993 | 0.031392 | 1.019 |
| quadtree_14_31_1_1 | 0.031474 | 0.031392 | 1.003 |

These are false hypotheses that the B environment suppresses but source-specific world shopping revives using A.

## 6. Interpretation

The R1 behavior is consistent with:

> a correct/shared forward environment improves source identity partly by excluding false source explanations.

It is therefore physically dangerous to let every source candidate independently adapt/select its own transport model.

This provides a concrete inverse-source motivation for M7's shared-world constraint.

## 7. Important negative finding: naive global PMFS-score world selection fails

A source-blind diagnostic using uniform-source average pseudo-evidence from the same PMFS scores gives:

- A log mean pseudo-evidence: -3.7215
- B log mean pseudo-evidence: -3.8256

Naively maximizing same-batch aggregate PMFS score would select **A**, even though B gives the better truth-source ranking.

Therefore:

\[
\boxed{
\text{same-batch total PMFS score is NOT an acceptable environment-selection objective}
}
\]

This is an important design constraint.

## 8. Required environment-selection rule

M7 should use one of the following, in order of preference:

### E1 — physical/context-only selection
Select operator composition from:
- measured/recovered wind;
- geometry;
- source-independent transport context.

No gas-source score is used.

### E2 — prequential gas evidence
At update \(t\):

1. use only history \(Y_{<t}\) to select/freeze environment composition \(z_t\);
2. evaluate the next observation batch \(Y_t\);
3. rank all sources under that same frozen \(z_t\).

This tests future predictive validity rather than same-batch fit.

### E3 — source-marginal evidence with held-out data
If source-marginal likelihood is needed, use a calibration/history window separate from the source-ranking evaluation window.

Do not select environment composition by maximizing the same PMFS compatibility scores being used to rank the source.

## 9. What this result does and does not establish

### Supports
- forward environment can suppress false source hypotheses;
- independent per-source world adaptation can reintroduce false hypotheses;
- one-world-many-counterfactuals is physically and empirically motivated.

### Does not establish
- M7 operator splitting works;
- B is universally the correct world;
- a particular environment-selection rule;
- full closed-loop benefit.

Those require O0/O1/O2/O3.

## 10. Current status

\`POSITIVE SECOND-DERIVATION SIGNAL\`

for:

\`ONE SHARED ENVIRONMENT WORLD, MANY SOURCE COUNTERFACTUALS\`

with the additional hard rule:

\`ENVIRONMENT SELECTION MUST BE PREQUENTIAL OR PHYSICAL, NOT SAME-BATCH SCORE MAXIMIZATION\`.
