# M1 Challenger 3 — Distributional Statistical Learning for Chaotic Transport

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: SCREENED / REJECTED AS M1

## Remote-domain provenance

Primary 2026 source:
- *Generative AI for efficient statistical computation of fluids*, Nature Communications (2026).

Core scientific claim:
- for chaotic turbulent systems, pointwise trajectory prediction has intrinsically limited value because small perturbations cause divergence;
- stable scientific targets are conditional distributions and statistical quantities;
- deterministic MSE-trained models tend to collapse toward smoothed conditional means, whereas generative distribution learning better preserves turbulent statistics.

Supporting 2026 source:
- *Learning turbulent flows with generative models for super resolution and sparse flow reconstruction*, Nature Communications (2026).

## Candidate transfer to GSL

Proposed thesis:
> localize the source by matching source-conditioned observation distributions/statistical fingerprints rather than matching a single simulated plume realization or a deterministic trajectory.

Possible source probability:
P(s | y) based on a learned source-conditioned distribution over intermittent observation statistics.

## Existing-data proxy

Using the 12 controlled H01/H02/H03 × {SA,SB} × {fast,slow} histories, compare:
- time-aligned pointwise RMS on log concentration;
- empirical Wasserstein distance between concentration distributions;
- Jensen–Shannon histogram distance;
- autocorrelation fingerprints.

Held-wind results:

H01:
- pointwise ratio = 0.307, 2/2 correct;
- Wasserstein ratio = 0.202, 2/2;
- JS ratio = 0.334, 2/2.

H02:
- pointwise = 0.079, 2/2;
- Wasserstein = 0.060, 2/2;
- JS = 0.259, 2/2;
- autocorrelation = 0.044, 2/2.

H03:
- pointwise = 0.471, 2/2;
- Wasserstein = 0.657, 2/2;
- JS = 0.461, 2/2;
- autocorrelation fails source identity, 0/2.

Thus distributional fingerprints improve nuisance/source separation in some Houses but not consistently.

## Fatal conflict with existing project evidence

A pure distributional/statistical representation is invariant to time permutation by construction.

However the project's CTT/first-passage evidence established that:
- native arrival timing contains source information;
- phase-label shuffle/time permutation degrades source ranking;
- coarse HIT compression can destroy that temporal information.

Therefore a method whose main scientific object is only the marginal observation distribution necessarily discards a source-informative dimension already established by project evidence.

A richer stochastic-process distribution could retain time dependence, but then:
- it becomes substantially heavier;
- it overlaps strongly with generative inverse plume/source models;
- existing R3B semantics provide only one stochastic realization per source×wind and cannot support a robust source-conditioned ensemble claim without new simulator ensembles.

## 2026 novelty collision

Direct collision:
- NeuPlume (EGUsphere 2026 preprint) already performs probabilistic inversion from sparse atmospheric observations with a latent diffusion plume prior and returns an ensemble/posterior over source/transport parameters.
- 2026 deep probabilistic indoor GSL also performs sequential physical dependency-guided posterior inference.

This does not make statistical turbulence modeling uninteresting, but it closes the clean novelty path for using distributional/generative inversion as the paper's main paradigm.

## Decision

**REJECT AS M1.**

Retain only two lessons:
1. do not train the predictive representation with a pointwise reconstruction objective that averages away turbulence;
2. evaluate higher-order/intermittency statistics as diagnostics.

Current M1 leader remains predictive self-supervised physical representation.
