# CODEX TASK — post-H01 shared cross-environment PF-DEI

Date: 2026-08-29
Branch: `research/cg-pc-ctt-v6-dynamic-transport-sbi`

Normative science:

`docs/PF_DEI_SHARED_CROSS_ENVIRONMENT_FREEZE_20260829.md`

This task is **conditional**. Do not execute it until the currently running H01 house-specific reference model finishes its original reserved qualification.

## Trigger

- If H01 reference qualification FAILS: terminate `NEURAL_PF_DEI_NO_GO`. Do not execute this task.
- If H01 reference qualification PASSES: preserve/freeze the H01 reference evidence and execute this task automatically.

The H01 reference model is not a deployable final method and must not be used as H01-specific runtime weights in the final shared method.

## 1. Preserve current banks and evidence

Preserve all V1/V2/V3 evidence, RNG parity, region support, native trace generator outputs, H01 reference training logs/weights/qualification, and all three House physical banks.

Do not regenerate a valid bank merely to change training behavior. Bank generation remains governed by the V3 physical contracts.

## 2. Implement the shared physics-conditioned comparator

Implement exactly `PF_DEI_SHARED_CROSS_ENVIRONMENT_FREEZE_20260829.md`.

Key differences from the H01 reference classifier:

- one shared architecture across Houses;
- no House ID input;
- observation is compared explicitly with each candidate carrier's frozen native predictive ensemble;
- observed and simulated sequences use one Siamese causal TCN encoder;
- candidate predictive members are permutation-invariantly aggregated;
- a training observation's exact generating nuisance member is excluded from its positive predictive set;
- negative candidate uses the same observation/trajectory/environment and changes only the carrier.

Mandatory selftests before large training:

- member permutation invariance;
- carrier index permutation invariance;
- exact same-pair reproducibility;
- leave-one-generating-member exclusion active;
- no House ID or forbidden truth field in tensors;
- causal prefix truncation: changing future samples cannot change current logit;
- q0 posterior reconstruction stable in log space.

## 3. Three strict LOHO folds

Run exactly:

- H01+H02 train -> H03 held out;
- H01+H03 train -> H02 held out;
- H02+H03 train -> H01 held out.

Use optimization seed `2701` for each fold. Do not use held-out House examples for training, early stopping, normalization fitting, feature scaling estimation, or checkpoint selection.

Any normalization constants that are not fixed physical constants must be fitted on the two training Houses only and then frozen before applying to the held-out House.

The held-out House physics bank is allowed only at inference/qualification time.

## 4. LOHO synthetic gate

Use only the held-out House reserved nuisance members and reserved trajectory skeletons as observation generators. Candidate predictive ensembles use the eight training nuisance members.

Apply all thresholds from the shared freeze.

If any fold fails, terminal:

`PF_DEI_SHARED_LOHO_NO_GO`

Do not train House-specific rescue models and do not modify architecture/hyperparameters.

## 5. LOHO historical truth-blind future-predictive gate

Only if all synthetic LOHO folds pass, apply each frozen fold model to the 10 historical OFF runs of its held-out House.

Do not read true source, localization error, ON/OFF performance, or historical true_gas_ppm.

Use the existing four chronological prefix/future splits and frozen energy-score future-predictive comparison.

Each held-out House must pass >=5/10 and have positive mean future-predictive gain.

If any fails, terminal:

`PF_DEI_SHARED_HISTORICAL_PREDICTIVE_NO_GO`

## 6. Final shared deployment ensemble

If all LOHO gates pass, train final shared models on simulation data from H01+H02+H03 using identical architecture/objective and seeds:

`2801,2802,2803`.

Freeze weights and hashes. There must be no House-specific runtime model selection.

Runtime score is the mean of the three shared logits.

## 7. Continue the V3 downstream contract

After final shared weights freeze, continue the already-defined V3 downstream sequence without method redesign:

- historical offline safety check;
- shared runtime integration replacing only the source-posterior channel;
- Python/runtime prefix and permutation parity;
- six infrastructure smoke runs;
- 60-arm H01/H02/H03 x seeds0..9 OFF/ON;
- if development GO, seeds10..19 confirmatory.

Use unchanged final performance criteria:

- pooled expected-location error reduction >=10%;
- >=20/30 improve;
- no House pooled mean degradation >5%;
- zero new false-confident collapses.

## 8. New-environment deployment artifact

If development/confirmatory succeeds, produce a deployment script/checklist that accepts a new source-independent environment definition and performs only:

1. map/3-D occupancy validation;
2. wind/config validation;
3. sensor calibration without source labels;
4. carrier-region construction;
5. latent-placement/native GADEN predictive bank generation;
6. frozen shared-model inference.

It must not expose a training/fine-tuning step for the new environment.

## 9. Stop behavior

Do not ask for a new method design between successful stages. Continue until one terminal state from this task/downstream V3 contract is reached.

Scientific/hyperparameter changes after any LOHO result are forbidden.
