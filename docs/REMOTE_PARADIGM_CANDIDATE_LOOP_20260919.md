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

## Loop-2 literature result: inverse-generative line collision

The initial leading M1, inverse generative modeling, has been downgraded after a stronger 2026 collision screen.

Direct/near-direct 2026 collisions:
- *NeuPlume: Probabilistic inversion of atmospheric point-source emissions from sparse observations* (EGUsphere 2026 preprint): diffusion posterior sampling over sparse plume observations jointly infers source/emission parameters, wind/turbulence parameters and the full concentration field, with a UAV methane field-transfer check.
- *Diffusion models for multivariate subsurface generation and efficient probabilistic inversion* (Computers & Geosciences 2026): diffusion posterior sampling for scientific inversion.
- *D-Flow SGLD: Source-space posterior sampling for scientific inverse problems with flow matching* (JCP 2026, forthcoming issue): flow-matching priors for source-space posterior sampling.

Decision:
- “use diffusion/flow posterior sampling to infer source under transport uncertainty” is no longer sufficiently collision-free to carry the paper.
- inverse generative models remain an implementation/comparator family, but not the preferred M1.

Status C1: DEMOTED FROM M1.

## New M1 family: Predictive Latent Physical Representation (JEPA-class)

### Remote-field top-venue anchors

- ICLR 2026: Qu et al., *Representation Learning for Spatiotemporal Physical Systems*.
  - evaluates general self-supervised objectives on active matter, shear flow and Rayleigh–Bénard systems.
  - latent-space JEPA prediction outperforms pixel-level reconstruction objectives for estimating governing physical parameters.
  - central lesson: for downstream scientific inference, learning physically relevant predictive latent structure can be superior to reconstructing every field detail.

- ICML 2025: Lei et al., *M3-JEPA: Multimodal Alignment via Multi-gate MoE based on the Joint-Embedding Predictive Architecture*.
  - latent predictive alignment, unseen-domain generalization, computational efficiency.

- CVPR 2025: Astruc et al., *AnySat: One Earth Observation Model for Many Resolutions, Scales, and Modalities*.
  - JEPA-based self-supervision across heterogeneous sensors/resolutions and external environmental datasets.

- ICLR 2025: D-JEPA demonstrates that JEPA is an active predictive architecture family rather than a single application.

- 2026 physical-dynamics supporting work includes JEPA state-space modeling and JEPA PDE control preprints; these are supporting context only, not primary provenance.

### Scientific translation to GSL

Turbulent plume samples contain:
1. a persistent hidden cause — source location;
2. transport-dependent but partly predictable structure;
3. high-frequency stochastic/intermittent details that are expensive or impossible to reconstruct exactly.

Main thesis:
> For turbulent GSL, the learning objective should not reconstruct the realized plume or directly classify the source. It should learn the latent structure that is predictive across time/space and therefore preserves governing source information while discarding unpredictable transport detail.

This is a different claim from world-model planning and from generative plume inversion.

### Existing-data proxy test

A conservative proxy separated each log-concentration trace into:
- a locally predictable component (causal moving-average proxy at several windows);
- an innovation/residual component.

Across the existing H01/H02/H03 × {SA,SB} × {fast,slow} controlled histories:

- after source support appears, the predictable component generally has a lower wind/source separation ratio than the innovation residual.
- H02 at 180 s:
  - predictable ratio approximately 0.046–0.077 depending on smoothing window;
  - residual ratio approximately 0.128–0.229.
- H03 at 180 s:
  - predictable ratio approximately 0.329–0.336;
  - residual ratio approximately 0.491–0.507.
- H01 at 240 s:
  - predictable ratio approximately 0.144–0.301;
  - residual ratio approximately 0.338–0.414.
- before physical support appears, neither component creates source information; H02 remains zero at 60 s and source≈wind at 120 s.

Interpretation:
- source signal is disproportionately represented in the temporally predictable part once it becomes physically observable.
- unpredictable innovations remain more transport-contaminated.
- crucially, predictive representation cannot manufacture information before support exists, matching the physical-support audits.

This is a positive premise for a JEPA-class M1, not a trained-model result.

Status C8: STRONG SURVIVOR / CURRENT M1 LEADER.

## Auxiliary candidate A: Intrinsic Dynamic Identity Representation

### Remote-field anchor
- ICLR 2025: Wu et al., *Neuron Platonic Intrinsic Representation From Dynamics Using Contrastive Learning*.
  - treats one neuron as a dynamical system observed in different peripheral conditions.
  - learns a time-invariant intrinsic representation from multiple activity segments.
  - same-system segments should be more similar than different-system segments and generalize to unseen animals.
- ICML 2024 Platonic Representation Hypothesis is the conceptual predecessor; 2025 work makes the dynamics/intrinsic-identity transfer concrete.

### GSL mapping
- one source location = one persistent system identity;
- wind/turbulence/route/sensor context = peripheral conditions;
- different plume histories from the same source should retain an intrinsic source representation after physically observable support exists.

Distinct role relative to M1:
- M1 learns what part of plume history is predictively meaningful.
- this auxiliary binds predictive histories from the same source across transport contexts into a persistent source identity while preserving transport-specific degrees of freedom.

Existing-data compatibility:
- paired current-runtime source×wind histories become much more source-dominant after support emerges;
- early source≈transport cases mean this module must not impose unconditional early invariance.
- therefore identity alignment must be support/reliability weighted rather than global.

Status: STRONG AUXILIARY CANDIDATE.

## Auxiliary candidate B: Shift-aware calibrated source regions

2025 anchors:
- ICLR 2025 *Wasserstein-Regularized Conformal Prediction under General Distribution Shift*.
- ICLR 2025 *Error-quantified Conformal Inference for Time Series*.
- ICLR 2025 *Learning Neural Networks with Distribution Shift: Efficiently Certifiable Guarantees*.
- NeurIPS 2025 conformal time series with change points.

Project necessity:
- existing PMFS/M1 histories include entropy collapse with incorrect localization;
- a sharp map is not a reliability guarantee;
- cross-house, DNS and simulator-to-real validation require explicit reliability under shift.

Distinct role:
- M1 produces a source-probability map from predictive latent evidence.
- M2 makes source identity persistent across transport contexts.
- M3 calibrates when that map can be trusted under unseen distribution shift and can output a larger source region / abstention state when it cannot.

Status: STRONG AUXILIARY CANDIDATE.

## Other candidates

### State-first / intermediate physical state
Nature Machine Intelligence 2025/2026 gives strong remote support, but existing handcrafted-state tests are mixed across Houses. It remains a reserve M2, not current leader.

### Koopman / spectral dynamics
ICLR 2025 and ICML 2025 contain modern Koopman representation work; Communications Physics 2025 applies deep Koopman operators to causal discovery.
Potential mapping: stationary source as slow/invariant dynamical content, turbulent realization as faster modes.
Not promoted because a specific source-identifying spectral object has not yet beaten the predictive-latent premise in existing evidence.

### World models
Demoted because planning/rollout machinery is unnecessary for the current inference target.

### Causal/invariance
Rejected as M1 by project evidence; unconditional source invariance fails under early/source-dependent transport mismatch.

### Test-time adaptation
Retained as deployment strategy only.

## Current leading 1+2 under second screening

### M1 — Predictive Latent Physical Representation
Working paradigm: JEPA-class predictive representation learning on sparse gas/wind/pose histories.

Scientific thesis:
> infer source from the latent structure of plume observations that is predictive across context, rather than from raw stochastic realizations or their reconstruction.

Output:
- a lightweight source probe produces PMFS-compatible source-location logits/probabilities.

### M2 — Intrinsic Source Representation from Dynamics
Working principle:
> bind multiple transport-conditioned predictive histories of the same source into a persistent source-identity representation, inspired by intrinsic representations of dynamical systems across peripheral conditions.

### M3 — Shift-aware calibrated probability map
Working principle:
> calibrate the final source map/region under House, simulator and real-sensor shift, and abstain/expand when reliability is unsupported.

## Lightweight implementation constraint

Not counted as innovation:
- small temporal encoder rather than a large vision foundation model;
- masked/segment latent prediction;
- no full 3-D plume decoder;
- frozen/shared encoder with a small source head;
- paired-context identity regularizer only where training pairs exist;
- post-hoc calibration as M3.

## Public-data compatibility

The three-module definitions need only:
- sparse/trajectory gas observations;
- timestamps / positions and optional wind;
- source labels for supervised probe/evaluation;
- paired same-source contexts only for M2 training where available.

They do not require privileged full CFD fields at deployment.
This is compatible in principle with:
1. VGR/GADEN;
2. DNS plume trajectory/field data sampled along synthetic robot paths;
3. real wind-tunnel trajectory data.

## Provisional scorecard v2

| Candidate M1 | Paradigm strength | 25/26 top-venue provenance | Project-mechanism fit | GSL novelty room | Lightweight fit | Public-data fit | Collision penalty | Adjusted /60 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Predictive Latent Representation / JEPA | 10 | 10 | 9 | 9 | 9 | 10 | 0 | 57 |
| Inverse Generative Modeling | 10 | 10 | 9 | 5 | 7 | 10 | -5 | 46 |
| State-first Inverse Inference | 8 | 10 | 9 | 8 | 7 | 9 | 0 | 51 |
| Physical World Models | 9 | 10 | 6 | 8 | 5 | 8 | 0 | 46 |
| Koopman/Spectral Representation | 8 | 9 | 7 | 8 | 8 | 8 | 0 | 48 |
| Causal/Invariance Factorization | 9 | 10 | 5 | 4 | 8 | 8 | -2 | 42 |

Current M1 survivor threshold: >=54 with no fatal collision.
Current leader: Predictive Latent Representation / JEPA.

## Next loop before any external promotion

1. Search direct GSL/OSL collision specifically for JEPA, predictive latent representation, masked predictive physical representations and intrinsic dynamic identity.
2. Build a stronger existing-data proxy than smoothing: latent-predictive linear/CCA or Hankel predictive-state representation, with source-blind training and held-wind evaluation.
3. Compare M2 intrinsic-identity alignment against state-first intermediate reconstruction using exactly the same latent base.
4. Test whether source support / early non-identifiability requires a lightweight validity gate or can be handled by M3 calibration without adding a fourth contribution.
5. Screen 2026 ICLR/CVPR/NeurIPS accepted papers for alternative paradigm-level M1 candidates before freezing.
