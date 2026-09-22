# Computational Mechanics / epsilon-machine transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Cross-domain origin: complex-systems science / statistical mechanics.

Computational Mechanics identifies **causal states** as equivalence classes of histories with identical future predictive distributions. The resulting epsilon-machine is the minimal optimal predictor of a stochastic process.

Recent Scite anchors:
- *Complementary Characterization of Agent-Based Models via Computational Mechanics and Diffusion Models* (2025), arXiv:2512.04771.
- *Temporal Memory in Repeating Fast Radio Bursts: Epsilon-Machine Reconstruction of Causal Structure in Burst Timing* (2026), MNRAS/arXiv:2607.14421.
- *What Is a Pattern in Statistical Mechanics? ... with Computational Mechanics* (2026), Entropy.

Public 2026 implementation:
- https://github.com/johnazariah/emic
  (epsilon-machine inference and characterization; CSSR, spectral, CSM, BSI, NSD).

## GSL transfer tested

A deliberately lightweight finite-history approximation was used before spending effort on full CSSR inference:

1. sample each source-conditioned candidate hit-probability field along the real robot trajectory;
2. ordinally symbolize measured-gas and candidate sequences into four states, removing marginal amplitude calibration;
3. construct fixed length-3 history -> next-symbol predictive word distributions;
4. compare measured and candidate predictive architectures with Jensen-Shannon divergence;
5. use the same construction on robot-to-candidate distance as a geometry-only control.

This is a source-blind screen of the mother principle: if candidate source identity is expressed as a shared predictive-state architecture, the plume version should materially exceed the geometry version.

## Joint old+new development result

Plume predictive-architecture score:
- mean endpoint = **4.6269 m**
- pooled reduction = **20.01%**
- non-worse = **9/12**
- old six = **13.41%**, 5/6
- new six = **26.11%**, 4/6

Geometry-only predictive architecture:
- mean endpoint = **4.7237 m**
- pooled reduction = **18.34%**
- non-worse = **10/12**

Plume-minus-geometry:
- mean endpoint = **4.6624 m**
- pooled reduction = **19.40%**
- non-worse = **9/12**

## Decision

The candidate-specific predictive structure is not materially stronger than the robot/source geometry predictive structure. The remote mother theory is valid, but the source-specific transfer is not supported.

No CSSR significance level, history depth, alphabet size, or inference algorithm was tuned after seeing the joint old+new result.

Final verdict:
`COMPUTATIONAL_MECHANICS_GSL_TRANSFER_NO_GO_20260922`
