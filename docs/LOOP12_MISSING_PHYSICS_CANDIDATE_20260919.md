# Loop 12 — Candidate-Conditioned Missing Physics

Date: 2026-09-19  
Status: **ACTIVE M1 SURVIVOR / OFFLINE FALSIFICATION ONLY**

## Remote-domain mother idea

**Hybrid physics–machine learning / learning missing physics.**

Recent high-level anchors:

- Nature Communications 2026 — Wang et al., *Learning missing physics from legacy simulators with alternating neural integrators*.  
  Core idea: keep a trusted callable physical prior and learn only the structured discrepancy between that prior and reference dynamics.
  https://www.nature.com/articles/s41467-026-74002-2

- Nature Communications 2026 — Malik et al., *Hybrid physics-machine learning models for quantitative electron diffraction refinements*.  
  Core idea: retain rigorous differentiable physics while learning hard-to-model experimental effects jointly with physical parameters.
  https://www.nature.com/articles/s41467-026-71673-9

- Journal of Computational Physics 2025 — Dong et al., *Data-driven stochastic closure modeling via conditional diffusion model and neural operator*.  
  Supporting closure literature: unresolved multiscale effects should be modeled rather than forcing a deterministic local closure.

The transfer is **not** “use a neural network to predict source”.
It is:

> PMFS/transport physics is an informative but structurally incomplete prior; learn the missing candidate-conditioned transport/sensor discrepancy, then perform source inference through the corrected physical response.

## Why this is now stronger than the previous candidates

Existing project evidence provides a direct model-form-error contrast.

### High-fidelity response retains source identity

`cstar_m1_exact_counterfactual_transfer_20260909.json`:
- H01: 4/4 rank-1;
- H02: 4/4;
- H03: 4/4;
- total: **12/12**.

Each target source/wind is scored only with opposite-wind candidate response traces, so this is not same-trace memorization.

### Approximate deployable provider can reverse the source

`cstar_m1_h01_same_provider_20260911.json`:
- actual SA -> ranks SB;
- actual SB -> ranks SB;
- **1/2 correct**.

For actual SA:
- SA-provider log1p MSE = 0.00733753;
- zero/SB response MSE = 0.000806054.

Thus the physically intended model can be worse than a null response and invert the source evidence.

### The missing physics is candidate-dependent

Using the two H01 same-provider residual traces:
- residual correlation = **0.0081**;
- residual cosine = **-0.0101**.

Copying one source residual onto the other yields MSE ≈ **0.007344** in both directions and catastrophically damages the originally easy SB case.

Therefore:
> a House-wide/global residual correction is not supported; the discrepancy must depend on the candidate source and transport context.

This matches the older cross-House result that transport error is candidate-dependent and survives simple centering/variance pooling.

## M1 scientific object

For candidate source (s), context (c_t), and reusable physical prior response (hat y_t^{,P}(s)),

[
y_t = hat y_t^{,P}(s) + Delta_	heta(s,c_{0:t},hat y_{0:t}^{,P}) + epsilon_t .
]

The new object is not a source feature. It is the **candidate-conditioned missing-physics operator** (Delta_	heta).

PMFS source evidence is computed from the corrected response, and the final output remains a source-location probability map.

## First auxiliary clue from the same evidence

For failing H01-SA:
- only 48/1200 samples belong to the union of observed/predicted >0.1 ppm event support;
- those samples contribute **97.92%** of total squared log-response error;
- the largest 5% of samples contribute **98.69%**.

So the model-form discrepancy is extremely concentrated in intermittent events rather than uniformly spread over the mission.

This makes the 2026 Nature Communications **Extreme Event Aware (η-) Learning** idea a physically motivated auxiliary candidate in the *residual-learning* setting, even though η features failed as a generic standalone representation in Loop 8.

## Hard kill gates

Kill M1 if:
1. a lightweight candidate-conditioned residual corrector cannot improve held-time/held-transport likelihood over the frozen physical prior;
2. a source-independent/global residual performs equally well;
3. correction improves response MSE but does not restore source ranking/proper source score;
4. gains require truth wind/full future gas at deployment;
5. the mechanism cannot be defined on public DNS and real wind-tunnel datasets.

Current verdict: **STRONGEST M1 SURVIVOR SO FAR**, but not validated.
