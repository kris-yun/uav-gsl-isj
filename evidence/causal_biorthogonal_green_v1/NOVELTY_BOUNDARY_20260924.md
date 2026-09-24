# Bi-Green Novelty Boundary — frozen before Gate 1A results

Date: 2026-09-24
Branch: `research/causal-biorthogonal-green-v1`

## Claims that are already occupied and forbidden

1. **"Use a Green function for gas source localization."**
   Occupied by Prieto Ruiz et al., EUSIPCO 2024,
   *Physics-Guided Neural Networks for Distributed Sparse Gas Source
   Localization Using Poisson's Equation and Green's Function Method*,
   DOI: 10.23919/EUSIPCO63174.2024.10715286.

2. **"Learn a Green operator that generalizes across source functions."**
   Occupied at the parent-operator level by Yoo et al.,
   *Neural Green's Functions*, NeurIPS 2025. Their setting is a neural
   solution operator for linear PDEs whose operators admit eigendecomposition,
   with source/boundary-function and irregular-geometry generalization.
   This project may transfer that mother idea but cannot claim it.

3. **"Learn backward transport / Schrödinger bridge for chemical source
   localization."**
   Occupied by Carbone & Piro, *Learning Backward Transport for Source
   Localization*, arXiv:2607.26892 (2026), which explicitly formulates
   chemical-source localization through a backward passive-tracer propagator,
   Schrödinger bridge and Langevin sampling.

4. **"Direct/adjoint biorthogonal receptivity for a non-normal flow operator."**
   This is an external mother-theory ingredient rather than our novelty.
   Kalathoor & Oefelein, arXiv:2606.20819 (2026), use direct/adjoint eigenmodes,
   an adjoint receptivity projection and a biorthogonal decomposition for a
   reacting mixing layer.

5. **"Non-Hermitian biorthogonal neural dynamics."**
   Also an external mother-theory ingredient. UniPhy, arXiv:2602.09030 (2026),
   uses non-Hermitian biorthogonal spectral operators in continuous weather
   modeling. It is currently a preprint and must not be described as a
   peer-reviewed top-conference/top-journal source unless that status is later
   verified.

## Candidate claim that remains open only if the gates pass

The candidate contribution is not "Green's function" or "adjoint" alone.

The potentially novel construction is:

> A causal, candidate-conditioned, non-self-adjoint source-to-sensor transfer
> operator for UAV gas-source localization, represented with distinct
> source-receptivity and sensor-response factors, queried at arbitrary unseen
> source coordinates, and used directly as the likelihood engine of a PMFS
> source-probability map without reconstructing a complete plume field.

The load-bearing scientific distinction is the combination of:

- arbitrary-source query, not two-source coordinate regression;
- non-self-adjoint directional transport, so source and sensor factors are not
  tied by a symmetry assumption;
- direct source-to-sensor likelihood, not full-field surrogate -> inverse;
- stochastic transfer law robust to independent plume realizations;
- PMFS-style final source-probability map;
- unseen-source generalization as the decisive learned-operator test.

## Evidence ladder required before any novelty claim

### Gate 1A — exact physical source-identifiability

630 arbitrary free source positions, W2, two independent target realizations,
two independent prediction RNG seeds. Exact GADEN forward oracle.

Failure kills the whole source-to-sensor Green family for this project.

### Gate 1B — adjoint/Bi-Green parity

No candidate-specific GADEN forward calls at inference. Build the physical
3-D stochastic adjoint/source-to-sensor kernel and require source-rank parity
with Gate 1A.

Failure means the physical oracle is identifying but the proposed Bi-Green
realization is not supported.

### Gate 2 — unseen-source biorthogonal compression

Train without a held-out subset of source coordinates. The compressed
left/right operator must preserve the physical rank on unseen source
coordinates and independent plume realizations.

Only Gate 1A + Gate 1B + Gate 2 together can freeze the main innovation.

## Publication-status caution

The strongest verified peer-reviewed parent in the current chain is Neural
Green's Functions at NeurIPS 2025. The two 2026 biorthogonal examples above are
useful current far-domain scientific anchors but are arXiv preprints as of this
freeze. They support the direction of second-order innovation; they do not by
themselves satisfy a "2026 top journal/conference" citation requirement.

If the main mechanism survives the data gates, a separate literature gate must
replace or supplement those 2026 preprints with the strongest peer-reviewed
non-Hermitian/biorthogonal operator sources available at manuscript freeze.
