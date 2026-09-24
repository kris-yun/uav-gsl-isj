# Causal Biorthogonal Source-to-Sensor Operator — Gate 1A Freeze

Date: 2026-09-24  
Branch: `research/causal-biorthogonal-green-v1`  
Parent: `c38c3e0e0d3a68b4cc734abf0fa262974670db37`  
Status: **FROZEN OFFLINE EXACT-PHYSICS ORACLE; NO CLOSED LOOP AUTHORIZED**

## 1. Why this gate exists

The previous source-lineage line is frozen as
`L1_FAIL_STOP_SOURCE_LINEAGE_MAINLINE`: deterministic 3-D physics explains most
predictable one-step filament motion, while the learned residual is at the
stochastic noise floor.

The unresolved problem is therefore inverse identifiability over arbitrary
source coordinates, not another forward-field residual model.

Hard project rule from this point onward:

> No result obtained only on the two intervention sources S1/S2 is admissible as
> evidence for a new main innovation. The first source-identifiability test must
> contain at least 143 arbitrary source hypotheses.

## 2. Candidate scientific object

The candidate object is the causal source-to-sensor transfer operator

[
G(t,x_q\mid \tau,x_s;W,O),
]

with a non-self-adjoint transport operator. A later compressed model may use
left/right source-receptivity and sensor-response factors, but **Gate 1 contains
no neural network**.

This project does not claim that using a Green function in gas-source
localization is new. Prior art already includes:

- V. S. Prieto Ruiz et al., *Physics-Guided Neural Networks for Distributed
  Sparse Gas Source Localization Using Poisson's Equation and Green's Function
  Method*, EUSIPCO 2024, DOI 10.23919/EUSIPCO63174.2024.10715286.
- S. Yoo et al., *Neural Green's Functions*, NeurIPS 2025 / arXiv:2511.01924,
  which learns source/query Green operators for linear PDEs and irregular
  geometries.
- S. P. Kalathoor and J. C. Oefelein, *Receptivity and Biorthogonal
  Decomposition in a Reacting Temporal Mixing Layer*, arXiv:2606.20819 (2026),
  which uses direct/adjoint mode pairs and biorthogonal receptivity for a
  non-normal reacting-flow operator.

Potential novelty is only the validated gas-localization construction:
candidate-conditioned, causal, non-self-adjoint source-to-sensor transfer used
directly to update a PMFS-style source probability map.

## 3. Why Gate 1A is exact forward physics before adjoint code

The frozen GADEN benchmark measured a 300 s realization at about 1.9 s wall
time on the verified VM binary. Therefore there is no scientific reason to
confound two questions:

1. is the physical source-to-sensor transfer object itself source-identifying?
2. can an adjoint / Bi-Green implementation approximate it efficiently?

Gate 1A answers (1) with the exact frozen simulator. If exact physics fails,
adjoint/neural compression is irrelevant.

## 4. Frozen House02 W2 target

Development-only environment: House02.

Wind:
`3,5-1_slow` = W2.

Target source:
[
S2=(-4.342730045, 2.899120331, 0.20);m.
]

Independent target realizations already frozen:

- `S2_W2_A`, GADEN RNG seed `2026092301`;
- `S2_W2_B`, GADEN RNG seed `2026092302`.

Each target supplies 10 exact GADEN concentration slices at the frozen
post-warmup indices `100,150,...,550` (approximately 50--275 s).

## 5. Frozen observation set

Use the already-frozen geometry-only 5x6 equal-area closest-free probe set from
`m4_c05_local_compare_20260923_frozen_v2/sparse_rank_diagnostic.json`.

This produces:

- 30 source-blind spatial probes;
- 10 target times;
- 300 concentration observations per realization.

Probe selection uses occupancy only and is independent of plume values and
source truth.

This is a controlled physical-identifiability gate, not a closed-loop flight
test. Existing HCMC 300 s trajectories are W1 (`3,5-1_fast`) and therefore
must not be mislabeled as W2 evidence.

## 6. Frozen arbitrary-source bank

Source support is derived from the House02 PMFS terminal-candidate manifest
`H02_R2026092212/context_bank/source_update_0001/candidate_manifest.csv`.

The manifest contains 164 quadtree leaves. Expanding each leaf onto the frozen
0.30 m PMFS source grid and deduplicating produces **631 arbitrary source-grid
positions** before the occupancy/free-space check.

Grid-cell centers are

[
x_i=x_{min}+0.15+0.30i,qquad
y_j=y_{min}+0.15+0.30j.
]

The target S2 location is exactly support cell `(i,j)=(3,34)`, so no
nearest-center surrogate is needed.

No source coordinate is learned from S1/S2.

## 7. Exact prediction bank

For every free source support cell, run the verified frozen GADEN generator
under W2 with two prediction seeds that are distinct from target A/B:

- C = `2026092401`;
- D = `2026092402`.

All other simulator parameters are identical to the frozen C0.5 contract:
300 s, dt 0.1 s, 7 filaments/s, sigma0 10 cm, gamma 15 cm^2/s,
filament-noise parameter 0.01, gas type 10, looping W2 iterations 1..10.

Extract the same 10 spatial slices and the same 30 probes. Retain only the
300-value probe vector plus hashes; delete temporary raw realizations after
successful extraction.

For each source cell, prediction is the arithmetic mean of C and D. C and D
are also retained separately for stability diagnostics.

## 8. Frozen rank score

Primary score for candidate source s and target y is

[
E(s)=\frac{\|\bar c_s-y\|_2^2}
          {\|y\|_2^2+10^{-12}}.
]

No candidate-specific amplitude fit, no offset fit, no source-dependent
hyperparameter, and no truth-based tuning is allowed.

Secondary diagnostics only:

- `log1p` normalized SSE;
- C-only rank;
- D-only rank;
- top-10 candidate coordinates and distances to S2.

Primary ranking is raw-ppm normalized SSE from the C/D mean.

## 9. Gate decision

Gate 1A **PASS** requires, for both independent targets A and B:

1. at least 143 free arbitrary source positions are scored;
2. the exact S2 support cell `(3,34)` has primary rank <= 3;
3. its C-only and D-only ranks are each <= 10.

Anything else is:

`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`

and stops Green / adjoint / biorthogonal / learned source-to-sensor compression
as the main line.

A PASS does **not** freeze the main innovation. It only authorizes Gate 1B:
construct a 3-D stochastic adjoint kernel and require rank/parity against this
exact forward oracle without candidate-specific forward simulation.

No ROS/closed-loop work is authorized by Gate 1A alone.
