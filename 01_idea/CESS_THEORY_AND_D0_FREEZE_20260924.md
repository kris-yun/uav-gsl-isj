# Causal-Emergent Source Scale v0 — Theory and D0 Freeze

Date: 2026-09-24  
Branch: \`research/causal-emergent-source-scale-v0\`

Status: **PROVISIONAL MAIN-INNOVATION CANDIDATE — D0 EXPLORATORY SIGNAL, D1 NOT YET AUTHORIZED**

## 1. Why this route exists

R0 independently established that repeated plume realizations support reproducible source-conditioned stochastic statistics. The most stable object was not a full 300-D concentration distribution but the binary encounter/support structure.

At the same time, several failed routes showed a recurring spatial pattern:

- exact 0.30 m source-cell identity can be reordered by a fresh stochastic realization;
- the highest-scoring alternatives often remain spatially close to the true source;
- therefore failure at micro-cell rank does not automatically imply loss of source-basin information.

The scientific question is now:

> **At what spatial source scale does the encounter process carry the maximum reproducible source information, and can that scale be derived from data rather than chosen by hand?**

This is different from manually smoothing a PMFS map or choosing a 0.5/1.0 m tolerance after seeing errors.

## 2. Far-domain mother theory

Primary theory family:

**causal emergence / effective information / information-theoretic coarse-graining.**

Recent anchors:

1. Jiang Zhang, Ruyi Tao, Mingzhe Yang et al.,
   **Dynamical reversibility and a new theory of causal emergence based on SVD**,
   *npj Complexity* (2025),
   DOI: \`10.1038/s44260-025-00028-0\`.

2. Kaiwei Liu, Pan Lingzhi, Zhipeng Wang et al.,
   **Singular-value-decomposition-based causal emergence for Gaussian iterative systems**,
   *Physical Review E* 112(5) (2025),
   DOI: \`10.1103/mfct-sxn5\`.

3. Mingzhe Yang, Zhipeng Wang, Kaiwei Liu et al.,
   **Finding emergence in data by maximizing effective information**,
   *National Science Review* 12(1), article nwae279.
   DOI: \`10.1093/nsr/nwae279\`.
   Published online 2024; journal volume/issue is 2025.
   Public implementation family:
   \`https://github.com/Matthew-ymz/Code-for-Finding-emergence-in-data-5.2\`
   and earlier NIS code:
   \`https://github.com/jakezj/NIS_for_Causal_Emergence\`.

These works motivate a general principle:

> a noisy or degenerate microscopic representation can possess less normalized effective information than a suitable coarse-grained macro representation.

## 3. GSL-specific second-order adaptation

The micro causal variable is the candidate source cell:

\[
S\in\mathcal S.
\]

The effect variable is the observed encounter/support history:

\[
H\in\{0,1\}^{T\times Q}, \qquad H_{tq}=\mathbf 1[C_{tq}>\tau].
\]

For the current R0 operator:
- \(T=10\)
- \(Q=30\)
- frozen exploratory threshold \(\tau=0\), because the existing data are exact simulator concentration rather than a physical sensor threshold.

The source intervention channel is:

\[
p(h\mid do(S=s)).
\]

A spatial coarse-graining is a deterministic map:

\[
g:\mathcal S\rightarrow\mathcal M,
\]

where each macrostate \(m\in\mathcal M\) contains spatially contiguous micro source cells.

The macro intervention is defined before seeing validation data as a uniform intervention over the microcells belonging to that macrostate:

\[
p(h\mid do(M=m))
=
\frac{1}{|\mathcal S_m|}
\sum_{s\in\mathcal S_m}
p(h\mid do(S=s)).
\]

This explicit intervention contract prevents an unequal-size macrostate from gaining information merely because it contains more sampled source cells.

## 4. Effective-information object

Under a uniform intervention distribution over the current source states,

\[
p(M=m)=1/|\mathcal M|,
\]

the macro effective information is the mutual information of the interventional channel:

\[
EI(M\rightarrow H)=I_U(M;H).
\]

Raw \(EI\) tends to favor more states. To ask whether a representation is efficiently distinguishable per available source-state bit, define

\[
\eta(M)=\frac{I_U(M;H)}{\log |\mathcal M|}.
\]

The candidate causal-emergence signal is a reproducible increase in normalized source information:

\[
\Delta\eta(g)=\eta(g(S))-\eta(S).
\]

### Important information-theory boundary

Because \(M=g(S)\), ordinary mutual information obeys data processing when compared under the same induced distribution. We therefore do **not** claim that arbitrary coarse-graining creates raw Shannon information.

The scientific claim, if later validated, concerns:

1. a macro intervention distribution defined at the macro level;
2. normalized effective information / causal effectiveness;
3. reproducible distinguishability at an emergent source scale.

This must not be described as violating the data-processing inequality.

## 5. Finite-sample held-out lower bound

The full \(p(h|m)\) is high-dimensional. D0 therefore uses a decoder-based lower bound rather than pretending to estimate the exact 300-D joint law.

For a held-out decoder \(q_\phi(m|h)\):

\[
I(M;H)
=
\log |\mathcal M|-H(M|H)
\ge
\log |\mathcal M|
-
\mathbb E[-\log q_\phi(M|H)].
\]

Define the held-out normalized lower bound:

\[
\underline{\eta}_{val}(M)
=
1-
\frac{\mathrm{CE}_{val}}{\log |\mathcal M|}.
\]

This quantity can be negative when the decoder is badly misspecified; that is allowed and informative.

D0 uses a deliberately simple factorized Bernoulli encounter decoder. It is only a measurement instrument for the information lower bound, not the proposed final localization model.

## 6. Spatial hierarchy requirement

A valid macrostate must be spatially coherent.

D0 uses a Ward hierarchy built **only from source x-y coordinates**. Plume observations cannot determine the hierarchy in D0.

This gives a nested set of candidate source resolutions with different macrostate counts.

The spatial hierarchy is compared against random partitions with identical macrostate-size vectors.

If random non-spatial grouping performs similarly, then “fewer classes” rather than source geometry explains the gain and the causal-emergence interpretation fails.

## 7. R0 exploratory D0 signal

Using the existing 18-source ×16-realization R0 calibration panel:

- first 8 realizations are used to estimate the encounter decoder;
- last 8 are held out;
- direction is reversed and repeated;
- smoothing is frozen at Beta(0.5,0.5) / Jeffreys pseudocount;
- spatial Ward hierarchy is generated from coordinates only.

The held-out normalized lower bound exhibits a non-monotonic relation with source resolution:
fine microstates are less efficient than several intermediate spatial macro partitions, whereas excessive merging eventually loses information.

Spatial partitions also substantially outperform random partitions with the same cluster-size vectors.

This is an exploratory object-selection result only because:
- the R0 panel has only 18 source locations;
- it was inspected after R0;
- it cannot determine a physical 0.5–1 m source scale;
- it does not satisfy the >=143-source mainline requirement.

## 8. Why Track A is currently auxiliary, not main

R0 also shows a real temporal-history signal.

A first-order binary Markov encounter decoder on the 18-source R0 panel improves held-out source discrimination over independent encounters, and temporal-order permutation weakens the advantage.

Therefore encounter history is load-bearing.

However, 2025 olfactory-search work already studies realistic encounter statistics and spatiotemporal correlations:
- *Exploring Bayesian olfactory search in realistic turbulent flows*, *Physical Review Fluids* (2025), DOI \`10.1103/9q6q-nlxc\`.

2026 olfactory / methane-search literature also discusses correlation-aware updates.

Moreover, the current R0 operator has only 10 temporal snapshots, so it cannot justify continuous-time point-process, inter-whiff-duration, or true first-passage claims.

Track A is retained as a likely **auxiliary temporal likelihood module**, not the current paper-level main innovation.

## 9. Prior-art boundary for the main candidate

Do NOT claim novelty for:
- smoothing a PMFS probability map;
- manually grouping nearby source cells;
- multiresolution grids alone;
- binary encounter likelihood;
- ordinary clustering;
- standard mutual information;
- NIS/NIS+ itself;
- causal emergence in general.

The possible new GSL contribution is narrower:

> **an intervention-defined, information-optimal source coarse-graining that discovers the source resolution at which turbulent encounter observations are maximally reproducible, and uses that emergent source macrostate as the PMFS inference state.**

A literature search has not yet found this causal-emergence/effective-information source-resolution mechanism in gas/odor source localization.

## 10. Provisional architecture if the mainline survives

### Main innovation
**Causal-Emergent Source Scale (CESS)**:
derive source macrostates by maximizing validated intervention-based source information under spatial-contiguity constraints.

### Auxiliary candidate 1
**Temporal encounter-history likelihood**:
use discrete event-history dependence beyond independent encounter probability.

### Auxiliary candidate 2
**Macro-to-micro calibrated PMFS representation**:
retain probability over emergent macrostates; only refine within a macrostate when additional evidence supports micro resolution.

Auxiliary modules are not authorized for full development until the CESS main gate passes.

## 11. D0 decision

Current status:

\`CESS_D0_ADVANCE_TO_GATE_DESIGN\`

This means only:
- the mother theory is relevant;
- the R0 object is compatible;
- exploratory macro-information signal exists;
- a >=143-source falsification gate is worth designing.

It does **not** establish a main innovation and does not authorize closed-loop work.

## 12. Next required action

Before generating new GADEN realizations, freeze D1:

1. >=143 equal-area 0.30 m micro source cells;
2. spatial hierarchy determined without plume validation data;
3. multi-realization development/validation split justified by R0;
4. micro versus macro normalized information lower bounds;
5. equal-size-vector random partition controls;
6. source-basin and exact-cell metrics kept separate;
7. no post-result scale selection;
8. explicit STOP rule.

D1 simulation is not authorized until that contract is reviewed and frozen.
