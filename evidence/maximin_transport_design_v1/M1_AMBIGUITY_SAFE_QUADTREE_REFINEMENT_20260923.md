# M1 PMFS-Native Structure — Ambiguity-Safe Quadtree Refinement

Date: 2026-09-23
Branch: research/maximin-transport-design-v1
Status: theoretical module inside M1; validate computational cost before implementation

## 1. PMFS-native failure point

Official PMFS performs hierarchical candidate-source simulation.

At each quadtree level:
1. simulate every current leaf;
2. compute one scalar source score;
3. sort leaves by that scalar;
4. subdivide only the top refineFraction.

This is efficient under a trusted forward model.

Under transport misspecification it can make an irreversible mistake:

a coarse region containing the true source can receive a poor nominal score and be removed from all finer source simulation before later measurements can recover it.

Robustifying only the movement objective does not repair this failure.

## 2. Interval scores

M1 produces a PMFS-native score interval for every candidate leaf j:

\[
S_j\in[L_j,U_j]
\]

where L_j is the worst admissible PMFS map-match score and U_j is the best admissible score.

Let

\[
K=\lceil rN\rceil
\]

where r is the original PMFS refineFraction and N is the number of current leaves.

The original algorithm refines exactly the K largest point scores.

## 3. Best and worst possible ranks

For leaf j, define

\[
\boxed{
r_j^{best}
=
1+
\#\{k\ne j:L_k>U_j\}.
}
\]

These competitors are guaranteed to beat j even when j takes its maximum admissible score.

Define

\[
\boxed{
r_j^{worst}
=
1+
\#\{k\ne j:U_k>L_j\}.
}
\]

Interpretation:

- if r_best(j) > K, j can never be top-K under any admissible score realization;
- if r_worst(j) <= K, j is guaranteed top-K under all admissible realizations;
- otherwise j is ambiguity-sensitive.

## 4. Ambiguity-safe refinement set

Define

\[
\boxed{
R_{\rm safe}
=
\{j:r_j^{best}\le K\}.
}
\]

Equivalent pruning rule:

A leaf may be discarded only if at least K other leaves have lower score bounds strictly larger than its upper score bound.

Thus M1 never prunes a leaf that could still belong to the original PMFS top-K under some admissible transport model.

This preserves PMFS hierarchical refinement but replaces overconfident point ranking with set-valued dominance.

## 5. Three leaf classes

Guaranteed-refine:

\[
r_j^{worst}\le K.
\]

Ambiguous-refine:

\[
r_j^{best}\le K<r_j^{worst}.
\]

Safe-prune:

\[
r_j^{best}>K.
\]

The classification is source-blind.

## 6. Computational consequence

Generally

\[
|R_{\rm safe}|\ge K.
\]

Therefore robust refinement may simulate more children than native PMFS.

Measure

\[
\text{refinement inflation}=|R_{\rm safe}|/K.
\]

Do not hide a large inflation factor with a truth-tuned cap.

If the safe set explodes, possible causes are:
- ambiguity is too broad;
- rectangular score intervals are too conservative;
- current data genuinely do not support aggressive source-space pruning.

## 7. Truth-rank relevance

For the source-containing coarse leaf, report:
- nominal point-score rank;
- best robust rank;
- worst robust rank;
- whether native PMFS would prune it;
- whether ambiguity-safe PMFS retains it.

Required positive signal:

Under controlled forward mismatch, the truth-containing region is sometimes incorrectly discarded by nominal PMFS but retained as ambiguity-sensitive by the robust rule, without retaining almost every leaf.

## 8. Negative controls

Matched-model control:

When transport is correct and ambiguity is tiny,

\[
L_j\approx U_j,
\]

so robust refinement must converge to ordinary PMFS top-K refinement.

Label-shuffle null:

Destroy the relationship between candidate source and simulated hit map while preserving interval-width statistics. Any truth-retention advantage should disappear.

Uniformly inflated ambiguity:

Artificially inflate all intervals. The safe set should expand sharply, proving that the mechanism responds to uncertainty.

## 9. Relationship to the rest of M1

One transport ambiguity model now changes three native PMFS operations:

1. candidate inference: point source score becomes interval / credal source map;
2. candidate computation: quadtree refinement becomes ambiguity-safe;
3. robot action: sensing position is chosen by transport-robust source information.

The main contribution is therefore structural rather than an acquisition-function swap.

## 10. Hard kill conditions

Kill ambiguity-safe refinement as an operational component if:
- R_safe is close to all leaves for most updates even under repaired matched Native PMFS;
- truth-leaf retention is no better than a width-matched random expansion;
- runtime inflation makes the 300 s closed loop infeasible;
- a useful result requires choosing interval widths from true source rank.

If rectangular interval conservatism causes failure, test a structured global wind-field adversary before killing M1 itself.

## 11. First test after baseline repair

Using saved source-update contexts:

- reconstruct native top-K;
- construct interval score bounds using a predeclared ambiguity level;
- compute rank intervals and R_safe;
- compare truth-containing leaf retention;
- report refinement inflation.

This is source-blind until final evaluation of whether the truth leaf survived.

No full trajectory replanning is needed for this falsification.
