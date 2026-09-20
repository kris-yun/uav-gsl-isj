# M1 Challenger 4 — State-Dependent Causality for Turbulent Source Inference

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / REJECTED AS M1

## Remote-domain provenance

Primary source:
- Martínez-Sánchez & Lozano-Durán, *Observational causality by states and interaction type for scientific discovery*, Communications Physics, 2026.

Core idea:
- causal influence in complex systems can change with the instantaneous system state;
- average/global causal scores can be misleading;
- causality should be decomposed by state and by unique / redundant / synergistic interaction type;
- demonstrated on turbulent boundary-layer scale interactions and climate dynamics.

This is materially more advanced than a global “one causal effect everywhere” assumption.

## Why it was reconsidered

The project’s earlier causal line repeatedly failed because:
- candidate-dependent transport error cannot be removed by global centering;
- source evidence changes with exposure regime;
- early histories can be non-identifying even when later histories become useful;
- intervention effects and time arrows exist without uniquely identifying source.

A state-dependent framework could, in principle, explain why a causal source effect is informative only in some plume regimes.

## Existing-data state decomposition

Using the controlled H01/H02/H03 × {SA,SB} × {fast,slow} histories:
- current pooled gas state was divided into blank (<0.001 ppm), weak (0.001–0.1 ppm), and strong (>0.1 ppm);
- future response was evaluated 5 s later;
- source, wind, and source×wind interaction contrasts were computed in each state.

Representative source/interaction RMS ratios:

H01:
- blank: 4.93
- weak: 2.08
- strong: 1.39 (only 8 strong-state samples)

H02:
- blank: 3.81
- weak: 20.89
- strong: 12.54

H03:
- blank: 2.12
- weak: 1.29
- strong: 2.85

Thus the relative source effect is strongly state dependent and differs by House.
A single global causal weighting is therefore empirically inappropriate.

## Why this still fails as M1

### 1. The source variable is not the same kind of object as in the source paper

The Communications Physics framework studies causal influence among time-varying observables and future system states.

In GSL, source location is a persistent hidden/intervention parameter, not an observed time-varying process.
Mapping static source hypotheses directly to state-wise observational causality is therefore not structurally exact.

### 2. Existing project evidence already separates action-response causality from source identity

The repository has established:
- causal action-response effects exist;
- global time-arrow effects exist;
- neither uniquely identifies the source under the available single-channel measurements;
- H03 can improve some horizon metrics while ending at the wrong source.

State-aware decomposition does not create missing physical support or source-identifying information.

### 3. The strongest states are House dependent

H02 becomes highly source-dominant in weak/strong states.
H01’s rare strong state remains heavily coupled to transport interaction and is extremely sparse.
H03 has a different state profile.

Thus a “high causal state” rule would itself need a second learned/physical mechanism and would not provide a universal paper-level source-localization principle.

## Decision

**REJECT AS M1.**

Potential retained use:
- a state-aware diagnostic for deciding when a source-evidence module is physically interpretable;
- not counted as an innovation unless it later passes a source-identification gate.

The result strengthens the current direction:
- M1 must learn source-relevant dynamics without assuming global invariance;
- M2 must preserve rare/intermittent evidence;
- the final map must remain uncertain in unsupported states.
