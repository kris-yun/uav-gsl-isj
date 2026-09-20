# TNQC offline advancement gate — 2026-09-20

## Frozen claim boundary

This file records the last offline gate before any new House01/02/03 closed-loop run. No House source truth may be used to change the equations below after this checkpoint.

Main candidate: **Transport-Nuisance Quotient Canonicalization (TNQC)**.

The online score compares the measured and candidate-predicted spatial fields only after quotienting independent positive affine actions in logit space. The candidate prediction remains conditioned on the PMFS transport model and the current wind field; the quotient removes non-identifying global release/background/gain coordinates rather than trying to learn them.

Secondary mechanism: **confidence-weighted local-order quotient**.

The local-order channel compares only adjacent free-cell order relations. It is invariant to arbitrary strictly increasing pointwise sensor transfer functions. It is fused 1:1 with the continuous affine-quotient cosine; the weight is not fitted.

## Independent measured-data signal

Dataset: public Orebro3DSEN (27 calibrated MOX sensors, 3x3x3 grid, 2 Hz). Exp01/02/06/08/09 share a physical source location while release and airflow conditions vary; the remaining experiments provide different source locations. Only 40–90 min data are used by the frozen probe.

A deliberately low-capacity 5 min window test gives:

| representation | same/different AUC | leave-condition-out repeated-source accuracy |
|---|---:|---:|
| raw sensor means | 0.486 | 0.20 |
| affine-quotient spatial shape | 0.789 | 0.62 |
| local neighbour order | 0.681 | 0.68 |
| equal continuous + local-order fusion | 0.791 | 0.70 |

The local-order channel remains non-trivial across window scales:

| window | affine quotient AUC / acc | local order AUC / acc | equal fusion AUC / acc |
|---|---|---|---|
| 2 min | 0.806 / 0.600 | 0.696 / 0.696 | 0.791 / 0.616 |
| 5 min | 0.789 / 0.620 | 0.681 / 0.680 | 0.791 / 0.700 |
| 10 min | 0.789 / 0.600 | 0.723 / 0.680 | 0.823 / 0.680 |

These numbers use a simple cosine/order prototype test and are intentionally more conservative than the earlier transductive/cross-standardized screen.

### Reproducibility reconciliation

A fresh independent re-evaluation against the current public Orebro3DSEN blobs and the current `reference/tnqc_orebro_offline.py` logic found that an earlier draft of this gate understated the affine-only LOCO accuracy at 2 and 5 min (and shifted its AUC slightly at 2/10 min). The table above has been corrected to the current reproducible values. The local-order and equal-fusion headline values are unchanged. The correction was made before any House closed-loop TNQC result was available and changes no online equation or threshold.

## Nonlinear monotone stress

Each experiment is subjected to a different fixed compressive transform g_a(c) = asinh(a c) / a, a > 0, with transform strength assigned without source truth.

5 min result:

| representation | original AUC / acc | nonlinear-stress AUC / acc |
|---|---|---|
| affine quotient | 0.789 / 0.62 | 0.760 / 0.66 |
| local neighbour order | 0.681 / 0.68 | 0.681 / 0.68 |
| equal fusion | 0.791 / 0.70 | 0.743 / 0.64 |

The local-order representation is exactly unchanged for every tested window. This is the intended role of the secondary channel: preserve a source-bearing signal when the continuous affine quotient is no longer exact.

## Novelty boundary

Do **not** claim monotone/rank invariance alone as novel.

Jin et al., ICRA 2026, *Calibration-Free Gas Source Localization with Mobile Robots: Source Term Estimation Based on Concentration Measurement Ranking* already performs probabilistic source estimation by comparing global ranking sequences of measured and modeled concentrations.

The current defensible distinction is the full TNQC construction:

1. explicit nuisance-group quotient formulation;
2. continuous affine-quotient spatial field comparison;
3. transport-conditioned candidate prediction from PMFS;
4. local **spatial adjacency** partial-order channel rather than a global trajectory rank sequence;
5. support/confidence weighting and identifiability abstention;
6. direct insertion into the PMFS candidate likelihood, with a shadow arm that must leave the native trajectory unchanged.

The local-order component is therefore an auxiliary robustness mechanism, not the paper-level novelty by itself.

## Code frozen for first closed-loop screen

- ros2_package/src/gsl_server/algorithms/PMFS/internal/TNQCScore.hpp
- PMFS modes: tnqc_mode={off,shadow,fused,only}
- ros2_package/test/test_tnqc_score.cpp
- reference/tnqc_orebro_offline.py
- reference/run_tnqc_closed_loop_matrix_20260920.sh

shadow computes TNQC diagnostics while preserving the native PMFS score. fused multiplies the native candidate score by exp(TNQC evidence). only removes the native likelihood and is a mechanism ablation.

## Pre-registered closed-loop decision gate

Run House01/02/03, seeds 0/1 with the same 300 s budget and stepsSourceUpdate=3.

Before interpreting fused or only:

1. OFF and SHADOW must produce the same final native PMFS result under the deterministic RNG contract. A mismatch invalidates the batch.
2. No parameter, fusion weight, evidence cap, support rule, PMFS cadence, or planner setting may be changed after reading source truth.
3. fused is the primary TNQC arm; only is diagnostic.

Advancement threshold for a first closed-loop development screen:

- pooled top-5%-expected-location error reduction versus native PMFS >= 10%;
- at least 4 of 6 House/seed pairs improve;
- no pair degrades by more than 25%;
- no false confident collapse.

A stronger result is required before a paper claim; this gate only decides whether TNQC deserves the next experimental cycle.

## Reproduction

Public-data probe:

    python3 reference/tnqc_orebro_offline.py --window-minutes 5

Closed-loop matrix after the installed launch overlay exposes tnqc_mode:

    bash reference/run_tnqc_closed_loop_matrix_20260920.sh

## Local implementation sanity check

The standalone TNQC score test was compiled with C++20 and `-Wall -Wextra -Wpedantic -Werror` against the frozen header and passed all assertions for affine invariance, monotone local-order invariance, negative reversed-field evidence, and insufficient-support abstention.
