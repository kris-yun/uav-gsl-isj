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


## Loop-3 auxiliary screening notes

### Predictive-coding precision weighting — literature strong, empirical proxy mixed

Remote support:
- Nature Communications 2025: *Uncertainty estimation with prediction-error circuits*.
- Nature Neuroscience 2026: *Human hippocampal ripples tune cortical responses based on predicted uncertainty*.

A simple inverse-local-variance weighting of plume windows was tested as a proxy for precision-weighted prediction/error assimilation.

Outcome:
- small improvements in some late cases;
- clear degradation of source/wind ratio in H02 180 s and H03 120/180 s;
- H01 240 s held-wind identity drops from 2/2 to 1/2.

Decision:
- generic precision weighting is NOT supported as an auxiliary innovation.
- do not promote “downweight noisy plume segments” without a source-specific precision mechanism.

### Simple wind-invariance / adversarial-removal proxy — no incremental evidence

A linear source-identity direction was trained on 120–180 s windows and evaluated on 180–240 s windows.
Explicit orthogonalization/penalization against the wind direction did not improve accuracy:
- H01 ~0.833 unchanged;
- H02 ~0.750 unchanged;
- H03 ~0.708 unchanged or slightly worse for naive orthogonalization.

Decision:
- M2 cannot be justified as generic wind removal/domain invariance.
- if intrinsic-source representation remains, it must be demonstrated by a stronger paired-dynamics objective with destructive pairing controls; otherwise replace it.

This keeps the main predictive-coding candidate alive while reopening the auxiliary-M2 search.


## Loop-4 M2 challenger: Common-vs-Unique Information Decomposition

### Remote provenance

Top-venue 2025/2026:
- NeurIPS 2025: *Partial Information Decomposition via Normalizing Flows in Latent Gaussian Distributions*.
  - decomposes target information into redundant, unique and synergistic components and makes PID practical for high-dimensional non-Gaussian representations.
- ICLR 2026: *Lossy Common Information in a Learnable Gray-Wyner Network*.
  - explicitly separates common information from task-specific/private information in a learnable representation.
- ICLR 2026: *Coupled Transformer Autoencoder for Disentangling Multi-Region Neural Latent Dynamics*.
  - separates shared and private temporal dynamics rather than conflating them.
- Nature Neuroscience 2026: *Neural population geometry and optimal coding of tasks with shared latent structure*.
  - independent neuroscience support for cross-context readout of shared latent structure.
- Nature 2025: *Inter-brain neural dynamics in biological and artificial intelligence systems*.
  - empirical shared-vs-unique dynamical subspaces across interacting individuals.

### GSL translation

For paired observations of the same source under different transport contexts:
- information about source that is redundant/shared across transport views is a candidate source-identifying signal;
- information unique to one wind/transport view is more likely transport-context specific;
- synergy is retained as a diagnostic rather than assumed useful.

This differs from generic domain invariance:
- unique transport information is not forced away;
- the representation is explicitly factorized into common/source and private/transport channels;
- no source information is assumed before physical support exists.

### Existing-data common-vs-unique proxy

Using aligned 5 s windows from fast and slow histories for the same source:
- COMMON proxy = mean of paired feature vectors.
- UNIQUE proxy = half-difference of paired feature vectors.
- train 120–180 s, evaluate source separation on 180–240 s.

Results:
- H01:
  - train source separation: common 0.121 vs unique 0.052.
  - test source separation: common 0.230 vs unique 0.010.
  - source classification: common 0.833 vs unique 0.458.
- H02:
  - train source separation: common 0.464 vs unique 0.014.
  - test: common 0.166 vs unique 0.032.
  - classification: common 0.500 vs unique 0.458; physical support remains the limiting issue.
- H03:
  - train source separation: common 0.577 vs unique 0.073.
  - test: common 0.232 vs unique 0.093.
  - classification: common 0.667 vs unique 0.667.

Interpretation:
- across all three Houses, source separation is concentrated much more strongly in the cross-transport common component than the transport-unique component.
- H02 confirms that common-information decomposition cannot manufacture source identity when support is weak.
- this premise is stronger than the previous generic wind-invariance and paired-prototype tests.

### Decision

M2 challenger status: STRONGER THAN GENERIC INTRINSIC-IDENTITY ALIGNMENT.

Preferred M2 working concept:
**Transport-Redundant Source Information (TRSI)**

Training concept:
- M1 predictive latent segments are produced independently for each transport context.
- M2 decomposes their source-target information into common/redundant and context-private components.
- source probability map consumes the common/source channel; private transport channel is retained for prediction and uncertainty, not forcibly erased.

NeurPIR remains a supporting analogy; PID/Gray-Wyner common-information decomposition is now the preferred mathematical basis for M2.


## Loop-5 M1 challenger: Learned Missing Physics / Gray-Box Prior Correction

### Remote provenance
- Nature Communications 2026: Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*.
  - non-intrusive reuse-and-correct paradigm;
  - frozen callable prior + learned structured discrepancy;
  - operator-splitting foundation;
  - effective subgrid correction in turbulence and correction under parameter shift.
- NeurIPS 2025: Wei et al., *INC: An Indirect Neural Corrector for Auto-Regressive Hybrid PDE Solvers*.
  - shows that correction placement matters; indirect physics-level correction controls error amplification better than naive direct updates.
- NeurIPS 2025: Yue et al., *DeltaPhi: Physical States Residual Learning for Neural Operators in Data-Limited PDE Solving*.
- NeurIPS 2025: Ilersich & Nair, *Learning Stochastic Multiscale Models*.

### Project-mechanism match
This line directly matches the strongest project asymmetry:
- exact candidate-conditioned physical responses preserve source identity in the controlled factorial microbank;
- estimated/deployable transport providers can be candidate-dependently wrong;
- H01 SA approximate response is worse than a null response under ordinary log1p MSE;
- PHIC can predict zero exposure where observed hits exist;
- local transport/wind providers show systematic predictive deficiencies.

Thus the premise is not “physics is useless”.
It is:
> the coarse prior contains useful inductive bias, but missing/unresolved transport physics corrupt the candidate evidence.

### Existing-data negative control
A global affine correction is NOT sufficient:
- it can lower response MSE by collapsing toward the dominant blank state;
- cross-source transfer can worsen an already-correct near-zero response;
- therefore M1 must be judged by source discrimination, support, onset and calibration, not forward MSE alone.

### Discrepancy anatomy
H01 SA-fast approximate provider:
- observed >0.1 ppm samples = 16;
- predicted >0.1 ppm samples = 44;
- overlap = 12;
- first arrival timing is relatively close, but the provider creates an excessive late tail;
- ~95.8% of total squared log-response error occurs on observed blank samples.

This explains why a generic regression objective can prefer “predict zero” and motivates an event-aware auxiliary rather than ordinary MSE fitting.

### Direct GSL collision boundary
2025 Journal of Turbulence, Piro et al., *Many wrong models approach to localise an odour source in turbulence with static sensors*:
- already addresses inaccurate turbulent source models by ranking/blending multiple wrong stochastic models.

Therefore novelty cannot be “model mismatch robustness” or “ensemble of approximate models”.
The surviving contribution must learn structured, candidate-conditioned missing physics relative to an executable prior and demonstrate restored source evidence.

### Comparative M1 decision
The JEPA/predictive-representation line is downgraded:
- linear temporal-order destructive tests did not show ordering/prediction as consistently load-bearing in H02/H03;
- source identity can live in rare events that a generic predictive objective suppresses.

Learned missing physics is elevated because it explains both:
1. the exact-forward positive premise; and
2. the estimated-provider negative premise.

### Provisional score v3

| M1 family | Paradigm strength | 25/26 provenance | Direct project fit | Novelty room after collision | Lightweight fit | Cross-dataset fit | Falsifiable now | Adjusted /70 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Learned Missing Physics / Gray-Box Correction | 10 | 10 | 10 | 8 | 9 | 9 | 10 | 66 |
| Predictive Latent Representation / JEPA | 10 | 10 | 7 | 8 | 9 | 10 | 7 | 61 |
| State-first Inverse Inference | 8 | 10 | 9 | 8 | 7 | 9 | 8 | 59 |
| Common-vs-Unique Information Decomposition | 8 | 10 | 8 | 8 | 8 | 8 | 8 | 58 |
| Inverse Generative Modeling | 10 | 10 | 9 | 5 | 7 | 10 | 7 | 58 |

Current primary challenger:
**Learned Missing Physics / Gray-Box Prior Correction**.

Dedicated candidate file:
`docs/CANDIDATE_MISSING_PHYSICS_PMFS_20260919.md`

### Preferred 1+2 attached to this M1
- M1: source-conditioned learned missing physics.
- M2: extreme-event-aware intermittency preservation (Nature Communications 2026 η-learning) to prevent blank-dominated correction.
- M3: structured shift-aware source regions (ICLR/ICML 2025 conformal-under-shift / structured prediction sets).

The previous common-information/PID M2 remains on reserve for the JEPA branch, not automatically carried into the missing-physics branch.

### Next hard gate
Before promotion:
1. pair exact/reference and approximate candidate responses on the same histories;
2. quantify whether discrepancy correction improves true-vs-wrong candidate margins;
3. test event-aware correction objectives against global MSE correction;
4. include many-wrong-model blending as a direct GSL comparator;
5. reject the line if learned correction only improves forward fit without improving source evidence.


## Loop-6 challenger: Learned Stochastic Multiscale Closure

### Remote provenance
- NeurIPS 2025 — *Learning Stochastic Multiscale Models*: resolved macrostate plus latent unresolved microscale SDE dynamics.
- Nature Machine Intelligence 2025 — *Learning cell dynamics with neural differential equations*: explicit state-dependent drift/diffusion rather than treating stochasticity as a constant residual.
- classical turbulence closure is a genuine remote scientific lineage, not an architecture trick.

### GSL hypothesis
A coarse transport prior predicts the resolved plume tendency, while unresolved turbulent intermittency is represented by a learned stochastic latent closure. Candidate source evidence is obtained by marginalizing over the closure-generated response distribution.

### Existing-project screen
Negative evidence is substantial:
- historical uniform transport-member marginalization is already NO-GO and can let a random member dominate;
- current frozen R3B/source×wind caches contain only one qualified stochastic realization per source×wind, so a new learned stochastic closure cannot be identified cleanly from those assets;
- the project’s strongest H01 failure is a systematic candidate-dependent tail/support bias, not merely missing variance.

Decision:
- stochastic closure is scientifically credible but not currently the best M1.
- it may become a subcomponent of learned missing physics only if new independent simulator realizations are generated under a preregistered seed contract.
- do not spend new simulations on it before the deterministic/structured discrepancy gate is passed.

Status: DEMOTED / DATA-SEMANTICS BLOCKED.

## Loop-6 challenger: State-First Intermediate Physical Representation

### Remote provenance
- Nature Machine Intelligence 2026 — *Current-diffusion model for metasurface structure discoveries with spatial-frequency dynamics*.
- Nature Machine Intelligence News & Views 2026 — *Learning intermediate physical states for inverse metasurface design*.

### GSL hypothesis
Infer a physically meaningful transport-response state before source location, instead of mapping sparse measurements directly to source.

### Existing-project screen
Mixed:
- exact candidate response state is highly source-identifying;
- coarse/estimated response state can be catastrophically wrong;
- handcrafted intermediate summaries are not uniformly better across Houses.

Decision:
- “state first” identifies a useful architectural principle but does not by itself solve the core model–reality gap.
- it is subsumed more naturally by the learned-missing-physics candidate, where the corrected response itself is the intermediate physical state.

Status: DEMOTED AS M1; possible interpretation of the M1 corrected state.

## Loop-6 updated ordering

1. Learned Missing Physics / Gray-Box Prior Correction — current leader.
2. Predictive Latent Physical Representation — reserve challenger.
3. State-First Intermediate Physical Representation — subsumed/auxiliary.
4. Stochastic Multiscale Closure — scientifically strong but current-data blocked.
5. Inverse Generative Modeling — collision-demoted.
