# Step 3 — Abstract-level triage

Timestamp: 2026-08-30

## Structured papers

### PMFS, IEEE TRO 2024

- Date: 2024.
- Problem framing: mobile robotic gas-source localization.
- Core mechanism: probabilistic mapping plus online candidate dispersion
  simulation and Bayesian inference.
- Key insight: simulated candidate hit fields constrain source location.
- Domain: robotic olfaction.
- Overlap score: 3/4; problem, domain and candidate-forward mechanism overlap.
- Source: DOI 10.1109/TRO.2024.3426368.

### Plume Mapping via Hidden Markov Methods

- Date: 2003.
- Problem framing: infer plume state under intermittent detections.
- Core mechanism: hidden-state/detection probabilistic model.
- Key insight: separate hidden plume state from observations.
- Domain: plume mapping.
- Overlap score: 2/4; observation object and domain overlap.
- Source: DOI 10.1109/TSMCB.2003.810873.

### Infotaxis as a Strategy for Searching without Gradients

- Date: 2007.
- Problem framing: locate a source from sparse stochastic detections.
- Core mechanism: information-driven motion under a probabilistic plume model.
- Key insight: use expected information when gradients are unreliable.
- Domain: odor/plume search.
- Overlap score: 2/4; problem/domain overlap, not persistent nuisance state.
- Source: Nature 445, 406–409.

### Bayesian inverse modeling of atmospheric transport and emissions

- Date: 2017.
- Problem framing: infer release and transport uncertainty from tracer data.
- Core mechanism: ensemble simulations, machine learning and Bayesian inversion
  over transport/emission inputs.
- Key insight: jointly account for meteorology, transport, diffusion and
  emissions rather than fixing one transport model.
- Domain: atmospheric science.
- Overlap score: 2/4; joint transport/source uncertainty overlaps, mobile GSL
  and native response-member persistence differ.
- Source: DOI 10.5194/acp-17-13521-2017.

### The Manticore Project I

- Date: 2025-05.
- Problem framing: reconstruct hidden cosmic fields from biased sparse
  observations.
- Core mechanism: Bayesian field-level inference followed by posterior
  physical resimulations.
- Key insight: infer a coherent latent initial field and propagate its
  realizations through a physical forward model with bias uncertainty.
- Domain: cosmology.
- Overlap score: 2/4; coherent latent/physical ensemble overlaps, task/domain
  differ.
- Source: DOI 10.1093/mnras/staf767.

### A unified framework for time-to-detection occupancy and abundance models

- Date: 2024-02.
- Problem framing: infer latent occupancy/abundance under imperfect detection.
- Core mechanism: time-to-detection observation models.
- Key insight: latent occurrence and observation process must be separated.
- Domain: ecology.
- Overlap score: 1/4; observation principle overlaps.
- Source: DOI 10.1111/2041-210X.14296.

### Guidelines for estimating occupancy from autocorrelated camera detections

- Date: 2024-05.
- Problem framing: occupancy inference with temporally autocorrelated
  detections.
- Core mechanism: hierarchical occupancy simulation and detection-window
  analysis.
- Key insight: pseudo-replicated correlated detections bias inference.
- Domain: ecology.
- Overlap score: 1/4; repeated-observation warning overlaps.
- Source: DOI 10.1111/2041-210X.14359.

### Data-Driven Plume Modeling for Gas Sensing Robots

- Date: 2023-05.
- Problem framing: efficient gas-leak detection in built environments.
- Core mechanism: learned plume model for gas-sensing robots.
- Key insight: replace costly dispersion evaluation with a data-driven
  surrogate.
- Domain: robotic gas sensing.
- Overlap score: 3/4 against a neural M1 surrogate; this is a collision warning.
- Source: DOI 10.1109/ICRA48891.2023.10160816.

### Gas Source Localization Using Physics-Guided Neural Networks

- Date: 2024-05.
- Problem framing: neural gas-source localization with physics guidance.
- Core mechanism: physics-guided neural inference.
- Key insight: encode dispersion physics in a learned model.
- Domain: gas-source localization.
- Overlap score: 3/4 against a neural scientific module.
- Source: DOI 10.1109/ISOEN61239.2024.10556061.

### Kim et al. 2026 lead

- Date: 2026-08.
- Problem framing: neural plume/source inference.
- Core mechanism: recent neural GSL method; exact publication status remains a
  preprint/submission lead.
- Key insight: learned physical dependence for source inference.
- Domain: robotic GSL.
- Overlap score: 3/4 against neural scientific novelty.
- Source: arXiv:2608.16221.

The JFR 2019 UAV source-term paper and 2022 review were retained as same-domain
scope checks but not promoted above PMFS for the closest-mechanism comparison.
