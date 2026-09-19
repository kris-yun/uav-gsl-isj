# Remote-Paradigm Candidate Loop — 2026-09-19

Status: INTERNAL SCREENING ONLY. No paper-level claim authorized.

## Hard acceptance standard

A final 1+2 design must satisfy all of the following:

1. M1 is a paradigm-level idea from a 2025/2026 top venue or comparably strong journal, capable of supporting the paper's main scientific narrative.
2. M2 and M3 are independent auxiliary ideas from recent remote domains, each solving a distinct failure of M1 rather than decorating it.
3. None of the three may reduce to planner/OED, generic loss engineering, an attention block, a GNN/PINN wrapper, or an already-colliding GSL method.
4. The combined method must preserve a source-location probability map.
5. Existing project evidence must provide at least one falsifiable offline discriminator before new closed-loop runs.
6. Lightweight implementation is required but is not counted as an innovation.
7. The design must remain definable across VGR/GADEN, a public DNS/plume dataset, and real wind-tunnel data.

## Candidate families screened

### C1 — Inverse Generative Modeling
Main idea: treat source localization as inverse generation under latent transport rather than direct source classification.

2025/2026 remote-domain anchors:
- ICML 2025: Wang, Dauwels, Du, *Compositional Scene Understanding through Inverse Generative Modeling*.
- ICML 2025: Zhang & Zhou, *Inverse Flow and Consistency Models*.
- ICML 2025 Spotlight: Feng et al., *On the Guidance of Flow Matching*.
- NeurIPS 2025: Yao et al., *Guided Diffusion Sampling on Function Spaces with Applications to PDEs*.
- Nature Communications 2026: Wang et al., *FunDiff: diffusion models over function spaces for physics-informed generative modeling*.
- Communications Physics 2026: diffusion regularization for inverse PDE problems.

Why it survives:
- paradigm-level thesis is clear: infer the hidden generative factors that explain observations, instead of training a direct source classifier.
- naturally outputs a posterior / sample distribution over source location.
- matches the project fact that exact candidate-specific forward responses can preserve source identity while approximate transport models can destroy it.
- can be implemented in latent/function space and with flow/consistency models for light inference.

Primary risk:
- novelty collapses if implemented as a generic diffusion posterior sampler with no GSL-specific latent structure.

Status: STRONG SURVIVOR.

### C2 — Physical World Models
2025 anchors include NeurIPS DALI contextual world models, persistent embodied world models, structured world models, ICLR SGF.

Why demoted:
- source localization target is a static hidden cause/probability map, not primarily action-conditioned long-horizon planning.
- adds rollout/policy machinery that is not needed for the inference claim.
- high risk of sliding into RL/agent framing, explicitly outside the desired main line.

Status: DEMOTED AS M1; possible representation inspiration only.

### C3 — Physics-informed Self-Supervised Representation
2025 anchors include ICLR self-supervised world/physical representations and ICLR EulerFlow-style self-supervised continuous fields.

Why demoted:
- powerful training strategy but weak paper-level scientific thesis by itself.
- likely reduces to pretraining + source head.
- 2026 GSL already contains unsupervised diffusion-state classification, increasing collision risk.

Status: AUXILIARY/TRAINING STRATEGY ONLY.

### C4 — State-first / Intermediate-physical-state Inference
Remote-domain anchors:
- Nature Machine Intelligence 2026: Li et al., *Current-diffusion model for metasurface structure discoveries with spatial-frequency dynamics*.
- Nature Machine Intelligence 2026 News & Views: *Learning intermediate physical states for inverse metasurface design*.
- Nature Machine Intelligence 2025: differentiable reconstruction of high-dimensional physical fields from sparse sensors.

Scientific principle:
- do not invert sparse observations directly to the final design/parameter; reconstruct a physically meaningful intermediate state that bridges measurement and hidden cause.

Project evidence:
- exact candidate-specific transport+sensor response gives clean source identity in the controlled microbank.
- deployable local-wind approximation creates physically wrong continuous exposure and destroys source evidence.
- native timing can carry information that coarse HIT compression destroys.

Counter-evidence:
- a handcrafted compact exposure-state signature improved transport/source separation in H01/H03 but worsened the wind/source ratio in H02.
- therefore “any intermediate state is better” is false; the state must be physically sufficient.

Status: STRONG AUXILIARY CANDIDATE, NOT M1.

### C5 — Causal/Invariance Factorization
Remote anchor:
- ICLR 2025: *Unifying Causal Representation Learning with the Invariance Principle*.
- ICLR 2025: *Identifiable Exchangeable Mechanisms for Causal Structure and Representation Learning*.

Project evidence against using it as M1:
- historical causal localization line failed to identify source uniquely.
- cross-House candidate-dependent transport bias survives simple centering/variance pooling.
- early source/transport interaction can be as large as the source main effect.

Current-runtime factorial proxy from existing controlled histories:
- H01 source/interaction RMS ratio at 180 s ≈ 2.76.
- H02 ≈ 6.85.
- H03 ≈ 2.67.
- at early horizons H02/H03 can collapse toward ratio ≈ 1 or zero source effect.

Status: REJECT AS M1. Retain only as a possible regularizer if a future generative model needs mechanism separation.

### C6 — Test-Time Adaptation
2025 anchors:
- NeurIPS 2025 SNAP (sparse low-latency TTA).
- NeurIPS 2025 ReservoirTTA.
- NeurIPS 2025 risk monitoring for TTA.

Why not M1:
- deployment adaptation is secondary to the source-inference mechanism.
- unlabeled adaptation can corrupt the source model under intermittent plume shifts.

Status: OPTIONAL DEPLOYMENT STRATEGY, NOT INNOVATION CORE.

### C7 — Shift-aware Conformal / Testable Uncertainty
2025 anchors:
- ICLR 2025 *Wasserstein-Regularized Conformal Prediction under General Distribution Shift*.
- ICLR 2025 *Error-quantified Conformal Inference for Time Series*.
- ICLR 2025 *Learning Neural Networks with Distribution Shift: Efficiently Certifiable Guarantees*.
- NeurIPS 2025 conformal time series with change points.

Project evidence:
- H02/H03 examples show entropy collapse can coexist with wrong localization.
- source-map sharpness therefore cannot be treated as reliability.
- public-dataset validation explicitly requires a principled response to simulator/house/tunnel shift.

Status: STRONG AUXILIARY CANDIDATE.

## Existing-data discrimination performed

### Factorial source-vs-transport audit
Using the 12 existing H01/H02/H03 × {SA,SB} × {fast,slow} measured histories:

- raw continuous responses show source-vs-transport separability is strongly horizon dependent.
- H02 has essentially no source main effect at 60 s and only source≈interaction at 120 s, then becomes strongly source-dominant by 180 s.
- H03 is close to source≈interaction at 60–120 s and only separates later.
- binary HIT representation can remove all early source signal entirely.

Consequence:
- a direct discriminative source classifier is not authorized as the conceptual core.
- preserving continuous generative/temporal structure is necessary.
- a mechanism-separation auxiliary must not assume early invariance.

### Representation proxy audit
Compared raw/log/block/HIT and a compact exposure-state signature across paired winds.

- raw/log traces retain cross-wind source identity in the controlled 2-source set.
- coarse binary HIT can lose source identity or all early signal.
- intermediate exposure summaries can reduce wind/source ratio in H01/H03 but are not uniformly superior in H02.

Consequence:
- state-first is viable only if the intermediate state is learned/physics-grounded, not a handcrafted statistic.

## Current leading 1+2 architecture under SECOND SCREEN

### M1 — Compositional Inverse Generative Modeling
Scientific thesis:
> Explain sparse gas/wind histories by inferring the hidden source and transport factors that could have generated them, rather than mapping observations directly to source labels.

Candidate implementation family:
- latent conditional flow / inverse flow / consistency model;
- transport latent marginalized to obtain the source-location probability map.

### M2 — Physically Meaningful Intermediate-State Reconstruction
Remote inspiration:
- 2025/2026 Nature Machine Intelligence state-first inverse design / sparse field reconstruction.

Role:
- reconstruct a compact transport-response state (not necessarily the full 3-D plume) that preserves arrival/support/intensity structure before source inversion.

Hard condition:
- must outperform direct raw-history inversion on held transport while surviving destructive temporal/coarsening controls.

### M3 — Shift-aware Calibrated Source Region
Remote inspiration:
- 2025 ICLR shift-aware conformal/time-series UQ.

Role:
- prevent false sharpness under new House/simulator/real-tunnel shift;
- accompany the PMFS-style probability map with a calibrated source region / abstention state.

## Lightweight requirement

Not counted as a contribution:
- latent-space flow rather than full 3-D diffusion;
- consistency/few-step inversion where possible;
- one shared backbone;
- M2 as a compact latent field head;
- M3 as post-hoc calibration;
- optional sparse test-time normalization only after offline qualification.

## Public-dataset target ladder

1. VGR/GADEN: cross-house / cross-wind simulation.
2. DNS turbulent plume dataset (e.g. TURB-Smoke-type public data): simulator-mechanism shift.
3. real wind-tunnel gas+wind dataset / challenge: simulator-to-real robustness.

## Provisional scorecard (10 = strongest)

| Candidate M1 | Paradigm strength | 25/26 provenance | Project-mechanism fit | Novelty room in GSL | Lightweight fit | Public-data fit | Total /60 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Inverse Generative Modeling | 10 | 10 | 9 | 8 | 8 | 10 | 55 |
| Physical World Models | 9 | 10 | 6 | 8 | 5 | 8 | 46 |
| Self-Supervised Physical Representation | 7 | 9 | 7 | 6 | 9 | 9 | 47 |
| State-first Inverse Inference | 8 | 10 | 9 | 8 | 7 | 9 | 51 |
| Causal/Invariance Factorization | 9 | 10 | 5 | 4 | 8 | 8 | 44 |
| Test-Time Adaptation | 7 | 10 | 6 | 7 | 9 | 9 | 48 |

M1 selection threshold: >=52 and no hard collision.
Current M1 survivor: Inverse Generative Modeling only.

## Next loop before promotion

1. Novelty collision screen specifically for generative/flow/diffusion GSL through 2026.
2. Verify whether M2 can be defined on all three public-data levels without requiring privileged full fields.
3. Test a minimal factorized generative proxy on existing factorial histories; reject if transport latent does not improve held-condition likelihood/ranking.
4. Compare M3 candidates: shift-aware conformal vs risk-monitored TTA; keep only the lighter and more defensible one.
5. Require at least three independent top-venue/peer-reviewed literature lineages supporting the M1 scientific pattern, and at least two independent project evidence families supporting its necessity.
