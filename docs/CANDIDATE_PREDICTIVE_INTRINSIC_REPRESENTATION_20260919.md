# Candidate M1 — Predictive Intrinsic Representation for Turbulent GSL

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. One-sentence thesis

Turbulent gas-source localization should infer source location from the **predictive latent structure** of sparse plume observations, rather than from direct source classification or reconstruction of the realized stochastic plume.

## 1. Main remote-field paradigm

### Predictive latent representation / JEPA

Primary provenance:
- ICLR 2026 Workshop on AI & PDE — Qu et al., *Representation Learning for Spatiotemporal Physical Systems* (workshop, not ICLR main conference).
- ICML 2025 — Lei et al., *M3-JEPA*.
- CVPR 2025 — Astruc et al., *AnySat*.

The load-bearing scientific transfer is not “use a JEPA block”.
It is:

> for downstream physical-parameter inference, predict latent structure that is stable enough to forecast/complete context, instead of spending capacity reproducing every low-level stochastic detail.

In GSL, source location is treated as a persistent hidden physical parameter of a stochastic transport process.

## 2. Project failure it addresses

Existing project evidence shows all of:
- transport realization can approach source variation in observation space;
- exact physical responses can preserve source identity while approximate full-response modeling destroys it;
- native temporal arrival structure can contain source information that coarse representations erase;
- some source hypotheses have no finite-horizon support, which no representation can repair;
- posterior sharpness can be wrong.

Therefore a useful representation should:
1. keep source-relevant temporal/transport structure;
2. discard innovations that are hard to predict and dominated by transport randomness;
3. remain uncertain when no predictive source signal exists.

## 3. Auxiliary innovation A — intrinsic identity from dynamics

Remote provenance:
- ICLR 2025 — Wu et al., *Neuron Platonic Intrinsic Representation From Dynamics Using Contrastive Learning*.

Transfer:
- neuron identity across peripheral conditions -> source identity across wind/transport contexts;
- activity segments -> plume observation segments;
- intrinsic neuron properties -> source-location identity.

This is not unconditional domain invariance.
Alignment is authorized only when the observation segment contains physical support; early zero-support histories cannot be forced to encode source identity.

## 4. Auxiliary innovation B — shift-aware calibrated source region

Remote provenance:
- ICLR 2025 — Wasserstein-regularized conformal prediction under general distribution shift.
- ICLR 2025 — error-quantified conformal inference for time series.
- NeurIPS 2025 — conformal time-series methods with change points.

Transfer:
- predictive source logits -> source probability map;
- calibrated set/region -> region of source hypotheses whose evidence remains credible under environment shift;
- unsupported shift -> abstention / expanded region, not a false sharp peak.

## 5. Minimal architecture

Input per observation event:
- gas measurement;
- local wind if available;
- robot position;
- time interval / sensor state metadata;
- optional geometry token.

M1:
- small temporal/spatiotemporal encoder;
- context segment and target segment encoders;
- predictor maps context latent + motion/wind context to target latent;
- no full plume decoder.

M2:
- source-identity projection from predictive latent;
- paired source-under-different-transport alignment where such pairs exist;
- transport/context degrees remain free rather than globally collapsed.

Source map:
- source candidate embeddings or coordinate head;
- similarity/likelihood over candidate cells;
- normalize to PMFS-compatible P(source cell | history).

M3:
- post-hoc shift-aware conformal calibration of source region / credibility.

## 6. Existing-data premise result

Using 12 controlled measured histories:
H01/H02/H03 × {SA, SB} × {fast, slow}.

A source-blind predictable/innovation proxy was evaluated by applying causal local averaging to log concentration and measuring:
wind separation / source separation.

At informative horizons, predictable components were consistently more source-dominant than innovations in the key comparisons:
- H02 180 s: predictable ~0.046–0.077 vs residual ~0.128–0.229.
- H03 180 s: predictable ~0.329–0.336 vs residual ~0.491–0.507.
- H01 240 s: predictable ~0.144–0.301 vs residual ~0.338–0.414.

At unsupported early horizons, the proxy cannot create identity:
- H02 60 s: both source and wind contrasts zero;
- H02 120 s: source and wind remain approximately tied.

This is consistent with, but does not prove, the predictive-latent thesis.

## 7. Falsification gates

M1 is killed if:
1. a source-blind predictive latent model does not improve held-wind source discrimination/calibration over matched reconstruction and direct-encoding baselines;
2. destructive target-time permutation does not remove its claimed benefit;
3. gains arise only from amplitude smoothing;
4. it fails on an independent plume dataset.

M2 is killed if:
1. same-source cross-transport alignment does not improve held-transport source identity;
2. it causes negative transfer in early/no-support segments;
3. a plain supervised source head matches it.

M3 is killed if:
1. calibrated source regions miss nominal coverage under realistic held-out shift;
2. coverage is obtained only by expanding to nearly the entire map.

## 8. Novelty collision checklist

Already screened:
- direct discriminative GSL CNN/ViViT/Mamba;
- unsupervised diffusion-state classification in OSL;
- generative inverse plume/source estimation (NeuPlume 2026);
- PINN/POD-PINN source inversion;
- ordinary world-model/planning GSL.

Still required before GO:
- predictive coding / self-supervised temporal representation in OSL;
- JEPA + source localization across adjacent sensing fields;
- representation learning for atmospheric inverse problems;
- intrinsic-dynamics identity methods in fluid/turbulent inverse problems.

## 9. Lightweight contract

- no foundation-scale encoder;
- no pixel/3-D plume reconstruction;
- masked/segment latent prediction;
- one shared encoder;
- small source head;
- M2 only a projection/alignment head;
- M3 post-hoc;
- inference must be compatible with online PMFS cadence after qualification.

## 10. Public-data contract

The method must be trainable/evaluable using sparse trajectories, not privileged dense CFD state at deployment.

Required validation ladder:
1. VGR/GADEN cross-house / cross-wind;
2. independent DNS turbulent plume data sampled along trajectories;
3. real wind-tunnel gas/wind trajectories.

## 11. Current decision

M1 = ACTIVE PRIMARY CANDIDATE.
M2 = ACTIVE AUXILIARY CANDIDATE.
M3 = ACTIVE AUXILIARY CANDIDATE.

No closed-loop run is authorized.
Next action is stronger linear predictive-state / CCA-style falsification on existing histories plus a direct 2025/2026 collision search.


## 12. Stronger linear predictive-state proxy (second falsification)

A stronger source-blind proxy was run on the same 12 controlled histories.

Procedure:
- 5 s windows;
- window features = mean log gas, standard deviation, hit fraction, within-window trend, mean wind magnitude;
- train a ridge next-window predictor only on the fast-wind histories of SA and SB inside each House;
- evaluate the predicted window representation on slow wind;
- compare source separation against same-source wind separation.

Results:

H02:
- 180 s: raw wind/source ratio 0.293 -> predictive representation 0.157; held-wind identity remains 2/2.
- 240 s: 0.376 -> 0.177; held-wind identity remains 2/2.

H03:
- 120 s: 0.720 -> 0.592; identity 2/2.
- 180 s: 0.663 -> 0.654; identity 2/2.
- 240 s: 0.601 -> 0.544; identity 2/2.

H01 is the counterexample:
- at 120 s raw held-wind identity is 2/2 but predictive representation drops to 1/2.
- at 240 s raw remains 2/2 but predictive representation remains 1/2.
- source contrast is partially collapsed by the generic predictor.

Scientific consequence:
> predictive compression alone is not sufficient. It can suppress transport nuisance while also suppressing source identity.

This counterexample upgrades the necessity of M2 from optional regularization to a distinct auxiliary mechanism:
- M1 should retain only predictively meaningful structure;
- M2 must explicitly preserve persistent source identity across transport contexts;
- destructive wrong-pair and source-permutation controls are mandatory.

This also forbids claiming that any JEPA-style predictor is automatically source-preserving.


## 13. Loop-3 correction: rare-event failure changes Auxiliary A

The H01 counterexample is more fundamental than ordinary cross-transport alignment.

Observed fact:
- H01 source evidence can arrive very late and intermittently (strong threshold crossing only near ~229 s for SA, none for SB in this controlled pair).
- a generic predictive/smoothing proxy can suppress exactly this late source-defining event and reduce held-wind identity from 2/2 to 1/2.

Therefore a pure JEPA/predictive objective is scientifically unsafe for turbulent GSL:
> the least predictable local events may be the most source-informative events.

### New Auxiliary A — Extreme-event-aware intermittency preservation

Primary 2026 remote-domain provenance:
- Nature Communications 2026 — Chang & Sapsis, *Extreme Event Aware (η-) Learning*.
  The method constrains learning with statistics of an observable that characterizes rare/extreme regimes, specifically to avoid fitting only quiescent common behavior while remaining uncertain or wrong in rare regimes.

Supporting turbulence provenance:
- Scientific Reports 2025 — conditional POD for predicting extreme events in turbulent-flow time signals.
- Physical Review Fluids 2026 — latent-space clustering/control of extreme events in turbulent flows.

GSL transfer:
- extreme-event observable -> plume intermittency observable;
- rare event -> source-informative whiff / onset / upper-tail concentration excursion;
- η statistics -> predeclared statistics such as exceedance probability, top-tail mass, onset/first-arrival structure, and burst duration.

This is not a threshold planner. It is a training constraint/auxiliary representation objective that prevents M1 from erasing rare but informative plume events.

### Existing-data η proxy

A fixed source-blind tail-observable vector was appended to the predictable component:
- q95, q99;
- maximum and top-1% mean exposure;
- exceedance fractions at fixed physical floors;
- first arrival at the pre-existing 0.1 ppm threshold.

Key outcomes:

H01, 240 s, 50-sample smoothing:
- predictive-only held-wind identity: 1/2;
- η-tail-only: 2/2;
- predictive + η: 2/2;
- wind/source ratio: predictive 0.861 -> combined 0.212.

H02, 180 s:
- predictive-only: 1/2;
- η-tail: 2/2;
- combined: 2/2;
- ratio approximately 0.889 -> 0.349.

H02, 240 s:
- all retain 2/2;
- combined ratio remains very low (~0.038).

H03, 180 and 240 s:
- predictive-only and combined both retain 2/2.
- η branch is not always lower-ratio than the predictive branch, so the mechanism is complementary rather than a universal replacement.

Interpretation:
- tail/intermittency statistics rescue source evidence precisely where generic predictive compression loses it.
- predictable structure and rare-event structure carry complementary information.

This supports replacing the former “intrinsic identity” Auxiliary A with an extreme-event-aware intermittency branch.

## 14. Loop-3 Auxiliary B — preserved dynamics across environments

The cross-environment problem remains distinct and still needs its own auxiliary mechanism.

2025 top-venue provenance:
- NeurIPS 2025 — Jiang et al., *Extracting task-relevant preserved dynamics from contrastive aligned neural recordings (CANDY)*.
  Learns a shared low-dimensional dynamical representation preserved across recording sessions/subjects while improving cross-session decoding.
- ICLR 2025 — Wu et al., *Neuron Platonic Intrinsic Representation From Dynamics Using Contrastive Learning*.
  Learns time-invariant intrinsic identity from multiple dynamical segments observed under different peripheral conditions.

GSL transfer:
- source = persistent hidden identity;
- wind/House/simulator = peripheral/session condition;
- plume segment dynamics = observed activity segment;
- desired representation = source-relevant dynamics preserved across transport contexts.

Hard restriction from project evidence:
- this alignment cannot be imposed before source support exists.
- it must be reliability/support weighted, because early H02/H03 source effect can be zero or comparable to transport interaction.

## 15. Revised 1+2 candidate

### M1 MAIN — Intrinsic / Preserved Source-Dynamics Representation
Primary anchor: ICLR 2026 Workshop on AI & PDE *Representation Learning for Spatiotemporal Physical Systems* (supporting evidence only; not main-conference provenance).

Main thesis:
> learn the latent physical structure that predicts plume evolution and encodes governing source information, instead of reconstructing the full stochastic plume or directly classifying source from raw samples.

### M2 AUX — Extreme-Event-Aware Intermittency Preservation
Primary anchor: Nature Communications 2026 η-learning.

Role:
> stop the predictive objective from washing out rare source-informative whiffs/bursts.

### M3 AUX — Cross-Context Preserved Source Dynamics
Primary anchors: NeurIPS 2025 CANDY + ICLR 2025 intrinsic dynamics.

Role:
> align the source-relevant dynamical identity across wind/House/simulator contexts after support is present.

### Output
A lightweight source head maps the fused representation to the same PMFS-compatible source-location probability map.

Conformal calibration is demoted to evaluation/deployment reliability tooling, not counted as one of the three innovations.

## 16. Collision status after loop 3

Direct 2025/2026 OSL/GSL search found:
- 2026 diffusion-state classification using UMAP/K-means;
- Scensory 2025/2026 preprint using supervised spatiotemporal neural decoding of short VOC sequences for identity/direction/distance;
- LLM, RL, Mamba, PINN, probabilistic/random-search, multi-robot and plume-patch approaches.

Important collision boundary:
- “spatiotemporal representation learning for olfaction” by itself is no longer novel because Scensory explicitly uses that framing.
- the surviving novelty must therefore be the specific **predictive self-supervised + extreme-intermittency-preserving + cross-context preserved-dynamics** decomposition, evaluated as a source-probability-map inference mechanism across heterogeneous plume datasets.
- no direct JEPA/predictive-latent OSL result was found in the current search.
- no direct η-learning / extreme-event-aware OSL result was found.
- no direct CANDY-style preserved-dynamics cross-transport OSL result was found.

## 17. Current verdict

The previous M1 label “JEPA alone” is too weak.
The stronger candidate is:

**Predictive–Intermittency Representation Learning for Turbulent Source Inference**

with:
- M1 predictive latent physical representation,
- M2 rare/intermittent-event preservation,
- M3 preserved source dynamics across transport contexts.

Status remains OFFLINE FALSIFICATION ONLY.


## 18. Loop-4: preserved-dynamics alignment falsified in its simple form

A fixed held-time proxy was used to test whether explicit cross-wind alignment is safe.

Protocol:
- 120–180 s used only to estimate a same-source fast-minus-slow nuisance direction from fixed 10 s windows.
- 180–240 s used as held time.
- the predictive+tail feature was projected orthogonally to the learned nuisance direction.
- no posterior or localization outcome was used to fit the direction.

Results:
- H01 pair identity: raw 12/12 -> projected 9/12; same-source/cross-source distance ratio 0.212 -> 0.407.
- H02: 10/12 -> 10/12; ratio 0.981 -> 0.977 (essentially neutral).
- H03: 12/12 -> 11/12; ratio 0.305 -> 0.383.

A second context-conditioning proxy that appended local wind to a source-blind next-window predictor did not provide a consistent improvement and generally increased the held-wind/source separation ratio.

Decision:
> direct nuisance removal, global identity alignment, or naive explicit wind conditioning is not supported as Auxiliary B.

This agrees with prior project evidence that candidate-dependent transport effects cannot simply be centered/projection-removed.

Therefore the CANDY / intrinsic-identity idea is retained as literature context but **rejected as a current auxiliary innovation** unless a future mechanism shows an actual positive gate.

## 19. Loop-4 replacement Auxiliary B — structured shift-aware source regions

Recent top-venue provenance:
- ICLR 2025 — *Wasserstein-Regularized Conformal Prediction under General Distribution Shift*.
- ICML 2025 — *Optimal transport-based conformal prediction*.
- ICML 2025 — *Volume Optimality in Conformal Prediction with Structured Prediction Sets*.
- ICML 2025 — *Online Conformal Prediction via Online Optimization*.

Project mechanism:
- PMFS/M1 can become sharply confident while wrong.
- raw physical ordering can be useful while the probability-map adapter degrades truth rank.
- simulator/House/real-sensor shift is a primary intended validation axis.

Scientific transfer:
- the source probability map remains the inference output;
- the auxiliary constructs a **spatially structured source region** from that map with explicit coverage calibration;
- under distribution shift the region expands / abstains rather than converting unsupported confidence into a false point source.

This is more compatible with project evidence than trying to force transport invariance.

Status: ACTIVE AUXILIARY B.

## 20. Current 1+2 after four screening loops

### M1 MAIN — Predictive Self-Supervised Physical Representation
Primary physical-specific anchor:
- ICLR 2026 Workshop on AI & PDE, *Representation Learning for Spatiotemporal Physical Systems* — supporting evidence only, not a top-main-conference anchor.

Main scientific claim:
> source-relevant physical structure should be learned through latent prediction rather than full plume reconstruction or direct raw-signal classification.

### M2 AUX — Extreme-Event-Aware Intermittency Preservation
Primary anchor:
- Nature Communications 2026, *Extreme Event Aware (η-) Learning*.

Why necessary:
- generic predictive compression loses H01-style rare source-defining events.
- fixed tail observables restore held-wind source identity in the existing proxy.

### M3 AUX — Structured Shift-Aware Source Region
Primary anchors:
- ICLR/ICML 2025 conformal-under-shift and structured/OT conformal prediction.

Why necessary:
- project evidence contains confident-wrong posteriors and raw-rank→probability-map degradation.
- cross-dataset robustness requires uncertainty that reacts to shift.

## 21. Current evidence score

Main candidate passes four distinct project checks:

1. **physical support sanity** — predictive representation creates no source identity before support exists.
2. **transport nuisance test** — predictable components are often more source-dominant than innovations after support.
3. **rare-event destructive test** — generic prediction can destroy H01 identity; M2 tail preservation rescues it.
4. **alignment negative control** — simple nuisance removal/alignment worsens H01/H03, preventing an unjustified invariance module.

This is a stronger scientific chain than the previous inverse-generative and causal candidates because it contains both positive and negative discriminators from existing data.

## 22. Remaining kill conditions before promotion

Kill the whole 1+2 if any of the following occurs:
- direct 2025/2026 GSL work already implements predictive self-supervised latent plume learning with rare-event preservation and cross-environment source-map inference;
- a trained lightweight JEPA proxy fails to beat reconstruction/direct-encoding on held wind/source ranking;
- η-style tail preservation only duplicates raw amplitude features and gives no incremental source evidence after a learned predictive encoder;
- structured conformal regions become nearly map-wide under the intended shifts;
- TURB-Smoke and Red:Vapor cannot supply compatible trajectory windows and source labels for the same model interface.



## 23. Provenance correction

Web verification on 2026-09-19 found that Qu et al., *Representation Learning for Spatiotemporal Physical Systems* is associated with the **ICLR 2026 Workshop on AI & PDE**, not the ICLR main conference. It must not be used to satisfy the hard “2025/2026 top-main-venue M1” provenance gate.

Main-conference support for predictive/context representation remains available from adjacent domains (e.g. CVPR 2025 physical-parameter inference and NeurIPS 2025 contextual dynamics), but the physical-specific JEPA anchor is workshop-level. This lowers the provenance score of the JEPA line and reinforces its reserve status behind learned missing physics.


## 23. Loop-5 literature convergence and benchmark correction

### Independent support for the M1 scientific pattern

The predictive-representation thesis is now supported by several independent 2025/2026 lines rather than one paper:

- ICLR 2026 main conference: *Representation Learning for Spatiotemporal Physical Systems* shows latent predictive objectives (JEPA-class) outperform pixel-level reconstruction for downstream estimation of governing physical parameters in active matter, shear flow and Rayleigh–Bénard systems.
- NeurIPS 2025 main conference: *seq-JEPA: Autoregressive Predictive Learning of Invariant-Equivariant World Models* separates invariant and equivariant representations while predicting future latent observations.
- AAAI 2026: AD-L-JEPA applies JEPA self-supervision to noisy sparse LiDAR observations and reports robust downstream detection.
- 2026 ultrasound JEPA work explicitly motivates latent prediction over pixel reconstruction because stochastic acquisition speckle/noise makes raw reconstruction a poor learning target.

These are separate sensing/physics domains with the same transferable principle:
> learn high-level predictive latent structure rather than reproduce stochastic low-level measurements.

Additional biological convergence:
- Nature Neuroscience 2026, *Representational learning by optimization of neural manifolds in an olfactory memory network*, finds that odor discrimination training increases separation of task-relevant odor manifolds and that manifold capacity predicts discrimination behavior.
This does not justify a neural-manifold algorithm by itself, but independently supports the premise that olfactory discrimination quality depends on representation geometry rather than raw response amplitude alone.

### Collision note

A direct 2026 visuo-olfactory self-supervised localization line now exists (*See & Sniff*), and 2026 OSL has unsupervised manifold/state classification.
Therefore the novelty claim cannot be “self-supervised olfactory representation learning”.
The candidate must specifically remain:
1. predictive latent learning from turbulent temporal transport;
2. preservation of rare/intermittent source evidence;
3. conversion to a spatial source-probability map under cross-environment validation.

### Public benchmark correction

TURB-Smoke remains an excellent independent numerical benchmark:
- five distinct point sources;
- fully resolved 3-D Navier–Stokes turbulence;
- Lagrangian trajectories plus coarse concentration fields;
- with and without mean wind.

Red:Vapor is valuable for real sensor dynamics and simulator-to-real transfer, but its published dataset uses a fixed synthetic source outlet across the reported experiments.
Therefore it is **not sufficient by itself for a supervised multi-source localization benchmark**.
Use it for:
- representation transfer;
- sensor/intermittency robustness;
- fixed-source probability-map sanity / uncertainty under real sensor dynamics;
but do not claim multi-source localization generalization from Red:Vapor alone.

The ICASSP 2025 GSL Grand Challenge explicitly asks participants to infer source location and uncertainty from real high-resolution gas+wind samples using separate training/validation settings.
Its exact source-position diversity must be audited from the competition files before treating it as the real multi-source benchmark.

Revised validation ladder:
1. VGR/GADEN — multi-house/multi-wind simulation.
2. TURB-Smoke — independent DNS with five point sources.
3. ICASSP 2025 GSL challenge — real wind-tunnel localization if source-position diversity is confirmed.
4. Red:Vapor — real sensor/plume transfer and dynamic-sensor robustness, not automatically multi-source localization.

## 24. Loop-5 invariant/equivariant factorization probe

A factorial source-vs-wind contrast audit tested whether source and transport are cleanly separable latent factors.

Cosine alignment between source contrast and wind contrast:
- H01: -0.91 at 120 s, +0.65 at 180 s, +0.12 at 240 s.
- H02: -1.00 at 120 s, -0.33 at 180/240 s.
- H03: +0.19 at 120 s, -0.45 at 180 s, -0.50 at 240 s.

Interpretation:
- there is no globally orthogonal source-vs-transport decomposition over the entire mission.
- early observations can make source and transport directions almost collinear.
- a seq-JEPA-style invariant/equivariant split is therefore useful architectural inspiration but **cannot be claimed as a clean physical factorization theorem**.

Decision:
- keep predictive latent representation as M1;
- do not add a fourth “source-invariant / transport-equivariant” contribution;
- M2 rare-event preservation remains the mechanism that has the clearest project-specific positive discriminator.



## 25. Loop-6 window-level held-wind classifier proxy

A small source classifier was used only as an evaluator of representation quality.

Protocol:
- 10 s windows from the existing 12 controlled histories;
- train ridge classifier on fast-wind windows;
- test on slow-wind windows;
- compare raw statistics, predictive temporal statistics, tail/η statistics, and predictive+η.

Same-time held-wind total across H01/H02/H03:
- raw: 52/72 correct;
- predictive: 56/72;
- η-only: 51/72;
- predictive+η: 56/72.

Future-time + held-wind (train fast 120–180 s; test slow 180–240 s):
- raw: 23/36;
- predictive: 26/36;
- η-only: 24/36;
- predictive+η: 26/36.

House-level pattern:
- H02 benefits most from predictive representation (future held-wind 6/12 -> 9/12).
- H03 η-only helps one future-time decision (8/12 raw -> 9/12), while predictive retains 8/12 but with larger positive margins.
- H01 predictive improves same-time held-wind 16/24 -> 18/24 but does not improve the harder future-time count.

Decision:
- M1 receives an additional weak-to-moderate positive proxy.
- fixed η features are **not** a general standalone improvement; M2 remains conditional on implementing the actual η-learning principle as a constraint on the learned representation, not simply appending tail statistics.

## 26. Generic conformal-localization collision and M3 refinement

New collision screen:
- ICASSP 2025 already contains *Conformal Prediction for Manifold-based Source Localization with Gaussian Processes* in acoustic localization.
- AAAI 2026 contains *Conformal Prediction for Multi-Source Detection on a Network* with statistically valid source-set recall guarantees.

Therefore:
> “add conformal prediction to source localization” is not a defensible auxiliary novelty.

M3 is refined to a newer, narrower mechanism:

### M3 — Distribution-Informed Online Calibration of Spatial Source Maps

Primary provenance:
- ICLR 2026 — *Distribution-informed Online Conformal Prediction*.
  It uses predictable structure in the sequence of nonconformity distributions to produce tighter online sets while retaining coverage control even when the distribution estimate is wrong.

GSL-specific transfer:
- PMFS produces a sequential source probability map as evidence arrives;
- map reliability and nonconformity distribution change over time with plume encounter regime, House and sensor dynamics;
- M3 updates a spatial source region online from the evolving map rather than applying one static post-hoc calibration threshold.

Novelty boundary:
- no claim that conformal localization itself is new;
- the proposed auxiliary would be the **online distribution-informed calibration of a sequential turbulent-source probability field under regime shift**.

Status:
- M3 = CONDITIONAL SURVIVOR; requires a source-map replay with sequential calibration before final promotion.


## 23. Loop-5 direct GSL collision screen

A direct 2025/2026 search was run for:
- JEPA / joint-embedding predictive architecture in gas or odor source localization;
- self-supervised predictive plume representations;
- contrastive source representation learning;
- predictive coding for electronic-nose source localization.

Found nearby work:
- 2026 odor diffusion-state classification using UMAP + K-means on multi-directional sensors; this is unsupervised state clustering, not predictive latent source inference.
- 2025/2026 electronic-nose drift work using contrastive/domain-adaptation objectives; these address sensor calibration drift, not turbulent source probability maps.
- 2025 Robotic OSL with LLMs; unrelated paradigm.
- older eLife turbulent-plume target prediction ranks hand-designed intensity/intermittency features, which makes plain “use intermittency” non-novel but does not implement predictive self-supervised representation learning.

No direct 2025/2026 GSL/OSL paper was found that combines:
1. source-blind latent prediction on plume histories,
2. extreme-event-aware preservation of rare plume evidence, and
3. a PMFS-compatible source probability map under cross-environment shift.

Novelty boundary is therefore narrowed to that combination and its mechanism tests.
The contribution must not be described generically as “spatiotemporal representation learning for olfaction”.

## 24. External physical-science support beyond ML venue papers

Independent physical-science evidence also supports the premise that sparse observations can reveal governing dynamics without reconstructing every realized detail:
- Nature Communications 2025: Zhai, Stern & Lai reconstruct unseen nonlinear dynamics from one-time sparse observations using a transformer trained on different synthetic systems.
- Nature Machine Intelligence 2025: differentiable sparse-field reconstruction emphasizes the ill-posed nature of inferring high-dimensional physical fields from sparse sensors.
- Nature Machine Intelligence 2026 News & Views: state-first inverse design argues for learning physically meaningful intermediate states rather than direct inverse maps.

These works support the scientific motivation but are not counted as direct novelty provenance for M1.

## 25. Reviewer-risk note

The strongest reviewer attack on the current M1 is now clear:

> “Why is JEPA/predictive representation necessary rather than a generic temporal encoder plus hand-engineered intermittency statistics?”

Required answer before promotion:
- trained predictive objective must beat an architecture-matched autoencoder/reconstruction objective and a direct supervised encoder on held transport;
- M2 must show incremental benefit beyond raw whiff/intermittency features;
- predictive-target time permutation must destroy the M1 benefit;
- rare-event permutation/truncation must specifically destroy the M2 benefit.

Until those gates are run, the candidate stays provisional.


## 27. Loop-7 stronger predictive-vs-reconstruction falsification

A linear latent-prediction baseline was built to test the core M1 claim against an architecture-matched reconstruction baseline.

Protocol:
- source labels were not used to learn either representation;
- 5 s past log-concentration windows predicted the next 5 s;
- training used both sources under fast wind;
- predictive subspace = leading eigenvectors of C_xy C_yx (future-predictive PLS/PSR proxy);
- reconstruction subspace = leading eigenvectors of C_xx (PCA proxy);
- held evaluation used slow-wind windows;
- source identity was evaluated only after the unsupervised subspaces were frozen.

Results, latent dimension 4:
- H01: PRED 0.607 accuracy, PCA 0.607; mean margins essentially identical.
- H02: PRED 0.598, PCA 0.598; margins essentially identical.
- H03: PRED 0.750, PCA 0.750; margins essentially identical.

Dimension sweep k=1,2,3,4,6:
- no reproducible predictive advantage over PCA.
- H03 k=1 has a tiny accuracy edge (0.768 vs 0.759), but H01 k=1 is slightly worse and H02 is identical.
- the two subspaces become nearly equivalent because the dominant variance modes in these short controlled traces are also the dominant linearly predictable modes.

Decision:
> the present evidence does **not** justify “predictive latent learning beats reconstruction” as a validated mechanism.

This is a hard downgrade of the current M1.

The earlier moving-average and classifier proxies showed that predictive structure can be useful, but the stronger matched linear comparison fails to separate the predictive objective from generic reconstruction.

### Revised status

- Predictive/JEPA M1: CONDITIONAL / NOT YET PRIMARY.
- It may survive only if a nonlinear masked-prediction model produces a mechanism-specific gain that survives architecture-matched autoencoding and direct supervised baselines.
- Because this would require a new trained-model experiment rather than a clear existing-data premise, the search loop must reopen for alternative M1 paradigms with stronger evidence on current data.



## 23. Loop-5: broaden M1 from JEPA architecture to Predictive Coding as the mother paradigm

### 2025 scientific-theory provenance

A 2025 Trends in Cognitive Sciences review, *Predictive Coding in the Human Olfactory System* (Lyons & Gottfried), develops predictive coding specifically as a unifying theory of olfaction:
- higher-level internal models issue predictions before sensory input arrives;
- sensory input is evaluated through prediction error rather than passive stimulus-response processing;
- prediction precision/context determines how much an error should influence belief;
- olfactory perception is described in terms of predictions, prediction errors, precision and predictive maps.

A second 2025 Trends in Cognitive Sciences review, *Predictive coding: a more cognitive process than we thought?*, highlights an important caveat: prediction-error-like responses alone do not prove the canonical neural mechanism. The transferred object must therefore be the **prediction/prediction-error inference principle**, not a biological-circuit claim.

### 2026 machine-learning realization

- ICLR 2026, *Representation Learning for Spatiotemporal Physical Systems*, shows that latent predictive objectives (JEPA-class) can yield representations better suited to governing-parameter estimation than pixel-level reconstruction.
- ICLR 2026, *Rethinking JEPA*, provides a simpler compute-efficient masked-latent realization.
- ICML 2025 M3-JEPA and NeurIPS 2025 latent-predictive work supply additional implementation support.

Revised hierarchy:
- mother paradigm = predictive coding / predictive processing;
- M1 computational realization = lightweight latent predictive representation;
- JEPA is an implementation family, not the paper-level scientific idea.

### GSL translation

For each source hypothesis s, robot history h_t induces an internal predictive state z_t(s).
The central evidence object becomes a source-conditioned predictive discrepancy:

    e_t(s) = d( z_target(y_{t:t+Δ}), g(z_context(h_t), s) )

The source map should accumulate evidence from which source-conditioned internal model best predicts future observation structure, instead of comparing only instantaneous concentration compatibility.

This retains the PMFS output while changing the semantics of evidence:
- old: “does the current measurement look compatible with source s?”
- new: “does source s support a predictive internal model that anticipates the next sensory state?”

### Offline source-conditioned AR proxy

To test whether source-specific prediction error contains source identity across transport changes, a simple candidate-specific autoregressive proxy was fit:
- train one AR model per source using the fast-wind trace;
- evaluate one-step log-concentration prediction error on the slow-wind trace;
- choose the source model with lower predictive error.

Results:
- H01: 2/2 correct for 120–180 s, 180–240 s and 120–240 s across lags 5/10/25.
- H02: 2/2 correct in all windows/lags; large margin appears specifically in the source-exposed window.
- H03: 2/2 correct at 120–180 s, but degrades to 1/2 in 180–240 s and the full 120–240 s window.

Interpretation:
- source-conditioned prediction error is a genuine source cue in H01/H02 and early H03;
- it is not universally stable under late H03 transport variation;
- this prevents a simplistic “prediction error alone solves GSL” claim.

This directly motivates M2:
> predictive coding must be made intermittency/extreme-event aware, because source-relevant rare plume structure can make ordinary prediction error unstable.

Status of M1 after loop-5:
- predictive coding = stronger paper-level mother idea than “JEPA”.
- latent prediction remains the lightweight implementation path.
- candidate survives, but requires M2 to pass H03/rare-event robustness rather than hiding that failure.


## 24. Loop-6: predictive evidence vs static observation model

A stricter comparator was added to test whether the predictive-coding premise is doing anything beyond static amplitude matching.

Protocol:
- training condition: fast-wind trace for each source;
- held condition: slow-wind trace;
- static baseline: per-source i.i.d. Gaussian log-concentration model;
- predictive baseline: per-source AR(10) one-step model;
- score: average held-window negative log likelihood under each candidate source model.

Results:

H01:
- 120–180 s: static 2/2, predictive 2/2.
- 180–240 s: static 2/2, predictive 2/2.
- no unique predictive advantage in this House.

H02:
- 120–180 s: both 2/2.
- 180–240 s: both 1/2.
- 120–240 s: both 2/2.
- predictive modeling does not rescue the late H02 low-support ambiguity.

H03:
- 120–180 s: static model fails 0/2 while predictive model succeeds 2/2.
- 180–240 s: static 1/2, predictive 0/2.
- 120–240 s: both 1/2.

Interpretation:
1. There is at least one real regime (H03 120–180 s) where source identity exists in temporal predictive dynamics while static distributional/amplitude matching gives the wrong source for both held-wind cases.
2. Predictive evidence is not universally better; late H03 reverses.
3. This is exactly the kind of non-monotone failure that requires an intermittency/extreme-event-aware auxiliary rather than claiming prediction error alone is sufficient.
4. The result strengthens Predictive Coding as a scientifically distinct M1 over generic representation learning, because the discriminating object is **candidate-specific prediction error across time**, not merely an embedding.

Current M1 premise:
- PASS as a mechanism candidate;
- NOT sufficient alone;
- M2 remains load-bearing.



## 25. Loop-7 collision refinement: old odor-dynamics work narrows M2 novelty

A direct precedent must be treated as a hard boundary:

- Rigolli et al., eLife 2022, *Learning to predict target location with turbulent odor plumes*:
  - uses high-resolution turbulent odor simulations;
  - explicitly compares intensity vs timing/intermittency features for source-location prediction;
  - shows that timing and intensity are complementary;
  - finds timing becomes more useful in sparse/dilute regimes;
  - combines intensity/timing features for robust prediction.

Therefore the following are NOT novel enough for this project:
- “use whiff/blank/intermittency features”;
- “combine timing and intensity features”;
- “rare plume events contain source information”;
- a hand-designed tail-feature branch by itself.

What remains potentially novel in M2 is the **2026 η-learning mechanism**:
> constrain the learned predictive representation with statistics of a predeclared extremeness/intermittency observable so that rare source-relevant regimes are preserved even when underrepresented in the training set.

Thus the existing tail-feature proxy is only a mechanism screen. Final M2 must alter the training objective/distribution, not merely concatenate old odor statistics.

## 26. Loop-7 collision refinement: Predictive Coding vs ordinary target prediction

The 2022 eLife precedent predicts target location from hand-designed odor features. It does NOT implement the current M1 object:
- source-conditioned internal prediction;
- latent prediction of future sensory structure;
- source evidence defined by candidate-specific prediction error;
- self-supervised physical representation before source supervision.

The distinction is therefore:

Old:
    odor statistics -> supervised target coordinate

Candidate M1:
    history -> latent predictive state
    candidate source -> predicted future latent
    observed future latent - predicted future latent -> source evidence
    accumulated evidence -> PMFS-compatible source probability map

This difference must survive ablation:
- if a supervised timing/intensity feature regressor matches the proposed M1 on held environments, the M1 novelty/mechanism claim is weakened.

## 27. Public-data qualification

### VGR/GADEN
- 120 gas-dispersion cases across 30 realistic house models.
- appropriate for cross-house/cross-condition training and held-environment tests.

### TURB-Smoke (Scientific Data 2026)
- fully resolved 3-D DNS;
- five distinct point sources;
- zero/intermediate/strong mean-wind cases;
- Lagrangian particle trajectories plus 2-D/3-D coarse-grained concentration fields.
- suitable for generating source-blind mobile trajectories and testing whether the learned predictive representation transfers from GADEN/RANS-style data to DNS turbulence.

### Red:Vapor (Scientific Data 2026)
- real wind-tunnel plume data in a complex scale-model landscape;
- 8 dense raster scans, 22 fly-through experiments, 9 purge runs;
- multiple real gas sensors plus environmental measurements.
- suitable for simulator-to-real and sensor-dynamics shift.

Hard rule:
The three-module method may not require a privileged dense CFD field at deployment; all deployable inputs must be derivable from sparse/mobile time series and available local context.

## 28. Independent review lenses (not external reviewers)

The current candidate is evaluated independently from four domain perspectives:

1. Olfactory neuroscience / predictive processing
   - positive: 2025 Trends in Cognitive Sciences explicitly proposes predictive coding as a unifying theory of olfaction.
   - caveat: biological circuit claims are not transferable; only prediction/error/precision semantics are.

2. Scientific ML / physical representation learning
   - positive: ICLR 2026 physical-system study supports latent predictive representations for governing-parameter estimation.
   - caveat: JEPA is implementation, not novelty by itself.

3. Turbulence / rare-event modeling
   - positive: Nature Communications 2026 η-learning supplies a modern mechanism for preserving underrepresented extreme regimes.
   - caveat: old plume literature already uses whiff/blank/timing statistics, so M2 must be a training principle, not a feature list.

4. Robotic GSL / deployability
   - positive: current searches found supervised spatiotemporal decoding, manifold state classification, PINN/RL/Bayesian/random-search methods, but no direct predictive-coding + η-learning source-map pipeline.
   - caveat: recent Advanced Materials 2026 AROMA and Scensory show that temporal plume dynamics are already an active localization direction; our novelty cannot be “temporal neural decoding”.

Consensus status:
- M1 predictive-coding semantics: 4/4 lenses see a defensible scientific role.
- M2 η-learning: 3/4 positive, with novelty conditional on objective-level implementation rather than hand-crafted features.
- M3 structured shift-aware source regions: 3/4 positive; empirical feasibility still untested with sufficient independent calibration cases.

No GO decision yet.


## 29. Loop-8: M3 upgraded to 2026 structured/adaptive conformal source areas

Newer 2026 top-venue support strengthens the uncertainty auxiliary:

- ICLR 2026 — *JAPAN: Joint Adaptive Prediction Areas with Normalising Flow*.
  - constructs compact, potentially disjoint, context-adaptive prediction areas;
  - retains finite-sample conformal coverage;
  - specifically targets multimodal predictive geometry where simple residual balls/convex regions are inefficient.

- ICLR 2026 — *Distribution-informed Online Conformal Prediction*.
  - incorporates predictable score-distribution structure into online conformal updating;
  - retains valid coverage while avoiding overly conservative sets under evolving distributions.

- ICLR 2026 — robust conformal methods under corrupted labels / covariate shift provide additional evidence that calibration can be adapted to non-i.i.d. deployment conditions.

Revised M3:
> **Adaptive Structured Conformal Source Areas**

Mapping:
- model output = spatial source probability map;
- nonconformity = probability/density/rank score attached to candidate source cells;
- conformal set = a compact, potentially disconnected spatial region of plausible sources;
- online/shift-aware update = calibration adapts as House/simulator/sensor distribution changes.

Why this is a better auxiliary than generic confidence calibration:
- GSL posteriors can be multimodal because obstacles/transport create several plausible source regions;
- a single radius/ellipse is physically inappropriate;
- disconnected conformal source areas preserve the map's geometry while attaching a statistical reliability layer.

Existing project limitation:
- the repository does not currently expose enough independent full per-case source maps on the research branch to run a valid conformal coverage study without pretending time samples are independent.
- therefore M3 receives literature/architectural PASS but empirical calibration remains PENDING until independent maps/cases are assembled.

Status M3: STRONG AUXILIARY CANDIDATE / EMPIRICAL PENDING.

## 30. Current evidence-backed architecture after eight loops

M1 MAIN:
**Predictive Coding for Turbulent Source Inference**
- scientific mother idea: predictive coding / predictive processing;
- latest physical-ML realization: latent predictive representation learning (ICLR 2026);
- evidence object: candidate-specific prediction error / predictive latent compatibility.

M2 AUX:
**Extreme-Event-Aware Intermittency Preservation**
- scientific source: η-learning, Nature Communications 2026;
- role: prevent M1 from fitting common/quiescent dynamics while erasing rare source-defining plume events;
- final mechanism must regularize the learned representation with extremeness statistics, not simply concatenate old whiff/blank features.

M3 AUX:
**Adaptive Structured Conformal Source Areas**
- source: ICLR 2026 structured/adaptive conformal prediction;
- role: turn the PMFS-compatible probability map into a calibrated, possibly disconnected source region under dataset/environment shift.

Current hierarchy:
- M1 supplies the paper-level main narrative.
- M2 repairs a demonstrated failure of M1 on rare/intermittent evidence.
- M3 repairs reliability under distribution shift without changing the source inference core.



## 31. Loop-9 destructive temporal control: simple AR proxy is NOT sufficient evidence

A time-order destructive control was run on the source-conditioned AR proxy:
- forward slow-wind trace;
- fully time-reversed held window;
- 5 s block-reversed held window.

Result:
- source ranking was largely unchanged under reversal in H01/H02 and in the informative H03 120–180 s window.
- prediction error magnitude often increased, but candidate ranking often survived.

Decision:
> the simple AR result is partly driven by source-specific amplitude/distribution structure and does NOT by itself establish a load-bearing temporal predictive mechanism.

Therefore the AR proxy is downgraded from positive mechanism evidence to a weak sanity check.

### Stronger existing evidence already in the repository

The frozen CTT H01 audit provides a substantially cleaner temporal premise:

Native 0.2 s first-passage observable over 1280 leave-one-transport-member-out cases:
- full first-passage mean normalized rank = 0.1417109;
- survival-only = 0.2564070;
- TIME-PERMUTE = 0.1573191;
- phase-label shuffle = 0.3040221;
- full vs survival: 788 wins / 283 losses / 209 ties, p = 6.56e-56;
- full vs TIME-PERMUTE: 346 / 175 / 759, p = 2.84e-14;
- full vs phase-label shuffle: 781 / 322 / 177, p = 7.69e-45.

This establishes that **native temporal phase / first-passage structure is genuinely source-informative**.

Equally important, the same audit contains a negative result:
- compressing 80 native samples into eight coarse HIT bits destroys the phase mechanism;
- multiple small neural first-passage surrogates failed to preserve the native temporal source information under held conditions.

Scientific implication for M1:
> the problem is not merely to “use temporal prediction”; it is to learn a latent predictive representation that preserves native source-relevant phase while avoiding reconstruction of stochastic detail.

This is a much better match to the ICLR 2026 physical-representation result than the AR toy proxy:
- full low-level reconstruction is unnecessary/fragile;
- coarse event compression loses source information;
- the desired object is a compact latent predictive state that retains governing/source-relevant temporal structure.

Scientific implication for M2:
> η-learning-style rare/intermittent constraints should be evaluated specifically by whether they preserve the CTT-native phase advantage under compression, not by whether they reproduce old whiff/blank features.

Revised evidence status:
- M1 literature foundation: STRONG.
- M1 physical premise from native temporal data: STRONG.
- M1 current learned realization: UNVALIDATED.
- M2 rationale: STRONG, because learned surrogates demonstrably lose rare/phase information.
- M3: literature STRONG, empirical PENDING.



## 32. Loop-10 window-level comparison against classical odor-dynamics features

A fixed 20 s matched-time held-wind diagnostic was run over 120–240 s.
For each slow-wind source window, the representation was compared with the same-time fast-wind windows of SA and SB.

Representations:
1. ELIFE_LIKE: approximate classical odor-dynamics features (whiff intensity, slope, blank/whiff duration, intermittency), motivated by Rigolli et al. 2022.
2. PRED: source-blind future-summary predictor from the first 10 s to the next 10 s.
3. ETA: fixed rare/intermittent tail-observable vector.
4. PRED+ETA: concatenation.

Diagnostic decisions (not independent replications):

H01, 12 source-window decisions:
- ELIFE_LIKE: 2/12
- PRED: 7/12
- ETA: 9/12
- PRED+ETA: 9/12

H02:
- ELIFE_LIKE: 5/12
- PRED: 6/12
- ETA: 7/12
- PRED+ETA: 7/12

H03:
- ELIFE_LIKE: 12/12
- PRED: 10/12
- ETA: 12/12
- PRED+ETA: 12/12

Aggregate diagnostic:
- ELIFE_LIKE: 19/36
- PRED: 23/36
- ETA: 28/36
- PRED+ETA: 28/36

Interpretation:
- predictive structure outperforms this classical-feature proxy in H01/H02 but not H03.
- η-style tail/intermittency observables are the strongest simple proxy overall.
- importantly, PRED+ETA does not improve over ETA alone in this handcrafted diagnostic.

Consequence:
> the current data do NOT yet establish incremental value of M1 over M2 in a simple feature space.

This is a critical non-promotion result. The paper cannot become “η features + predictive branding”.
M1 must demonstrate a unique gain on the CTT-native phase/predictive-state task or on an independent dataset where tail statistics alone are insufficient.

New hard M1 gate:
- compare a learned latent-predictive encoder against classical timing/intensity features, η-only constrained representation, and reconstruction/self-encoding baselines;
- require incremental held-context source rank / calibration gain that disappears under destructive target-time permutation.

Until then:
- M1 = PROMISING BUT NOT VALIDATED
- M2 = STRONG MECHANISM CANDIDATE
- M1+M2 SYNERGY = NOT YET ESTABLISHED


## 33. Loop-12: conformal auxiliary rejected; replace with anytime-valid sequential evidence candidate

### Conformal collision — reject as innovation slot

Direct recent precedents make generic conformal source regions too close to existing source-localization work:
- AAAI 2026 — Jian et al., *Conformal Prediction for Multi-Source Detection on a Network*: statistically valid source-set detection with calibrated coverage/recall.
- ICASSP 2025 — Rozenfeld & Laufer Goldshtein, *Conformal Prediction for Manifold-based Source Localization with Gaussian Processes*: conformal prediction intervals for source localization across acoustic conditions.

Decision:
> conformal calibration may remain an evaluation/deployment baseline, but it no longer qualifies as Auxiliary Innovation 3.

### New Auxiliary-3 candidate — Game-Theoretic Anytime-Valid Source Evidence

Remote-field provenance:
- NeurIPS 2025 — Kilian, Cortinovis & Caron, *Anytime-valid, Bayes-assisted, Prediction-Powered Inference*: prediction-powered confidence sequences valid uniformly over time.
- JRSSB 2026 — Koning & van Meer, *Anytime validity is free: inducing sequential tests*: classical terminal tests can be converted into anytime-valid sequential tests, valid under data-dependent stopping.
- JRSSB 2026 — Choe & Ramdas, *Combining evidence across filtrations*: e-processes quantify accumulated evidence against composite hypotheses at arbitrary stopping times and can be combined across different information filtrations with validity corrections.

Mother idea:
> In sequential inference, evidence should be accumulated by a process whose validity survives continuous monitoring and adaptive stopping, rather than by repeatedly multiplying correlated compatibility scores as if every propagated quantity were independent evidence.

### Why this maps to PMFS

Existing project facts already identify the relevant failure mode:
- native PMFS multiplies cell-wise compatibility factors, but those factors are not established calibrated observation likelihoods;
- one physical observation can affect multiple map cells, so multiplying cell contributions can recount correlated evidence;
- the failure-first audit explicitly warns that repeated map propagation may change posterior odds without a new sensor event;
- in the 30-case CPIR audit, A0 becomes more confident while true-source ranking worsens: entropy 3.27 -> 1.57, max posterior 0.19 -> 0.46, while mean normalized true-source rank changes 0.720 -> 0.767.

### Candidate role

M1 would provide one candidate-conditioned predictive score/residual per distinct sensor event.
M3 would convert/accumulate those event-level scores using an anytime-valid evidence process, so that:
- each distinct physical observation enters once;
- adaptive stopping does not invalidate the evidence threshold;
- map contraction/elimination is authorized only by accumulated valid sequential evidence;
- spatial propagation may redistribute an event spatially but may not multiply its evidential mass as independent observations.

The final output remains a source-location probability map. The e-process/test-martingale object is an auxiliary gate/weight on source-evidence accumulation, not a replacement output.

### Hard validity warning

No valid e-process has yet been constructed for PMFS.
A product of arbitrary predictive scores is NOT automatically an e-process.
The next gate must identify the event-level filtration and a betting/likelihood-ratio factor with the required conditional expectation bound under each candidate-source null. If this cannot be established, this candidate is rejected rather than renamed.

### Collision screen

Current exact searches for e-process / anytime-valid gas- or odor-source localization returned no direct matching source-localization method. This is only a positive novelty signal, not proof of novelty.

Status: M3 CONFORMAL = REJECTED AS INNOVATION; GAME-THEORETIC ANYTIME-VALID EVIDENCE = ACTIVE CANDIDATE / THEORY QUALIFICATION REQUIRED.


## 34. Loop-14: direct M1+M2 additive synergy test — NO-GO for naive fusion

Date: 2026-09-20

A fixed candidate-specific predictive score and a fixed η-style intermittency score were evaluated on the same 12 controlled histories.

Protocol:
- train/reference condition = fast wind;
- held condition = slow wind;
- windows = 120–180 s, 180–240 s, 120–240 s;
- M1 proxy = per-source AR(10) predictive negative log likelihood on log concentration;
- M2 proxy = fixed tail/intermittency distance using q95, q99, max, top-1% mean, exceedance fractions, and first arrival;
- naive fusion = equal-weight standardized sum of the two candidate scores;
- no localization output or truth-conditioned parameter tuning was used.

Results:
- H01: predictive 2/2, η 2/2, fusion 2/2 in all three windows.
- H02: all methods 2/2 in 120–180 and 120–240; all remain 1/2 in the low-support 180–240 window.
- H03 120–180: all 2/2.
- H03 180–240: predictive 1/2, η 1/2, fusion 1/2.
- H03 120–240: predictive 1/2, η 2/2, but naive equal-weight fusion falls back to 1/2.

Decision:
> M1+M2 synergy is NOT established by simple score concatenation or equal-weight fusion.

Important implication:
- M2 cannot be a bolt-on tail-feature branch whose score is simply added to predictive error.
- the η-learning paper's actual scientific mechanism is training-time distributional regularization of the learned model/representation; the next valid test must implement that mechanism directly.
- H03 provides a hard negative case: when predictive and rare-event evidence disagree, arbitrary fusion can destroy the correct rare-event signal.

Current closed-loop status after Loop-14:
- MAIN_CANDIDATE = Predictive Coding / latent predictive physical representation.
- AUX_2 = η-learning-style extreme-event-aware representation regularization.
- AUX_3 = game-theoretic anytime-valid event evidence, theory qualification pending.
- LEARNED_M1_REALIZATION = UNVALIDATED.
- M1_PLUS_M2_INCREMENT = NOT YET ESTABLISHED.
- CLOSED_LOOP_AUTHORIZATION = NO.

Next decisive experiment:
1. train a lightweight source-blind latent predictive encoder on existing histories;
2. compare plain predictive loss vs η-regularized predictive loss using identical encoder/head capacity;
3. evaluate candidate-source rank on held wind and destructive target-time permutations;
4. require η-regularization to rescue the H03/H01 rare-event failures without harming supported H02/H03 regimes;
5. only after this passes, construct the event-level predictive score needed to test the anytime-valid M3.



## 23. Loop-5 provenance correction and stronger intrinsic-dynamics proxy

### Provenance correction

The prior document over-promoted the 2026 physical-representation paper. It is published at the **ICLR 2026 Workshop on AI & PDE**, not the ICLR main conference. It is retained only as supporting evidence that latent prediction can preserve physical parameters better than pixel reconstruction in several physical systems.

The main top-venue provenance is therefore shifted to the 2025 preserved/intrinsic-dynamics line:

1. **ICLR 2025** — Wu et al., *Neuron Platonic Intrinsic Representation From Dynamics Using Contrastive Learning*.
   - treats each neuron as a dynamical system observed under different peripheral conditions;
   - learns a time-invariant intrinsic representation from multiple segments;
   - same-system segments should be closer than different-system segments;
   - emphasizes out-of-domain generalization.

2. **NeurIPS 2025 Spotlight** — Jiang et al., *Extracting task-relevant preserved dynamics from contrastive aligned neural recordings (CANDY)*.
   - aligns high-dimensional recordings from different sessions into a shared low-dimensional space;
   - fits preserved latent dynamics;
   - improves cross-session decoding and generalizes to new sessions/subjects.

3. **CVPR 2025** — Astruc et al., *AnySat*.
   - JEPA-based self-supervision across heterogeneous Earth-observation sensors/resolutions;
   - supports the use of latent predictive objectives for heterogeneous environmental sensing, but is not the main scientific source.

### Revised main thesis

> A fixed gas source should be represented by a persistent dynamical identity that survives changes in transport context, while source inference should be based on this preserved dynamics rather than on raw plume realizations.

This is stronger and more defensible than “JEPA for GSL”.

### Held-time intrinsic-metric proxy

A second offline test was run on the existing 12 controlled histories.

Protocol:
- 10 s windows;
- features include log-concentration moments, upper quantiles, hit fraction, short-lag autocorrelation, derivative energy and mean wind magnitude;
- 120–180 s is used to learn feature weights that maximize source separation relative to within-source variation across fast/slow winds;
- 180–240 s is held out in time;
- no localization outcome is used for fitting.

Results:

- **H01**:
  - uniform metric: 10/12 held-time same-source pair decisions, mean margin 0.186;
  - source-intrinsic metric: 10/12, margin 0.217;
  - transport-label destructive control: 9/12, margin 0.212.

- **H02**:
  - uniform: 8/12, margin 0.101;
  - source-intrinsic metric: 8/12, margin 0.112;
  - transport control: 8/12, margin 0.058.

- **H03**:
  - uniform: 11/12, margin 0.409;
  - source-intrinsic metric: 11/12, margin 0.561;
  - transport control: 11/12, margin 0.361.

Interpretation:
- the simple source-stability weighting does not improve discrete accuracy, so this is **not a PASS for the final method**;
- however it increases held-time source margin in all three Houses;
- the transport-label control does not reproduce the margin gain, especially in H02/H03;
- this is positive evidence that a source-specific preserved representation is a meaningful target, but a learned nonlinear model is still required.

This result is materially stronger than the earlier nuisance-projection test, which worsened H01/H03. It suggests that “preserve source identity” is more promising than “remove wind nuisance”.

## 24. Revised architecture candidate after provenance audit

### M1 — Intrinsic / Preserved Source-Dynamics Representation
Remote sources:
- ICLR 2025 intrinsic dynamical identity;
- NeurIPS 2025 Spotlight preserved dynamics across sessions.

GSL translation:
- source location = persistent latent system identity;
- wind / turbulence / House / simulator = peripheral recording context;
- gas/wind history segments = observations of the same hidden dynamical identity.

### M2 — Extreme-Event-Aware Intermittency Preservation
Remote source:
- Nature Communications 2026, *Extreme Event Aware (η-) Learning*.

Reason:
- a generic preserved/predictive representation can erase late rare whiffs that are source-defining;
- fixed tail/arrival statistics already rescued H01/H02 proxy failures.

### M3 — Multiscale Partial-Observability Memory
Remote source:
- NeurIPS 2025, *Predicting partially observable dynamical systems via diffusion models with a multiscale inference scheme*.

Transferred principle:
- when the current observation sees only a small fraction of the hidden state, fine recent history and progressively coarser long history can preserve long-range dependencies at controlled computational cost.

GSL role:
- recent plume events retain fine timing;
- older history is compressed more coarsely;
- this supplies M1 with long-memory context without a full recurrent world model or full plume reconstruction.

Structured conformal calibration is retained as an evaluation/reliability layer, not counted among the three innovations unless the multiscale module later fails.

## 25. Current status after loop 5

Current strongest 1+2 candidate:

**Main:** intrinsic/preserved source dynamics (ICLR 2025 + NeurIPS 2025 Spotlight)  
**Aux 1:** extreme-event-aware intermittency preservation (Nature Communications 2026)  
**Aux 2:** multiscale memory for partially observable dynamics (NeurIPS 2025)

This combination now satisfies the requested venue standard more cleanly than the earlier JEPA-only framing.

Still OFFLINE FALSIFICATION ONLY.


## 26. Loop-6 multiscale partial-observability proxy

The NeurIPS 2025 multiscale partial-observability idea was tested with a fixed equal-dimensional history representation.

Protocol:
- compare 12 uniform history bins against 12 multiscale bins;
- multiscale bins allocate finer resolution to the latest 60 s, medium resolution to the previous 60 s, and coarse resolution to older history;
- no source labels, no outcome tuning.

Results:

H02:
- 180 s wind/source ratio: 0.055 (uniform) -> 0.029 (multiscale), both 2/2 held-wind identity.
- 240 s: 0.029 -> 0.033, no improvement.

H03:
- 180 s: 0.289 -> 0.251, both 2/2.
- 240 s: 0.392 -> 0.427, worse.

H01:
- 180 s: 0.339 -> 0.330, small improvement.
- 240 s: 0.146 -> 0.212, worse.

At 120 s, H02 remains non-identifiable under both representations.

Decision:
> the multiscale partial-observability principle is useful as an implementation option, but the current evidence does not support it as a stable auxiliary innovation.

Status M3-multiscale: DEMOTED.

## 27. Auxiliary B restored to structured shift-aware uncertainty

Because the multiscale-memory proxy is mixed, the stronger third contribution candidate returns to:

**Structured shift-aware source-region calibration**

Top-venue provenance:
- ICLR 2025 — *Wasserstein-Regularized Conformal Prediction Under General Distribution Shift*.
- ICML 2025 — *Volume Optimality in Conformal Prediction with Structured Prediction Sets*.
- NeurIPS 2025 — *Conformal Prediction for Time-series Forecasting with Change Points*.

Why this survives the project evidence better:
- it does not assume transport nuisance can be removed;
- it does not create source information before support exists;
- it directly addresses the documented confident-wrong posterior failure;
- it is naturally lightweight and can be attached to any source probability map.

Current auxiliary ranking:
1. M2 extreme-event-aware intermittency preservation — STRONG.
2. M3 structured shift-aware source region — STRONG.
3. multiscale partial-observability memory — RESERVE IMPLEMENTATION IDEA ONLY.


## 28. Loop-7: temporal-transformation auxiliary from CVPR 2026

A newer top-conference idea was screened as a replacement for the mixed multiscale-memory auxiliary.

Remote-domain provenance:
- **CVPR 2026 — TimeBridge: Self-Supervised Video Representation Learning via Start-End Joint Embedding and In-Between Frame Prediction**.
  - learns temporal transformations rather than only static frame identity;
  - uses start/end representations plus prediction of the in-between evolution;
  - explicitly targets temporal consistency and lightweight decoding.

GSL translation:
- start/end gas states alone may be ambiguous;
- the **shape of the transition between them** can contain source-dependent transport information;
- a lightweight bridge head should encode the in-between temporal evolution without reconstructing the full plume field.

### Existing-data bridge proxy

For each held 180–240 s segment:
- split into fixed 5/10/20 s windows;
- represent endpoints separately;
- compute the residual temporal shape relative to linear start-end interpolation (“bridge” feature);
- compare source separation against same-source wind separation.

Key results:

**H02**
- 5 s windows:
  - endpoint-only: wind/source ratio 1.014, held-wind identity 1/2;
  - bridge-only: ratio 0.536, identity 2/2;
  - endpoint+bridge: ratio 0.582, identity 2/2.
- 10/20 s bridge windows do not help, indicating a short-timescale effect.

**H03**
- 5 s:
  - endpoint-only ratio 0.602, identity 1/2;
  - bridge-only ratio 0.462, identity 2/2.
- 10 s:
  - endpoint-only ratio 0.792, identity 1/2;
  - bridge-only ratio 0.309, identity 2/2.
- 20 s:
  - endpoint-only ratio 0.769, identity 1/2;
  - bridge-only ratio 0.450, identity 2/2.

**H01**
- bridge features remain 2/2 at all tested widths;
- at 20 s the bridge ratio improves from endpoint 0.210 to 0.091.

Interpretation:
- temporal transition shape contains source information not present in endpoints alone;
- the effect is strongest at short windows in H02/H03 and a longer window in H01;
- this is consistent with the project's earlier first-passage/timing evidence;
- the timescale is environment-dependent, so the final module must not hard-code one window.

Status:
**Temporal bridge / transformation representation = STRONG AUXILIARY CANDIDATE.**

## 29. Revised auxiliary ranking after loop 7

1. **M2 Extreme-event-aware intermittency preservation** — strong, supported by Nature Communications 2026 and existing H01/H02 rescue tests.
2. **M3 Temporal bridge representation** — strong, supported by CVPR 2026 and positive held-time source-discrimination proxies in H01/H02/H03.
3. Structured shift-aware conformal source regions — reserve reliability layer, not currently counted among the three main innovations.
4. Multiscale partial-observability memory — demoted to implementation option.

## 30. Current leading 1+2

### Main innovation — Intrinsic / Preserved Source Dynamics
Top-venue roots:
- ICLR 2025 intrinsic dynamical identity;
- NeurIPS 2025 Spotlight preserved dynamics across sessions.

Main thesis:
> a source is a persistent hidden dynamical identity observed through changing transport contexts; localization should infer this preserved identity rather than classify raw plume realizations.

### Auxiliary 1 — Extreme-event-aware intermittency preservation
Top-journal root:
- Nature Communications 2026 η-learning.

Role:
> preserve rare, source-informative whiffs/onsets that a representation optimized for average/predictable dynamics can erase.

### Auxiliary 2 — Temporal transformation / bridge representation
Top-conference root:
- CVPR 2026 TimeBridge.

Role:
> encode the in-between transition geometry of short plume segments, because endpoint values alone can remain source-ambiguous.

### Output
A lightweight source head converts the fused representation into the PMFS-compatible source-location probability map.

## 31. Next hard gate

Before any closed-loop or heavy network training:
- construct a fixed lightweight learned proxy that jointly uses:
  1. source-intrinsic metric learning,
  2. η/tail constraints,
  3. bridge-transition features;
- train only on frozen development source×transport histories;
- test held time and held wind;
- require each auxiliary to produce an incremental improvement over the previous arm, with destructive controls.


## 32. Loop-8 combined-arm gate: current 1+2 does NOT yet pass

A stricter sequential proxy was run to test whether the three candidate ideas add value incrementally rather than only in isolated diagnostics.

Protocol:
- train only on fast-wind windows from 120–180 s;
- test on slow-wind windows from 180–240 s;
- no wind feature is used in the corrected version;
- M1 = intrinsic source metric over basic temporal dynamics;
- M2 = append fixed extreme/tail observables;
- M3 = append bridge-transition observables;
- evaluation reports held-wind classification and source margin, with a separate physical-support flag.

Result:
- H01 informative windows are already correctly separated by M1; naïve M2/M3 concatenation does not improve margin and often reduces it.
- H03 shows the same pattern: accuracy is unchanged while naïve concatenation reduces the margin.
- H02 slow-wind test windows in 180–240 s have no >0.01 ppm support in this controlled asset; any above-chance classifier result is not admissible source evidence and must be treated as abstention, not localization success.

Decision:
> The current “M1 + tail features + bridge features” implementation fails the required incremental module gate.

This does **not** invalidate the remote ideas themselves; it invalidates naïve feature concatenation as the way to combine them.

Consequences:
- M2 must act as an η-style training/statistical constraint, not just extra tail features.
- M3 TimeBridge-style dynamics must be tested as a predictive auxiliary objective, not just appended bridge statistics.
- no three-module paper architecture is authorized yet.

## 33. 2026 novelty collision: plume-dynamics latent localization already exists

A new high-impact collision was identified:

- **Advanced Materials 2026 — “Receptor-Mimetic Stereo Olfaction for Simultaneous Odor Recognition and Spatial Localization” (AROMA).**
- It explicitly treats odor plumes as chemophysical fields coupling molecular identity with transport.
- receptor-mimetic stereo sensors encode onset, rise and amplitude dynamics;
- a multi-task Transformer decodes mixture identity and 3-D source location;
- the paper describes a unified latent representation of evolving plume dynamics and includes room-scale mobile-robot tracking.

Implication:
> “use plume dynamics / latent temporal representation for localization” is already too generic to support our novelty claim.

The surviving main idea must be narrower and stronger:

**preserved source identity across changing transport contexts**, not simply “spatiotemporal plume representation”.

No evidence was found in the current search that AROMA learns one source-intrinsic dynamical representation across wind/House/simulator changes; that distinction remains open but must be screened aggressively.

## 34. Revised status after loop 8

- Generic JEPA / predictive plume representation: DEMOTED.
- Generic plume-dynamics latent localization: COLLIDED by Advanced Materials 2026 AROMA.
- **Intrinsic / preserved source identity across transport contexts:** remains the active M1 hypothesis.
- Extreme-event-aware η-learning: remains a candidate auxiliary principle, but not as feature concatenation.
- TimeBridge temporal transformation: reserve auxiliary objective; isolated proxy positive, combined proxy not yet additive.
- Structured shift-aware conformal source regions: strong fallback auxiliary because it addresses unsupported/confident-wrong cases without fabricating source information.

Next search target:
1. 2025/2026 top-venue work on persistent identity / preserved dynamics across domain/session conditions;
2. direct OSL/GSL collisions involving domain-invariant or contrastive source identity;
3. a lightweight objective that can be tested with current source×transport pairs without assuming early observability.
