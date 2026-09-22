# Performative-Feedback GSL V1 — 300 s R2 mechanism screen

Date: 2026-09-22
Status: **MECHANISM PASS / REMEDY INCOMPLETE / DO NOT RUN CLOSED LOOP YET**

## Mother idea

Gas-source localization is treated as a **performative inference** problem:

> the current source posterior influences robot motion; robot motion changes the future observation distribution; those observations are then reused to update the source posterior.

Therefore the data distribution is endogenous to the inference policy rather than fixed.

This is conceptually different from ordinary model mismatch, posterior calibration, or active information gain.

Recent remote-field anchors:
- NeurIPS 2025 — *Statistical Inference under Performativity*.
- NeurIPS 2025 — *Tight Lower Bounds and Improved Convergence in Performative Prediction*.
- ICML 2025 — *Clipped SGD Algorithms for Performative Prediction: Tight Bounds for Stochastic Bias and Remedies*.
- AAAI 2025 — *Identifying Predictions That Influence the Future: Detecting Performative Concept Drift in Data Streams*.

## Authoritative data

GitHub Release:
`tnqc-v5-r2-execution-20260921`

Archive:
`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

SHA256:
`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

Six 300 s cases:
- House01 seed0/1, truth (-0.4, -2.9)
- House02 seed0/1, truth (0.0, -1.0)
- House03 seed0/1, truth (-0.45, 1.9)

Frozen baseline fact:
- 6/6 integrity PASS
- 6/6 false-confident collapse
- pooled TNQC improvement -0.009162%

## Mechanism test 1 — candidate score follows the visited trajectory

At final source update, for every native candidate source location:
1. compute its minimum distance to the actually executed 300 s robot trajectory;
2. rank candidates by native PMFS source score;
3. compute Spearman association between score rank and trajectory distance.

Spearman association of **worse native rank with larger distance from the visited trajectory**:

- H01 seed0: +0.643
- H01 seed1: +0.679
- H02 seed0: +0.756
- H02 seed1: +0.807
- H03 seed0: +0.689
- H03 seed1: +0.697

Thus, in all six cases, candidates close to the policy-induced observation path receive systematically better native rank.

By contrast, native score rank is weakly or inconsistently associated with distance to the true source.

## Mechanism test 2 — terminal estimate collapses onto sampled support

Minimum executed-trajectory distance:

| Case | to truth (m) | to native top-5% estimate (m) | native error (m) |
|---|---:|---:|---:|
| H01 s0 | 1.024 | 0.276 | 5.527 |
| H01 s1 | 2.997 | 0.071 | 4.002 |
| H02 s0 | 1.389 | 0.012 | 4.107 |
| H02 s1 | 1.581 | 0.037 | 3.701 |
| H03 s0 | 1.647 | 0.207 | 7.782 |
| H03 s1 | 1.647 | 0.175 | 8.212 |

All six final native estimates lie very near visited support while remaining far from truth.

This is consistent with a self-confirming sampling loop.

## Historical-deployment screen

Truth-blind intervention:
- retain all five source-update snapshots;
- use equal-weight historical candidate risk rather than only the final snapshot;
- candidate risk = unweighted mean absolute measured-vs-simulated support residual;
- no truth tuning.

Top-5% centroid error after historical aggregation:

- H01 s0: 1.053 m
- H01 s1: 1.139 m
- H02 s0: 1.209 m
- H02 s1: 1.750 m
- H03 s0: 9.482 m
- H03 s1: 7.688 m

Interpretation:
historical snapshots strongly repair H01/H02, but not H03.

## Cross-policy / two-seed screen

For each House, align candidate source coordinates between seed0 and seed1 and aggregate source-blind MAE percentile risk.

Average-risk result:
- H01 truth-near rank: 3; top-5% centroid error 1.294 m
- H02 truth-near rank: 10; top-5% centroid error 1.519 m
- H03 truth-near rank: 111; top-5% centroid error 7.691 m

Worst-case/minimax risk:
- H01 truth-near rank: 1; top-5% centroid error 2.295 m
- H02 truth-near rank: 8; top-5% centroid error 1.213 m
- H03 truth-near rank: 108; top-5% centroid error 7.157 m

Therefore diverse historical/policy support helps when at least one policy visits an informative region, but cannot recover information absent from both H03 trajectories.

## Truth-blind trajectory-residualization control

A linear source-blind residualization of candidate risk against minimum trajectory distance was tested.

It did not solve H03 and does not constitute a sufficient remedy.

## Current scientific conclusion

**Mechanism: PASS.**

The authoritative six-case R2 data contain a strong, repeatable signature of policy-induced candidate bias:
native source score is systematically coupled to where the robot has already sampled.

**Remedy: INCOMPLETE.**

Historical deployment data and cross-policy robust aggregation materially improve H01/H02 but fail H03 because both H03 policies occupy the same wrong support basin.

Therefore the load-bearing main-innovation hypothesis must include an **active feedback-breaking intervention**, not merely reweight old data.

## Promotion gate before any closed-loop implementation

Do not authorize ROS closed loop until a cheap offline/counterfactual mechanism demonstrates all of:

1. a source-blind rule detects when the inference-support feedback loop is becoming self-confirming;
2. a policy-independent or counterfactual exploration action can be selected without endpoint truth;
3. on available data/simulator assets, that intervention creates source-discriminative support not present in the native policy;
4. the intervention is distinct from generic entropy/information-gain exploration;
5. expected native 300 s endpoint gain is large enough to justify a six-case closed-loop matrix.

Current state:
**KEEP AS LEADING MAIN-THESIS CANDIDATE; DO NOT PROMOTE TO CLOSED LOOP YET.**
