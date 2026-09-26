# 2. Prior-art / collision boundary

## Distant-domain mother theory

Primary 2026 inspiration:
- Maan et al., **Anticipating decoherence in quantum systems**,
  Nature Communications 17, 8239 (2026), DOI 10.1038/s41467-026-72829-3.
  The paper explicitly analyzes a **quasi-quenched regime** in which fast
  fluctuations are conditioned on slowly evolving disorder configurations and
  defines time windows over which slow disorder is treated as effectively
  quenched.

Classical root:
- quenched vs annealed averaging in statistical mechanics / random
  environments.  QA-PMFS uses the timescale-separation principle, not replica
  physics as an algorithmic transplant.

## Near-domain collisions that must NOT be claimed as novelty

1. Heinonen, Biferale, Celani & Vergassola,
   **Exploring Bayesian olfactory search in realistic turbulent flows**,
   Physical Review Fluids 10, 064614 (2025).
   Already studies olfactory search under spatiotemporally correlated
   encounters.  Therefore QA-PMFS cannot claim "first temporal correlation".

2. Piro, Heinonen, Cencini & Biferale,
   **Many wrong models approach to localise an odour source in turbulence with
   static sensors**, Journal of Turbulence 26(5), 153-173 (2025),
   DOI 10.1080/14685248.2025.2492711.
   Already ranks/blends multiple stochastic environmental models.  QA-PMFS
   cannot claim "first ensemble / multiple transport hypotheses".

3. Kim et al.,
   **Deep Probabilistic Indoor Gas Source Localization via Physical
   Dependency-Guided Sequential Inference**, arXiv:2608.16221 (2026),
   submitted to IEEE T-RO.
   Already propagates probabilistic wind and concentration fields to a source
   posterior.  QA-PMFS cannot claim "first probabilistic GSL".

## Defensible novelty target

The candidate contribution is narrower:

**a source likelihood with explicit timescale-separated random-environment
marginalization: fast transport uncertainty is marginalized event-wise, while
a slow episode-level latent environment is shared and marginalized once over
the episode, with the single-event PMFS marginals provably unchanged.**

The novelty claim must remain conditional until fresh cross-environment
confirmation and a broader prior-art search are complete.
