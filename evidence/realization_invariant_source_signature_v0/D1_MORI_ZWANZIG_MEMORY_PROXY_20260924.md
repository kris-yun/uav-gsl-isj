# D1 — Mori–Zwanzig Non-Markovian Memory Proxy

Date: 2026-09-24  
Branch: `research/realization-invariant-source-signature-v0`

Decision: **D1_ADVANCE_MZ_NONMARKOVIAN_MEMORY_SIGNAL**

This is a data-only mechanism gate. It is **not** an exact Mori–Zwanzig kernel implementation and does not yet establish the final main innovation.

## Scientific question

The Gate-1A failure showed that exact deterministic source-to-sensor physics can identify the correct local source basin but is not robust to independent stochastic plume realizations at 0.30 m source-cell resolution.

D0 then showed that removing realization-dependent total plume mass while retaining spatial mass allocation improves truth rank from A/B = 1/7 to 2/3.

D1 asks a narrower question:

> Is cross-time non-Markovian stochastic memory itself load-bearing for source identity, or is D0 only a static rescaling effect?

## Mother-theory anchors

### 2025 Nature Computational Science — biomolecular dynamics

B. Liu et al., **Memory kernel minimization-based neural networks for discovering slow collective variables of biomolecular dynamics**, Nature Computational Science 5, 562–571 (2025), DOI: `10.1038/s43588-025-00815-8`.

MEMnets is built on integrative generalized master equation theory. Projection from high-dimensional dynamics into reduced collective variables introduces non-Markovian memory. MEMnets identifies reduced variables by minimizing the time-integrated memory kernel.

Code: `https://github.com/xuhuihuang/memnets`.

### 2026 PNAS — turbulent particle dynamics

X. M. de Wit et al., **Data-driven Mori–Zwanzig modeling of Lagrangian particle dynamics in turbulent flows**, PNAS 123(13), e2525390123 (2026), DOI: `10.1073/pnas.2525390123`.

This work uses the Mori–Zwanzig formalism to separate resolved dynamics, history-dependent memory, and unresolved dynamics in Lagrangian turbulence, recovering short-time trajectory accuracy and long-time statistics.

These two papers support the same mother principle from two far domains: unresolved fast stochastic degrees of freedom should not be forced into an instantaneous Markovian observation model; their effect appears as memory/noise after projection.

## Prior-art boundary

Generalized Langevin / Lagrangian stochastic models already exist in atmospheric and gas-dispersion forward modeling. Therefore the novelty cannot be:

- “use Langevin dynamics”;
- “use a generalized Langevin equation”;
- “add temporal correlation to a gas plume simulator”.

The screened GSL/olfaction literature did not reveal Mori–Zwanzig memory-kernel source inference.

The candidate novelty, if later gates survive, is specifically:

> project stochastic plume observations into a realization-robust source collective representation and use a learned/identified non-Markovian memory kernel directly inside the source-hypothesis likelihood / PMFS probability-map update.

## Frozen D1 proxy

Inputs are exactly the independently audited Gate-1A review bank:

- 630 arbitrary candidate sources;
- target A/B are independent W2 realizations;
- prediction seeds C/D are independent from targets;
- 10 times × 30 fixed probes;
- no target-dependent fitting;
- no source labels in the memory estimate;
- no neural network;
- no hyperparameter tuning.

Each time slice is first mapped to spatial mass fractions:

`p_t(i) = c_t(i) / sum_j c_t(j)`

with zero retained when the total observed mass is zero.

The stochastic temporal covariance is estimated only from the C–D realization differences across the candidate bank.

Three frozen metrics are compared:

1. identity temporal metric — no temporal memory;
2. diagonal temporal covariance — different time variances but independent times;
3. full covariance — retains off-diagonal temporal memory.

## Result

Truth source ranks:

| Temporal model | S2_W2_A | S2_W2_B |
|---|---:|---:|
| identity / no memory | 2 | 8 |
| diagonal only | 1 | 7 |
| **full temporal memory** | **1** | **2** |

The key observation is that simply reweighting time variance does not fix B. The gain appears only when off-diagonal cross-time structure is retained.

### Leakage / robustness checks

The full-memory result remains **A/B = 1/2** when the temporal covariance is estimated from:

- all 630 candidates;
- even-index candidates only;
- odd-index candidates only;
- all candidates except the true source.

Therefore the result is not explained by truth-source leakage into the temporal covariance.

### Measured memory structure

Average temporal correlation from independent-realization differences:

- lag 1: ~0.580;
- lag 2: ~0.478;
- lag 3: ~0.376;
- lag 4: ~0.297;
- lag 5: ~0.216;
- lag 6: ~0.133;
- lag 7: ~0.055;
- lag 8/9: approximately zero.

Off-diagonal temporal covariance contributes ~0.283 of the covariance Frobenius norm.

This is a finite-memory pattern rather than white realization noise.

### Independent memory diagnostic

A cross-realization VAR(1) versus VAR(2) diagnostic was also run.

Adding a second lag reduces held-out prediction error by:

- raw ppm: ~38.0% and ~40.1%;
- per-time mass-fraction representation: only ~8.1% and ~13.4%.

Thus D0's mass-fraction representation removes a large fraction of the historical dependence, but residual temporal memory remains and is useful for source ranking.

## Interpretation

The current data support a more specific scientific mechanism:

> Absolute concentration is strongly realization-dependent. A source-conditioned spatial mass-fraction representation suppresses much of this nuisance, while the remaining stochastic plume uncertainty is temporally correlated rather than independent. Retaining that finite memory restores robust source identity across independent plume realizations.

This directly explains why the deterministic source-to-sensor family could show strong local physical signal yet fail exact-cell ranking.

## What D1 does NOT prove

D1 does not prove that MEMnets itself should be transplanted into GSL.

The source coordinate is a fixed hidden parameter, whereas MEMnets was designed to discover slow dynamical collective variables. A direct copy would therefore be conceptually weak.

The next innovation must be a second-order adaptation of the mother theory, not “MEMnets for gas”.

## D2 authorization

D1 is strong enough to authorize a **Mori–Zwanzig source-inference D2**, still offline only.

D2 must explicitly derive a source-hypothesis memory model:

- resolved variable: source-conditioned realization-robust observation coordinate;
- orthogonal/unresolved component: stochastic plume realization fluctuations;
- memory: source-independent or structured finite history estimated without target leakage;
- output: PMFS-style source probability map.

D2 must beat these frozen controls on independent target realizations:

- raw exact-forward likelihood;
- D0 static mass-fraction signature;
- diagonal-only temporal weighting.

No closed-loop experiment is authorized yet.
