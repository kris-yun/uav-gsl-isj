# Sim-to-observation marginal bridge pre-audit on authoritative R2

Date: 2026-09-23
Status: **NO-GO for source-blind scalar sim2obs bridge**

## Mother idea being screened

NeurIPS 2025 Astro-DSB (Dynamic Diffusion Schrödinger Bridge in Astrophysical Observational Inversions) treats the mismatch between physical simulations and real observations as a distribution-bridging problem rather than assuming that the simulator output already lives in the observation domain. This is a good conceptual match to the established PMFS failure: candidate simulations can be internally sharp and reproducible while assigning poor rank to the true source in real observations.

This pre-audit does **not** implement DSB. It asks a cheaper necessary question: is there a transferable, source-blind marginal sim-to-observation map at all?

## Frozen test

Authoritative R2 final <=300 s banks, all six House x seed runs.

For each held-out House:
- training data are the truth-nearest candidate's simulated hit probabilities and measured probabilities from the other two Houses, both seeds;
- fit one confidence-weighted monotone isotonic map `q_sim -> p_obs` (no held-out truth used);
- apply exactly the same map to every candidate in the held-out House;
- rescore candidates with the unchanged Native PMFS likelihood `log S = sum log(1 - c |p_obs-q|)`;
- evaluate the held-out truth-nearest candidate only after scores are frozen.

This is intentionally a weak marginal bridge. Its only purpose is to test whether a candidate-shared observation-domain calibration is a viable mechanism before considering a high-dimensional dynamics-preserving bridge.

## Results

| run | Native truth rank | bridge truth rank | apparent rank gain |
|---|---:|---:|---:|
| House01 seed0 | 110/152 | 76.5/152 | +33.5 |
| House01 seed1 | 117/148 | 74.5/148 | +42.5 |
| House02 seed0 | 123/148 | 74.5/148 | +48.5 |
| House02 seed1 | 121/144 | 72.5/144 | +48.5 |
| House03 seed0 | 149/197 | 99/197 | +50.0 |
| House03 seed1 | 148/199 | 100/199 | +48.0 |

The apparent 6/6 improvement is **not source identification**. The learned monotone bridge collapses to a constant for each leave-one-House-out split:

- hold out House01: all corrected probabilities ~= 0.483372;
- hold out House02: all corrected probabilities ~= 0.439348;
- hold out House03: all corrected probabilities ~= 0.393749.

Therefore every candidate receives the same bridged score (up to numerical equality), producing the average tie rank near N/2. The source-distance Spearman correlation is undefined because the candidate scores have zero variance.

## Interpretation

This is a destructive degeneracy result. A source-blind scalar sim2obs calibration can make the truth rank numerically look better solely by erasing candidate discrimination. It does not repair the source-identifying forward semantics.

**Do not treat the +33 to +50 rank changes as a positive result.**

The only Schrödinger-bridge-style route still scientifically open is a **source-conditioned, dynamics-preserving bridge** in which the coupling is constrained to preserve candidate/source identity and plume dynamics. A candidate-shared marginal bridge is closed.

Machine-readable results: `DSB_MARGINAL_BRIDGE_PREAUDIT_R2.csv`.
