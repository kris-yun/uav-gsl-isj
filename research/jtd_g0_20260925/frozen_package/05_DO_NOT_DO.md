# 05 — DO NOT DO / STOP RULES

This file overrides any temptation to "improve" a failed Gate.

## Forbidden scientific rescue

- no alternative block counts after seeing result
- no alternative PCA dimension
- no supervised embedding
- no neural sequence classifier
- no selecting easy source pairs
- no removing hard sources
- no excluding zero-heavy sources unless R0 contract already excludes them
- no new threshold
- no truth-tuned source prior
- no use of source coordinates as features
- no calibration fitted on eval fold
- no adding fresh plume runs
- no ≥143-source expansion
- no House01/02/03 expansion
- no closed-loop run
- no active planner
- no paper novelty claim

## Forbidden statistical inflation

- 300 observation entries are not n=300 independent tasks
- 120 pairwise distances from 16 runs are not 120 independent plume runs
- 200 shuffles are a null distribution, not 200 independent physical experiments
- 4 CV folds reuse the same 288 realizations and are not four independent studies

## If GO

Stop after packaging evidence.
Do not automatically start confirmation.

## If HOLD

Stop and report exactly which criterion failed.

## If STOP

Record failure as useful evidence.
Do not change the method in the same branch/run.
