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


## Literature triangulation update

### M1 now has three independent 2025/2026 lineages

1. **Olfactory neuroscience**
   - Trends in Cognitive Sciences 2025: *Predictive Coding in the Human Olfactory System*.
   - Proposes olfactory perception as predictive rather than purely reactive, including prediction errors and a predictive-map hypothesis.
   - This is directly relevant to chemical sensing but does not address robotic gas-source localization.

2. **General neuroscience / predictive processing**
   - Annual Review of Neuroscience 2026: *Rethinking Predictive Processing*.
   - Nature Reviews Neuroscience 2025: predictive cerebellar computation.
   - ICLR 2026: *Bidirectional Predictive Coding*.
   - These establish predictive coding as an active computational paradigm rather than a one-off JEPA architecture.

3. **Scientific machine learning**
   - ICLR 2026: *Representation Learning for Spatiotemporal Physical Systems*.
   - Predictive latent JEPA representations are explicitly tested by their ability to recover governing physical parameters and outperform reconstruction objectives across multiple physical systems.
   - AAAI 2026: *Koopman Invariants as Drivers of Emergent Time-Series Clustering in Joint-Embedding Predictive Architectures* gives a dynamical-systems explanation for why JEPA objectives can recover invariant regime structure.

Direct collision search for robotic GSL/OSL found no predictive-coding or JEPA-based source-localization method through the current 2026 search. Existing 2026 OSL diffusion-state classification is unsupervised manifold clustering rather than predictive latent source inference.

### M2 provenance strengthened

In addition to ICLR 2025 NeurPIR:
- NeurIPS 2025: *Generalized and Invariant Single-Neuron In-Vivo Activity Representation Learning*.
- Its explicit target is a stable functional identity from dynamic activity despite changes in animal, stimulus, experimental design and recording platform.
- This independently strengthens the transfer: stable source identity should be distilled from plume dynamics despite wind/simulator/sensor context.

### M3 collision status

Search found no use of Testable Learning with Distribution Shift (TDS) in gas/odor source localization.
However, heuristic uncertainty/entropy abstention already appears in a 2025 GSL Mamba paper, so M3 cannot be described merely as abstention.
The scientific transfer must remain the stronger TDS principle:
- use unlabeled target data to test whether the predictor/source evidence is valid under shift;
- reject when that validity cannot be certified/qualified.

A naive global mean-shift proxy was already falsified as sufficient; task-localized discrepancy is required.


## 13. M3 revision after practical screening

TDS remains an important theory baseline, but the primary M3 candidate is revised to **Sequential Risk Monitoring of Predictive Evidence**.

Recent top-venue / strong-conference provenance:
- NeurIPS 2025: *Monitoring Risks in Test-Time Adaptation* — sequential testing with confidence sequences to raise alarms when deployed predictive performance becomes unsafe under shift.
- UAI 2025: *On Continuous Monitoring of Risk Violations under Unknown Shift* — testing-by-betting risk monitoring under evolving shifts with false-alarm control.
- 2026 follow-up: prediction-powered risk monitoring extends the same line toward limited-label deployment.

Why this is a better fit than generic conformal/TDS:
- M1 already produces an online self-supervised prediction error when the next gas/wind observation arrives.
- therefore validity monitoring can use the model's own predictive-evidence loss stream, without source truth at deployment.
- this is lightweight and genuinely sequential.

Offline boundary:
- H01 held-slow next-window prediction MSE is not larger than fast-wind MSE even though the generic predictive representation can lose source identity.
- H02 held-slow prediction MSE rises (~1.18x), while source identity remains usable.
Thus prediction-error monitoring alone cannot guarantee source identity.

Consequence:
- M2 is responsible for preserving source identity.
- M3 is responsible only for detecting degradation of the predictive evidence model itself.
- final M3 must monitor a source-evidence-aware risk statistic, not raw prediction MSE alone.

Current preferred 1+2:
- M1 Predictive Coding / predictive latent physical representation.
- M2 Intrinsic source identity from dynamics.
- M3 Sequential risk monitoring of source-evidence validity.

TDS and conformal calibration are retained as comparators, not preferred auxiliary innovations.


## 14. M2 destructive pairing proxy

A nonparametric pairing test was run on existing 5 s window features.

Train window: 120–180 s.
Test window: 180–240 s.

Three source prototypes were compared:
- fast-only prototype;
- correct paired prototype using the same source across fast+slow wind;
- destructive wrong-paired prototype that swaps the slow-wind source identity.

Results:
- H01: fast-only 0.833, correct-paired 0.833, wrong-paired 0.167.
- H02: 0.500, 0.500, 0.500.
- H03: fast-only 0.688, correct-paired 0.688, wrong-paired 0.354.

Interpretation:
- correct source-context pairing is semantically load-bearing in H01/H03 because wrong pairing catastrophically degrades identity.
- however, correct pairing gives no incremental gain over fast-only prototypes.
- H02 remains non-discriminative under this crude late-window prototype.

Decision:
- M2 has mechanism support but no demonstrated incremental benefit yet.
- M2 remains CANDIDATE, not validated auxiliary innovation.
- next comparison must include a stronger paired-dynamics objective and at least one alternative M2 paradigm.
