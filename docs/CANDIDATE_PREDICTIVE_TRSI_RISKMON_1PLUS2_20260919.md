# Candidate 1+2 V2 — Predictive Coding + Transport-Redundant Information + Sequential Risk Monitoring

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: OFFLINE SCREENING / NO CLOSED LOOP

## M1 — Predictive Coding of Turbulent Plume Evidence

### Scientific mother idea

Predictive coding / predictive processing:
- Trends in Cognitive Sciences 2025: *Predictive Coding in the Human Olfactory System*.
- Annual Review of Neuroscience 2026: *Rethinking Predictive Processing*.
- ICLR 2026: *Rethinking JEPA: Compute-Efficient Video Self-Supervised Learning with Frozen Teachers* (SALT).
- ICML 2025 / ICLR 2025 JEPA-family predictive representation work provides current ML implementation lineage.
- Physical-system evidence: Qu et al. 2026 show latent predictive representations can preserve governing physical parameters better than pixel reconstruction; note carefully that this paper is an ICLR 2026 AI&PDE workshop paper, not a main-track provenance anchor.

### Main scientific thesis

Turbulent plume observations should not be treated primarily as raw concentration patterns to classify or fields to reconstruct exactly.

Instead:
> source evidence should be extracted from the latent structure of gas/wind/pose history that remains predictive through time, while unpredictable plume realization details are treated as innovations rather than source identity.

This is a computational transfer of predictive coding to robotic olfaction, not a claim that biological olfaction proves the robotic algorithm.

### Existing-data premise

Across H01/H02/H03 controlled source×wind histories, source-blind predictable/innovation decompositions repeatedly show that, after physical support appears, predictable components are more source-dominant than innovations.

A stronger linear next-window predictor improves wind/source separation in H02 and H03, but H01 is a counterexample where generic prediction can suppress source identity.

Therefore:
- predictive coding is supported as M1;
- generic predictive compression alone is falsified;
- an explicit source-preserving auxiliary is required.

### Novelty boundary

Direct 2026 GSL collision:
- *Deep Probabilistic Indoor Gas Source Localization via Physical Dependency-Guided Sequential Inference* (arXiv 2608.16221, submitted to T-RO) sequentially infers wind/concentration fields before source posterior estimation.

Our M1 must remain distinct:
- no privileged full-field reconstruction at deployment;
- no staged wind-field -> concentration-field -> source posterior pipeline;
- self-supervised latent prediction from sparse trajectory observations;
- source posterior is read from predictive latent evidence.

## M2 — Transport-Redundant Source Information (TRSI)

### Remote mother idea

Common / redundant information decomposition:
- NeurIPS 2025: *Partial Information Decomposition via Normalizing Flows in Latent Gaussian Distributions*.
- ICLR 2026: *Lossy Common Information in a Learnable Gray-Wyner Network*.
- ICLR 2026: *Coupled Transformer Autoencoder for Disentangling Multi-Region Neural Latent Dynamics*.
- Nature Neuroscience 2026: shared latent structure across contexts.
- Nature 2025: shared vs unique neural dynamical subspaces.

### Scientific transfer

For the same source observed under different transport contexts:
- information redundantly available across wind/transport views is candidate source identity;
- information unique to one context is transport-private;
- synergistic information is measured rather than assumed useful.

This is not generic domain invariance. Transport-private information is retained in a private latent channel.

Working factorization:
[
z_{s,w} = [z^{common}_{s}, z^{private}_{s,w}]
]

Source probability update consumes the common/source channel; the private channel remains available to M1 prediction and M3 validity monitoring.

### Existing-data premise

Paired fast/slow 5 s window features, train 120–180 s / test 180–240 s.

H01:
- train source separation common 0.121 vs unique 0.052;
- test source separation 0.230 vs 0.010;
- common source classification 0.833 vs unique 0.458.

H02:
- train 0.464 vs 0.014;
- test 0.166 vs 0.032;
- common classification remains 0.500 because physical support/late-window identifiability remains limiting.

H03:
- train 0.577 vs 0.073;
- test 0.232 vs 0.093;
- classification common and unique 0.667, but common source separation is substantially larger.

Conclusion:
source separation is consistently concentrated in the cross-transport common component, while unique transport components carry much less source separation.

This is a stronger premise than generic wind removal and stronger than the previous paired-prototype M2.

### Kill criteria

Kill M2 if:
- learned common-information latent does not outperform matched source-head baseline on held transport;
- source-label permutation / wrong pairing preserves the gain;
- common channel collapses to amplitude-only statistics;
- gains disappear on an independent dataset.

## M3 — Sequential Risk Monitoring of Source-Evidence Validity

### Remote mother idea

- NeurIPS 2025: *Monitoring Risks in Test-Time Adaptation*.
- UAI 2025: *On Continuous Monitoring of Risk Violations under Unknown Shift*.

Core transfer:
- deployment under unknown shift should continuously test whether predictive performance/risk remains within a predeclared acceptable regime;
- if not, raise an alarm / abstain instead of silently trusting the model.

### GSL role

M3 does not localize the source.
It monitors whether M1+M2 source evidence remains valid under House/simulator/real-sensor shift.

Possible observable streams:
- predictive-latent residual;
- private/common information drift;
- source-evidence margin stability;
- calibrated source-region coverage proxy where labels are available offline.

### Existing-data boundary

Simple global feature shift and raw next-window prediction MSE do not detect the H01 source-identity failure reliably.
Therefore M3 cannot be a generic OOD score.

The monitored risk must be localized to source-evidence validity.

### Kill criteria

Kill M3 if:
- its alarm statistic cannot separate reliable vs unreliable evidence regimes better than entropy/confidence;
- false alarms dominate valid held-environment cases;
- the method needs source truth online.

## Lightweight realization

Not an innovation:
- small temporal encoder;
- masked / future latent prediction;
- no full 3-D plume decoder;
- one shared backbone;
- M2 implemented as a low-dimensional common/private projection head or information-decomposition objective;
- M3 post-hoc sequential monitor;
- PMFS-compatible probability-map output.

## Public-data validation contract

1. VGR/GADEN cross-house/cross-wind.
2. Independent DNS turbulent plume data sampled along synthetic robot trajectories.
3. Real wind-tunnel trajectory data.

The method must not depend on deployment-time dense CFD fields.

## Current evidence score

M1 predictive-coding premise: STRONG, with an H01 counterexample that motivates M2.
M2 common-information premise: STRONGER THAN PREVIOUS M2, but not trained end-to-end yet.
M3 theory provenance: STRONG; source-evidence-aware risk statistic not yet validated.

Overall: PROMISING 1+2 CANDIDATE, NOT FINAL.
