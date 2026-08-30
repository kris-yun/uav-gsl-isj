# CTT temporal audit review pointer

Date: 2026-08-30

This branch is audit-only and remains `CLOSED_LOOP_NOT_AUTHORIZED`.

Codex1 must review the exact branch/PR head commit reported by GitHub at review start. Do not review a moving worktree or an earlier intermediate commit.

Required reading order:

1. `docs/CTT_TEMPORAL_AUDIT_UPLOAD_COMPLETENESS_20260830.md`
2. `experiments/cg_pc_ctt/ctt_temporal_audit_20260830/CTT_TEMPORAL_AUDIT_FILE_SHA256.tsv`
3. `docs/CTT_CAUSAL_TEMPORAL_V3_V7_AUDIT_20260830.md`
4. `docs/CODEX1_REVIEW_CTT_CAUSAL_TEMPORAL_V3_V7_20260830.md`
5. all 12 Python files under `experiments/cg_pc_ctt/ctt_temporal_audit_20260830/`

Evidence status at branch freeze: source audit `FULL`; combined V3--V7 per-case/checkpoint archive in current branch/artifact set `PARTIAL/MISSING`. Missing historical evidence must not be recreated with new data or tuning.

No closed-loop, shadow, retraining, or posterior/planner integration is authorized from this branch.
