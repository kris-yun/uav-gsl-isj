# CODEX HANDOFF — PASI D0 Fresh S3 Confirmation

Date: 2026-09-24  
Branch: `research/path-action-source-inference-v0`

Status: **FRESH CONFIRMATION ONLY — NO RESCUE, NO CLOSED LOOP**

Read first:

`01_idea/PATH_ACTION_SOURCE_INFERENCE_FREEZE_20260924.md`

## Mission

Freshly test the frozen source-conditioned stochastic path-action proxy on S3.

S1/S2 were used during exploration and must not be used to alter the frozen formula.

## Frozen S3

- source id: `pmfs_3_12`
- xyz: `(-4.342730045, -3.700880051, 0.20)`
- House02
- W2 = `3,5-1_slow`

Fresh target seeds:

- S3_W2_E = `2026092403`
- S3_W2_F = `2026092404`

Prediction bank remains the existing Gate-1A 630-source bank:

- C = `2026092401`
- D = `2026092402`

Do not regenerate the 630-source bank.

## Hard freeze

Do not change:

- S3 source;
- target seeds;
- prediction seeds;
- W2 wind;
- occupancy/GADEN/extractor contracts;
- frozen 30 pooled probes and 10 times;
- raw ppm representation;
- local variance formula `(C-D)^2/2`;
- global floor = mean local variance over all 630 sources;
- floor multiplier = 1.0;
- path-action formula;
- PASS/STOP predicates.

No neural network.
No normalization.
No memory-kernel rescue.
No House01/03.
No closed loop.

## Run

```bash
git checkout research/path-action-source-inference-v0
git pull --ff-only
git status --short

python3 -m py_compile research/path_action_source_inference_v0/score_pasi_d0_s3.py
bash -n research/path_action_source_inference_v0/run_pasi_d0_s3_w2_vm.sh

bash research/path_action_source_inference_v0/run_pasi_d0_s3_w2_vm.sh
```

## Frozen decision

PASS:

`PASI_D0_PASS_FRESH_S3_PATH_ACTION_SIGNAL`

FAIL:

`PASI_D0_FAIL_STOP_PATH_ACTION_MAINLINE`

If FAIL, stop immediately. Do not tune or generate more targets.

If PASS, also stop after packaging; cross-House is not yet authorized.

## Commit evidence

```bash
git add evidence/path_action_source_inference_v0/
git commit -m "evidence: record fresh S3 path-action D0 result"
git push origin research/path-action-source-inference-v0
```

## Package

```bash
bash research/path_action_source_inference_v0/package_pasi_d0_s3_review.sh
```

Upload:

`/home/zyc/PASI_D0_S3_W2_REVIEW_20260924.tar.gz`

Report:

1. branch;
2. final commit;
3. decision;
4. S3_E raw / homoscedastic / heteroscedastic-residual-only / path-action ranks;
5. S3_F same four ranks;
6. rank sums;
7. package path;
8. package bytes;
9. package SHA256;
10. any infrastructure-only patch.
