# CG-PC-CTT V3 — resolution cells and posterior projection

Date: 2026-08-27  
Status: **THEORY + REGRESSION-TESTED PROTOTYPE, BEFORE H02 replacement outcomes**

## 1. Pairwise non-separability is not automatically an equivalence relation

A local source pair `(i,j)` can be unresolved while another pair `(i,k)` is resolved. Pairwise non-separability is not generally transitive.

Therefore V3 should not claim that all candidates in a coarse region have identical statistical distributions.

Instead define the physical local source graph on unique coordinates and remove local edges that are currently supported as resolved. A **resolution cell** is a connected component of the remaining unresolved-edge graph.

For candidates `i,j`,

`i ~_t j`

means there exists a physical path from `i` to `j` consisting only of currently unresolved local edges.

This is an equivalence relation by graph connectedness. Its interpretation is conservative:

> there is not yet a fully resolved local physical boundary separating the two candidates.

It does not claim direct pairwise distributional equality between every pair in the component.

## 2. Why posterior projection is required

Suppose bridge/rank evidence gives very different scores to two candidates that are in the same current resolution cell. Using those raw scores directly would reintroduce point precision that the observation-resolution layer just declared unsupported.

Therefore evidence must be projected onto the current physical resolution partition before it can modify the source posterior.

Let the fixed geometry/base prior be `q0(s)` and let `C_t(s)` be the current resolution cell containing candidate `s`.

For any candidate evidence score `g(s)`, define the cell-projected evidence

`g_bar(C) = sum_{s in C} q0(s) g(s) / sum_{s in C} q0(s)`.

Then every candidate in that cell receives

`g_proj(s) = g_bar(C_t(s))`.

The posterior is

`q_t(s) propto q0(s) exp(g_proj(s))`.

Within one unresolved cell,

`q_t(s_i) / q_t(s_j) = q0(s_i) / q0(s_j)`.

Thus current evidence can move probability mass **between resolved cells** but cannot invent unsupported probability structure **inside an unresolved cell**.

Using `q0` rather than equal candidate counts prevents adaptive candidate-density or duplicate-ID artifacts from defining the within-cell mass measure.

## 3. Reversible split/merge semantics

The resolution partition can evolve as the trajectory changes.

### Split

If a previously unresolved cell later separates into finer cells, all historical events collected while it was unresolved remain projected to the old coarse cell. They cannot retroactively create fine-scale distinctions.

Only newly accepted evidence after the split can distinguish the new cells.

### Merge

If the current observation support later no longer supports a previous fine boundary, the final cumulative evidence is projected again onto the **current** partition. Any historical fine-scale distinction that is no longer supported is erased.

This gives a reversible coarse-to-fine / fine-to-coarse interface rather than an irreversible first-crossing gate.

## 4. Compatibility with the existing V11-style rank architecture

The fast-track branch uses tie-safe normal ranks and even/odd evidence folds to avoid fitting a score temperature.

V3 preserves that scale-free architecture but adds two projections:

1. event-time projection: rank evidence is projected onto the resolution cells valid for that event;
2. current-time projection: cumulative evidence is projected again onto the current partition before posterior construction.

This prevents old unresolved events from gaining fake resolution after a later split and prevents old fine evidence from surviving a later merge.

## 5. Code and regression tests

Implementation:

`closed_loop/cg_pc_ctt/v3_quotient_rank_posterior.py`

Regression test:

`closed_loop/cg_pc_ctt/selftest_v3_quotient_posterior.py`

The test verifies:

- two unresolved candidates keep their geometry-prior odds despite arbitrarily contradictory raw scores;
- one all-source unresolved cell collapses the posterior exactly to `q0`;
- a later split does not let old coarse events retroactively distinguish candidates;
- new evidence after a split can create fine distinctions;
- a later merge erases those fine distinctions and restores the within-cell `q0` odds.

## 6. Scientific boundary

This is a resolution-consistency mechanism, not itself proof that the bridge score is a calibrated likelihood.

Observation adequacy, source-resolution support and sensor/bridge evidence remain separate premises. The final closed-loop endpoint remains localization error, not resolution-cell count alone.
