# Loop 12 — Transport-Regime Sparse MoE Auxiliary: NO-GO

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: auxiliary candidate screened and rejected in current form.

## Remote-domain motivation

Recent top-conference work makes sparse conditional routing an attractive lightweight mechanism:

- NeurIPS 2025 — *RoME: Domain-Robust Mixture-of-Experts for MILP Solution Prediction across Domains*.
- NeurIPS 2025 — *Principled Model Routing for Unknown Mixtures of Source Domains*.
- ICLR 2025 — *ReMoE: Fully Differentiable Mixture-of-Experts with ReLU Routing*.
- ICLR 2026 — *Routing Manifold Alignment Improves Generalization of Mixture-of-Experts LLMs*.

Project-specific motivation:
the prior PMFS M2 audit explicitly found that uniform Monte-Carlo member marginalization was not a transport-regime model and could let one random member dominate. A principled regime router therefore looked like a plausible auxiliary for the predictive M1.

## Offline test

Data:
H01/H02/H03 × {SA,SB} × {fast,slow} controlled histories.

Setup:
- two source-blind linear predictive experts per House, specialized to fast and slow transport;
- train on 60–175 s;
- held-time test on 180–235 s;
- compare:
  1. correct regime routing;
  2. uniform averaging of experts;
  3. deliberately wrong routing.

Metrics:
- held next-window predictive MSE;
- held-wind source identity of the predicted representation;
- same-source wind distance / cross-source distance.

## Results

### H01
- routed MSE 0.006102; uniform 0.006108; wrong 0.006116.
- all source identity only 1/2.
- routed is not meaningfully superior to uniform.

### H02
- routed MSE 0.03895; uniform 0.03660; wrong 0.03746.
- all source identity 1/2.
- uniform averaging is better than the nominally correct router.

### H03
- routed MSE 0.07914; uniform 0.06344; wrong 0.06681.
- routed source identity 1/2; uniform reaches 2/2.
- uniform averaging clearly beats the correct-regime proxy.

## Decision

The required mechanism gate fails:

```
CORRECT_ROUTING > UNIFORM = FALSE
WRONG_ROUTING_DESTRUCTIVE_CONTROL = INSUFFICIENT
REGIME_MOE_AS_M2 = NO_GO
```

The historical statement “uniform random-member marginalization is not a transport-regime model” remains true, but it does not imply that a learned regime router will improve source inference.

Do not add MoE routing to the current architecture.

## Current M2 search status

Rejected/demoted:
- η rare-event weighting;
- generic multiscale history;
- handcrafted event features;
- censoring/first-passage as a new module;
- direct nuisance projection/alignment;
- transport-regime MoE.

State-first intermediate physical representation remains unqualified because the frozen current asset does not contain an appropriate intermediate-field supervision target.

Next search moves to spatial evidence memory / state representation only if it can demonstrate an offline source-identity mechanism beyond an ordinary PMFS map.
