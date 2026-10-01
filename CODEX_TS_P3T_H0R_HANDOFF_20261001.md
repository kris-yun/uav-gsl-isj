# CODEX handoff — TS-P3T-H0R exact snapshot-difference test

Date: 2026-10-01
Branch: \`research/ts-p3t-h0r-snapshot-difference-20261001\`

Read:
1. \`research/ts_p3t_h0r/H0R_SNAPSHOT_DIFFERENCE_CHARTER.md\`
2. \`research/ts_p3t_h0r/POST_H0_INVALID_RECOVERY_NOTE.md\`
3. parent H0 INVALID evidence under \`evidence/ts_p3t_h0_temporal_closure_20261001/\`
4. D0 evidence under \`evidence/p3t_d0_gaussian_support_20261001/\`

Do not change the parent H0 decision.

## Inputs

Use the same verified authoritative archive:
\`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz\`

For each of the four cases take exact:
- update4 measured map;
- update5 measured map;
- source-update timing;
- frozen PMFS prior/confidenceMeasurementWeight/sourceDiscriminationPower.

Use saved D0 P2/P3/G2/G3 candidate hit maps only.

No HCMC or later-run substitution.

## Step 1 — exact RECENT map

Use \`research/ts_p3t_h0r/reconstruct_recent_map.py\`.

Recover update4->update5 interval from logOdds and omega differences.

Independently verify recomposition at <=1e-12.

Commit/hash RECENT maps before truth is opened.

## Step 2 — source-blind scoring

Recompute unchanged PMFS log scores for every candidate under:
- FULL update5 map;
- RECENT exact map.

Do this for P2/P3/G2/G3.

Freeze:
- candidate score tables;
- rank correlations;
- omega age fractions;
- all input/output hashes.

Do not read truth ownership until this freeze is committed or separately hashed and timestamped.

## Step 3 — truth evaluation

Evaluate the frozen charter exactly.

Required outputs:
- \`H0R_RECENT_MAP_AUDIT.json\`
- \`H0R_OBSERVATION_MEMORY.tsv\`
- \`H0R_CANDIDATE_SCORES.tsv\`
- \`H0R_CASES.tsv\`
- \`H0R_RESULT.json\`
- \`H0R_DECISION.md\`
- \`INDEPENDENT_H0R_AUDIT.json\`
- \`SHA256SUMS.txt\`

Independent audit must derive RECENT directly from update4/update5 again and independently recompute scores/ranks.

## Return exactly

1. branch/final commit;
2. integrity result;
3. update4->5 duration for each case;
4. older-than-final-update omega fraction for each case;
5. P3 FULL/RECENT truth score/rank/margin;
6. G3 FULL/RECENT truth score/rank/margin;
7. decision;
8. H0R_RESULT SHA256;
9. new GADEN=0, forward=0, training=0, H03=0, closed-loop=0.

STOP after decision.
