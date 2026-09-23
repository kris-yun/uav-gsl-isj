# Novelty boundary: predefined multi-dispersion-model source inference is NOT the main innovation

Date: 2026-09-23

## Decision

Do not promote the naive `source x discrete transport-model hypothesis` formulation as the paper's main innovation.

A direct prior-art collision exists:

- S. Julier et al. / Signal Processing 108 (2015), *Bayesian likelihood-free localisation of a biochemical source using multiple dispersion models*, DOI 10.1016/j.sigpro.2014.08.023.
- The paper explicitly treats source localization under a set of candidate atmospheric dispersion models and performs model selection / averaging with likelihood-free Bayesian computation on real data.

Therefore the 2025 PhysPDE physical-hypothesis-selection idea is scientifically relevant to diagnosing PMFS model misspecification, but **a literal transfer of finite-model selection into gas-source localization is not sufficiently novel**.

## What survives

The failure mechanism remains supported: PMFS assumes one fixed online transport law, while our R2 evidence shows that changing downstream scoring semantics repeatedly fails to restore truth-source identity.

The only version worth screening next is materially stronger than 2015 multi-model inference:

> infer or learn an environment-specific latent transport law from the current observation context, then condition source evidence on that inferred law.

This is not a finite menu of predefined plume models. It is a test-time / in-context system-identification problem.

## Next-screen boundary

Reject any candidate that is only:
- Bayesian model averaging over a fixed plume-model bank;
- more stochastic replicas of the same PMFS simulator (A0 already NO-GO);
- scalar tuning of PMFS `noiseSTDev` presented as the innovation;
- posterior tempering / robust likelihood under a fixed forward family.

A new main line must demonstrate source-identity recovery from **context-conditioned transport adaptation** without source truth, House ID, or candidate-specific fitting.
