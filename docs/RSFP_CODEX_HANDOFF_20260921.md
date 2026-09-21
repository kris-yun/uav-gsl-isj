# RSFP V1 — Codex / VGR VM Offline Gate Handoff

Date: 2026-09-21  
Branch: `research/renormalization-source-fixed-point-v1`  
Method: `RENORMALIZATION_SOURCE_FIXED_POINT_V1`  
Status before execution: **STAGE-1 POSITIVE / 300-s DECISIVE GATE PENDING / CLOSED LOOP FORBIDDEN**

## 1. Goal

Run the already-frozen House01/02/03 × seed0/1 native PMFS trajectories through the pre-registered RSFP counterfactual replay.

Do **not** generate a new trajectory batch.

The only scientific question is:

> Does source evidence that survives the frozen 1/2/4/8 spatial coarse-graining flow improve the original native 300-s PMFS top-5% ExpectedValue localization endpoint, and does it outperform single-scale smoothing and naive multiscale averaging?

## 2. Authoritative frozen input

Use only:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

Frozen SHA-256:

`81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`

The package was independently verified with:

- declared files: 428
- missing files: 0
- SHA mismatches: 0

Do not substitute earlier House01 diagnostics, 240-s assets, a newly generated GADEN realization, or a different PMFS run.

Required six case directories after extraction:

- `House01_seed0_off_off`
- `House01_seed1_off_off`
- `House02_seed0_off_off`
- `House02_seed1_off_off`
- `House03_seed0_off_off`
- `House03_seed1_off_off`

Each must retain its original `context_bank/` and `launch.log`.

## 3. Frozen repository files

Execute from this branch with no method edits:

- `research/rsfp_v1/README.md`
- `reference/rsfp_vgr_fixed_trajectory_replay.py`
- `reference/aggregate_rsfp_vgr_offline_gate.py`
- `reference/test_rsfp_multiscale_score.py`
- `reference/run_rsfp_vgr_offline_gate_20260921.sh`

The replay imports the already-audited TNQC V7 loader / PMFS reconstruction / linked-native endpoint machinery from:

- `reference/tnqc_vgr_fixed_trajectory_replay.py`

## 4. Frozen RSFP definition

Spatial coarse factors are exactly:

`[1, 2, 4, 8]`

With the native 0.3-m PMFS grid these correspond to:

`[0.3, 0.6, 1.2, 2.4] m`

For every source candidate and scale:

1. aggregate supported measured hit-logit and candidate predicted hit-logit within that scale's spatial blocks using PMFS confidence weights;
2. compute the centered weighted canonical cosine;
3. retain the candidate only when all four predeclared scales are valid.

Required variants:

- `fine_only`: factor-1 canonical score;
- `coarse_only`: factor-8 canonical score;
- `mean_only`: equal arithmetic mean over factors 1/2/4/8;
- `fixed_only`: minimum/lower envelope over factors 1/2/4/8.

Scientific primary:

`fixed_only/only`

The lower envelope is deliberate: evidence must survive every predeclared scale. It is not legal to choose the best scale after seeing truth.

Also record each variant's `tilt` version, but do not substitute it for the primary after seeing results.

## 5. Why primary is RSFP-only rather than a weak native tilt

The previous frozen six-case diagnosis already established that native PMFS can be extremely concentrated several metres from truth and that true-source candidate ordering itself can be wrong/missing.

Therefore a weak bounded tilt of the false-confident native posterior is not a decisive test of whether RSFP contains source-identifying information.

The gate evaluates:

- RSFP-only source map as the scientific primary;
- native+RSFP tilt only as an integration diagnostic.

This choice is frozen before inspecting RSFP 300-s outcomes.

## 6. Required controls

RSFP is not promoted merely because a coarse map works.

The primary must beat all three pooled controls:

- `fine_only/only`;
- `coarse_only/only`;
- `mean_only/only`.

Interpretation:

- if `fine_only` wins, there is no load-bearing renormalization contribution;
- if `coarse_only` wins, the effect is ordinary coarse smoothing;
- if `mean_only` wins, the effect is naive multiscale fusion;
- only a positive `fixed_only` advantage supports the scale-stability thesis.

The already-frozen TNQC V5 result remains an external negative reference:

- pooled native: 5.555060292 m
- pooled TNQC fused: 5.555569247 m
- pooled improvement: -0.009162%
- improved cases: 1/6
- false-confident-collapse: 6/6

`fine_only` is a single-scale canonical-score control; it is **not** to be relabeled as the full frozen TNQC V5 fused method.

## 7. Endpoint

Use only the linked-native evaluator that directly calls:

`GSL::Utils::ExpectedValue(sourceProbability, 0.05)`

The replay refuses scientific validity unless the same evaluator reproduces the native logged PMFS endpoint within the frozen rounding tolerance.

No Python tie-breaking endpoint may replace the linked-native result.

No 5-min/10-min substitute metric.

## 8. Execution

First verify the exact checked-out branch and commit.

Then locate the extracted frozen six-case root and linked-native endpoint binary.

Example:

```bash
git checkout research/renormalization-source-fixed-point-v1
git rev-parse HEAD

export RUN_ROOT=/path/to/extracted/frozen_six_case_root
export ENDPOINT_EVAL_BIN=/path/to/tnqc_expected_value_native

bash reference/run_rsfp_vgr_offline_gate_20260921.sh
```

The runner performs:

1. Python syntax compilation;
2. deterministic algebra/invariance unit test;
3. six frozen 300-s replays;
4. linked-native endpoint evaluation for native and all RSFP variants;
5. six-case aggregation.

A final process exit code `10` means scientific **HOLD**, not an execution crash.

## 9. Frozen promotion rule

RSFP may proceed to closed-loop implementation only if all are true:

- all six integrity checks valid;
- pooled `fixed_only/only` endpoint improvement >= 2% versus native;
- at least 4/6 cases improve;
- worst single-case degradation <= 25%;
- no false-confident collapse;
- pooled `fixed_only/only` error is strictly lower than:
  - `fine_only/only`,
  - `coarse_only/only`,
  - `mean_only/only`.

If any condition fails:

**RSFP_VGR_300S_OFFLINE_HOLD**

Stop. Do not tune this six-case batch.

## 10. Forbidden after seeing output

Do not change any of the following after inspecting any House result:

- factors 1/2/4/8;
- block construction;
- confidence weighting;
- canonical cosine equation;
- lower-envelope definition;
- primary variant;
- evidence coefficient;
- endpoint;
- House truth;
- 2% promotion threshold;
- 4/6 requirement;
- 25% degradation cap;
- false-collapse rule.

Do not replace `min(q_1,q_2,q_4,q_8)` with max, median, selected scale, fitted weights, or a truth-selected plateau.

If the frozen result is negative, record the negative result and resume the main-innovation search under a new method/version.

## 11. Required return artifacts

Return/upload without manual editing:

1. `rsfp_vgr_300s_offline_gate.json`
2. each case's `rsfp_fixed_trajectory_evaluation.json`
3. all `rsfp_endpoint_posteriors/*.csv`
4. exact repository commit SHA
5. exact `tnqc_expected_value_native` SHA-256
6. terminal stdout/stderr from the runner
7. archive SHA-256 verification result

Do not report only a summarized percentage.

## 12. Current scientific rationale before the 300-s result

The controlled 240-s mechanism screen found a finite source-identity scale plateau:

- factor 1 / 0.3 m: 12/12
- factor 2 / 0.6 m: 12/12
- factor 4 / 1.2 m: 12/12
- factor 8 / 2.4 m: 12/12
- factor 16 / 4.8 m: 11/12

Mean signed source margin increased from approximately 0.776 at factor 1 to 0.837 at factor 8.

The eliminated fine-scale residual was only 10/12 at factors 2/4/8.

Hard controls:

- factor-2 grid phase: 4/4 phase offsets remain 12/12;
- factor-4 grid phase: 16/16 remain 12/12;
- factor-8 grid phase: mean accuracy 96.7%, 46/64 phase offsets 12/12;
- independent spatial-value shuffle preserves each episode's gas-value distribution but collapses mean accuracy to approximately 49–50%, with 0/100 perfect runs at factors 2/4/8.

These results justify the 300-s replay; they do not authorize closed loop.
