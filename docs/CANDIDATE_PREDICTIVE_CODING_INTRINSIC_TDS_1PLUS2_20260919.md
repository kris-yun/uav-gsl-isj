# 1+2 Candidate — Predictive Coding + Intrinsic Dynamics + Testable Shift

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: SECONDARY SCREEN / NO CLOSED LOOP

## Main innovation M1 — Predictive Coding for Turbulent Source Evidence

### Mother idea

Predictive coding / predictive processing is a neuroscience-level theory of sensory representation: an internal model predicts sensory input and representations are organized around what is predictable versus prediction error.

Recent high-level support:
- Nature Reviews Neuroscience 2025: predictive computation in cerebellar circuits.
- Annual Review of Neuroscience 2026: Rethinking Predictive Processing.
- ICLR 2026: Bidirectional Predictive Coding.
- ICLR 2026: Representation Learning for Spatiotemporal Physical Systems — JEPA latent prediction is explicitly evaluated by recovery of governing physical parameters and outperforms reconstruction objectives on multiple physical systems.
- Nature Communications 2025: Predictive Coding Light — predictive coding as efficient unsupervised representation learning.

### GSL scientific translation

A turbulent plume contains:
- persistent source information;
- transport-conditioned predictable structure;
- stochastic/intermittent innovations.

The proposed source evidence is therefore derived from predictive latent structure, not from direct source classification, exact reconstruction of the realized plume, or coarse hit statistics.

Working scientific claim:

> Source identity is preferentially carried by the component of sparse plume history that remains predictively structured across transport contexts, while unpredictable innovations are more transport-contaminated.

### Existing-data evidence

Source-blind predictable/innovation proxy:
- H02 180 s: predictable wind/source ratio ~0.046–0.077 vs residual ~0.128–0.229.
- H03 180 s: predictable ~0.329–0.336 vs residual ~0.491–0.507.
- H01 240 s: predictable ~0.144–0.301 vs residual ~0.338–0.414.

Hard negative boundary:
- H02 60 s has no source signal; prediction cannot manufacture source information.

Stronger linear next-window predictive proxy:
- H02 180 s raw 0.293 -> predictive 0.157; 2/2 held-wind identity.
- H02 240 s raw 0.376 -> predictive 0.177; 2/2.
- H03 120 s 0.720 -> 0.592; 2/2.
- H03 240 s 0.601 -> 0.544; 2/2.
- H01 is a counterexample: generic prediction suppresses source contrast and held-wind identity can drop from 2/2 to 1/2.

Conclusion:
M1 has a positive physical premise but requires an explicit identity-preservation auxiliary. Generic prediction alone is rejected.

## Auxiliary innovation M2 — Intrinsic Source Identity from Dynamics

### Remote mother idea

ICLR 2025:
Neuron Platonic Intrinsic Representation From Dynamics Using Contrastive Learning.

That work treats the same dynamical system observed under different peripheral conditions as having a time-invariant intrinsic representation and learns that representation from multiple temporal segments.

### GSL transfer

- neuron/system identity -> source-location identity;
- peripheral condition -> wind / turbulence / route / sensor context;
- temporal activity segment -> gas/wind trajectory segment.

Role:
M2 prevents M1's predictive compression from discarding the persistent hidden cause we care about.

Constraint:
- alignment is activated only when physical support exists;
- no unconditional early invariance;
- wrong source pairing and source-label permutation are mandatory destructive controls.

M2 is justified by the H01 predictive-collapse counterexample.

## Auxiliary innovation M3 — Test-before-Trust under Distribution Shift

### Remote mother idea

COLT 2024 introduced Testable Learning with Distribution Shift (TDS).
ICLR 2025 extended it to neural-network regression with efficiently certifiable guarantees:
Learning Neural Networks with Distribution Shift: Efficiently Certifiable Guarantees.

Core principle:
> use unlabeled target-distribution samples to test whether a learned predictor can be trusted; otherwise reject instead of silently extrapolating.

### GSL transfer

The source map is returned as trusted only when target predictive-latent statistics pass a predeclared validation test; otherwise the system returns an unsupported/abstain state or broad fallback map.

Important limitation discovered offline:
- a simple global train-vs-test mean-shift statistic does not flag the H01 predictive-collapse case.
- H01/H02/H03 standardized fast-to-slow mean shifts are approximately 0.424 / 0.448 / 0.349.
- therefore M3 cannot replace M2 and cannot be a generic OOD-distance threshold.
- it must test task-localized predictive discrepancy / source-evidence validity, consistent with the localized-discrepancy direction in TDS theory.

This is a useful negative result: M2 and M3 solve different failures.

## Combined method

Sparse gas/wind/pose history
-> M1 predictive latent
-> M2 intrinsic source representation
-> source probability map.

M3 operates on target latent/evidence distribution:
- PASS -> trusted source probability map;
- REJECT -> unsupported / broad fallback map.

## Lightweight strategy

Not counted as contribution:
- small temporal encoder;
- latent prediction, no full plume decoder;
- one shared backbone;
- M2 small projection/VICReg-like head;
- M3 post-hoc localized discrepancy test;
- no agent/RL planner.

## Public-dataset requirement

The 1+2 method must remain definable from trajectory-level observations:
1. VGR/GADEN cross-house/cross-wind;
2. independent DNS turbulent plume data sampled along trajectories;
3. real wind-tunnel gas/wind trajectories.

No deployment-time full CFD field is required.

## Kill criteria

Kill M1 if a trained source-blind predictive latent model fails to beat reconstruction/direct-encoding baselines under held transport, or if time permutation leaves performance unchanged.

Kill M2 if correct same-source cross-transport pairing gives no gain over a matched predictor, or wrong pairing performs similarly.

Kill M3 if localized validation cannot separate reliable from unreliable target regimes better than ordinary entropy/confidence, or if it rejects most valid cases.

## Current evidence status

- M1 physical premise: POSITIVE BUT NOT COMPLETE.
- M2 necessity: POSITIVE (H01 generic-predictor counterexample).
- M3 principle: LITERATURE-STRONG; SIMPLE GLOBAL-SHIFT PROXY FAILED; localized test still required.
- final 1+2: NOT YET VALIDATED.
