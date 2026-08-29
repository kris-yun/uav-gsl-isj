# CODEX TASK — FAST DEPLOYABLE SHARED PF-DEI

Date: 2026-08-29
Branch: research/cg-pc-ctt-v6-dynamic-transport-sbi

Normative science:
docs/PF_DEI_SHARED_FAST_DEPLOYABLE_FREEZE_20260829.md

This task supersedes the heavier shared Siamese-eight-TCN implementation proposal before any shared-model result has been observed.

## Trigger and current H01 reference

If the old H01 house-specific reference training is still running, preserve each seed's current best-validation checkpoint, logs and hashes, then stop additional reference-only epochs. Run at most one reserved qualification on those frozen checkpoints and label it H01_REFERENCE_DIAGNOSTIC_ONLY. It is not a hard gate for the shared deployable model.

Do not start H02/H03 house-specific neural training.

Preserve all completed physical banks and V1/V2/V3 evidence.

## 1. Implement shared residual-set TCN

Implement exactly the compute-efficient architecture from PF_DEI_SHARED_FAST_DEPLOYABLE_FREEZE_20260829.md:
- per-time observation-vs-predictive-member residual features;
- shared 5->24->16 member MLP;
- permutation-invariant mean and second-moment aggregation across predictive members;
- one causal TCN over the resulting per-time sequence;
- no House ID;
- no separate full TCN encoding for all eight simulated traces.

Mandatory selftests before large training:
- member permutation invariance;
- carrier permutation invariance;
- exact generating-member exclusion active;
- causal prefix test: future changes cannot affect current score;
- no forbidden fields;
- q0 posterior reconstruction in log space;
- same input/checkpoint reproducibility within frozen numerical tolerance.

## 2. Training efficiency audit

Before any LOHO full fold, run exactly 200 training steps and report:
- examples/s;
- GPU utilization;
- peak VRAM;
- data-loader wait fraction if measurable;
- projected epoch minutes.

If projected epoch >12 minutes, optimize engineering only: packed batching, mmap/pinned-memory reads, prefetch, vectorized member MLP, fused batch candidate scoring, AMP/TF32. Do not change architecture, labels, nuisance members or data split.

Proceed only when the implementation is not obviously I/O-bound or redundantly encoding the same tensors.

## 3. Three strict LOHO folds

Run one seed 2701 per fold:
- H01+H02 -> H03
- H01+H03 -> H02
- H02+H03 -> H01

Training recipe is frozen:
- AdamW 3e-4, wd 1e-4;
- batch 64 where feasible, else batch32+gradient accumulation;
- max25 epochs;
- patience4;
- gradient clip1.0;
- AMP/TF32 allowed;
- held-out House contributes zero training/validation/normalization examples.

Run reserved synthetic gate for each fold. Any fold fail => PF_DEI_SHARED_LOHO_NO_GO and stop neural expansion.

## 4. Historical truth-blind gate

Only after all LOHO synthetic gates pass, run the held-out-House historical future-predictive test under the frozen contract. No true source/error fields.

Any House failing >=5/10 or positive mean gain => PF_DEI_SHARED_HISTORICAL_PREDICTIVE_NO_GO.

## 5. Final reusable shared weights

Only after all LOHO gates pass, train final shared models on H01+H02+H03 using seeds 2801,2802,2803 in parallel if possible. These are the final deployable weights; no House-specific runtime model remains.

## 6. Runtime and real deployment

Implement batched incremental causal inference with per-candidate state caching. Measure runtime source-update latency; target <=10% of native source-update/sensing interval on target deployment hardware.

A new environment may regenerate map/wind-conditioned native predictive bank and perform source-independent sensor calibration, but must not retrain neural weights with source labels.

Before physical-world experiments, explicitly resolve the Q=10 ppm deployment condition: either control/calibrate physical release strength to the benchmark regime or freeze a source-independent Q-nuisance extension before observing localization outcomes. Do not use real source labels for this calibration.

## 7. Downstream closed loop

If shared LOHO + historical gates pass, continue with offline safety, runtime parity, six smoke runs, 60-arm development, and confirmatory seeds under existing frozen performance criteria. No scientific redesign after LOHO results.

Return terminal GO/NO-GO with compute/time accounting as well as scientific metrics.
