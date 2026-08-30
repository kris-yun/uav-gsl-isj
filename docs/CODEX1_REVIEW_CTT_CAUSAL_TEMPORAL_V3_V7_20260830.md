# CODEX1 REVIEW CONTRACT — CTT causal-temporal V3--V7 audit

Date: 2026-08-30

Review branch: `research/ctt-causal-temporal-audit-v3-v7-20260830`
Base: `research/pf-dei-direct-set-nre-v3-spatial-audit-20260830`

## Objective

Independently review whether the V3--V7 implementation/evidence supports the frozen conclusion that the current generic candidate-forward residual TCN is **not ready for closed-loop intervention**, despite real temporal sensitivity in V3.

## Mandatory checks

1. Verify this branch only adds audit/reference material; it must not rewrite any earlier V2/V3 verdict.
2. `py_compile` every Python file under `experiments/cg_pc_ctt/ctt_temporal_audit_20260830/`.
3. Inspect V3 source split, checkpoint hashes, and pre-test fresh-source SHA.
4. Verify V4's score is always inside `[lower, upper]` and its hard non-overlap guarantee is algebraically correct.
5. Verify V5 Kahn extension has zero robust-order violations but can produce cascading reordering; do not call zero violations a performance PASS.
6. Verify V6 stopped on the frozen numerical certificate rather than silently changing solver tolerance.
7. Verify V7 dual derivation: for `Bx<=0`, projection of raw score `r` has dual NNLS `min_{lambda>=0} ||B^T lambda-r||^2/2` and `x=r-B^T lambda`.
8. Verify V7 checks the dense original constraints after solving on the transitive reduction.
9. Recompute summary metrics from checked-in case CSVs and confirm JSON summaries.
10. Confirm V7 final held subset is disjoint from V1/V2, V3, V4, V5, and conservatively consumed V6 source subsets.
11. Confirm no geometry-prior posterior or closed-loop claim is authorized by V4--V7.

## Forbidden review shortcuts

- Do not select the best version post hoc and call it GO.
- Do not average V3 and V7 outcomes into a positive claim.
- Do not change Top5/Top10/time gates.
- Do not add a blend coefficient, temperature, threshold, or loss weight.
- Do not run closed loop.

## Required review output

Return:
- `CODEX1_CTT_TEMPORAL_AUDIT_REVIEW.md`
- `CODEX1_CTT_TEMPORAL_AUDIT_VERDICT.txt` with exactly one of:
  - `AUDIT_CONFIRMS_CLOSED_LOOP_NOT_AUTHORIZED`
  - `AUDIT_FINDS_IMPLEMENTATION_OR_EVIDENCE_DEFECT`
- exact commit SHA reviewed;
- per-file findings with line/function references;
- recomputed V3/V4/V5/V7 summary metrics;
- any defect must distinguish scientific-design defect from implementation defect.
