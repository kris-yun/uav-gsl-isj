# Main-Innovation Theory Freeze — Mori–Zwanzig Non-Markovian Source Inference

Date: 2026-09-24  
Branch: `research/realization-invariant-source-signature-v0`

Status: **CANDIDATE MAIN INNOVATION — D3 PENDING**

## 1. Scientific failure that motivates the new mainline

The previous exact source-to-sensor Green-family gate failed under independent stochastic plume realization:

- S2_W2_A truth rank: 1;
- S2_W2_B truth rank: 7.

The failure was local rather than global: the highest-ranked wrong candidates remained near the true source. This showed that deterministic source-to-sensor transport carries source-basin information but is not realization-robust at 0.30 m support-cell resolution.

The main scientific problem is therefore not merely forward-model accuracy:

> How can source identity remain inferable when the unresolved stochastic plume realization changes?

## 2. Far-domain mother theory

### 2.1 Mori–Zwanzig projection

The mother principle is Mori–Zwanzig model reduction:

A high-dimensional dynamical system is projected onto a reduced set of resolved observables. The eliminated degrees of freedom do not disappear; after projection they appear as:

1. resolved / instantaneous dynamics;
2. history-dependent memory;
3. orthogonal unresolved fluctuation / noise.

The research thesis is that PMFS-style gas-source inference should not treat stochastic plume observations as conditionally independent instantaneous evidence when the unresolved plume degrees of freedom induce finite temporal memory.

### 2.2 2026 turbulence anchor

X. M. de Wit et al.,
**Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows**,
Proceedings of the National Academy of Sciences 123(13), e2525390123 (2026).
DOI: `10.1073/pnas.2525390123`.

This is the closest far-domain physical anchor. It applies Mori–Zwanzig to Lagrangian turbulence, where reduced particle trajectories lack access to the full turbulent field, and learns a history-dependent reduced dynamical system that is point-wise useful at short times and statistically stable at long times.

### 2.3 2025 biomolecular anchor

B. Liu et al.,
**Memory kernel minimization-based neural networks for discovering slow collective variables of biomolecular dynamics**,
Nature Computational Science 5, 562–571 (2025).
DOI: `10.1038/s43588-025-00815-8`.

MEMnets is built on integrative generalized master equation theory. It identifies collective variables by minimizing an upper bound on the time-integrated memory kernel rather than assuming Markovian reduced dynamics.

Reference implementation:
`https://github.com/xuhuihuang/memnets`

The code is a theory/reference parent, not a package to copy directly into GSL.

## 3. Our second-order innovation

A direct transplant of MEMnets or a generic autoregressive model is not the innovation.

The proposed GSL-specific second-order idea is:

> **Mori–Zwanzig non-Markovian source inference:** project the stochastic gas observation history into a realization-robust source-conditioned observation coordinate, represent unresolved plume fluctuations through finite temporal memory, and use the resulting history-dependent likelihood to update a PMFS-style source probability map.

The hidden source position is a fixed cause, not a slow dynamical state. Therefore our problem differs fundamentally from molecular CV discovery and from turbulent trajectory forecasting.

The source hypothesis enters the inverse likelihood, while the unresolved plume realization enters the memory/noise model.

## 4. Data-derived projection discovered before model training

The D0 data-only probe showed that absolute plume mass is strongly realization dependent.

Frozen projection at each observation time:

[
p_t(i)=\frac{c_t(i)}{\sum_j c_t(j)}
]

with the zero vector retained when total observed mass is zero.

This converts each time slice from absolute ppm into a spatial mass-fraction observation.

It is not claimed as the main innovation.

Its role is nuisance removal / resolved-coordinate construction.

Empirical evidence:

- raw exact-forward A/B rank: 1 / 7;
- temporal mean: 1 / 5;
- global normalization controls: no robust improvement;
- per-time mass-fraction then time aggregation: 2 / 3.

Same-source target A/B discrepancy:

- raw cosine ~0.9774;
- projected cosine ~0.9952;
- raw relative L2 ~21.2%;
- projected relative L2 ~10.1%.

## 5. D1 memory evidence

Using the frozen 630 arbitrary-source bank, temporal stochastic covariance was estimated only from independent prediction realization differences C-D.

Truth ranks:

| temporal model | A | B |
|---|---:|---:|
| identity / no memory | 2 | 8 |
| diagonal variance only | 1 | 7 |
| full off-diagonal temporal memory | **1** | **2** |

The full-memory result remains 1/2 when estimated from:

- all candidates;
- even-index candidates only;
- odd-index candidates only;
- all candidates except the true source.

Measured mean residual temporal correlation:

- lag 1 ~0.580;
- lag 2 ~0.478;
- lag 3 ~0.376;
- lag 4 ~0.297;
- lag 5 ~0.216;
- lag 6 ~0.133;
- lag 7 ~0.055;
- lag 8 and later approximately zero.

This supports finite memory rather than independent white realization noise.

## 6. D2 sequential finite-memory likelihood

The memory horizon is selected without looking at target A/B ranks:

> retain positive lags preceding the first non-positive mean temporal correlation of C-D realization differences.

Frozen all-source estimate:

- first non-positive lag: 8;
- retained memory horizon: 7.

Rank curve:

| memory horizon | A | B |
|---:|---:|---:|
| 0 | 1 | 7 |
| 1 | 1 | 4 |
| 2 | 1 | 5 |
| 3 | 1 | 3 |
| 4 | 1 | 2 |
| 5–9 | 1 | 2 |

The automatically selected horizon 7 gives A/B = **1/2**.

Split estimates and truth-excluded estimation also give 1/2.

Decision:

`D2_ADVANCE_FINITE_MEMORY_SOURCE_LIKELIHOOD`

## 7. Prior-art boundary

Do NOT claim novelty for:

- Langevin plume models;
- generalized Langevin equations for gas dispersion;
- temporal filtering;
- autoregressive concentration prediction;
- MEMnets itself;
- generic non-Markovian modeling;
- simply using concentration history.

Lagrangian stochastic / generalized-Langevin-type dispersion modeling already exists in atmospheric/gas transport.

The only defensible candidate claim, if D3 and later cross-environment gates survive, is the inverse-localization construction:

> source-conditioned PMFS likelihood under a Mori–Zwanzig-style projection in which unresolved stochastic plume degrees of freedom induce explicit finite memory.

## 8. D3 falsification is load-bearing

D3 tests a second true source S1 at the same House02/W2 condition.

Truth:
- source id `pmfs_10_17`;
- xyz `(-2.242730141, -2.200880051, 0.20)`.

Only two new target realizations are required. The frozen 630-source C/D prediction bank is reused.

No result-driven tuning is permitted.

D3 PASS requires both new target realizations to have memory rank <=3 and the memory model to dominate/preserve the pre-frozen raw, D0-static, and diagonal controls according to `CODEX_D3_S1_W2_HANDOFF_20260924.md`.

D3 failure freezes:

`D3_FAIL_STOP_MZ_SOURCE_INFERENCE_MAINLINE`

D3 pass freezes only:

`D3_PASS_SECOND_SOURCE_MEMORY_GENERALIZES`

A D3 pass is still not sufficient for the final main innovation. Cross-House / cross-environment evidence is mandatory before closed-loop authorization.

## 9. Working three-module architecture if the mainline survives

This is a hypothesis architecture only; auxiliary modules are not yet frozen.

**Main innovation:** Mori–Zwanzig non-Markovian source likelihood.

**Auxiliary candidate A:** realization-robust source projection / plume-mass nuisance removal.

**Auxiliary candidate B:** memory-aware observation/action policy, to be selected only after the main offline source-inference mechanism survives cross-environment testing.

The final representation remains a PMFS-style source probability map.

## 10. Current action

Do not broaden literature search and do not develop auxiliary modules now.

The only authorized next scientific result is D3 S1-W2 second-source falsification.
