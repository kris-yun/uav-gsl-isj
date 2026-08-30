# CODEX1 REVIEW CONTRACT — CTT causal-temporal V1--V7 audit

Date: 2026-08-30

Review branch: `research/ctt-causal-temporal-audit-v3-v7-20260830`  
Base: `research/pf-dei-direct-set-nre-v3-spatial-audit-20260830`

## Objective

Independently review whether the implementation and available provenance support the frozen conclusion that the current generic candidate-forward residual TCN is **not ready for closed-loop intervention**, despite real temporal sensitivity in V3.

This is an audit-only task. Do not turn the best-looking V1--V7 variant into a deployment method.

## Mandatory source checks

1. Record the exact reviewed commit SHA. Verify the branch only adds audit/reference material and does not rewrite an earlier V2/V3 verdict.
2. Verify all 12 files listed in `experiments/cg_pc_ctt/ctt_temporal_audit_20260830/CTT_TEMPORAL_AUDIT_FILE_SHA256.tsv` are present as independent Python source/evaluator files. Run `py_compile` on every checked-in `.py` file in that audit directory.
3. For the five recovered original core files V1/V4/V5/V6/V7, independently compute SHA-256 and byte size and require exact equality with the manifest. Do the same for the other source/evaluator files where practical. Do not substitute Git blob SHA for file SHA-256.
4. Inspect V1/V2/V3 source split semantics, candidate conditioning, member marginalization, causal prefix construction, TIME-PERMUTE construction, and absence of future/source-truth/posterior leakage.
5. Inspect V3 fresh-source exclusion logic, checkpoint-hash contract, fixed physics anchor and soft physics-order loss.
6. Verify V4 score is always inside `[lower, upper]` and its hard non-overlap guarantee is algebraically correct. Confirm V4 does not silently tune an interval margin from H01 results.
7. Verify V5 Kahn extension has zero robust-order violations but can produce cascading reordering; zero violations is only a certificate check, not a performance PASS.
8. Verify V6 stopped on its frozen numerical certificate rather than silently weakening solver/rank tolerance.
9. Verify V7 dual derivation: for `Bx<=0`, Euclidean projection of raw score `r` has dual NNLS `min_{lambda>=0} ||B^T lambda-r||^2/2` and `x=r-B^T lambda`. Verify it solves on the transitive reduction and checks the dense original constraints afterward.
10. Confirm the held truth-source subsets are constructed to be disjoint across V1/V2, V3, V4, V5 and conservatively consumed V6 before V7. Verify the observation-member/trajectory contracts from source rather than trusting the prose summary.
11. Confirm V4--V7 never authorize a geometry-prior posterior, planner change, shadow intervention, or closed-loop run.
12. Confirm the scientific conclusion follows the full falsification chain: post-hoc physical protection does not establish nuisance-stable temporal evidence; the next method must change the temporal representation rather than tune a fusion/projection rule.

## Evidence completeness gate

The GitHub branch contains the complete V1--V7 source/evaluator audit chain and human-readable frozen-result summary, but it does **not** currently contain the combined V3--V7 per-case/checkpoint evidence archive.

Recorded but currently unavailable combined archive:
- `CTT_TEMPORAL_AUDIT_V3_V7_EVIDENCE_20260830.tar.gz`
- recorded SHA-256 `3b28577f8d617645a2573d75dd1dbbe9d6cdc7c33e8b7af585f7a99aaa98eade`

A separate V3-only evidence archive exists outside this branch:
- `CTT_TEMPORAL_V3_H01_FRESH_GATE_EVIDENCE_20260830.tar.gz`
- SHA-256 `27a6e9aa89526f41a452b61caa9a0e45f0b4799224ac1cbd43c580059b5c7cce`

Therefore:
- if the exact V3--V7 evidence archive is supplied and its SHA matches, recompute V3/V4/V5/V7 summary metrics from the frozen case files;
- if it is not supplied, **do not regenerate cases, retrain, change a source subset, or substitute new data to imitate reproduction**;
- instead set `EVIDENCE_COMPLETENESS=PARTIAL`, audit the source/contracts/frozen summaries, and explicitly state that V4/V5/V7 metric claims were not independently recomputed in this review;
- absence of the archive is a provenance limitation, not by itself an implementation defect and not a reason to authorize closed loop.

## Forbidden review shortcuts

- Do not select the best version post hoc and call it GO.
- Do not average V3 and V7 outcomes into a positive claim.
- Do not change Top5/Top10/TIME-PERMUTE gates.
- Do not add a blend coefficient, temperature, threshold, loss weight, Top-K router, or projection margin.
- Do not retrain using a held-test subset already opened by an earlier version.
- Do not run shadow or closed loop.

## Required review output

Return:
- `CODEX1_CTT_TEMPORAL_AUDIT_REVIEW.md`
- `CODEX1_CTT_TEMPORAL_AUDIT_VERDICT.txt` with exactly one of:
  - `AUDIT_CONFIRMS_CLOSED_LOOP_NOT_AUTHORIZED`
  - `AUDIT_FINDS_IMPLEMENTATION_OR_EVIDENCE_DEFECT`
- `EVIDENCE_COMPLETENESS=FULL` or `EVIDENCE_COMPLETENESS=PARTIAL`;
- exact commit SHA reviewed;
- per-file findings with line/function references;
- source SHA-256 verification table;
- metric recomputation table only for evidence actually supplied and hash-verified;
- every defect classified as `IMPLEMENTATION`, `SCIENTIFIC_DESIGN`, or `PROVENANCE`.

A `PARTIAL` evidence status is compatible with `AUDIT_CONFIRMS_CLOSED_LOOP_NOT_AUTHORIZED`: it means the code/falsification logic supports the conservative no-closed-loop decision while some historical metric values remain non-independently-recomputed.
