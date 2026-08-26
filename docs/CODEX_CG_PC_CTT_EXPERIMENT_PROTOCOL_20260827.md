# CODEX EXECUTION PROTOCOL — CG-PC-CTT V1
Date: 2026-08-27
Branch: `research/cg-pc-ctt-gate-v1`

## Scientific status

This branch is a **candidate main-innovation experiment**, not a frozen claim.

**CONFIRMED**
- M1 wind-conditioned transport field is GO on House03.
- Source observability is strongly time-varying.
- Raw singular-ratio/full-rank gating alone is insufficient.
- Historical H02 simple transport scoring failed badly and is the mandatory hard challenge.
- Rejected evidence must not sharpen the source posterior.

**REJECTED**
- RMFE macro ranking.
- SCTT downstream module.
- naive matched-context mean subtraction as deployable M2.
- simple H02 transport gate/penalty.
- contrast-direction cosine stability as second gate.
- gamma-only/full-rank-only gate as complete solution.

**CURRENTLY TESTING**
- transport-uncertainty-whitened completeness gate.
- minimal proximal causal bridge.

**HOLD**
- transition-dynamics M3.
- broad 300 s closed-loop qualification.

## Hypothesis
A source is safe to update only when the weakest source-contrast direction is both (1) sufficiently conditioned relative to the strongest source direction and (2) sufficiently strong in absolute units relative to unresolved transport-member uncertainty.

This is a project-specific operationalization motivated by completeness / weak-identification ideas. Do not claim that the singular-value rule itself is a causal-identification theorem.

## Binding gate
At decision context `t`, M1 provides `phi[s,m,t] in R^d` for source candidate `s` and transport member `m`.

`mu[s,t] = mean_m phi[s,m,t]`

`B[s,t] = mu[s,t] - mean_j mu[j,t]`

`e[s,m,t] = phi[s,m,t] - mu[s,t]`

Do **not** invert a high-dimensional covariance with only a few transport members. Let `Q_t` span the source-contrast subspace from the right singular vectors of `B_t`, dimension `r <= S-1`. Project `B_low=BQ`, `E_low=EQ`. Estimate pooled transport covariance `C_tr=cov(E_low)+lambda I`, then whiten `B_white=B_low C_tr^(-1/2)`.

Let `sigma_1 >= ... >= sigma_r` be singular values of `B_white`.

Primary statistics:
- `gamma = sigma_r / sigma_1` — relative conditioning.
- `alpha = sigma_r` — absolute weakest source strength after transport-uncertainty normalization.
- `beta = min_{i<j} ||B_white[i]-B_white[j]||` — diagnostic only in V1.

PASS requires target numerical rank, `gamma >= gamma_min`, and `alpha >= alpha_min`. `beta` must not be added to the primary gate after looking at held-out results.

On FAIL: `q_t(s)=q_{t-1}(s)` exactly. No low-weight update, no entropy sharpening, no planner side effect from rejected source evidence.

## Anti-overfitting threshold policy
Historical raw source-contrast qualification used `gamma=0.05`. Because the new gate is whitened, treat 0.05 only as the first reference screen, not as mathematically identical to the old raw threshold. On **development only**, report sensitivity at `{0.02,0.05,0.10}` and freeze one value before held-out evaluation.

`alpha_min` has no historical frozen value. Select it only on development contexts using `calibrate_gate.py`, with default minimum development coverage `0.20`, then write the chosen value into an immutable run manifest before reading held-out H02/final results. Never retune after test visibility.

## Required M1 data product
Create NPZ:
- `phi[N_context,N_candidate,N_transport_member,D]`
- `context[N_context]`
- `split[N_context]` with `dev` / `test`
- `house[N_context]`
- `margin[N_context]` where available, defined only for evaluation as `true_source_score-max_false_source_score`.

Source truth may be used to compute evaluation margin but must never enter `phi`, gate inputs, R, Z, or runtime features. Record candidate list, transport member IDs, wind/context construction, feature normalization, commit SHA, and input SHA-256.

## Phase A — sanity
```bash
git checkout research/cg-pc-ctt-gate-v1
cd experiments/cg_pc_ctt
python3 selftest.py
```
Required: `SELFTEST PASS`. If it fails, stop.

## Phase B — House03 M1 completeness screen
Use the existing House03 M1 bank: 206 source candidates × 8 transport members × 10 source-update contexts. Do not redesign M1 physics.

Preserve the prior held-out structure: training/development transport members vs held-out members 6–7, and the two existing held-out wind contexts.

For every context record raw source spectrum plus whitened `gamma,alpha,beta`, gate PASS/FAIL, true score, nearest/hardest false score, margin, and true rank.

Primary checks:
1. accepted contexts have higher true-vs-hard-negative margin than rejected contexts;
2. positive-margin rate is higher in accepted contexts;
3. gate is not trivially all-pass/all-fail;
4. result persists with held-out transport members.

Use bootstrap at context/route-cluster level, not individual feature-row level.

## Phase C — mandatory H02 hard challenge
Historical H02 evidence: 28/28 `true_score-wrong_score < 0`, mean about `-34.22`, true rank median about `118.5/201`, wrong rank median about `5/201`.

For all 28 cases:
1. reconstruct candidate × transport-member `phi` from the frozen M1 family where possible;
2. compute `gamma,alpha,beta`;
3. record PASS/FAIL before inspecting score outcome;
4. for FAIL, verify exact posterior no-update and no entropy sharpening;
5. for PASS, evaluate `true_source_score-max_false_source_score`.

Gate GO does **not** require the gate itself to make a negative score positive. Its job is safe abstention/identifiability.

Provisional Gate GO requires all:
- substantial rejection of catastrophic negative-margin contexts;
- accepted H02 contexts have a better margin distribution than rejected contexts;
- accepted contexts do not retain a catastrophic tail comparable to historical un-gated failure;
- held-out transport-member result persists.

If it succeeds only by accepting almost nothing, verdict is `DEGENERATE_ABSTENTION`, not GO.

## Phase D — minimal Proximal Causal Bridge M2
Run only after a non-degenerate gate result.

Hidden nuisance `U_t`: unresolved plume/transport realization.
Observed outcome `Y_t`: deployable gas encounter response.
Candidate intervention: `S=s`.

Source-side proxy `Z_t(s)` may use only candidate-dependent M1 physical predictions: arrival hazard, travel time/path statistic, source-relative wind alignment, predicted phase/support.

Outcome/transport-side proxy `R_t` may use only source-independent onboard history: recent local wind sequence/variability, pose/yaw/velocity/action history, gas encounter history, sensor transient state. **Every candidate must receive identical R_t.**

Forbidden runtime inputs: source truth, wind ID, route ID, plume seed, simulator phase, future data, oracle fields.

Start with the provided regularized linear/interacting bridge `h_theta(R,Z(s))`. Do not jump to a transformer merely to rescue failure.

Evaluate conditional moment residual plus the hard-negative endpoint. For every gated PASS context compare M1 versus M1+bridge using `true_source_score-max_false_source_score` as primary endpoint, true source rank/top-k as secondary.

M2 GO only if held-out hard-negative margin improves, the effect survives negative controls, no route/world/source leakage exists, and H02 PASS cases move materially toward or through zero. If H02 remains strongly negative, M2 is NO-GO.

## Mandatory negative controls
Run with identical evaluation code:
1. candidate-source permutation of `Z(s)`;
2. time reversal of sequential proxy features;
3. source-query/proxy shuffle;
4. R leakage audit: hash/serialize R and prove it is identical across candidates at one decision context;
5. forbidden-feature audit for source truth, wind ID, route ID, plume seed, simulator phase, future timestamps;
6. ABSTAIN invariant: on every gate FAIL, `max_abs(q_after-q_before)==0` apart from explicitly declared normalization-only machine tolerance.

If the bridge also improves under candidate permutation/shuffle, mark invalid.

## Phase E — closed loop only after offline GO
Do not start mass 300 s experiments before B/C/D pass.

First run one historically failed House03 scene OFF/ON. Then freeze code, formula, thresholds, cadence and stopping rule. Only after that run unseen H01/H02 seeds.

Reuse the V11 fixed-prior reversible cumulative posterior as the outer update. Do not create a second sequential Bayes mechanism in this branch.

## Required outputs
Create `results/cg_pc_ctt/<RUN_ID>/` containing:
- `RUN_MANIFEST.json`
- `gate_metrics.csv`
- `gate_summary.json`
- `h02_hard_challenge.csv`
- `bridge_metrics.csv`
- `negative_controls.csv`
- `forbidden_feature_audit.txt`
- `ABSTAIN_INVARIANT.txt`
- `VERDICT.md`

Manifest must contain commit SHA, all frozen thresholds, dataset/input SHA-256, exact commands, environment versions, split definitions, and `threshold_changed_after_test_visibility=false`.

## Verdict vocabulary
Use exactly one:
- `CG_PC_CTT_OFFLINE_GO`
- `GATE_GO_M2_NO_GO`
- `DEGENERATE_ABSTENTION`
- `NO_GO_IDENTIFIABILITY`
- `INVALID_PROTOCOL`

Do not promote this to the paper main innovation before non-degenerate Gate GO + M2 held-out improvement + negative controls + at least one closed-loop validation.

## What Codex may change
Allowed: adapters for existing M1 artifacts, deterministic data conversion, logging, unit tests, mathematically equivalent numerical ridge implementation.

Not allowed without a new protocol version: changing M1 physics, truth-derived runtime features, held-out threshold tuning, softening ABSTAIN, changing endpoint after seeing results, adding a large model to rescue failure, or launching broad closed-loop sweeps before offline gates pass.

## Immediate order
1. Pull branch.
2. Run self-test.
3. Write adapter from existing M1 bank to NPZ schema.
4. Freeze dev/test split.
5. Calibrate alpha on development only.
6. Freeze thresholds in manifest.
7. Evaluate held-out House03.
8. Evaluate 28 H02 historical hard cases with no retuning.
9. If Gate GO, run minimal bridge.
10. Run all negative controls.
11. Write `VERDICT.md`.
12. Only for `CG_PC_CTT_OFFLINE_GO`, prepare first 300 s OFF/ON.

Priority is falsification, not manufacturing a GO by threshold search.
