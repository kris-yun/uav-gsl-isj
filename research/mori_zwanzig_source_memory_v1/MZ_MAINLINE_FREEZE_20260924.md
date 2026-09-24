# Mori–Zwanzig Source-Memory v1 — Mainline Freeze

Date: 2026-09-24  
Branch: `research/mori-zwanzig-source-memory-v1`  
Parent evidence: Bi-Green Gate 1A independent review `02eadd90cba01c418ac6bacec8888ca3e1df13d0`

Status: **CANDIDATE MAINLINE — NOT YET ESTABLISHED**

## 1. Scientific failure that motivates this route

The frozen 630-source exact-GADEN Gate 1A showed:

- S2_W2_A truth rank mean/C/D = 1/2/1;
- S2_W2_B truth rank mean/C/D = 7/7/4;
- the B top candidates remained local to truth (roughly 0.3–0.67 m);
- independent target realizations had high cosine similarity but non-negligible realization-level L2 variation.

Thus the deterministic source-to-sensor transfer object is informative about the **source basin**, but exact-cell evidence is realization-sensitive.

The question is no longer “can forward transport be modeled more accurately?”

The new question is:

> Can the source-relevant slow/resolved dynamics be separated from realization-specific turbulent degrees of freedom whose elimination induces non-Markovian memory and orthogonal noise?

## 2. Mother theory

**Mori–Zwanzig projection / generalized master equation (GME)** from statistical mechanics and reduced-order dynamical systems.

For a high-dimensional full state (X_t), a projection onto reduced observables (z_t=P(X_t)) yields reduced dynamics of the schematic form

[
dot z(t)=R(z(t))+int_0^t K(t-	au,z(	au)),d	au+eta(t),
]

where:

- (R): resolved/Markov contribution;
- (K): memory kernel induced by eliminated degrees of freedom;
- (eta): orthogonal/unresolved dynamics.

The load-bearing idea is **not** “use more history.” It is that partial observation of turbulent transport is generically non-Markovian after unresolved flow/plume degrees of freedom are projected away.

## 3. Far-domain theory anchors

### 2026 turbulence anchor — primary

X. M. de Wit et al.,
“Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows,”
*Proceedings of the National Academy of Sciences*, 123(13), 2026.
DOI: `10.1073/pnas.2525390123`.

Relevant point: reduced Lagrangian turbulent dynamics are modeled as dependence on the current state **and past history** of reduced observables, with unresolved orthogonal dynamics representing omitted degrees of freedom. The paper reports short-time pointwise and long-time statistical recovery.

This is the strongest current parent because it is both:
- peer-reviewed 2026;
- directly about turbulence, transport and dispersion.

### 2025 biomolecular/statistical-mechanics anchor — secondary

B. Liu et al.,
“Memory kernel minimization-based neural networks for discovering slow collective variables of biomolecular dynamics,”
*Nature Computational Science* 5, 562–571, 2025.
DOI: `10.1038/s43588-025-00815-8`.

Relevant point: MEMnets abandons a purely Markovian collective-variable assumption and uses an integrative generalized master equation. Optimal slow collective variables are obtained by minimizing a time-integrated memory-kernel objective.

Public implementation:
`https://github.com/xuhuihuang/memnets`

The MEMnets neural architecture is **not** our innovation and need not be copied. It is a theoretical/computational parent showing that memory kernels can define useful reduced coordinates in another scientific domain.

## 4. GSL novelty boundary

Literature screen through 2026-09-24 found no direct paper applying:

- Mori–Zwanzig projection;
- memory-kernel minimization;
- GME-derived source collective variables;

to gas/odor/plume **source localization**.

This is only a screening result, not a claim of exhaustive novelty.

Occupied / forbidden claims:

- “using temporal history for odor localization” — occupied;
- RNN/LSTM/sequence model as novelty — too generic;
- spatial memory / bio-inspired memory navigation — occupied;
- POMDP/sequential inference — occupied;
- generalized Langevin equations as a forward plume simulator — already used in atmospheric dispersion (e.g. QES-Plume);
- “non-Markovian” as a label without an identified memory kernel — insufficient.

The candidate novelty is narrower:

> **MZ-projected source evidence:** infer source identity through reduced observables whose memory structure separates persistent source-conditioned dynamics from orthogonal turbulent realization noise, then use that evidence to update a PMFS-style source probability map.

## 5. Why this is scientifically different from previous routes

Previous failed routes mostly changed one of:

- forward transport representation;
- field prediction;
- source-to-sensor kernel;
- causal/compositional parameterization;
- deterministic lineage.

MZ-v1 instead treats the observed plume as a **partial projection of a stochastic high-dimensional system**. It asks whether the missing degrees of freedom leave a measurable, source-dependent memory signature.

If the memory term is not load-bearing for source discrimination, this entire family must stop even if a neural sequence model can be made to fit trajectories.

## 6. Existing offline evidence before new simulation

From the frozen 630-source Gate 1A package:

- simple temporal mean / moments / quantiles / Haar-like summaries did not rescue B;
- ordinary covariance/Mahalanobis whitening did not rescue B;
- linear realization-invariant generalized-eigen projections did not legitimately rescue B under target-independent model selection;
- coarse target/prediction histories show strong lag correlation;
- simple AR(1) prewhitening did not rescue B.

Therefore the hypothesis is **not** “smoothing or one autoregressive term will solve it.”

The only reason to proceed is to test whether a genuine finite-memory reduced dynamics contains source-discriminative information unavailable to the instantaneous/Markov model.

## 7. Frozen progression

1. **M0 — dense-history physical/mechanistic gate.**
   Test >=143 arbitrary source identities (planned: all 630) with multiple independent W2 realizations. Compare Markov reduced dynamics against finite-memory reduced dynamics under held-out realization source retrieval.

2. **M1 — MZ source collective variable.**
   Only after M0 PASS. Adapt memory-kernel minimization / slow collective-variable theory so the learned representation preserves source identity while rejecting orthogonal plume realization noise.

3. **M2 — PMFS probability-map integration and cross-House test.**
   Only after M1 PASS. No closed loop before cross-realization and unseen-source offline gates pass.

## 8. Stop rule

If M0 shows that finite memory improves trajectory prediction but **not held-out source discrimination**, decide:

`MZ_M0_FAIL_STOP_MEMORY_MAINLINE`

Do not rescue with LSTM/Transformer/GNN.

If M0 shows reproducible held-out source-rank improvement across the frozen arbitrary-source bank, decide:

`MZ_M0_PASS_MEMORY_IS_LOAD_BEARING`

This only authorizes M1; it does not establish the paper’s main innovation.
