# BINDING ADDENDUM — CG-PC-CTT V1 rank definition
Date: 2026-08-27

This addendum supersedes any ambiguous wording in the main experiment protocol about using the full rank of a dense candidate grid.

## Frozen V1 definition

Use `rank_k = 3` for the primary CG-PC-CTT V1 completeness gate.

Therefore, after projecting source contrasts and whitening by transport-member uncertainty, the primary statistics are:

- `gamma = sigma_3 / sigma_1`
- `alpha = sigma_3`

The reason is structural: the historical observability qualification was a four-source contrast test with target contrast dimension `S-1 = 3`. Applying `S-1` to all 206 dense candidate sources, or requiring every response-feature direction to be identifiable, would change the scientific object and can cause degenerate all-abstain behavior.

The 206 candidates remain the source hypothesis set used to construct M1 response ensembles and score localization. They do **not** imply a 205-dimensional identifiability requirement.

## Rules

1. Primary held-out test: `rank_k=3` only.
2. `rank_k` must not be tuned on H02 or final held-out results.
3. Optional development-only sensitivity may report `rank_k in {2,3,4}`, but this is an ablation and cannot replace the frozen primary result after test visibility.
4. Record `rank_k=3` in `RUN_MANIFEST.json`.
5. If the three-direction gate is still degenerate (nearly all-pass or all-fail), report that failure; do not silently search larger/smaller ranks.

The implementation in `experiments/cg_pc_ctt/completeness_gate.py` now defaults to `rank_k=3`.
