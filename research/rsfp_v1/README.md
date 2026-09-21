# RSFP V1 — Renormalization Source Fixed Point

Date: 2026-09-21  
Status: **CURRENT LEADING MAIN-INNOVATION CANDIDATE / STAGE-1 POSITIVE / NOT CLOSED-LOOP AUTHORIZED**

## Main thesis

**In turbulent gas-source localization, source identity should be treated as a macroscopic variable that remains stable under a finite renormalization/coarse-graining flow, while unresolved turbulent fluctuations are marginalized as microscopic nuisance rather than multiplied into the source posterior.**

This is not generic multiscale feature fusion.

The scientific object is the **scale flow of source evidence**.

Let a spatial gas observation field be repeatedly coarse-grained:
`X -> C_2(X) -> C_4(X) -> C_8(X) -> ...`

For a physically identifiable source, the source ranking should enter a stable plateau over a finite range of scales. Evidence that exists only at one microscopic resolution should not be trusted as source identity.

## Recent remote-field roots

Primary 2025 anchors:

1. Ilersich & Nair, **Learning Stochastic Multiscale Models**, NeurIPS 2025 main conference.
   - separates resolved macroscale state on a coarse mesh from unresolved stochastic microscale dynamics.

2. Hao et al., **RINO: Renormalization Group Invariance with No Labels**, NeurIPS 2025 ML4PS spotlight / arXiv:2509.07486.
   - learns representations invariant along a renormalization-group scale flow to improve robustness to simulation/data mismatch.

3. Hernandez et al., **Data-driven particle dynamics: Structure-preserving coarse-graining for emergent behavior in non-equilibrium systems**, 2025.
   - uses coarse-graining to retain emergent non-equilibrium behavior while removing microscopic degrees of freedom.

Classical physical background:
renormalization/coarse-graining has long been used in turbulence and passive-scalar problems; that history is background, not the novelty claim.

## Project-specific transfer

The present GSL hypothesis is:

- plume intermittency and transport realization are microscopic nuisance;
- source identity is a coarse observable;
- correct source evidence should persist across a range of spatial coarse-graining scales;
- posterior evidence should be released only from a **scale-stable source ranking plateau**;
- when the ranking changes under further coarse-graining, the method has left the source-identifiable scale range and should stop coarse-graining rather than forcing certainty.

Targeted novelty claim:

**source localization by identifying source-hypothesis evidence that is stable under a renormalization flow across spatial scales, then using that scale-stable macro evidence inside PMFS while treating fine-scale residuals as unresolved turbulent nuisance.**

This is distinct from:
- using a coarse grid for speed;
- multiresolution path planning;
- fusing handcrafted multiscale features;
- ordinary smoothing;
- TNQC's single-scale affine quotient.

## Stage-1 frozen data

Controlled VGR asset:

- H01/H02/H03
- SA/SB
- fast/slow
- 12 cases
- identical within-House route/timing
- native fine grid: 0.3 m
- evaluation: cross-wind source identity only

This is not yet the authoritative 300-s PMFS localization endpoint.

## Stage-1 result

Centered-cosine / positive-affine-invariant source identity after block coarse-graining:

| effective scale | factor | accuracy | mean signed margin | min margin |
|---|---:|---:|---:|---:|
| 0.3 m | 1 | 12/12 | 0.77598 | 0.00919 |
| 0.6 m | 2 | 12/12 | 0.78591 | 0.00888 |
| 1.2 m | 4 | 12/12 | 0.80231 | 0.00621 |
| 2.4 m | 8 | 12/12 | 0.83687 | 0.02869 |
| 4.8 m | 16 | 11/12 | 0.83767 | -0.60497 |

The important result is the finite stable plateau at factors 1/2/4/8, followed by failure at excessive coarse-graining.

Fine-scale residual after subtracting the block macro field:

- factor 2 residual: 10/12;
- factor 4 residual: 10/12;
- factor 8 residual: 10/12.

Thus the source signal is stronger in the macro field than in the eliminated micro residual.

## Hard controls

### Coarse-grid phase

All possible integer phase offsets:

- factor 2: 4/4 phase choices remain 12/12;
- factor 4: 16/16 remain 12/12;
- factor 8: 46/64 remain 12/12; mean accuracy 96.7%.

Therefore the signal is not tied to one special block origin.

### Spatial-value destruction

Independently shuffle gas values among occupied cells in every episode, preserving each episode's concentration distribution.

Across 100 deterministic shuffles:

- factor 2 mean accuracy: 48.6%;
- factor 4 mean accuracy: 48.8%;
- factor 8 mean accuracy: 50.2%;
- perfect 12/12 runs: 0 at every factor.

Therefore the positive result depends on spatial organization.

### Time-to-identifiability

Coarse-graining does **not** create earlier information.

Coverage remains:

- 160 s: 5/12 valid;
- 176/200 s: 5/12 valid, all valid cases correct;
- 220 s: 9/12 valid, all correct;
- 240 s: 12/12 valid, all correct.

The effect is evidence stabilization / margin strengthening after information exists, not earlier plume detection.

## Collision screen

Targeted searches found no direct GSL/OSL work that formulates source identity as a renormalization-flow fixed point or scale-stable source-hypothesis variable.

Known nearby work is not equivalent:

- multiresolution OSL planning changes environmental/planner resolution;
- turbulence RG models forward transport coefficients;
- generic multiscale ML learns dynamics across resolutions;
- RINO learns RG-invariant embeddings in high-energy physics.

No exhaustive novelty proof is claimed yet.

## Proposed main mechanism

### Renormalization-stable source evidence

For each candidate source hypothesis:

1. construct its source-consistency evidence at a hierarchy of spatial scales;
2. track candidate ordering under successive coarse-graining;
3. identify a scale interval where ordering is stable;
4. for each candidate pair, release signed evidence only if its ordering has the same nonzero sign at every predeclared scale;
5. if a pair crosses or ties at any scale, abstain for that pair;
6. aggregate stable pairwise wins/losses with final-partition physical source-space measure;
7. do not count microscopic residual fluctuations as independent source evidence.

## Next decisive gate

Do **not** go directly to closed loop.

Implement an offline 300-s R2 replay on the authoritative H01/H02/H03 × seed0/1 archive using the native PMFS `ExpectedValue(sourceProbability, 0.05)` endpoint.

Required comparators:

- native PMFS;
- frozen TNQC single-scale quotient;
- one arbitrarily chosen coarse scale;
- multiscale equal fusion;
- per-candidate multiscale lower envelope;
- **RSFP scale-stable pairwise evidence**;
- spatial-shuffle / scale-instability controls.

Promotion bar:

- pooled endpoint improvement >= 2% over native;
- at least 4/6 non-worse;
- no false-confident collapse;
- RSFP must beat fine-only, single-scale coarse smoothing, naive multiscale fusion, and the per-candidate lower-envelope control;
- scale choice / stopping rule must be truth-independent.

## Current decision

**RSFP V1 = STAGE-1 PASS.**

This is currently the leading candidate because it has:

- a clear paper-level mother idea;
- recent top-tier remote scientific roots;
- a project-specific physical interpretation;
- 12/12 source identity over a finite scale plateau;
- a destructive spatial control that collapses to chance;
- a clear failure scale at over-coarsening;
- no direct GSL novelty collision found so far.

### Frozen 300-s primary definition

For every active source-hypothesis pair `(s_i,s_j)`, compute the sign of
`q_i(scale)-q_j(scale)` at factors 1/2/4/8.

- same nonzero sign at all four scales -> one scale-stable signed pair contribution;
- any sign flip -> abstain for that pair;
- any tie -> non-comparable pair;
- pair mass = product of represented final-partition free-cell counts.

A candidate's RSFP score is its signed stable-pair mass divided by its
comparable reference pair mass, bounded in [-1,1].

This candidate-wise pairwise fixed-point score is the scientific primary.
The old `min(q_1,q_2,q_4,q_8)` construction is retained only as a required
lower-envelope control.

This definition was frozen before any RSFP 300-s result was inspected.

It is still only a candidate until the authoritative 300-s endpoint gate is positive.
