# Interim first-paper innovation analysis — 2026-10-07

## Executive decision

**Do not restart another PMFS feature search and do not revive the transferable plume-world-model route.**

The most defensible current first-paper direction is provisionally:

> **Physics-probabilistic UAV gas-source inversion under lakeshore 3D transport uncertainty, with source-task-oriented use of sparse meteorology.**

This is **not** yet PRIMARY_GO. It is **PRIMARY_CANDIDATE / PHENOMENON-GATE REQUIRED**.

The scientific question is not “can we reconstruct wind more accurately?” and not “can we add a 3D feature to PMFS?” It is:

> **Do wind-field errors with similar global magnitude cause systematically different source-inversion damage depending on where/which flow structures are wrong; and if so, can the GSL estimator prioritize/propagate the transport information that matters for source posterior rather than optimizing global wind-field accuracy alone?**

If the phenomenon gate fails, stop this line before inventing a new network.

---

## Why the project needs this pivot

The recent evidence chain is coherent:

1. R0-C1: an initially promising vertical dynamic signal failed equal-height independent confirmation in 2/4 contexts.
2. R0-D: transport context clearly matters locally, but the driver is not repeated across Houses; H01 is mainly gas-sensitive, H02 mainly wind-sensitive.
3. P0: a transferable plume-state dynamics model did not satisfy cross-context transfer gates.

The shared lesson is that the bottleneck is not simply “missing one better plume feature”. The plume/source relationship is strongly context dependent.

The next question therefore has to move upstream to the **transport model actually used by source inference**.

---

## Target research object

Still strictly:

**UAV gas source localization / source inversion.**

Required main outputs remain:
- source coordinate;
- source posterior / probability map;
- localization error;
- true-source rank / Top-k / MAP or equivalent success metrics;
- calibrated uncertainty if possible.

Wind/plume outputs are supporting variables.

---

## What prior work already covers

### 1. PMFS / probabilistic mapping + online dispersion
Ojeda et al., IEEE TRO 2024:
**Robotic Gas Source Localization with Probabilistic Mapping and Online Dispersion Simulation**
DOI: 10.1109/TRO.2024.3426368

Core idea: contrast online candidate-source dispersion simulation with gas concentration / gas-hit mapping to form probabilistic source evidence in complex indoor turbulent scenes.

Implication for us:
- PMFS remains an important strong baseline.
- It already combines probability and forward transport.
- Therefore our novelty cannot be “probability map + forward simulation”.

### 2. Topography-aware learned GSL
Tian et al., ICRA 2025:
**Deep Learning Based Topography Aware Gas Source Localization with Mobile Robot**
DOI: 10.1109/ICRA55743.2025.11128134

It explicitly integrates gas observations, wind and a 2D occupancy/topography context and reports robustness under dynamic wind/obstacles.

Implication:
- “add map/topography to learned GSL” is already occupied.
- Our method must go beyond 2D map context by addressing physically structured **3D transport uncertainty / source-likelihood distortion**.

### 3. Sparse wind-field reconstruction
Gao et al., Computer-Aided Civil and Infrastructure Engineering 2024:
**Urban wind field prediction based on sparse sensors and physics-informed graph-assisted auto-encoder**
DOI: 10.1111/mice.13147

It reconstructs high-resolution urban wind fields from sparse sensors and embeds continuity constraints.

2026 work goes further:
- GenDA, ICML 2026, geometry-aware generative wind data assimilation from sparse fixed/trajectory observations.
- Physics-informed street-canyon sensor placement, Sustainable Cities and Society 2026.
- Rooftop sparse-sensor reconstruction, Building and Environment 2026.
- Hierarchical urban wind reconstruction and GFNO, Building and Environment 2026.

Implication:
- “sparse sensors → dense 3D wind” is not a novel problem by itself.
- A pure wind-reconstruction first paper would drift away from UAV GSL.

### 4. Wind reconstruction for chemical spill dispersion already exists
Wang et al., Chinese Journal of Chemical Engineering 2019:
**Wind field reconstruction for the dispersion modeling of accidental chemical spills on complex geometry**
DOI: 10.1016/j.cjche.2019.02.029

It used CFD databases + PCA/ELM + local anemometer correction + sensor placement to reconstruct wind for chemical-spill consequence modeling.

Implication:
- “wind reconstruction for gas dispersion” is also not novel by itself.

### 5. Bayesian / inverse source estimation is a mature alternative backbone
Examples:
- Hutchinson et al., Journal of Field Robotics 2019, UAV source-term estimation via Bayesian inference and analytical advection-diffusion models.
- Science of the Total Environment 2024: Bayesian + adjoint inverse source estimation under dynamic wind.
- Building and Environment 2025: time-varying source estimation via Bayesian inference + unsteady adjoint equations.
- 2025–2026 drone methane work combines Bayesian inverse modeling with adaptive path planning.

Implication:
- The first-paper backbone should be selected between **probabilistic candidate-source inference / Bayesian source-term inversion / physics-probabilistic hybrid**, not assumed to be PMFS.

---

## Provisional gap

A targeted literature sweep did **not** identify a paper that clearly closes all of:

**sparse UAV/ground meteorology  
→ lakeshore/complex-terrain 3D transport-state inference  
→ gas dispersion/source-receptor prediction  
→ source posterior/localization  
→ task objective explicitly tied to source-inversion utility rather than only wind-field RMSE.**

This is a **targeted-search observation, not a claim of world-first novelty**. Pro must perform the systematic literature audit.

The candidate knowledge gap is therefore:

> Wind-field reconstruction and GSL are usually optimized as separate problems. Existing wind reconstruction emphasizes field fidelity, while GSL methods consume local/precomputed wind information. It remains unclear whether equal global wind error is equal in source-inversion consequence, and which spatial/structural wind errors most distort source likelihood in a lakeshore 3D transport environment.

---

## Provisional method family if the phenomenon is confirmed

### Preferred backbone
A **physics-probabilistic source inversion** framework, not necessarily PMFS internals.

Candidate formulation:

1. Sparse ground/UAV meteorological observations define a posterior or ensemble over plausible 3D wind/transport states.
2. Each candidate source is evaluated under that transport uncertainty.
3. Source likelihood marginalizes over transport uncertainty rather than treating one estimated wind field as truth:
   p(y | s, O_w) = ∫ p(y | s, U) p(U | O_w) dU.
4. Transport-field approximation is allocated preferentially to modes/regions that change source likelihood/posterior most strongly.
5. Output remains a 2D source probability map + source coordinate.

### Potential main novelty if W0 confirms it
**Source-posterior / source-likelihood-oriented transport relevance**, rather than global wind RMSE.

Longer-term implementation options:
- reduced CFD wind basis + sparse-data assimilation;
- ensemble wind library;
- posterior-weighted transport relevance mask;
- finite-difference source-likelihood sensitivity;
- a learned wind prior only if simple reduced-basis methods fail.

Do not choose GenDA / diffusion / PINN merely because they are new. They are candidate tools after the mechanism is established.

---

## Candidate competition

### Candidate A — task-sensitive 3D transport uncertainty in probabilistic source inversion
**Status: PRIMARY_CANDIDATE / gate required**

Strengths:
- directly remains GSL;
- fits lakeshore 3D transport;
- explains why generic wind RMSE is insufficient;
- preserves interpretable source posterior;
- can use FSR controlled CFD cleanly;
- PMFS can be a fair strong baseline without constraining the method.

Risks:
- novelty depends on W0 phenomenon being real;
- wind uncertainty marginalization may be computationally expensive;
- task sensitivity must not use true source at inference.

### Candidate B — 3D topography/wind-aware direct learned source-posterior predictor
**Status: BACKUP_CANDIDATE**

Extend ICRA-2025-style topography-aware GSL from 2D occupancy/local wind to 3D lakeshore geometry and sparse meteorology.

Strengths:
- straightforward implementation;
- source posterior directly optimized.

Risks:
- high data demand;
- domain shift likely severe;
- novelty may be judged incremental relative to topography-aware GSL;
- recent P0 transfer failure warns against relying on learned latent generalization.

### Candidate C — pure sparse 3D wind reconstruction + downstream GSL demonstration
**Status: STOP as first-paper main innovation**

Reason:
- dense prior art in 2019–2026;
- may publish as meteorology/flow reconstruction, but violates the user's requirement that the first paper be fundamentally UAV GSL.

### Candidate D — task-sufficient source–plume world model
**Status: STOP under current evidence**

Reason:
- R0C/R0D/P0 do not provide the transferable dynamic-state evidence needed to justify it.

### Candidate E — multi-UAV information-driven / RL search
**Status: DEFER TO RESEARCH CONTENT 2**

Reason:
- good downstream use after source posterior/plume state are available;
- substantial prior art already exists;
- first paper needs a stronger lakeshore-specific source-inference contribution.

---

## Proposed paper-level claim if and only if W0 passes

Not:
“we reconstruct wind more accurately.”

Instead:
> **For lakeshore UAV GSL, wind errors are task-anisotropic: equal global wind-field error can produce unequal source-posterior distortion. A source-inversion-oriented transport representation therefore yields more reliable source inference than globally optimized wind reconstruction or local-wind baselines under equal sensing budgets.**

This claim has a clear falsifiable phenomenon and a direct reviewer-facing contribution.

---

## Boundary conditions

- FSR geometry is real-site-constrained, but meteorological forcing may be controlled simulation.
- Controlled CFD must never be described as measured FSR weather.
- House H01/H02 are stress tests, not lakeshore evidence.
- Public shoreline atmospheric datasets may validate meteorological structure, but without known leak labels cannot validate source-localization accuracy.
- A method is not successful because wind/plume RMSE improves; the first paper must improve or more reliably calibrate source inference.
