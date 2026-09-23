# C0.5 M4-v2 read-only preflight audit

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`  
Scope: read-only audit of the committed House/wind inventory and source validation. No plume generation, new seed, model training, PMFS replay, ROS/live-loop change, or charter edit was performed.

## Inputs and integrity

- Charter read: `C0_5_REAL_GADEN_INTERVENTION_BANK_CHARTER_20260923.md`.
- Task order read: `CODEX_M4_C0_5_TASK.md`.
- Inventory file SHA-256: `dec3b877783b606fc3bd1fceaa06acb32e6616b2cae2d2f2e2f7f52fc4ed71fb`.
- Source-validation file SHA-256: `75ea97b3260d1fbbfd794f1db290361c3f90912a5fdcbd092c5dc810040bc332`.
- Working tree was clean before this audit; the two input files are committed in `4d0258a` (`audit: inventory same-House physical wind interventions`).

## Physical same-geometry prerequisite

**READY (precondition only).** The inventory is source-blind and covers House01/02/03. Each House has one occupancy hash, four canonical GADEN wind configurations, 11 contiguous iterations per configuration, finite values, and byte size equal to `3 * cell_count * sizeof(double)`.

House02 is the selected cost-based House:

- occupancy SHA-256: `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`;
- dimensions: `83 x 119 x 26`; cell size `0.1 m`;
- W1: `3,5-1_fast`, 11 iterations, 6,163,248 bytes/iteration;
- W2: `3,5-1_slow`, 11 iterations, 6,163,248 bytes/iteration;
- both paths carry the same House02 geometry and source/gas metadata (`gasType_10`, `sourcePosition_0.00_-1.00_0.20`);
- W1/W2 iteration hashes are distinct for 10/11 iterations (iteration 0 is byte-identical); all-iteration max component delta is `1.032032 m/s`, mean absolute delta `0.0214427 m/s`, and 62.2115% of components differ by more than `1e-12`.

This supports the charter's same-geometry physical-wind prerequisite. The initial identical field is retained as an audit fact and is not counted as a difference.

## Source validation

**PASS for the two predeclared points.** Both points are inside the House02 bounds and free at the fixed source-height plane:

- S1 = `(-2.242730141, -2.200880051, 0.20)`, grid `(31,52,12)`, cell state `0`, nearest nonfree distance `0.50 m`.
- S2 = `(-4.342730045, 2.899120331, 0.20)`, grid `(10,103,12)`, cell state `0`, nearest nonfree distance `0.80 m`.
- source separation: `5.51543320993013 m`.

The validation occupancy hash equals the selected House02 inventory hash. No source coordinate was changed after truth or PMFS inspection in the audited artifacts.

## What this does and does not authorize

The committed artifacts make the **physical entry condition** for a future C0.5 bank generation READY. They do **not** constitute C0.5 scientific evidence:

- no 30/120/300 s generation-cost benchmark is present in this checkpoint;
- no 2 x 2 x 2 plume bank exists here;
- no independent plume-seed replication audit exists;
- no spatial plume slices, model comparison, held-out field result, PMFS source-rank result, or destructive null result exists;
- therefore there is no C0.5 ADVANCE or scientific PASS to report.

The appropriate status for execution now is **HOLD**: M6's separate DATA gate must be completed first, and no new plume seeds may be consumed in this preflight.

## Unseen-world boundary

C0.5 is explicitly one-House. Its preregistered S2-W2 fold is an unseen **source x wind recombination**, but S2, W2, and the House02 geometry are each already represented in training (S2-W1, S1-W2, and the same occupancy). It does not test:

- an unseen House or geometry;
- a leave-one-House-out transfer;
- a completely unseen physical wind family (an entire wind intervention held out);
- an unseen source location held out in all winds.

Thus M4-v2 currently cannot support the broader claim of generalization to an unfamiliar real world. Before promoting M4 as the main line, add a separately preregistered zero-shot gate after (or alongside) the single-House mechanism test:

1. **Leave-one-House-out geometry gate:** train/freeze on two Houses, test on the third House's occupancy and canonical wind without truth-tuned changes; compare monolithic, operator-compositional, and native/direct baselines.
2. **Leave-one-wind-family-out gate:** hold out an entire physical wind configuration/family, rather than only a source x wind cell where that wind is seen elsewhere; evaluate both independent plume seeds.
3. **Leave-one-source-out gate:** if source positions permit, hold out a source location across all training winds, so source novelty is not reduced to recombination.

These gates must use source-blind normalization/hyperparameters, report truth-containing candidate rank plus spatial diagnostics, and retain destructive intervention/null controls. A failure or reversal on either independent held-out seed is HOLD, not a tuning invitation.

## Decision

`C0.5 PREFLIGHT: READY for physical prerequisites; HOLD for scientific execution and main-innovation claim.`

`M4-v2 unseen-world coverage: NOT ESTABLISHED.`

No tracked file was modified and no new seed or raw plume data was consumed.
