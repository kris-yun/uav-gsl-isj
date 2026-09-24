# D1C Precommit V1 — Fixed-Panel Proper-Score Confirmation

Date: 2026-09-25

Status: NUMERICAL PRINCIPLES FROZEN BEFORE D1R RESULTS / FINAL TARGETS

## Estimand

For fixed source s and fresh target realization r:

d_sr = log2[q_candidate(s|Y_sr) / q_identity(s|Y_sr)].

With equal J, Delta_B is the equal-source average of within-source mean d_sr.

All methods use the same 168-cell support, prior pi_s=1/168, target, observation input and reference bank.

## Minimum meaningful effects

Candidate vs identity:
delta_id = log2(1.15) ~= 0.2016 bits per whole target.

Candidate vs locked ordinary champion:
delta_ordinary = log2(1.05) ~= 0.0704 bits per whole target.

These are project-level minimum effect margins, not information-theory constants, and are not reduced after results.

## Primary CI

The target population is the fixed 168-source panel.

Keep every source in every bootstrap. Within each source, resample complete target-realization indices with replacement.

Do not resample 300 observation coordinates. Do not use source resampling as the primary fixed-panel CI. Do not mechanically double-bootstrap source and realization levels.

## Primary predictive PASS

Candidate vs identity:
- one-sided alpha = 0.025;
- lower confidence bound > delta_id.

Candidate vs ordinary champion:
- one-sided alpha = 0.025;
- lower confidence bound > delta_ordinary.

Both are required.

## Calibration guard

Frozen HPD coverage levels: {0.50, 0.80, 0.95}.

eta_cal = 0.05
eta_abs = 0.10

Require the conservative candidate-minus-identity maximum coverage-error upper bound <= 0.05 and the candidate absolute maximum coverage-error upper bound <= 0.10.

This is a coverage-profile guard, not a claim of complete multiclass calibration.

## Target count planning

J is chosen from {2,4,8,16}.

D1R may provide only variance/tail estimates from outer-OOF paired score differences. D1R mean gains are not used to reduce effect margins.

Frozen planning alternatives:
- identity comparison: Delta_plan = log2(1.30);
- ordinary comparison: Delta_plan_ordinary = log2(1.10).

Choose the smallest J with planned >=80% power for the identity margin test, ordinary margin test, and calibration guard.

If no J <=16 is adequate, state = D1C_NOT_POWERED_UNDER_FROZEN_BUDGET and do not generate a partial target set.

## Final-target firewall

Before target seeds are assigned, freeze/hash final partition, all models, likelihood family, hyperparameters, temperature, floor, prior, scoring/bootstrap/calibration code, J, target seed namespace and every PASS/STOP rule.

## D1C decision

PASS = D1C_PASS_FSEI_FRESH_TARGET.

STOP = D1C_FAIL_STOP_FSEI_MAINLINE.

No scientific HOLD after target reveal. Rank, MAP error, top-k and 0.5/1 m mass cannot rescue a failed primary result.