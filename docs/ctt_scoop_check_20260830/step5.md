# Step 5 — Candidate deep dive

Timestamp: 2026-08-30

## PMFS

- Verified setup: mobile robot, online candidate dispersion simulation,
  probabilistic gas-hit maps and Bayesian source localization.
- Scope: same application and baseline; does not establish the exact CTT
  source–native-response-member joint state.
- Refined overlap: problem match, application match, candidate-forward partial
  mechanism match, key persistence insight differs.

## Lucas et al. 2017

- Verified setup: controlled tracer release; ensemble WRF configurations and
  Bayesian inversion constrain meteorology, transport, diffusion and
  emissions.
- Scope: atmospheric source-term inversion, not mobile closed-loop GSL.
- Refined overlap: joint transport/source uncertainty matches partially;
  persistent native member across robot stops and PMFS replacement differ.

## Manticore Project I

- Verified method: BORG field-level Bayesian inference samples a latent initial
  field and evolves posterior realizations through an N-body solver while
  jointly accounting for observational bias.
- Scope: cosmic density/velocity reconstruction, not gas transport.
- Refined overlap: coherent latent physical realization and posterior
  resimulation match; source target, event sensor and planner loop differ.

## Farrell et al. 2003 and MEE 2024 occupancy papers

- Verified principle: hidden presence/plume state and imperfect detection are
  distinct; temporally autocorrelated repeat detections can bias uncertainty.
- Scope: plume mapping/ecology, not the exact source–transport joint filter.
- Refined overlap: M3 object is established and cannot be standalone novelty.

## Jin 2023 and Prieto Ruiz 2024

- Verified scope from official conference records: learned plume modelling for
  gas sensing robots and physics-guided neural gas-source localization.
- Refined overlap: a neural plume/source-conditioned scientific module has
  high overlap. Restricting a model to exact forward-operator parity changes
  its engineering contract, not enough to make neural surrogacy the main
  scientific novelty.

Coverage limitation: full text was available for Manticore and Lucas through
publisher/PDF sources. Some IEEE records were verified through DOI metadata and
official abstract records rather than unrestricted full text. The limitation
is preserved; no unsupported full-paper claim is made.
