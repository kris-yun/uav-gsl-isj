# CODEX handoff — TS-P3T-H0 temporal closure audit

Date: 2026-10-01
Work branch: research/ts-p3t-h0-temporal-closure-20261001

Read:
1. research/ts_p3t_h0/POST_D0_INTERPRETATION_20261001.md
2. research/ts_p3t_h0/H0_TEMPORAL_CLOSURE_CHARTER.md
3. evidence/p3t_d0_gaussian_support_20261001/P3T_D0_DECISION.md
4. research/pmfs3d_r1/R1_TRANSFER_AUDIT_20261001.md

## Critical provenance rule

Use only the exact authoritative TNQC archive that supplied the R1 frozen cases:
\`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz\`
or the verified extracted VM copy whose hashes match that archive.

Do not substitute:
- HCMC 20260922 runs;
- native-recovery 20260923 runs;
- a repeated later H01 run.

If exact measurement events/raw trace cannot be tied to the R1 case hashes, return
\`TS_P3T_H0_INVALID_STOP\`.

## Execution order

### P0
Recover the exact historical measurement event stream and reconstruct each terminal measured hit/confidence map.

Do not proceed until archived terminal parity passes.

Commit P0 evidence before truth evaluation.

### H0
Construct exactly:
- O_full;
- O_40;
- O_update.

Score the already-saved P2/P3/G2/G3 D0 candidate hit maps under each observation map.

Do not rerun a candidate forward and do not run GADEN.

Freeze all candidate scores and source-blind diagnostics before loading truth ownership.

Then evaluate the frozen gate and STOP.

## Required evidence

At minimum:
- P0_PROVENANCE.md
- P0_TERMINAL_MAP_PARITY.json
- H0_OBSERVATION_MEMORY.json
- H0_CANDIDATE_SCORES.tsv
- H0_CASES.tsv
- H0_RESULT.json
- H0_DECISION.md
- INDEPENDENT_H0_AUDIT.json
- SHA256SUMS.txt

Independent audit must rebuild O_full/O_40/O_update and candidate scores from retained event inputs.

## Return

Report:
1. branch/final commit;
2. P0 parity result;
3. exact O_40 and O_update event counts/durations per case;
4. fraction of terminal confidence memory older than 40 s;
5. P3 and G3 truth score/rank/margin under O_full/O_40/O_update;
6. decision;
7. SHA256 of H0_RESULT.json;
8. confirmation new GADEN=0, new forward=0, training=0, H03=0, closed-loop=0.
