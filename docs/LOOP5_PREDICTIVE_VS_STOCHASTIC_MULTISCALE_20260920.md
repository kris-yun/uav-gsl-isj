# Loop 5 — Predictive Representation vs Stochastic Multiscale Modeling

Date: 2026-09-20
Branch: research/remote-paradigm-loop-20260919
Status: internal screening; no promotion to paper claim.

## A. New paradigm-level candidate

### C9 — Stochastic Multiscale Modeling

Primary 2025 top-venue anchor:
- NeurIPS 2025 — Andrew F. Ilersich, Prasanth B. Nair, *Learning Stochastic Multiscale Models*.
  Core object: an explicit decomposition into a resolved macroscale latent state and an unresolved microscale latent state with coupled stochastic dynamics, learned directly from observational data.
  The paper roots the construction in classical multiscale/closure modeling rather than generic feature pyramids.

Strong 2025/2026 physical-science context:
- ICML 2025 — *Adaptive Flow Matching for Resolving Small-Scale Physics*: deterministic coarse component plus stochastic fine-scale component for multiscale physical fields.
- Nature Communications 2026 — *Generative AI for efficient statistical computation of fluids*: deterministic MSE surrogates collapse turbulent distributions toward mean behavior; probabilistic distributional modeling is required for chaotic turbulent statistics.
- 2026 Lagrangian-turbulence work on conditional reconstruction of unresolved intermittent fluctuations further supports the macro-conditioned stochastic-micro viewpoint (supporting context; not used as the primary venue anchor).

### GSL translation

For sparse turbulent gas observations:

- macroscale latent: persistent/coherent transport structure carrying source geometry;
- microscale latent: unresolved turbulent/intermittent fluctuations;
- source location: a persistent hidden parameter coupled to both scales;
- probability map: marginalize the stochastic microscale state and infer the source posterior.

Scientific thesis:
> source inference should model the coupling between resolved source-bearing structure and unresolved stochastic plume dynamics instead of treating turbulence as either deterministic signal or disposable noise.

This is a stronger scientific object than generic “multi-scale features”.

## B. Direct collision screen

2024–2026 GSL/OSL search identified:
- *Many wrong models approach to localize an odor source in turbulence with static sensors* (2024 preprint): explicitly acknowledges multiscale, out-of-equilibrium turbulent transport and blends multiple stochastic forward models.
- Advanced Materials 2026 AROMA: uses evolving concentration onset/rise/amplitude patterns and a multi-task Transformer to learn a unified latent representation for odor identity and 3-D source location.
- 2026 diffusion-state classification: UMAP + clustering for diffusion-state perception.
- INFOCOM 2026 PLOS-RS: PDE forward-model + randomized MAP/MLE candidate search.

No direct result was found in this screen that performs:
- explicit learned macro/micro stochastic latent decomposition,
- coupled inter-scale dynamics,
- PMFS-style mobile source probability mapping.

Collision consequence:
- “use temporal plume dynamics” is not novel;
- “use a multiscale neural network” is not novel;
- the only defensible transfer would be explicit stochastic scale separation with coupled latent dynamics.

## C. Existing-data proxy screen

Same frozen 12 histories:
H01/H02/H03 × {SA,SB} × {fast,slow}.

Proxy representation:
- macro = 10 s causal coarse component of log concentration;
- mid-scale = 2 s minus 10 s component;
- micro = native log concentration minus 2 s component;
- η-tail = q95/q99, maximum/top-tail mass, exceedance fractions, first-arrival.

Held-wind source identity and wind/source distance ratio were compared at 120/180/240 s.

Important findings:

### H01
- 180 s: macro-only fails source identity (0/2), while micro and explicit multiscale both retain 2/2.
- 240 s: macro-only is 1/2; micro/multiscale are 2/2.
- adding rare-event/tail information to the macro branch restores 2/2 at 240 s.

Interpretation:
- H01 directly falsifies any model that equates “macroscale/predictable = source” and “microscale = nuisance”.
- microscale/intermittent events can carry source identity.

### H02
- 120 s: all branches remain effectively non-identifying; source and transport remain confounded.
- 180 s: simple macro/micro/multiscale proxies are only 1/2; macro + η-tail reaches 2/2.
- 240 s: macro and multiscale become 2/2; η substantially lowers the wind/source ratio.

Interpretation:
- physical support is a prerequisite.
- stochastic scale separation alone does not create source identity; rare-event support still matters.

### H03
- 120–240 s: macro, micro and multiscale generally retain 2/2.
- at 240 s, micro-scale structure is more source-dominant than macro structure in this proxy.

Interpretation:
- source identity can reside at different scales in different regimes.
- a useful multiscale model must preserve coupled scale information rather than privileging one scale.

## D. Decision vs current JEPA-class M1

### Predictive latent representation strengths
- cleaner lightweight path;
- direct ICLR 2026 physical-system evidence that JEPA-like latent prediction can better preserve governing physical parameters than reconstruction;
- existing source-blind prediction proxies suppress some transport variability.

### Predictive latent representation weakness
- H01 shows prediction/smoothing can erase late, source-defining intermittency.
- Advanced Materials 2026 AROMA increases the collision risk for a generic “plume dynamics latent representation” story.

### Stochastic multiscale strengths
- more physically faithful to turbulence;
- explicitly retains unresolved stochastic dynamics rather than discarding them;
- H01/H03 proxy evidence supports the need for micro-scale channels.

### Stochastic multiscale weakness
- simple multiscale decomposition is not uniformly better than predictive + η.
- source is static while the NeurIPS framework targets dynamical states; a source-identifying latent object must still be derived.
- implementation is heavier than a small predictive encoder.

## E. Current scoring

| M1 candidate | Paradigm-level strength | 25/26 venue strength | project-mechanism fit | collision room | lightweight | public-data portability | score /60 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Predictive latent physical representation | 10 | 10 | 9 | 7 | 9 | 10 | 55 |
| Stochastic multiscale modeling | 9 | 10 | 10 | 9 | 7 | 9 | 54 |
| State-first intermediate physical state | 8 | 10 | 9 | 8 | 7 | 9 | 51 |
| Inverse generative modeling | 10 | 10 | 9 | 5 | 7 | 10 | 51 before direct-collision penalty; demoted |

Threshold for continued M1 screening: >=54 and no fatal direct collision.

Current M1 survivors:
1. Predictive latent physical representation — 55.
2. Stochastic multiscale modeling — 54.

No winner is frozen.

## F. Shared auxiliary candidate retained

M2 extreme-event/intermittency preservation remains necessary under both M1s:
- Nature Communications 2026, *Extreme Event Aware (η-) Learning*.
- Physical Review Fluids 2025/2026 work shows intermittency/extreme events are structurally important in turbulent flows.

M3 structured shift-aware source region remains the current reliability auxiliary, but it is not yet frozen.

## G. Next discrimination

1. Perform destructive time-order permutation and amplitude-preserving shuffle tests:
   - predictive M1 should fail when temporal predictability is destroyed;
   - stochastic-multiscale M1 should retain scale statistics but lose cross-scale coupling.
2. Compare which representation predicts held-wind source identity incrementally beyond η-tail alone.
3. Search 2025/2026 top venues for **predictive information / multi-timescale latent dynamics / turbulence intermittency representations** that may unify the current two M1 survivors.
4. Continue direct GSL collision search, especially after Advanced Materials 2026 AROMA.

