# Loop 6 — Temporal-Order Destructive Control for Predictive M1

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: internal offline premise test only.

## Purpose

Distinguish the current predictive-latent M1 from:
- static amplitude summarization;
- generic smoothing;
- a multiscale feature bank with no predictive semantics.

A valid predictive-representation mechanism should depend on the correct temporal relation between context and future target.

## Frozen proxy

Data:
- existing 12 controlled histories:
  H01/H02/H03 × {SA,SB} × {fast,slow}.

Representation:
- 5 s windows;
- current-window input features:
  log-gas mean/std/hit fraction/trend + local wind u/v/speed + mean pose x/y;
- target:
  next-window log-gas mean/std/hit fraction/trend;
- ridge predictor trained only on fast-wind histories of SA/SB in each House;
- held-wind identity evaluated on slow wind.

Destructive control:
- preserve exactly the same current windows and target-window value set;
- reverse the target-window order during training;
- therefore amplitude/statistics remain available but the correct predictive temporal pairing is destroyed.

No PMFS output, source truth or localization error is used to fit the representation.

## Results at 240 s

### H01
Ordered predictive:
- held-wind source identity = 2/2
- wind/source distance ratio = 0.346

Target-order reversed:
- identity = 1/2
- ratio = 6.770

### H02
Ordered predictive:
- identity = 2/2
- ratio = 0.134

Target-order reversed:
- identity = 1/2
- ratio = 1.963

### H03
Ordered predictive:
- identity = 2/2
- ratio = 0.172

Target-order reversed:
- identity = 1/2
- ratio = 2.142

## Interpretation

The same source-blind linear predictor has a 3/3 House mechanism result:

> correct context→future temporal pairing preserves held-wind source identity; destroying only that pairing collapses the source-discriminative predictive representation.

This is substantially stronger evidence for the predictive-latent M1 than the earlier smoothing proxy.

It also gives a mandatory future destructive control for any JEPA-class implementation:
- target-time permutation / target-segment reversal must remove the claimed advantage.

## Important M2 correction

A naive concatenation of fixed η-tail features with the predictive proxy is **not** uniformly valid.

- H01/H02 tail features can rescue rare/sparse-source evidence.
- H03 naive predictive+tail concatenation can worsen held-wind identity.

This does **not** invalidate η-learning as an auxiliary idea, because the Nature Communications 2026 method is a statistical regularization principle, not “append tail statistics to the decoder input”.

Revised M2 semantics:

> use extreme-event observables as a training constraint/regularizer so the predictive encoder does not erase intermittent tails; do not expose a hard tail-feature branch to the final source head unless separately qualified.

Mandatory M2 ablation:
1. M1 only;
2. M1 + η-statistical regularization;
3. M1 + naive tail concatenation negative control.

M2 passes only if (2) improves rare-event/source retention without the H03 degradation of (3).

## Decision after Loop 6

Predictive latent representation receives a positive mechanism upgrade.

Current rank:
1. Predictive latent physical representation — PRIMARY SURVIVOR.
2. Stochastic multiscale modeling — SECONDARY SURVIVOR.

Reason:
- stochastic multiscale modeling has strong physical provenance, but the current project evidence does not yet show a unique incremental source-identification object beyond scale decomposition + intermittency.
- predictive M1 now has a direct destructive temporal-order control that passes 3/3 Houses.

No closed-loop run is authorized.
Next step: search for a second recent top-venue scientific paradigm that could challenge or strengthen M1, and tighten the M2/M3 literature collision screen.
