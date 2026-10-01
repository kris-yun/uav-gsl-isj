# CODEX handoff — PMFS3D-R1P5 saved-score suppression audit

Date: 2026-10-01
Branch: `research/pmfs3d-r1p5-suppression-audit-20261001`

## Read first

1. `research/pmfs3d_r1p5/R1P5_SUPPRESSION_SELECTIVITY_CHARTER.md`
2. `research/pmfs3d_r1p5/analyze_suppression_selectivity.py`
3. parent result: `evidence/pmfs3d_r1_oracle_ranking_20261001/R1_FINAL_REPORT_20261001.md`

The charter is frozen. Do not change gates after seeing outputs.

## Task

Run **only** the saved-score R1P5 audit on the already-completed R1 scientific outputs.

Expected existing source folder on the same VM/workspace:

`PMFS3D_R1_SCIENTIFIC_20261001/`

It must contain:

`repeat1/<case>/oracle2d/candidate_log_scores.csv`
`repeat1/<case>/oracle3d/candidate_log_scores.csv`

for the four frozen R1 cases.

Use the R1 result JSON from either:
- the saved science folder `evaluation1/R1_RESULT.json`, or
- the byte-identical frozen evidence copy.

If the science folder is absent, locate/unpack the **existing** R1 review/scientific archive only. Do not regenerate forward maps.

## Command template

```bash
python3 research/pmfs3d_r1p5/analyze_suppression_selectivity.py \
  --science-root /ABS/PATH/TO/PMFS3D_R1_SCIENTIFIC_20261001 \
  --r1-result /ABS/PATH/TO/R1_RESULT.json \
  --out evidence/pmfs3d_r1p5_suppression_audit_20261001
```

Run once. The output directory intentionally refuses overwrite.

## Required outputs

Commit all four:
- `R1P5_RESULT.json`
- `R1P5_CASES.tsv`
- `R1P5_CANDIDATES.tsv`
- `R1P5_DECISION.md`

Also create:
- `RUN_PROVENANCE.md` with absolute input locations, git HEAD, Python version, SHA256 of the input R1 result and every input candidate score CSV.
- `SHA256SUMS.txt` for the R1P5 evidence files.

## Forbidden

Do not:
- run GADEN;
- rerun Oracle-2D/Oracle-3D forwards;
- edit R1 scores/maps;
- add or tune a scorer;
- create fusion weights;
- open H03 or confirmation;
- train a model;
- run ROS or 300 s closed loop;
- change any threshold in the frozen charter.

## Decision handling

Valid decisions are:
- `PMFS3D_R1P5_SELECTIVE_FALSE_SUPPRESSION`
- `PMFS3D_R1P5_HOLD_PARTIAL_SELECTIVITY`
- `PMFS3D_R1P5_FRAGILE_TOP_COMPETITOR_SUPPRESSION_STOP`
- `PMFS3D_R1P5_INVALID_STOP`

Regardless of result: **STOP after committing evidence.**

Do not start the counterexample-guided method. That requires a separate review of R1P5.

## Return exactly

Report:
1. branch;
2. final commit SHA;
3. decision;
4. selective cases / 4;
5. House01 common-candidate count and Spearman;
6. House02 common-candidate count and Spearman;
7. for each case: ahead2d count, fraction A>0, median A, repaired crossings, harmful crossings, ties added/removed;
8. SHA256 of `R1P5_RESULT.json`;
9. confirmation: new GADEN=0, new forward=0, training=0, closed-loop=0.
