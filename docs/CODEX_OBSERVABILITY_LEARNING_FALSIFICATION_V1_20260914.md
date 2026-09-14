# Codex continuation — observability-aware learning falsification

Date: 2026-09-14  
Branch: `codex/dual-uav-two-point-premise-20260913`

## Status boundary

This is the first learning falsification stage after the completed C0–C3 sensing-support diagnostic. The candidate is **not** a confirmed main innovation. The purpose is to test whether a deployable observation history can predict a counterfactual source-distinguishability state without source identity, route ID, posterior repair, or new simulation.

Do not relabel earlier causal/spatiotemporal representation, signed-increment, route-design, or sensor-lag work as this candidate.

## Frozen data and inputs

- use only the already committed `experiments/sensing_support_upper_bound_v1/endpoint_design_traces` and the frozen route files;
- sources: `S_truth`, `S_k01`, `S_k10`, `S_k22`;
- winds: `W_fast`, `W_slow` only;
- configuration: C2 ordered plus/minus processed channels;
- window: 5.0 s inclusive, 26 samples at 0.2 s cadence;
- examples begin at sample index 25 and use only the preceding 26 samples;
- no source ID, route ID, source coordinate, future sample, or aggregate score may enter the student input;
- student features are the history of ordered processed `(c_plus,c_minus)`, mean endpoint wind `(u,v,w)`, center `(x,y,z)`, and center velocity `(vx,vy,vz)`;
- target labels may use all four source interventions for the same route/wind/time window because they are training-only privileged counterfactual supervision;
- no new GADEN, no `W_altfast`, no new source intervention, and no held-wind response query.

## Frozen teacher label

For each `(route, wind, end_index)` window, form one row per source intervention:

```text
v_s = [c_plus_processed(window), c_minus_processed(window)]
Y = stack_s(v_s)                    # four source rows
R = (I - 11^T/4) Y
sigma = svd(R)
r = sigma_3 / sigma_1              # zero if sigma_1 is zero
M = R R^T
q = lambda_3(M) / lambda_1(M)       # zero if lambda_1 is zero; clamp negative round-off to zero
d = min_{i<j} ||v_i - v_j||_2
h = min_s 1[any(c_s > 0.1 ppm in window)]
z_obs* = [r, q, log1p(d), h]
```

The student is evaluated on all four targets, but the rich distinguishability score is the mean normalized error over `r`, `q`, and `log1p(d)`. The support bit `h` is reported separately and cannot by itself establish the candidate.

## Frozen split

- train: `W_fast`, routes `AO_00`–`AO_07`;
- development: `W_fast`, routes `AO_08`–`AO_11`;
- held condition: `W_slow`, routes `AO_08`–`AO_11`.

The held condition is evaluated only after labels, features, model family, alpha, metrics, and thresholds are frozen. The held data already exists in the committed C2 endpoint traces; no new response is read.

## Frozen models and controls

Use deterministic standardized Ridge regression with `alpha=1.0`, fit only on train examples:

1. constant train-mean predictor;
2. gas-only: ordered processed plus/minus history;
3. gas+wind: gas history plus endpoint wind history;
4. full: gas+wind+position+velocity history.

For the full model, evaluate these precommitted controls on development and held examples:

- reverse each temporal history (`time_reverse`);
- reverse wind history only (`wind_reverse`);
- zero position and velocity history (`motion_zero`);
- swap ordered plus/minus gas histories (`receiver_swap`).

No source or route identifier is included. Model coefficients and scalers are fit only on the training split.

## Frozen metrics and promotion gate

For each target report RMSE, normalized RMSE using the training target standard deviation, and Pearson correlation when defined. Report the rich score as the mean normalized RMSE over `r`, `q`, and `log1p(d)`.

The candidate can continue toward a main-innovation gate only if all conditions hold:

1. train rich-label standard deviation is non-zero for all three rich targets;
2. full model improves held rich score over the constant predictor by at least 20%;
3. full model improves held rich score over gas-only by at least 10%;
4. the same two improvements hold on development data;
5. on the held set, `time_reverse`, `wind_reverse`, and `motion_zero` each worsen rich score by at least 5% relative to the full model;
6. receiver swap is reported and does not improve the full model by more than 5%;
7. no split or label definition is changed after aggregate results are inspected.

If any condition fails, mark this candidate `OBSERVABILITY_AWARE_LEARNING_FALSIFICATION_NO_GO` and do not call it the main innovation. A later candidate requires a new written freeze; no rescue tuning is allowed in this stage.

## Required outputs

Under `experiments/observability_learning_falsification_v1/`:

- `LEARNING_POLICY_FREEZE.json`;
- `DATASET_INTEGRITY.json`;
- `LABEL_DISTRIBUTION.json`;
- `FALSIFICATION_RESULTS.json`;
- `FINAL_GATE.json`;
- `PRE_MODEL_SHA256SUMS`;
- `FINAL_SHA256SUMS`;

Also write `docs/OBSERVABILITY_LEARNING_FALSIFICATION_V1_RESULT_20260914.md`.

The main-innovation claim remains unauthorized unless this gate and a later independent confirmation stage both pass.
