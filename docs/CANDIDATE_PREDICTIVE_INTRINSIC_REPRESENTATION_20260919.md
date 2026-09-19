# Candidate M1 — Predictive Intrinsic Representation for Turbulent GSL

Date: 2026-09-19
Branch: research/remote-paradigm-loop-20260919
Status: CANDIDATE / OFFLINE FALSIFICATION ONLY

## 0. One-sentence thesis

Turbulent gas-source localization should infer source location from the **predictive latent structure** of sparse plume observations, rather than from direct source classification or reconstruction of the realized stochastic plume.

## 1. Main remote-field paradigm

### Predictive latent representation / JEPA

Primary provenance:
- ICLR 2026 — Qu et al., *Representation Learning for Spatiotemporal Physical Systems*.
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
