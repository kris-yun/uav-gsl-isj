# R-IDeA GSL V1 — offline mechanism screen

Date: 2026-09-21
Status: **NO-GO AS MAIN INNOVATION / INCREMENTAL MECHANISM NOT ESTABLISHED**

## Remote idea

AISTATS 2026:
*Representative, Informative, and De-Amplifying: Requirements for Robust Bayesian Active Learning under Model Misspecification*.

Transferred GSL hypothesis:
a useful sensing location should not only separate source hypotheses; it should also avoid locations where nuisance/model variation is larger than the source effect.

## Proxy

Controlled 240-s VGR asset:
H01/H02/H03 × SA/SB × fast/slow.

At each common spatial cell, using per-episode z-normalized gas fields:

- informativeness = between-source separation;
- nuisance = mean same-source fast/slow discrepancy;
- de-amplifying weight = max(0, informativeness - nuisance).

Compare weighted cross-wind centered-cosine source identity for:
1. uniform spatial weight;
2. informativeness-only weight;
3. de-amplifying weight.

No endpoint truth was used to define the weights.

## Result

At 160 s:
- uniform valid coverage 5/12, accuracy 3/5;
- informativeness-only valid coverage 5/12, accuracy 5/5;
- de-amplifying valid coverage only 2/12, accuracy 2/2.

At 176 / 200 / 220 / 240 s:
- informativeness-only and de-amplifying both achieve 100% accuracy on valid cases;
- de-amplification sometimes raises mean margin, but does not consistently improve minimum margin;
- at 240 s:
  - uniform mean margin 0.776, min 0.009;
  - information-only mean margin 1.120, min 0.159;
  - de-amplifying mean margin 1.159, min 0.082.

## Interpretation

The strong effect is **source-discriminative spatial weighting**.

The specific R-IDeA transfer — subtracting nuisance/error-amplifying locations beyond informativeness — is not independently established:
- it does not improve discrete source identity over information-only weighting;
- it reduces early usable coverage;
- its 240-s worst-case margin is lower than information-only.

## Decision

Do not promote R-IDeA / error de-amplification as the new paper-level main innovation from this evidence.

The 2026 idea remains useful literature for future planner robustness, but the current data do not show it is load-bearing beyond ordinary source informativeness.
