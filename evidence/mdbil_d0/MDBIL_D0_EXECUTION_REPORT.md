# MDBIL-D0 execution report — 2026-10-01

## Frozen decision

`MDBIL_D0_SOURCE_BLOCK_SIGNAL_HOLD`

G1, G2 and G4 pass. G3 fails. The source block is discriminative and stable under the frozen diagnostics, but the extra meteorological disentangling objectives do not establish an independent improvement over the ordinary TCN. The prior `CDSI_T01B_SOURCE_INFORMATION_STATIC_ONLY_HOLD` is preserved.

Relative to VANILLA-TCN, MDBIL improves the general invariance ratio in 3/8 folds, below the required 6/8. Its paired median general ratio gain is -2.045194742095191e-05; its paired median same-gas cross-wind ratio gain is -3.0065996213579638e-05. Lower ratios are better. Accuracy gains in X06/X07 cannot rescue this frozen gate.

## All eight held-out folds

Learned metrics are medians over the three frozen seeds. General and same-gas cross-wind ratios below are for MDBIL. Exact values for every arm, margin, ratio, reconstruction and context diagnostic are in `pass1/FOLD_METRICS.tsv`; all 48 learned seed rows are in `pass1/SEED_METRICS.tsv`.

| House | Context | Wind | Gas | RAW accuracy | STATIC accuracy | VANILLA accuracy | MDBIL accuracy | MDBIL general ratio | MDBIL wind ratio |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| H01 | X00 | 1,3-2,4_fast | 13 | 75% | 75% | 100% | 100% | 8.487062587e-06 | 7.128526249e-06 |
| H01 | X01 | 1,3-2,4_slow | 13 | 100% | 100% | 100% | 100% | 3.143081994e-05 | 3.307306906e-05 |
| H01 | X02 | 2,4-1_fast | 10 | 50% | 50% | 50% | 50% | 0.4994928837 | 0.4994353652 |
| H01 | X03 | 2,4-1_slow | 10 | 100% | 100% | 100% | 100% | 0.0001835722 | 0.0001748629 |
| H02 | X04 | 3,5-1_fast | 10 | 87.5% | 100% | 100% | 100% | 3.647593985e-05 | 3.000298966e-05 |
| H02 | X05 | 3,5-1_slow | 10 | 100% | 100% | 100% | 100% | 5.546843749e-05 | 5.435839557e-05 |
| H02 | X06 | 4,5-3_fast | 13 | 100% | 100% | 62.5% | 100% | 3.792756252e-05 | 3.454184116e-05 |
| H02 | X07 | 4,5-3_slow | 13 | 87.5% | 75% | 87.5% | 100% | 0.0001909965 | 0.0002058500 |

## Across-fold medians

These are medians across eight fold metrics, not pooled target accuracy.

| Arm | Accuracy | General ratio | Same-gas cross-wind ratio |
|---|---:|---:|---:|
| RAW-300D | 93.75% | 1.0931767225265503 | 0.4623962938785553 |
| STATIC-30D | 100% | 0.8899083733558655 | 0.23670466244220734 |
| VANILLA-TCN | 100% | 2.3732368390483316e-05 | 8.486678780172952e-06 |
| MDBIL | 100% | 4.669800000556279e-05 | 4.445011836651247e-05 |

Context decoding medians: VANILLA z_s = 1/6; MDBIL z_s = 0; MDBIL z_m = 1. Median z_s decoding reduction = 1/6; all eight folds are non-worse. This is cosine-prototype leave-one-out decoding on the 24 training-context embeddings. Zero accuracy in this diagnostic does not prove that all environment information has been removed, and it is not decoding a held-out meteorological class.

## Gate evidence

| Gate | Result | Frozen evidence |
|---|---|---|
| G1 | PASS | Median accuracy 1; 7/8 folds >=0.75; median margin 1.1087209582328796; 8/8 margins positive |
| G2 | PASS | Median general ratio 4.669800000556279e-05; 8/8 below 1; median wind ratio 4.445011836651247e-05; 8/8 below 1 |
| G3 | FAIL | Ratio improves against RAW and STATIC in 8/8 folds, but against VANILLA in only 3/8; paired median general and wind gains against VANILLA are negative |
| G4 | PASS | Median z_m decoding 1; median leakage reduction 1/6; non-worse z_s leakage in 8/8 folds |

## Input, split and execution provenance

- Branch: `research/mdbil-d0-source-weather-invariance-20261001`.
- Initial user freeze: `6eb41085e5853c66fdd4083a1bde494abb96d459`.
- Pre-scientific runtime freeze: `59893020ed56a44be142bca949ae85424701a475`.
- Manifest SHA256: `b504ec95324a9fe3ea9ef7f81999bfa9234ace4b3e65f1d09ba36b7723dd84b1`.
- Executed runner SHA256: `5ea7c885d5b170eb71acc6db7c3d1faa1d92a4ad4b40b992c3f9c550ae16856b`.
- Minimal VM input payload SHA256: `b3c6a2e1200a99944882b8b2715600f3440f6075234f4030d724fcdbc952f54e`.
- All 64 frozen concentration tensors and referenced metadata passed SHA256 checks; binary inputs use exactly C>0 and shape 10x30. No new extraction or threshold choice.
- Each fold trains on 24 samples and holds out eight samples within the same House; all same-gas, different-wind siblings were independently checked.
- Seeds: 2026100101, 2026100102, 2026100103. Fixed 500 epochs, one CPU thread per process. No checkpoint selection.
- A Windows integer-label compatibility error was repaired before scientific outputs by explicitly converting source/context labels to torch.long. Values, splits, architecture, losses and gates were unchanged. See the tracked repair note.
- Two Windows starts failed with duplicate OpenMP runtime Error #15 before any fold/seed metrics or scientific decision. Both attempts are preserved in `WINDOWS_OPENMP_ATTEMPTS/`; no unsafe OpenMP override was used.
- The unchanged repaired script then ran in the existing Linux VM environment: Python 3.10.12, NumPy 1.26.4, PyTorch 2.12.1+cpu. No VM packages or ROS build/install were changed.
- Full pass 1: exit 0, 365.4301484839525 seconds. Full pass 2: exit 0, 364.77545678196475 seconds. Separate processes/output directories ran concurrently. Both finished on 2026-10-01 at approximately 13:56:34 UTC.

## Determinism and independent audit

`MDBIL_D0_DETERMINISTIC_REPEAT_PASS`: all six official repeat outputs are byte-identical. The independent audit additionally checked INPUT_SHA256.tsv, so all seven key output files match byte-for-byte.

`MDBIL_D0_INDEPENDENT_OUTPUT_AUDIT_PASS`: independently checked 64 tensor/metadata hashes, binary definition, all eight splits/siblings, RAW/STATIC diagnostics, 48 seed rows, seed-to-fold medians and G1–G4 decision logic. Baseline and aggregation maximum absolute differences are exactly zero for both passes.

The frozen runner does not save trained weights or latent arrays. The independent audit therefore does not independently forward the learned embeddings; the two complete runs establish their reported numerical reproducibility. No weights or latent arrays were fabricated after the fact.

## Scope and STOP

This is within-House held-out-context evaluation in two Houses, not a model trained in one House and transferred to another. The A/B source configurations differ in x,y,z, including z; no pure XY identifiability, continuous source inversion, causal block identification or PMFS candidate-map claim follows.

New GADEN = 0; new source interventions = 0; PMFS runs = 0; closed loop = 0; confirmation access = 0; House03 access = 0. The minimal VM payload contained only the authorized H01/H02 discovery assets.

Completed and stopped. No retuning, PMFS integration, fixed-z data generation or further model experiment is authorized by this result.
