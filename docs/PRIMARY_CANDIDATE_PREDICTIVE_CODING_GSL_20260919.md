# Primary Candidate — Predictive Coding for Turbulent Source Inference

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: PRIMARY CANDIDATE / OFFLINE FALSIFICATION ONLY

## 1. Paper-level main thesis

The paper is not “JEPA for PMFS”.

The main scientific idea is **predictive coding**:

> A turbulent odor stream should be interpreted through what the sensing system can predict from recent physical context and, equally importantly, through the structured prediction errors that violate that expectation.

For GSL, the source is inferred from the joint structure of:
1. expected/predictable plume dynamics;
2. source-informative prediction errors;
3. uncertainty about whether these two evidence channels remain valid after environment shift.

The final output remains a PMFS-compatible source-location probability map.

## 2. Main innovation M1 — Predictive Coding / Predictive Physical Representation

### Big-science source

**Trends in Cognitive Sciences 2025 — Lyons & Gottfried, _Predictive coding in the human olfactory system_.**

This paper develops predictive coding as a unifying theory for olfaction:
- olfactory processing is not purely reactive;
- the system issues predictions about sensory input;
- prediction errors carry information not already explained by expectation;
- the paper proposes a “predictive map” view of piriform cortex.

This is a neuroscience-level mother idea, not a GSL algorithm.

### Modern machine-learning realization

**ICLR 2026 — Qu et al., _Representation Learning for Spatiotemporal Physical Systems_.**

Key recent result:
- latent JEPA-style prediction is evaluated on physical systems;
- downstream governing-parameter estimation is used to judge whether learned representations are physically meaningful;
- latent predictive objectives can outperform pixel-level reconstruction for recovering governing physical parameters.

Independent supporting direction:
- ICLR 2026 continuous-time fMRI representation learning reframes self-supervision through continuous-time latent dynamics and explicitly unifies MAE and JEPA-like objectives.
- 2026 JEPA work in noisy physical sensing/ultrasound independently argues that latent prediction can avoid spending capacity on stochastic low-level detail.

### GSL transfer

For sparse gas/wind/pose history (H_t):

[
z_t = E(H_t),qquad
hat z_{t+Delta}=P(z_t,c_t)
]

and define prediction error in latent/observable space

[
e_{t+Delta}=z_{t+Delta}-hat z_{t+Delta}.
]

Source inference does not use only (z), only (hat z), or only (e).

It uses a source-evidence representation

[
r_t = F(hat z_{t+Delta},, eta(e_{t+Delta}),, c_t)
]

where (eta(cdot)) is the auxiliary extreme-event statistic defined below.

A lightweight source head evaluates (r_t) at source query cells and produces

[
P(S=smid H_t).
]

## 3. Why predictive coding is more than “a temporal encoder”

Direct 2026 collision:
- Advanced Materials AROMA already uses evolving plume onset/rise/amplitude and a multi-task Transformer to learn a unified latent representation for odor identity and 3-D source localization.

Therefore these claims are already occupied:
- temporal plume features;
- Transformer encoding;
- latent plume representation;
- direct temporal decoding to source coordinates.

The proposed M1 is narrower and testable:
- **source-blind predictive self-supervision** is load-bearing;
- source labels are not needed to learn the physical representation;
- the prediction-error stream is explicitly retained rather than hidden inside a supervised encoder;
- destructive target-time permutation must destroy the predictive benefit.

## 4. Auxiliary innovation M2 — Extreme-Event-Aware Prediction Error Preservation

### Remote source

**Nature Communications 2026 — Chang & Sapsis, _Extreme Event Aware (eta-) Learning_.**

Transferred principle:
> ordinary learning is dominated by common regimes; constrain the representation/model with statistics of an observable that identifies rare/extreme regimes so important tails are not erased.

GSL mapping:
- common regime = blank / low concentration / ordinary fluctuations;
- extreme regime = rare whiff, abrupt onset, high-tail exposure, or large positive predictive surprise;
- eta observable = fixed source-blind statistics of prediction error / plume intermittency.

M2 is not “use whiff duration features”.
Older plume literature already does that.

M2 is:
> enforce that the learned predictive representation preserves the distributional statistics of rare source-informative prediction errors.

Possible predeclared eta statistics:
- upper quantiles of positive prediction error;
- tail mass;
- rate/duration of large surprise events;
- onset timing relative to the sensor model;
- burst integral.

## 5. Existing-data test of M1 + M2 semantics

The existing 12 controlled histories were decomposed source-blind into:
- causal predicted component (moving-average proxy);
- signed/absolute prediction-error stream.

A fixed extreme-surprise descriptor was then computed from prediction errors.

### H03, 240 s — key counterexample/rescue

With a 50-sample causal predictor:
- predicted component alone: held-wind identity **1/2**;
- extreme prediction-error descriptor: **2/2**;
- predicted + extreme-error combination: **2/2**.

Wind/source distance ratio:
- predicted: ~0.801;
- extreme surprise: ~0.590;
- combined: ~0.674.

Thus a pure predictive-compression model loses a source distinction, while preserving structured surprise restores it.

### H03, 120 s
- predicted ratio ~0.308;
- surprise ratio ~0.145;
- combined ~0.210;
- all retain 2/2 identity.

### H01, 120 s
- predicted ratio ~0.233;
- surprise ~0.160;
- combined ~0.187;
- all retain 2/2.

### H02, 180 s
The complementary case:
- predicted component is much more source-dominant than surprise;
- predicted ratio can be ~0.030 at the longer smoothing window;
- surprise ratio ~0.449.

So surprise is not universally “better”.
The two channels are complementary, which is exactly the predictive-coding interpretation.

### Physical-support sanity
H02 at 120 s:
- prediction, surprise and combination are all 0/2;
- source and transport remain indistinguishable.

Therefore the proposed representation does not manufacture source identity before the plume produces physical evidence.

## 6. Auxiliary innovation M3 — Shift-Aware Structured Source Region

### Recent remote sources

Primary:
- **ICLR 2025 — Wasserstein-Regularized Conformal Prediction under General Distribution Shift.**

Supporting 2025 line:
- error-quantified conformal inference for dependent/time-series data;
- ICML 2025 structured/optimal-transport conformal prediction;
- online conformal optimization.

Transferred principle:
> a sharp model score is not a reliability guarantee under shift; output a prediction set whose size responds to evidence/shift.

GSL object:
- base output remains (P(S=smid H_t));
- M3 outputs a spatial source region (Gamma_alpha(H_t));
- under unsupported House/simulator/sensor shift, the region expands or the system abstains instead of reporting a false sharp MAP.

This directly targets historical PMFS cases where entropy collapsed while localization was wrong.

## 7. The 1 + 2 structure

### M1 MAIN
**Predictive Coding Source Representation**
- learn expected latent plume dynamics;
- explicitly retain prediction-error evidence;
- source-blind self-supervision.

### M2 AUX
**Extreme-Event-Aware Surprise Preservation**
- prevent rare source-defining prediction errors from being averaged away.

### M3 AUX
**Shift-Aware Structured Source Region**
- turn the source probability map into calibrated spatial uncertainty under environment shift.

The three modules solve different problems:
- M1: what representation of plume evidence should be learned?
- M2: what critical information does predictive learning tend to erase?
- M3: when should the resulting probability map be trusted?

## 8. Lightweight implementation contract

Not counted as innovation:
- small temporal encoder;
- latent-block prediction rather than plume reconstruction;
- shared encoder for prediction + source head;
- M2 implemented as a few tail-statistic heads/losses;
- M3 post-hoc;
- pruning/quantization only after mechanism validation.

No full 3-D plume decoder.
No agent.
No RL.
No OED/planner contribution.

## 9. Public-dataset validation contract

Already interface-qualified on:
1. VGR/GADEN — 30 houses, 120 cases;
2. TURB-Smoke 2026 DNS — five point sources, Lagrangian particles, 3-D/quasi-2-D concentration, mean-wind variants;
3. ICASSP 2025 real wind-tunnel GSL challenge;
4. Scientific Data 2026 real wind-tunnel fly-through dataset.

Frozen per-observation interface:
- time;
- sensor/robot position;
- gas;
- optional local wind;
- optional sensor metadata.

Output:
- source probability at arbitrary query cells;
- calibrated source region.

## 10. Direct novelty screen

Focused searches through 2026 found no direct robotic GSL paper combining:
- predictive-coding / JEPA-style source-blind plume representation learning;
- explicit prediction-error evidence;
- eta-style rare-event preservation;
- spatial source-probability-map output.

Important nearby collision:
- AROMA 2026 occupies supervised spatiotemporal latent plume decoding.
- older biological/GSL work occupies ordinary whiff/intermittency features.
- therefore both M1 and M2 need destructive mechanism tests.

## 11. Hard kill tests

Kill M1 if:
1. architecture-matched direct supervised or reconstruction encoder matches it on held House/wind;
2. context parroting/simple moving average matches trained latent prediction;
3. target-time permutation does not remove the benefit;
4. source gain comes only from amplitude smoothing.

Kill M2 if:
1. ordinary raw intermittency features match it;
2. permuting/truncating high-surprise events does not specifically remove the M2 increment;
3. eta statistics do not add after the learned predictive encoder.

Kill M3 if:
1. nominal coverage fails on held distribution shifts;
2. valid coverage requires nearly the entire map.

## 12. Current score

- paper-level theme: 10/10
- 2025/26 distant-domain support: 10/10
- physics/mechanism fit: 9/10
- novelty room after AROMA collision: 8/10
- existing-data positive + negative evidence: 9/10
- lightweight feasibility: 9/10
- heterogeneous public-data compatibility: 10/10

**Provisional: 65/70.**

This is the first candidate in the loop whose main thesis is supported simultaneously by:
- a current olfactory-neuroscience theory paper;
- a current top-ML physical-representation paper;
- the project's own positive and destructive offline evidence.

It is still not promoted to validated main innovation until a trained lightweight predictive model beats matched baselines.


## 13. Independent 2025/2026 convergence around the main idea

The main idea is no longer supported by only one JEPA paper.

### Olfactory neuroscience — Trends in Cognitive Sciences 2025
Lyons & Gottfried explicitly develop predictive coding as a theory of human olfaction:
- anticipatory sensory prediction;
- prediction-error signaling;
- a predictive-map hypothesis.

### Systems neuroscience — Nature Neuroscience 2026
Tsukano et al., *Orbitofrontal cortex drives predictive filtering of sensory responses*:
- experimentally distinguishes predictive filtering from a novelty-only account;
- identifies top-down signals that grow with experience and suppress predicted sensory responses;
- describes prediction as a “negative image” that cancels expected sensory input.

Although the experiment is auditory rather than olfactory, it independently supports the core computation:
[
	ext{sensory input} - 	ext{predicted input} ightarrow 	ext{residual evidence}.
]

### Scientific machine learning — ICLR 2026
Qu et al. show in physical systems that latent-space prediction can produce representations better suited to downstream governing-parameter inference than pixel-level reconstruction.

These are three independent communities:
- olfactory neuroscience;
- systems neuroscience;
- scientific representation learning.

They converge on the same high-level principle without being GSL papers.

## 14. Important theoretical caution from Annual Review of Neuroscience 2026

Furutachi & Hofer, *Rethinking Predictive Processing* (Annual Review of Neuroscience 2026), emphasize that:
- “prediction error” is not a single unambiguous biological quantity;
- superficially similar error responses can arise from different computations;
- predictive-coding claims require operational definitions and mechanism-specific evidence.

This review is treated as a constraint, not supporting decoration.

For this project, “prediction error” is therefore frozen operationally as:
[
e_{t+Delta}=z_{t+Delta}-P(z_t,c_t)
]
or the corresponding observation-space residual in a matched proxy.

The paper must not claim a biological neural mechanism.
It transfers the computation:
- build a prediction from context;
- represent what the prediction fails to explain;
- test whether the residual contributes independent source evidence.

## 15. Prediction-error proxy strengthens M2 necessity

A source-blind proxy split each trace into a predicted channel and an extreme prediction-error (“surprise”) channel.

Examples:

### H03, 240 s, 50-sample predictor
- predicted-only identity: 1/2;
- surprise-only: 2/2;
- combined: 2/2.
- wind/source ratio: predicted ~0.801, surprise ~0.590, combined ~0.674.

### H03, 120 s
- predicted ~0.308;
- surprise ~0.145;
- combined ~0.210;
- all 2/2.

### H01, 120 s
- predicted ~0.233;
- surprise ~0.160;
- combined ~0.187;
- all 2/2.

### H02, 180 s
The direction reverses:
- predicted component can be very source-dominant (~0.030 ratio);
- surprise is much less clean (~0.449).

Therefore:
> expected structure and prediction-error structure are complementary; neither channel is universally superior.

This is stronger support for predictive coding than for “JEPA compression” alone.

It also gives M2 a precise target:
- not raw high concentration;
- not all residuals;
- preserve **extreme source-informative prediction errors** that the primary predictive objective can otherwise underweight.

## 16. Updated reviewer-proof novelty sentence

Do not write:
> “We use a temporal latent representation for plume localization.”

Use:
> “We reformulate turbulent source evidence as a predictive-coding pair: a source-blind latent predictor captures expected plume structure, while an extreme-event-aware auxiliary preserves source-informative prediction errors that the predictor cannot explain; the resulting evidence is mapped to a calibrated spatial source probability field.”

This sentence remains conditional on trained-model falsification.
