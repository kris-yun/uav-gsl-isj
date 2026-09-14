# Big-Science Theory Map and Novelty Boundaries

Date: 2026-09-14

This file separates **mother theories we can legitimately borrow** from **claims that are already occupied by prior work**.

The project goal is not to collect prestigious citations. A mother theory is useful only when it explains an observed failure mechanism and creates a falsifiable GSL module.

---

# 1. PRIMARY MOTHER THEORY — Persistent excitation / informativity / experiment design

## 1.1 Scientific field

Control theory, system identification, optimal experimental design, inverse problems.

## 1.2 Core principle

A parameter cannot be reliably identified when the experiment does not sufficiently excite the response directions associated with that parameter.

This is exactly the pattern now visible in the project: source-response matrices may be numerically full rank while the weakest source direction has negligible amplitude.

## 1.3 2026 support

### Automatica 2026

**Ao Cao, Fuyong Wang — Informativity conditions for multiple signals: Properties, experimental design, and applications**

https://doi.org/10.1016/j.automatica.2026.112868

Key transferable idea:

- persistent excitation is fundamentally about data richness / rank;
- multiple individually weak signal segments can be designed to become collectively informative;
- experiment design can synthesize excitation conditions.

Direct project mapping:

```text
multiple input/signal trajectories
        -> multiple UAV trajectories / sensing episodes
collective informativity
        -> stacked source-response operator retains all source modes
```

This is the strongest current mother theory for a possible **second module** if one trajectory cannot excite all source directions.

### Annual Reviews in Control 2026

**Control-oriented system identification: Classical, learning, and physics-informed approaches**

https://doi.org/10.1016/j.arcontrol.2026.101067

Useful principle:

- identification should not be judged only by prediction error;
- data/model design must preserve properties needed by downstream analysis/control;
- experiment design and identifiability remain central challenges.

Project translation:

> a gas forward model that predicts average concentration well is not enough if the resulting measurement operator destroys source identifiability.

---

# 2. PRIMARY SUPPORTING THEORY — Optimal Experimental Design (OED)

## 2.1 Statistics and Computing 2026

**Pathiraja, Schillings, Wacker — An optimal experimental design approach to sensor placement in continuous stochastic filtering**

https://doi.org/10.1007/s11222-026-10855-3

The paper treats sensor placement / observation schedules as design variables for filtering and inverse problems.

Useful principle:

> data acquisition itself is part of the estimator design.

What we may borrow:

- observation location/time should be optimized rather than accepted as fixed;
- filtering quality depends on measurement design;
- experimental design can be coupled to sequential estimation.

What is **not** novel for us:

- generic sensor placement;
- generic expected-information maximization;
- generic optimal experimental design.

## 2.2 ICML 2026 — important novelty collision

**Pérez-Vieites, Iqbal, Särkkä, Baumann — Online Bayesian Experimental Design for Partially Observed Dynamical Systems**

ICML 2026.

https://arxiv.org/abs/2511.04403
https://icml.cc/virtual/2026/poster/66678

This work develops online Bayesian experimental design for partially observed nonlinear dynamical systems, including a **moving source location task**.

Therefore the following cannot be our main novelty:

```text
online Bayesian experimental design for source localization
maximize expected information gain to choose the next measurement
active sensing in a partially observed source-location problem
```

Our novelty boundary, if it survives experiments, must be narrower:

> **protect the weakest source-intervention response mode from rank collapse across transport regimes before Bayesian assimilation, rather than optimize generic posterior information gain.**

This distinction must be tested explicitly against an EIG / information-gain baseline.

---

# 3. PRIMARY SUPPORTING THEORY — Physics sensing / sensor placement

## NeurIPS 2025 Oral

**PhySense: Sensor Placement Optimization for Accurate Physics Sensing**

https://proceedings.neurips.cc/paper_files/paper/2025/hash/332b4fbe322e11a71fa39d91c664d8fa-Abstract-Conference.html

PhySense jointly considers physical-field reconstruction and sensor placement and shows that optimized sensor locations can materially change reconstruction accuracy.

Useful principle:

> sparse physical sensing quality is limited not only by the reconstructor but by where measurements are taken.

Collision boundary:

We cannot claim:

```text
physics-aware sensor placement
optimize sensor location for physical-field information
```

as new.

Possible project-specific innovation is instead:

```text
source-parameter observability under turbulent transport,
with a worst-transport weakest-mode objective rather than field-reconstruction variance.
```

---

# 4. SECONDARY MODULE CANDIDATE — Collective multi-trajectory informativity

## Motivation from our failure

The dual-UAV fixed difference failed because the second UAV did not provide the missing source mode in a stable way.

A more principled two-UAV use is not:

```text
z1 - z2
belief1 × belief2
more measurements
```

but:

> choose `R1` and `R2` so their **joint response operator** covers complementary source directions.

For four sources:

\[
C_w^{joint}=[C_w(R_1)\;C_w(R_2)].
\]

Optimize the smallest source mode across transport regimes:

\[
\max_{R_1,R_2}\min_w
\frac{\sigma_3(C_w^{joint})}{\sigma_1(C_w^{joint})}.
\]

This maps directly to multi-signal informativity / collective persistent excitation.

### Why this is a credible second innovation module

The module is activated only if:

1. the single-route observability objective is supported;
2. one trajectory cannot satisfy the full excitation gate under deployment constraints;
3. two complementary source-blind trajectories satisfy it jointly;
4. ordinary redundant two-robot sampling does not provide the same gain.

Until then it remains `CANDIDATE`.

---

# 5. BIOPHYSICAL THEORY CANDIDATE — Plume boundary as an information-bearing landmark

## Nature 2026

**Siliciano et al. — A vector-based strategy for olfactory navigation in Drosophila**

https://doi.org/10.1038/s41586-026-10827-7

The experiments show Drosophila use the plume boundary as a dynamic landmark and retain directional memory for returning to that boundary. The paper argues the lateral boundary is especially informative because it provides strong spatial contrast.

Potential project translation:

> route generation could deliberately seek plume-boundary transitions because these regions may excite source-dependent spatial response modes more strongly than remaining in the plume core.

This is **not** currently a module.

Before promotion, prove:

- boundary-oriented routes increase weakest source-mode observability;
- the effect survives wind changes;
- the idea is not already covered by casting / plume-edge tracking / infotaxis literature.

Do not call it 'bio-inspired' merely for presentation value. Use it only if the mechanism improves the measured observability deficiency.

---

# 6. DEMOTED THEORY — Differential / gradiometric sensing

## Nature 2026

**A prototype differential atom interferometer for fundamental physics**

https://www.nature.com/articles/s41586-026-10617-1

The work demonstrates a powerful general measurement principle: spatially separated differential sensors can reject common-mode noise and recover signals inaccessible to a single sensor.

This was a scientifically legitimate mother theory for the dual-UAV difference experiment.

However, our preregistered House02 experiment produced:

```text
per-wind sigma3/sigma1 ~ 10^-3
held-wind source identity = 2/4
time-mismatch control = 3/4
```

Therefore the simple signed two-point difference is **REJECTED as the current main innovation**.

The Nature result remains conceptual background for measurement design, not a justification to keep tuning the failed module.

---

# 7. DEMOTED THEORY — Turbulent two-point structure

## Physical Review Letters 2026

**Mailybaev, Thalabard — Perturbative Anomalous Exponents from Kolmogorov Multipliers**

https://doi.org/10.1103/6qrr-3646

This supports the broad physical importance of scale-dependent increments and multiplier statistics in turbulent transport.

But our test shows:

> a physically meaningful two-point statistic is not automatically a source-identifying statistic.

Therefore structure functions / signed increments cannot remain the main line unless a future observability-designed measurement geometry independently demonstrates source identity.

---

# 8. NOVELTY COLLISION — Stereo olfaction

## Advanced Materials 2026

**Receptor-Mimetic Stereo Olfaction for Simultaneous Odor Recognition and Spatial Localization**

https://doi.org/10.1002/adma.202521410

This work uses spatially separated chemical sensors and plume-dynamic disparities for odor recognition and 3-D source localization.

Therefore the following claims are occupied:

```text
stereo olfaction
spatially separated gas sensors encode source geometry
use onset/rise/amplitude disparities for localization
```

Our failed fixed two-point experiment further argues against trying to compete by relabeling a simple disparity score.

---

# 9. NOVELTY COLLISION — Multi-robot gas source localization

## 2026 DARS / EPFL DISAL

**Probabilistic Multi-Robot Gas Source Localization with Uncalibrated Sensors: A Distributed Estimation Approach**

https://arxiv.org/abs/2608.28214

The work uses rank-based local beliefs, Product-of-Experts fusion, informative-region allocation, and path planning for multi-robot GSL.

Therefore the following are not novelty:

```text
use two robots
fuse two beliefs
Product of Experts
rank-based multi-robot fusion
allocate informative regions among robots
```

If our secondary multi-UAV module survives, it must be about **collective source-mode excitation / informativity**, not generic distributed fusion.

---

# 10. Causal theory — retained as an evaluation language, not the current main module

Controlled source/transport interventions were useful for demonstrating an important distinction:

```text
source effect exists
!=
source identity is identifiable
```

The current project no longer treats 'causal' as a requirement in the method name.

Causal/interventional language remains useful for:

- defining controlled source-response matrices;
- testing source × transport interactions;
- preventing environment leakage;
- constructing falsification controls.

It is not currently the main contribution.

---

# 11. Current theory ranking

| Rank | Theory / module | Status | Why |
|---|---|---|---|
| 1 | Persistent excitation + worst-transport source observability | **PRIMARY CANDIDATE** | Directly matches observed source-mode rank collapse |
| 2 | Collective multi-trajectory informativity | **SECONDARY CANDIDATE** | Natural two-UAV extension if a single trajectory is insufficient |
| 3 | OED / online experimental design | **SUPPORT + STRONG BASELINE** | Powerful theory but generic OED/source-location is already occupied |
| 4 | Plume-boundary vector sensing from Drosophila | **ROUTE-PRIOR CANDIDATE** | Mechanistically interesting; not yet linked to source observability |
| 5 | Differential gradiometry / two-point structure | **DEMOTED / NO-GO AS CURRENT MAIN MODULE** | Preregistered dual-UAV test did not establish source identity |
| 6 | Causal posterior correction / invariance | **FROZEN AS MAIN LINE** | Repeatedly failed to overcome missing source information |

---

# 12. The novelty sentence we are allowed to test next

Not a claim yet:

> **Instead of optimizing where the posterior is expected to change most, design the UAV sensing trajectory to maximize the weakest physically measurable source-contrast mode under multiple transport regimes, preventing source-response rank collapse before Bayesian assimilation.**

If this does not beat generic information-gain/OED and classic GSL planning under the same data and constraints, it is not a publishable main innovation.
