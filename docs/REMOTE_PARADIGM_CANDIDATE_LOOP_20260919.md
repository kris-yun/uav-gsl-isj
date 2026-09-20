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


## Loop-7/8 update: learned-missing-physics survives a stronger collision and mechanism screen

### Distant source-localization analogue found
2025 underwater acoustics contains correction-based source localization:
- JASA 2025 CrPINN-aided matched-field processing corrects imperfect propagation-model replicas using sparse measurements.
- CISS 2025 mismatch-robust differentiable modular forward localization adapts the propagation model under environmental mismatch.

Effect on decision:
- global novelty claim “correct physics model for source localization” is forbidden;
- the distant analogue **supports the transferability** of the paradigm;
- GSL novelty must be turbulent-specific: candidate-conditioned transport correction + intermittency preservation + PMFS source evidence.

### Existing-data mechanism sharpened
Same-route H01 SA-fast exact-vs-estimated audit:
- exact transport+FOPDT: true SA rank 1;
- estimated provider: false SB rank 1.
- approximate SA has delayed/missing intermediate support and a large spurious late tail.
- MSE-optimal scalar correction collapses all >0.1 ppm hits and only wins by predicting blank.

Therefore the target discrepancy is:
- time structured;
- sign changing;
- source/candidate dependent;
- upstream of the already-audited FOPDT sensor model.

Preferred M1 implementation is now an **indirect transport-level corrector before FOPDT**, not a generic output residual.

### M2 collision screen
Recent OSL literature already uses whiff/blank timing and intermittency as informative cues.
Therefore M2 cannot claim novelty for “use whiff statistics”.
Its novelty must be the 2026 η-learning transfer:
- use rare-event/intermittency statistics as a training constraint on the missing-physics corrector;
- prevent blank-dominated regression from erasing source evidence.

No direct 2025/2026 GSL η-learning application was found in the current screen.

### M3 collision screen
Conformal source-location uncertainty already exists in 2025 acoustic localization.
Therefore M3 is auxiliary only, not a novelty centerpiece.
Its GSL-specific role is a spatially structured, shift-aware source region attached to the PMFS map.

### Cross-dataset feasibility correction
- TURB-Smoke 2026: suitable mechanistic cross-simulator source test (5 sources, multiple winds, source-resolved DNS trajectories/fields).
- ICASSP 2025 GSL Challenge: preferred real source-localization benchmark.
- Red:Vapor 2026: fixed physical source across runs; useful for real plume/sensor/geometry correction transfer but NOT independent multi-source-position localization.

### Current confidence
Learned Missing Physics remains the primary M1 because it is the only screened paradigm that simultaneously explains:
1. exact-forward source-identity success;
2. approximate-provider rank reversal;
3. candidate-dependent transport bias;
4. why global correction/MSE can fail;
5. why a lightweight correction can preserve existing PMFS semantics.

No promotion to closed-loop yet.


## Loop-9 challenger: Equation / Missing-Law Discovery

### Remote provenance
- Nature Computational Science 2025 — *Bi-level identification of governing equations for nonlinear physical systems*.
- Nature Communications 2025 — *Generative discovery of partial differential equations by learning from math handbooks*.
- Nature Communications 2025 — *Learning interpretable network dynamics via universal neural symbolic regression*.
- Nature Communications 2026 — *From data chaos to physically interpretable deterministic mapping*.

### Candidate GSL thesis
Instead of learning a black-box correction, identify an interpretable missing transport/sensor correction law that upgrades the coarse PMFS forward model.

### Existing-data gate
The current project does **not** support this as M1:
- the strongest discrepancy evidence is route-local and candidate-dependent;
- the estimated-vs-exact H01 discrepancy changes sign in time and depends on plume support;
- current qualified stochastic data do not provide enough repeated field-state/derivative observations to identify a universal correction PDE or closure term;
- a symbolic law discovered from one/few route traces would be underidentified and likely geometry-specific.

Cross-dataset risk is also high:
- an equation fitted to GADEN indoor geometry may not remain meaningful under DNS TURB-Smoke or real wind-tunnel sensor dynamics.

Decision:
**REJECT AS CURRENT M1 / DATA-IDENTIFIABILITY NO-GO.**
If the missing-physics corrector later reveals a stable low-dimensional correction across Houses and datasets, symbolic distillation may become a post-hoc interpretability analysis, not one of the three core innovations.

## Loop-9 ranking

1. Learned Missing Physics / gray-box prior correction — remains leader.
2. Predictive latent representation — reserve.
3. Equation discovery — rejected by current identifiability/data.
4. State-first — subsumed.
5. Stochastic closure — ensemble-data blocked.


## Loop-10 — literature verification + composition test

### M1 provenance now independently convergent

Verified primary/independent 2025–2026 lineages:

1. **Nature Communications 2026** — Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*.
   - published 23 June 2026, DOI 10.1038/s41467-026-74002-2;
   - explicitly targets model–reality gaps from unresolved physics/structural incompleteness;
   - non-intrusive reuse-and-correct around a fixed callable prior;
   - demonstrates effective subgrid correction in turbulence.

2. **NeurIPS 2025 Main Conference** — Wei et al., *INC: An Indirect Neural Corrector for Auto-Regressive Hybrid PDE Solvers*.
   - correction is integrated inside the physical evolution rather than appended to outputs;
   - includes formal error-amplification analysis;
   - evaluated through 3-D turbulence.

3. **NeurIPS 2025 Main Conference** — Yue et al., *DeltaPhi: Physical States Residual Learning for Neural Operators in Data-Limited PDE Solving*.

4. **NeurIPS 2025 Main Conference** — Ilersich & Nair, *Learning Stochastic Multiscale Models*.
   - explicitly represents unresolved microscale dynamics on top of a resolved coarse state.

These are independent scientific-ML groups and methods converging on the same high-level principle:
**retain useful coarse physics, model only the unresolved discrepancy/dynamics.**

### Direct GSL novelty boundary strengthened

A current search finds:
- 2019 GSL already studies probabilistic robustness to model mismatch;
- Journal of Turbulence 2025 uses *many wrong models* and model blending for turbulent odor-source inference;
- 2026 deep probabilistic indoor GSL uses physical dependency-guided sequential inference;
- 2025/2026 odor-source learning includes PINN/ML/RL, LLM, Mamba and other direct estimators.

No current search result directly implements:
**a learned candidate-conditioned missing-physics correction inserted upstream of the PMFS sensor likelihood, trained to restore source-discriminative event structure while preserving the final source probability map.**

Therefore forbidden novelty claims remain:
- not first to consider mismatch;
- not first hybrid physics+ML;
- not first probabilistic source localization.

The surviving claim is narrower and more defensible:
**learn the structured, source-conditioned discrepancy of an existing GSL physical prior, because that discrepancy is experimentally shown to reverse source evidence.**

### M1+M2 capacity gate

A two-segment scalar corrector on H01 SA-fast was used as an oracle-only capacity test.

- false SB/null MSE ~0.0008061;
- uncorrected SA prior MSE ~0.0073375;
- a tiny time-structured correction can reduce true-SA MSE below false SB while retaining event topology;
- η-regularized choice preserves substantially more hits/top-tail/integrated response than the pure-MSE optimum.

This establishes that:
1. correction need not be a full plume surrogate;
2. average loss alone is unsafe;
3. M2 can be load-bearing rather than decorative.

### Challenger: multi-fidelity learning

Nature Communications 2026 MFTabPFN gives recent high-level multi-fidelity/UQ support.
However, generic multi-fidelity fusion does not specify the missing physical object, and source-independent cross-fidelity correction is contradicted by current data.
Decision: **demoted to training strategy**, not M1.

### M3 alternative screened: risk monitoring

NeurIPS 2025 *Monitoring Risks in Test-Time Adaptation* provides a strong recent framework for detecting silent model failure under distribution shift with sequential risk monitoring.

Potential GSL use:
- monitor whether the learned missing-physics corrector leaves its validity domain;
- gate/fallback to the frozen prior when risk exceeds a threshold.

Current limitation:
- present project assets do not yet provide enough independent labeled shifts to calibrate a meaningful runtime risk monitor;
- a hand-designed correction-magnitude gate would be unsupported.

Decision:
- keep as reserve M3;
- structured shift-aware conformal source regions remain the more directly defined output-level auxiliary for public-dataset validation.

### Current leading 1+2

M1: **Source-Conditioned Learned Missing Physics / Gray-Box Prior Correction**

M2: **Extreme-Event-Aware Intermittency Preservation (η-learning transfer)**

M3: **Structured Shift-Aware Source Regions**

Current state:
**ACTIVE PRIMARY CANDIDATE / NOT YET VALIDATED**

Next hard gate:
a learned lightweight corrector must improve held-condition source margin/ranking, not merely forward MSE, and M2 must provide incremental value over M1.


## Loop-5 — Main-candidate reversal test: predictive latent vs extreme-event-aware learning

A stricter matched-window held-wind test was run on the same 12 controlled histories.

Protocol:
- fixed 10 s windows from 120–240 s;
- fast-wind histories provide source prototypes;
- slow-wind histories are held transport;
- dimensions are standardized only from fast-wind windows;
- compare three fixed source-blind representations:
  1. predictable bulk summaries,
  2. η/extreme-intermittency summaries,
  3. their concatenation.

Held-wind source identity across 72 source-window decisions:

| Representation | Correct | Accuracy |
|---|---:|---:|
| predictive bulk | 50/72 | 0.694 |
| η/extreme-intermittency | 53/72 | 0.736 |
| predictive + η | 53/72 | 0.736 |

By House:
- H01: predictive 14/24, η 15/24, combined 15/24.
- H02: all 15/24.
- H03: predictive 21/24, η 23/24, combined 23/24.

Interpretation:
- in this linear/handcrafted premise test, the predictive branch is **not load-bearing** once the rare/intermittency observable is present.
- therefore a paper whose main claim is simply “predictive latent structure is the source-information carrier” is not yet justified.
- the current data are at least as compatible with a stronger thesis: **source evidence is disproportionately concentrated in sparse tail/intermittency events, while average-risk/predictive objectives can wash it out**.

### New paradigm-level M1 candidate C10 — Extreme-Value-Aware Scientific Learning

Large-science source:
- classical Extreme Value Theory (EVT): peaks-over-threshold, tail laws, max-stability.
- Nature Communications 2026: Chang & Sapsis, *Extreme Event Aware (η-) Learning*.
- UAI 2026: Hasan et al., *Learning Max-Stable Representations that Extrapolate*.
- ICLR 2026: *EVEREST: A Transformer for Probabilistic Rare-Event Anomaly Detection with Evidential and Tail-Aware Uncertainty*.
- NeurIPS 2025: *Deciphering the Extremes: A Novel Approach for Pathological Long-tailed Recognition in Scientific Discovery*.

Scientific GSL thesis:
> turbulent source evidence is not uniformly distributed over observations; a small set of intermittent tail events can carry disproportionate source identity, while ordinary empirical-risk and reconstruction objectives are dominated by blanks/common regimes.

This is different from the old odor-literature statement “whiffs and blanks are informative”.
The transferred object is **tail-aware learning/extrapolation under scarce extreme evidence**, not a handcrafted whiff feature.

Potential M1 form:
- shared lightweight temporal encoder;
- an EVT/η constraint shapes the latent/source-evidence distribution so that tail observables remain statistically represented;
- source probability map is computed from bulk + tail-conditioned evidence, with a calibrated mechanism that does not let common blank regimes dominate the posterior.

Novelty risk:
- eLife 2022 and related turbulent-odor literature already establish that timing/intermittency features carry source-location information.
- therefore novelty cannot be “use whiff duration / intermittency”.
- it must be a true transfer of modern rare-event learning (η-statistical regularization / max-stable representation / tail-aware uncertainty) into source-probability inference.

Status C10: STRONG SURVIVOR; currently tied with / possibly stronger than predictive-JEPA M1.

### Evolution-operator candidate C9 — screened and not promoted

Top provenance:
- ICLR 2026: Turri et al., *Self-Supervised Evolution Operator Learning for High-Dimensional Dynamical Systems*.
- NeurIPS 2025: DynaMix zero-shot dynamical-system reconstruction.

Existing-data proxy:
- AR/evolution fingerprints can improve held-wind source discrimination in several cases:
  - H01 240 s AR10 wind/source ratio ~0.112 vs static ~0.617;
  - H02 240 s AR10 ~0.081 vs static ~0.161.
- but the operator representation fails or becomes transport-dominated in other regimes:
  - H01 180 s AR10 ratio >1 and identity falls to 1/2;
  - H03 240 s AR10 ratio ~0.727 and identity 1/2.

Physical objection:
- in the advection–diffusion equation, source location is primarily a forcing/source term, while the evolution operator is governed by transport/geometry.
- treating the operator itself as source identity risks encoding the wrong physical object.

Decision:
- C9 is rejected as M1 despite recent top-venue provenance.
- operator ideas may remain implementation tools, not the scientific thesis.

### Current M1 competition after Loop-5

1. C10 Extreme-Value-Aware Scientific Learning — strongest project-specific mechanism fit.
2. C8 Predictive Latent Physical Representation / JEPA — strongest generic physical-representation provenance, but no longer empirically load-bearing in the current linear proxy.
3. C4 State-first inverse inference — reserve.
4. C1 inverse generative — collision-demoted.
5. C9 evolution operator — physics-object mismatch.

No M1 is frozen yet.


## Loop-6 — auxiliary search and direct sequence-model falsification

### Event-aware representation learning (ICLR 2026): not promoted

Remote anchor:
- ICLR 2026 — Peng et al., *From Observations to Events: Event-Aware World Models for Reinforcement Learning*.

Existing-history proxy:
- fixed 20 s windows;
- explicit ordered event onset/duration/peak/mass features;
- fast-wind prototypes, slow-wind held transport.

Accuracy (36 held-wind source decisions):
- aggregate classical features: 28/36;
- tail features: 28/36;
- event-order features: 25/36;
- tail + event: 27/36.

Time reversal changes event representation but does not yield a positive source-localization increment.
Decision: NO-GO as current auxiliary.

### Rough-path signatures: order-sensitive but not source-useful here

2025/2026 top anchors:
- ICML 2025 — *Learning with Expected Signatures: Theory and Applications*.
- NeurIPS 2025 — *Scalable Signature Kernel Computations via Local Neumann Series Expansions*.
- ICLR 2026 — *Random Controlled Differential Equations*.

Level-2/3 signatures of (time, log gas):
- normal held-wind: signature 27/36, tail 28/36, tail+signature 28/36.
- time-reversed slow traces: signature 20/36, tail unchanged 28/36, tail+signature 23/36.
- complementarity audit: signature corrects **0** tail errors; tail corrects 1 signature error.

Conclusion:
- path signature genuinely captures temporal order (destructive reversal works),
- but order information does not add source discrimination on this controlled set.
Decision: retain as negative/destructive control only; not an innovation module.

### Modern marked temporal point process (MTPP): screened, not promoted

Recent top anchors:
- NeurIPS 2025 — *Deep Continuous-Time State-Space Models for Marked Event Sequences* (Spotlight).
- NeurIPS 2025 — *Transformers for Mixed-type Event Sequences*.
- NeurIPS 2025 — *Addressing Mark Imbalance in Integration-free Marked Temporal Point Processes*.
- ICLR 2026 — *Edit-Based Flow Matching for Temporal Point Processes*.

A minimal marked Poisson-process proxy used threshold-crossing arrivals with duration/peak/mass marks and the no-event survival term.

Whole 120–240 s held-wind:
- H01: MTPP proxy 2/2; tail 2/2.
- H02: 2/2; tail 2/2.
- H03: MTPP 1/2; tail 2/2.

Held 180–240 s 10 s windows:
- H01: MTPP 6/12 vs tail 9/12.
- H02: 6/12 vs 6/12.
- H03: 7/12 vs 7/12.

Decision:
- a point-process framing is scientifically natural but is not presently supported as the main innovation.
- it also risks reducing to a sophisticated re-expression of known whiff timing.
Status C11: DEMOTED/NO-GO.

### Censoring-aware survival evidence: promoted as auxiliary candidate

Remote top anchors:
- ICLR 2025 — *Conformalized Survival Analysis for General Right-Censored Data*.
- ICML 2025 — *Doubly Robust Conformalized Survival Analysis with Right-Censored Data*.
- AISTATS 2025 — proper scoring for censored survival/competing risks.

Existing data with frozen 0.1 ppm arrival event:
- T=120 s: H01/H02 both source hypotheses censored -> no distinction; H03 distinguishes.
- T=180 s: H01 remains censored -> abstain; H02/H03 distinguish.
- T=240 s: all three Houses distinguish the two held-wind source identities.
- the first-arrival/censoring pattern is highly stable across fast/slow winds in this controlled bank.

This matches the project's physical-support logic exactly:
no event by finite horizon is a right-censored time-to-event observation, not proof that a source is impossible.

Status: ACTIVE M2 candidate for EVT-aware M1.

## Direct EVT novelty collision screen through 2026

Targeted searches for:
- gas/odor source localization + extreme value theory,
- max-stable source localization,
- generalized Pareto plume source localization,
- tail-aware GSL/OSL,
- EVT turbulent source inference

did not surface a direct recent GSL method using EVT/max-stable/η-learning for source probability inference.

Collision remains with **classical intermittency/whiff statistics**, not with modern EVT-aware learning.
Therefore the novelty statement must remain:
- NOT “extreme concentrations/whiffs matter”;
- YES candidate: modern extreme-event-aware statistical learning for source evidence under sparse turbulent observations.

## Current ranking after Loop-6

1. **C10 Extreme-Value-Aware Scientific Learning** — current main leader.
2. **C8 Predictive Latent Physical Representation / JEPA** — reserve; linear premise tests weak/negative.
3. State-first inverse inference — reserve.
4. Inverse generative — collision-demoted.
5. Evolution operator — physical-object mismatch.
6. MTPP/event-aware/path-signature — no positive incremental gate.

Current leading 1+2:
- M1: EVT / η / max-stable source-evidence learning.
- M2: censoring-aware survival evidence.
- M3: structured shift-aware conformal source region.

No promotion to validated main innovation yet.


## Loop-7 — M3 conformal collision and replacement search

### Structured conformal source region: collision-downgraded

New direct/near-direct collisions:
- AAAI 2026 — Jian et al., *Conformal Prediction for Multi-Source Detection on a Network*.
  Provides statistically valid source-set detection guarantees for single/multi-source diffusion on networks.
- ICASSP 2025 — Rozenfeld & Laufer Goldshtein, *Conformal Prediction for Manifold-based Source Localization with Gaussian Processes*.
  Provides conformal uncertainty intervals for acoustic source localization.

Decision:
> “apply conformal prediction to a source-location output” is no longer sufficiently remote or unique to count as our third innovation.

Shift-aware/Wasserstein conformal remains a strong evaluation baseline/tool, but M3 is demoted from innovation status.

### New M3 candidate — Neyman–Pearson selective source inference under shift

Primary latest anchor:
- ICLR 2026 — Heng & Soh, *Know When to Abstain: Optimal Selective Classification with Likelihood Ratios*.

Core transferred object:
- distinguish the distribution of **correct source-map decisions** from **wrong source-map decisions**;
- accept a localization only when a likelihood-ratio selector supports the “correct-decision” hypothesis;
- otherwise retain the probability map but explicitly abstain from source declaration.

Why this is different from entropy/margin stopping:
- historical PMFS already uses entropy/margin-like confidence, and project evidence contains confident-wrong maps;
- the ICLR-26 selector is derived from Neyman–Pearson optimality and targets correct-vs-wrong decision distributions under covariate shift, rather than thresholding confidence alone.

Current status:
- literature fit: strong;
- direct GSL collision: none found in current search beyond a 2025 Mamba-GSL paper that uses heuristic entropy/top-two-margin abstention;
- offline project test required before promotion.

### Risk-monitoring reserve

NeurIPS 2025 — Schirmer et al., *Monitoring Risks in Test-Time Adaptation* uses sequential testing/confidence sequences to detect model-performance degradation under unlabeled deployment shift.

This is kept as a reserve deployment mechanism, not current M3:
- valuable for online simulator→real monitoring,
- but less tightly integrated with the source-probability map than selective inference.


## Loop-6: stronger project evidence + alternative-family elimination

### Exact opposite-wind source identity supports a representation-first hypothesis

The existing current-runtime factorial counterfactual transfer audit is stronger than the earlier heuristic proxies:

- target source/wind history is scored **only** against candidate histories under the opposite wind;
- no same-source same-wind candidate is allowed;
- fixed log1p-FOPDT MSE, no fitted calibration;
- H01/H02/H03: 4/4 rank-1 in every House, 12/12 overall.

Interpretation:
> the measured time history already contains a source-persistent cross-transport signature in this controlled two-source setting.

This is exactly the kind of structure a predictive representation should preserve without requiring a full transport surrogate.

### Surrogate-support failure strengthens the anti-reconstruction argument

A separate PHIC audit finds a candidate for which:
- 299 positive observed events exist;
- surrogate candidate exposure is zero in every selected member row;
- verdict: MODEL_ZERO_WITH_OBSERVED_HITS.

Thus a physically structured forward surrogate can be confidently wrong at the event level even while the raw sensor stream contains real source evidence.

This supports the main distinction:
- do not make accurate full-response reconstruction a prerequisite for source inference;
- learn a source-relevant latent predictive representation directly from observable histories, with physical support controls.

### Alternative M1: Koopman / spectral dynamics

Recent top-level support is strong:
- ICML 2025 ResKoopNet;
- ICLR 2025 Balanced Neural ODE / Koopman approximation;
- NeurIPS 2025 COLoKe;
- Nature Communications 2026 learnability/impossibility theory for Koopman spectral learning.

However, novelty and project tests are weaker:
- PLOS ONE 2025 already directly quantifies spectral information about source separation in multisource odor plumes and shows frequency-dependent localization information.
- existing spectral/autocorrelation proxy on our factorial histories is not uniformly transport-stable: H02 fails at 120/180 s and H03 degrades to 1/2 held-wind identity at 240 s.

Decision:
- KOOPMAN/SPECTRAL M1 = NO-GO as primary innovation.
- may remain as a comparator or analysis tool.

### Alternative M1: neural-manifold / representation-geometry learning

Nature Neuroscience 2026 gives powerful biological evidence that odor discrimination is stored in representational manifold geometry.
But:
- 2026 OSL already includes manifold-learning diffusion-state classification;
- a “manifold-based GSL” claim would be too close to existing OSL framing and lacks a unique transport mechanism.

Decision:
- MANIFOLD M1 = NO-GO.
- retain only as biological motivation for why representation geometry matters.

### Alternative M1: extreme-event-aware learning

Nature Communications 2026 η-learning is strong and the H01 proxy gives direct positive evidence.
But turbulent odor localization has a long prior literature on whiff/blank timing, intermittency, frequency and mixed intensity/timing cues, including direct source-location prediction from those statistics.

Decision:
- EXTREME-EVENT AWARE LEARNING = not sufficiently collision-free as M1.
- retain as M2 because the novelty there is not “whiffs matter”, but **constraining a predictive latent learner so that rare source-informative regimes are not erased**.

## Loop-6 leader confidence

Current M1 leader remains predictive latent physical representation.

Independent support now comes from:
1. ICLR 2026 physical representation learning;
2. NeurIPS 2025 seq-JEPA predictive/invariant-equivariant world representations;
3. 2026 noisy-sensing JEPA work (LiDAR/ultrasound);
4. Nature Neuroscience 2026 olfactory representational geometry;
5. our 12/12 opposite-wind counterfactual source identity audit;
6. our surrogate-zero-with-observed-hit failure audit.

This is the first candidate in the loop with convergence from machine learning, physics, biological olfaction, and project evidence.



# Loop-5 update — finalists broadened and venue correction

## Venue correction for predictive-JEPA line

The directly physical paper *Representation Learning for Spatiotemporal Physical Systems* is an **ICLR 2026 Workshop on AI & PDE** paper, not an ICLR 2026 main-conference paper.

Therefore:
- the JEPA paradigm still has strong 2025/2026 main-conference provenance;
- but the most direct physical-parameter evidence is workshop-level;
- its previous top-venue provenance score is reduced.

## New finalist M1-B — Delay-coordinate invariant measures

Primary source:
- **Physical Review Letters 135, 167202 (2025)** — Botvinick-Greenhouse, Martin, Yang, *Invariant Measures in Time-Delay Coordinates for Unique Dynamical System Identification*.

Independent lineage:
- ICML 2025 long-time-statistics/ergodic learning in chaotic prediction;
- ICML 2025 modern Koopman representation;
- Nature Communications 2026 learnability/impossibility boundaries for Koopman spectral learning;
- NeurIPS ergodic/invariant-measure learning literature.

Existing-data evidence:
- H01 180 s marginal distribution: 1/2 source identity, wind/source ratio 0.759.
- delay measure m=4, tau=10 s: **2/2**, ratio 0.472.
- destroying temporal order while preserving every one-point value returns it to 1/2, ratio 0.696.
- H03 240 s ordered long-delay ratio 0.475; time-permuted 0.691.
- H02 120 s remains 0/2 for all delay choices, so the representation does not manufacture source support.

Risk:
- finite-horizon empirical measures can remain far from the 240 s reference, especially H03.
- delay dimension/lag cannot be held-out tuned.

Status: **STRONG M1 FINALIST**.

## New finalist M1-C — Non-intrusive missing-physics correction

Primary source:
- **Nature Communications 2026** — Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*.

Project evidence:
- exact candidate-conditioned physical response gives true-source rank1 in 12/12 crossed source/wind cases.
- approximate PHIC provider has a candidate with 299 exported positive events but zero modeled exposure in all three members; first conflict is 0.1134 ppm measured vs zero model support.
- evaluator-only affine calibration on H01-SA-fast drastically rescales the prior but leaves only a small held-tail SA-vs-SB advantage and cannot reconstruct support/timing.

Risk:
- direct collision with physics-guided/source-surrogate GSL is substantial.
- must be a genuinely non-intrusive structured prior-corrector, not a residual neural network.

Status: **STRONG MECHANISM-FIT / NOVELTY-AT-RISK**.

## Updated provisional finalist score

| M1 | Scientific/paradigm depth | Direct 25/26 strong venue | Existing-data mechanism evidence | GSL novelty room | Lightweight | Cross-public-data portability | Main risk | Adjusted /60 |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| Delay-coordinate invariant measures | 10 | 10 | 9 | 9 | 10 | 8 | finite-horizon convergence | **56** |
| Predictive latent / JEPA | 9 | 8 | 8 | 8 | 9 | 10 | direct physical anchor is workshop; representation-learning collision | **52** |
| Missing-physics prior-corrector | 9 | 10 | 10 | 6 | 9 | 6 | hybrid-GSL collision / prior portability | **50** |
| Inverse generative modeling | 10 | 10 | 9 | 5 | 7 | 10 | direct 2026 inversion collision | **46** |

Current order is not frozen.
The delay-invariant candidate is the first to pass a destructive temporal-order control with a primary 2025 PRL theory source.

## Next loop

- search for a third/alternative 2025–2026 paradigm with equally strong primary science provenance;
- run matched dynamic baselines against M1-B to determine whether the PRL object adds more than autocorrelation/event statistics;
- continue collision screen for time-delay/invariant-measure source localization;
- only after that choose auxiliary innovations.


# Loop-6 rejection — rough-path/path-signature M1

A third paradigm was screened from:
- ICLR 2025 *Deep Signature: Characterization of Large-Scale Molecular Dynamics*;
- ICLR 2026 *Random Controlled Differential Equations*;
- NeurIPS 2025 signature-kernel work.

A low-order path-signature proxy on [time, log-gas, cumulative exposure] looked initially promising:
- H01 180 s: 2/2 held-wind identity;
- H02 early unsupported regime remained 0/2;
- H03 120 s remained a failure, preserving a finite-horizon warning.

However, a deliberately simple physically interpretable baseline using:
- total exposure,
- first three concentration-weighted time moments,
- temporal spread/skew,
- first threshold crossing,
- hit fraction,
- peak time and peak amplitude

matched or exceeded the signature proxy:
- H01 180 s: moment baseline 2/2, wind/source ratio 0.142 versus signature ~0.18–0.20.
- H03 180 s: moment baseline ratio 0.081 versus signature ~0.31–0.35.
- H03 120 s: moment baseline 2/2 while signature remained 1/2.

Decision:
> rough-path signatures are mathematically elegant but do not currently earn a main-innovation role; their apparent benefit is explainable by much simpler event-timing moments on the available data.

Status: **M1 REJECTED / no module slot**.


## Loop-8 alternative-M1 search after JEPA downgrade

The search was reopened because the matched linear predictive-state test did not distinguish predictive latent learning from PCA/reconstruction.

### C9 — Koopman / operator-geometry source identity

Recent remote-domain anchors:
- ICLR 2025 — *MamKO: Mamba-based Koopman operator for modeling and predictive control*.
- NeurIPS 2025 — *MetaKoopman: Bayesian Meta-Learning of Koopman Operators for Modeling Structured Dynamics under Distribution Shifts*.
- Communications Physics 2025 — *Deep Koopman operators for causal discovery*.
- ICLR 2026 — *A Spectral-Grassmann Wasserstein metric for operator representations of dynamical systems*.
- Nature Communications 2026 — *Adversarial dynamical systems characterize when data-driven learning succeeds or fails*.

Potential GSL thesis:
> represent each plume observation stream through an operator/dynamical signature and infer source from source-specific dynamics rather than raw concentration values.

Existing-data proxy:
- fit source-blind AR/finite-dimensional Koopman proxies to log-concentration histories;
- compare same-source across wind against cross-source distances.

Result:
- H01 is strong after 150 s: wind/source ratios ~0.116–0.129, 2/2 held-wind identity.
- H02 is good over 120–240 s (~0.28–0.32, 2/2) but collapses on the late 180–240 s interval: ratio ~1.0 and only 0–1/2 identity.
- H03 is inconsistent: 120–240 s ratio ~0.94–1.01 with only 1/2 identity; late 180–240 s improves to ~0.67–0.79 and 2/2.

Decision:
- operator dynamics can expose useful source structure in some regimes but is not stable enough across Houses/horizons to support the main claim.
- the strongest recent operator papers also frame operator comparison as a general system-classification tool, making a plain “Koopman signature for source ID” conceptually too close to a generic feature substitution.

Status: RESERVE / NO-GO AS M1.

### C10 — Rough-path / path-signature representation

Recent remote-domain anchors:
- ICLR 2026 — *Random Controlled Differential Equations*, including rough-path/log-signature variants.
- NeurIPS 2024 — *Rough Transformers: Lightweight and Continuous Time Series Modelling through Signature Patching*.
- SIAM JCO 2025 — *Stochastic Control with Signatures*.
- ICLR 2025 physical coarse-graining work already uses path signatures to represent temporal interactions.

Potential GSL thesis:
> treat gas+wind+time observations as a continuous rough path and infer source from ordered iterated-integral geometry rather than marginal statistics.

Existing-data proxy:
- construct 4-D paths [time, log gas, wind_u, wind_v];
- compute exact piecewise-linear signatures through level 2 and level 3;
- compare held-wind same-source identity against simple path statistics.

Result:
- H01: level-2/3 signatures reduce or lose held-wind identity in all tested intervals (mostly 1/2 vs simple-stat 2/2).
- H02: signatures retain 2/2 on long intervals but have much worse wind/source ratios (e.g. 120–240: ~7–8 vs ~0.63 for simple stats); late interval is only 1/2.
- H03: signatures are usually more wind-contaminated and often drop to 1/2 while simple statistics retain 2/2.

Decision:
- raw path geometry is dominated by transport/wind variation rather than stable source identity in this evidence.
- rough-path theory remains mathematically elegant but fails the project-mechanism gate.

Status: NO-GO AS M1.

## Loop-8 consequence

Three high-level alternatives have now failed or weakened under matched existing-data screens:
1. inverse generative modeling — direct 2026 scientific-inversion collision;
2. predictive/JEPA representation — no matched linear advantage over PCA;
3. Koopman/operator identity — unstable across House/horizon;
4. rough-path signatures — transport contamination dominates source identity.

The next search must prioritize a paradigm whose **unique scientific object** is directly tied to the one project property that remains strongest across audits:
> source evidence appears only in specific physically supported, intermittent transport events, while average/global representations repeatedly mix source and transport.



## Loop-11 competing M1 paradigms: system identification and Koopman

### C9 — Self-supervised nonlinear system identification
2025 top-venue anchor:
- ICLR 2025, Gonzalez Laiz et al., Self-supervised contrastive learning performs non-linear system identification. The paper proves that temporal SSL can identify latent linear, switching-linear and nonlinear dynamics under nonlinear observations.

Strength:
- stronger theoretical identifiability than generic SSL;
- naturally treats observed plume histories as nonlinear observations of hidden dynamics.

Collision / fit problem:
- contaminant-source inference has already been explicitly formulated as system identification/model-class selection in adjacent transport domains;
- source location is a persistent hidden cause/parameter rather than the full dynamical state;
- adopting DynCL verbatim would risk becoming a representation-learning wrapper without a source-specific scientific object.

Status: RESERVE M1, below Predictive Coding.

### C10 — Koopman / operator-spectral source identity
2025/2026 anchors:
- ICML 2025 ResKoopNet: Koopman representations with spectral residuals.
- ICLR 2026 Spectral-Grassmann Wasserstein metric for operator representations of dynamical systems.
- Automatica 2026 stable Koopman embeddings for identification and control.

Direct novelty collision:
- Sustainable Cities and Society 2024 already applies Dynamic Mode Decomposition to source-term estimation in unsteady flow.
- contaminant inversion literature already contains Koopman/DMD surrogate inversion and 2026 sparse-plume DMD reconstruction.

Existing-data spectral proxy:
- normalized PSD/autocorrelation signatures separate SA/SB across winds in many H01/H02/H03 horizons;
- H02 at 120 s correctly collapses to 0/2 when physical source support is absent;
- however H03 240 s autocorrelation gives 0/2 and combined spectral-dynamics gives 1/2.

More importantly, power spectra and ordinary autocorrelation are invariant or nearly invariant to destructive time reversal/permutation and therefore cannot represent the native first-passage phase object already proven load-bearing by CTT.

Status: REJECT AS M1. Useful comparator only.

### C11 — biological/artificial sensory adaptation
2026 strong journal anchor:
- Nature Communications 2026, Jung et al., Intelligent artificial olfactory nervous system with sensory adaptation capabilities. The system adapts receptor sensitivity and filters background interference to identify gases across changing environments from limited training settings.

Why not promoted:
- excellent supporting evidence that adaptation is central to robust olfaction, but it is close to the gas-sensing domain and its primary task is gas identity rather than source localization;
- a software adaptation module risks duplicating sensor preprocessing/test-time adaptation rather than changing source evidence semantics.

Status: supporting biological/olfactory evidence, not current innovation slot.

## Loop-11 competitive decision

Current ordering after direct literature collision + existing-data tests:
1. Predictive Coding / latent predictive physical representation — CURRENT LEADER.
2. Self-supervised nonlinear system identification — RESERVE.
3. State-first intermediate physical inference — RESERVE auxiliary/main fallback.
4. Koopman spectral representation — REJECT as main due direct source-estimation collision and phase-information mismatch.
5. Sensory adaptation — SUPPORTING/DEPLOYMENT mechanism only.

Predictive Coding remains leader not because JEPA is fashionable, but because it uniquely matches the strongest frozen project fact: native temporal phase/first-passage information is source-informative while coarse or learned surrogates can erase it.


## Loop-12 — matched falsification of delay-coordinate invariant-measure M1

Date: 2026-09-20

### Literature / collision check

Primary source remains strong:
- Physical Review Letters 135, 167202 (2025), Botvinick-Greenhouse, Martin, Yang, *Invariant Measures in Time-Delay Coordinates for Unique Dynamical System Identification*.
- The paper proves that invariant measures in time-delay coordinates can identify dynamics up to topological conjugacy, with multiple observables resolving the remaining ambiguity under assumptions.
- Its public code demonstrates Lorenz, Kuramoto–Sivashinsky, and partially observed cylinder-wake flow.
- Targeted searches did not find a direct gas/odor-source-localization implementation of this 2025 delay-measure object. This is a positive novelty signal only.

### Frozen matched project test

Data:
- existing H01/H02/H03 × {SA,SB} × {fast,slow} controlled histories;
- no new simulator runs.

Protocol:
- train/reference wind = fast; held wind = slow;
- horizons = 120, 180, 240 s;
- delay measure fixed before inspection at m=4 and tau=10 s (50 samples at 0.2 s);
- empirical delay-coordinate measure compared by a deterministic sliced-Wasserstein proxy over fixed coordinate/mixed directions;
- same protocol applied to four comparators:
  1. one-point marginal empirical measure;
  2. autocorrelation vector;
  3. physically interpretable event-time/exposure moments;
  4. destructive time-order controls.

Primary diagnostics:
- held-wind same-source nearest-prototype count out of 2;
- same-source wind distance / cross-source distance (lower is better).

### Results

| House | Horizon | Delay correct | Delay ratio | Marginal correct | Marginal ratio | ACF correct | ACF ratio | Event-moment correct | Event-moment ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H01 | 120 | 2/2 | 0.127 | 2/2 | 0.127 | 2/2 | 0.021 | 2/2 | 0.017 |
| H01 | 180 | 2/2 | 0.495 | 1/2 | 0.422 | 2/2 | 0.281 | 2/2 | 0.072 |
| H01 | 240 | 2/2 | 0.233 | 2/2 | 0.153 | 2/2 | 0.548 | 2/2 | 0.060 |
| H02 | 120 | 0/2 | 1.000 | 0/2 | 1.000 | 0/2 | 1.000 | 0/2 | 1.000 |
| H02 | 180 | 2/2 | 0.058 | 2/2 | 0.072 | 1/2 | 0.491 | 2/2 | 0.103 |
| H02 | 240 | 2/2 | 0.066 | 2/2 | 0.080 | 2/2 | 0.044 | 2/2 | 0.135 |
| H03 | 120 | 1/2 | 0.435 | 2/2 | 0.197 | 2/2 | 0.130 | 2/2 | 0.136 |
| H03 | 180 | 2/2 | 0.157 | 2/2 | 0.171 | 2/2 | 0.097 | 2/2 | 0.074 |
| H03 | 240 | 2/2 | 0.310 | 2/2 | 0.419 | 0/2 | 1.010 | 2/2 | 0.551 |

Important positive controls:
- H02 120 s remains 0/2 and ratio ≈1 for every representation: the delay measure does not manufacture source support.
- H03 240 s is a genuine case where the delay-coordinate measure is substantially better than marginal/event-moment/ACF alternatives.

Important negative controls:
- H03 120 s delay measure is worse than all simple comparators and drops to 1/2.
- Across the 9 House×horizon conditions, delay-coordinate measures are not uniformly better than the physically interpretable event-moment baseline.
- Full deterministic time permutation does **not** consistently destroy the delay-measure advantage; in H03 120 s it actually improves held-wind identity from 1/2 to 2/2.
- Time reversal changes little in most cases, consistent with the fact that an empirical delay measure can retain substantial distributional structure without uniquely encoding chronological direction.

### Decision

The PRL object is scientifically deep and has attractive novelty room, but the project's matched evidence does not show that its unique object is consistently load-bearing.

The earlier 56/60 score was too optimistic because it was based on selected positive horizons rather than a matched multi-House baseline.

New status:

DELAY_COORDINATE_INVARIANT_MEASURE_M1 = DEMOTED_TO_RESERVE / NO-GO AS CURRENT MAIN

Reason:
- no consistent advantage over simple event-time moments;
- destructive order controls are mixed rather than decisive;
- finite-horizon and sparse-support effects are large enough to defeat the invariant-measure premise in some relevant cases.

It remains a useful comparator and possible diagnostic for H03-like regimes, but it no longer outranks the current predictive/intermittency line.

### Consequence for the search loop

The main-candidate search remains open.

The next M1 challenger must satisfy a stricter criterion:
> its unique remote-field scientific object must outperform matched simple temporal/event baselines across the existing House/horizon panel, not only on selected positive cases.



## Loop-13 — extreme-event-aware learning tested as a possible M1

Primary remote source:
- Nature Communications 2026, Chang & Sapsis, *Extreme Event Aware (η-) Learning*.

Direct odor/plume collision boundary:
- turbulent-odor literature already uses whiff/blank duration, intermittency, concentration tails and timing to infer source distance or drive source search;
- a 2024 Royal Society study shows source distance can be predicted from integrated odor statistics over 5–10 s in large outdoor plumes;
- eLife work on turbulent odor plumes already compares intensity, blanks, whiffs and intermittency for target localization.

Therefore the novelty cannot be “rare whiffs contain source information” or “use intermittency statistics”.
The transferable 2026 novelty is specifically η-learning: impose statistics of an extreme-regime observable during representation/model learning so that rare regimes are not erased by the dominant quiescent data.

### Matched existing-data screen

Fixed source-blind representations were compared on the same H01/H02/H03 × {SA,SB} × {fast,slow} panel at 120/180/240 s:
- tail/intermittency vector: q95, q99, max, top-1% mean, fixed-threshold exceedance fractions, first arrival;
- central-distribution vector;
- full physically interpretable event/exposure moments.

Key results:
- H02 180 s: tail ratio 0.038 vs central 0.418 and full moments 0.252; all tail 2/2.
- H02 240 s: tail 2/2, ratio 0.102; central/full moments each only 1/2.
- H03 120 s: tail 2/2, ratio 0.169 vs central 0.401.
- H01 240 s: tail 2/2, ratio 0.152 vs central 0.510.
- but H01 180 s: tail only 1/2 while full moments are 2/2.
- H03 240 s: tail only 1/2 while central/full moments are 2/2.
- H02 120 s: all methods collapse to 0/2, preserving the no-support control.

### Decision

EXTREME_EVENT_AWARE_LEARNING_AS_M1 = NO-GO.

Reason:
- the rare/intermittent branch is strongly useful in specific sparse-plume regimes but is not sufficient to carry source identity across all Houses/horizons;
- its raw observable family has substantial prior odor-plume precedent;
- its strongest value is as a **second innovation that protects M1 from rare-event erasure**, not as the full inference paradigm.

M2_EXTREME_EVENT_AWARE_ETA = RETAINED / STRONG AUXILIARY.

The M2 novelty claim, if retained, must be:
> η-style distributional regularization of the learned source representation using physically defined intermittency/extreme observables,

not:
> whiff statistics are useful.

