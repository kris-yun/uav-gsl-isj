# R0 Independent Review and Post-PASS Scientific Interpretation

Date: 2026-09-24

Reviewed branch:
`research/stochastic-benchmark-refoundation-20260924`

Reviewed result commit:
`e527beea07c33cdbc362d156545409245f029968`

Independent decision:
**R0_PASS_STOCHASTIC_BENCHMARK_USABLE — CONFIRMED**

This review independently recomputes the frozen R0 metrics from the 288 compact pooled realizations. It then asks a separate post-PASS question: which stochastic objects are actually stable enough to justify the next mainline search?

---

## 1. Package integrity

Review package:
`R0_STOCHASTIC_BENCHMARK_REVIEW_20260924.tar.gz`

- bytes: 245604
- SHA256:
  `030c7aa814c4edfe0c6912bb4fc7faf36970142911e0f6c28822f2dd39049c1e`

All 595 files listed in the internal SHA256 manifest independently verify.

The package contains:

- 18 frozen source identities;
- 288 unique new RNG seeds;
- 16 independent 10×30 pooled realizations for every source;
- frozen R0 protocol and code;
- final clean Git state at commit `e527beea07c33cdbc362d156545409245f029968`.

No infrastructure-only patch was reported.

---

## 2. Independent recomputation of frozen R0

The committed result JSON was not trusted.

All primary metrics were independently recomputed from the 288 `pooled.npy` arrays.

### Split reproducibility

Primary source stochasticity:
median pairwise relative-L2 same-source discrepancy.

Independent result:

| split | variability Spearman | mass Spearman | variability-tercile agreement |
|---|---:|---:|---:|
| replicates 1–8 vs 9–16 | **0.721362** | 0.979360 | **0.666667** |
| odd 8 vs even 8 | **0.742002** | 0.966976 | **0.722222** |

Therefore:
- minimum variability Spearman = **0.721362**;
- minimum tercile agreement = **0.666667**.

Both satisfy the frozen PASS gate.

### K-convergence

Independent recomputation:

K8 -> K16 relative change:
- median = **0.154564**
- q75 = **0.263679**
- max = 0.634599

K12 -> K16:
- median = **0.104050**
- q75 = **0.189217**
- max = 0.379987

All frozen PASS thresholds are met.

### Legacy two-realization audit

Legacy C/D discrepancy versus 16-realization source stochasticity:

Spearman = **0.504644**.

This confirms the previous diagnosis:

> two realizations contain some signal about source stochasticity but are too noisy to be treated as a stable source-conditioned stochastic law.

---

## 3. What R0 PASS does and does not establish

R0 PASS establishes:

1. source-conditioned stochastic plume behavior is not pure realization noise;
2. with repeated realizations, source-level stochastic descriptors become reproducible;
3. a multi-realization stochastic benchmark is scientifically usable;
4. the old C/D two-sample labels were materially noisy.

R0 PASS does **not** establish:

- Gaussianity;
- PASI;
- a stable 300-D covariance;
- a full path probability law;
- Onsager–Machlup / large deviations;
- exact 0.30 m source-cell identifiability;
- cross-House generalization.

The next mainline must therefore be based on the stochastic objects that R0 actually shows are stable.

---

## 4. Which objects are most reproducible?

Using the same two independent 8/8 splits, additional diagnostics were computed.

Approximate source-order Spearman reproducibility:

| descriptor | first8 vs last8 | odd8 vs even8 |
|---|---:|---:|
| median pairwise relative-L2 | 0.721 | 0.742 |
| q90 pairwise relative-L2 | 0.822 | 0.719 |
| median pairwise cosine | 0.893 | 0.829 |
| median total plume mass | **0.979** | **0.967** |
| median zero fraction | **0.997** | **0.977** |
| median first-arrival index | ~**1.000** | ~**1.000** |

The last statistic is discrete and tied, so its near-perfect rank correlation should not be overinterpreted.

The main scientific observation is stronger:

> encounter/support statistics are more reproducible across realization subsets than raw amplitude variability.

---

## 5. Encounter-probability profile convergence

For each source define the empirical binary encounter field over the frozen 10×30 observation coordinates:

[
P_s(t,q)=Pr[C_s(t,q)>0].
]

Estimate (P_s) from the first K realizations and compare to the K=16 estimate.

Relative profile error versus K=16:

| K | median | q75 | max |
|---:|---:|---:|---:|
| 2 | 0.204 | 0.262 | 0.320 |
| 4 | 0.147 | 0.163 | 0.309 |
| 8 | **0.081** | **0.097** | **0.141** |
| 12 | **0.043** | **0.052** | **0.088** |

At K=8 the encounter field is already substantially more stable than the primary amplitude-based stochasticity descriptor.

This suggests that the stochastic object most justified by R0 is **not a full concentration path density**, but the source-conditioned structure of intermittent encounters / support occupancy.

---

## 6. Split profile reproducibility

First-8 versus last-8 empirical profiles:

### Full 10×30 binary encounter-probability field

Across the 18 sources:

- median cosine ~0.988;
- median relative profile discrepancy ~0.161.

### Time-only encounter profile

- median cosine ~0.998;
- median relative discrepancy ~0.068.

### Probe-only encounter profile

- median cosine ~0.997;
- median relative discrepancy ~0.085.

### Mean concentration trajectory

Its direction is also highly reproducible, but absolute magnitude shows larger split variability.

Thus binary encounter structure is not simply a noisy surrogate for ppm magnitude; it is a particularly stable component of the observation process.

---

## 7. Exploratory source-identity diagnostic — NOT a confirmation gate

This analysis was performed after R0 PASS only to determine which object deserves theory search.

It is **not** a new mainline result and it uses only the 18 calibration sources.

Protocol:

- use 8 realizations/source to estimate a 10×30 Bernoulli encounter-probability field;
- score each held-out single realization under all 18 source-specific Bernoulli fields;
- swap train/test halves and repeat.

Results:

### first8 -> last8

Bernoulli encounter likelihood:
- top-1 source = **90.3%**
- top-3 = **99.3%**

Raw mean-path SSE:
- top-1 = 88.2%
- top-3 = 97.9%

### last8 -> first8

Bernoulli encounter likelihood:
- top-1 = **89.6%**
- top-3 = **100%**

Raw mean-path SSE:
- top-1 = 81.9%
- top-3 = 97.2%

Interpretation:

> source-conditioned encounter/support structure carries strong single-realization source identity on the R0 calibration panel.

This is encouraging but cannot be used as the paper innovation because:
- only 18 source candidates are involved;
- the analysis is post-R0 exploratory;
- simple encounter likelihood has prior art in olfactory search.

---

## 8. Prior-art boundary

The next mainline must not claim:

“first use of encounter probability for turbulent olfactory search.”

2025 Physical Review Fluids work by Heinonen et al. already extracts spatially dependent odor-encounter statistics from realistic turbulent DNS and uses them to construct Bayesian olfactory-search policies.

Therefore a Bernoulli encounter map alone is **not** a defensible main innovation.

The R0 result should instead be used to search for a higher-level far-domain theory that explains:

1. why intermittent support is a more reproducible observable than exact concentration amplitude;
2. how source identity should be represented when fine source cells are stochastically indistinguishable;
3. how the appropriate source scale can emerge from observation statistics rather than be fixed ad hoc.

---

## 9. Mainline scientific conclusion after R0

The project should now stop asking:

> Which full stochastic plume distribution should we fit?

The R0-supported question is narrower and better identified:

> Which source-conditioned **encounter/intermittency structures** are reproducibly identifiable across plume realizations, and at what spatial source scale do they carry unique source information?

This simultaneously addresses:

- the stochastic-realization problem;
- the exact-cell versus local-basin problem;
- the need to preserve a PMFS-style source probability representation.

---

## 10. Authorized next activity

Do not return to PASI.

Do not yet run PMFS closed loop.

The next activity should have two parts:

### Theory search

Search far-domain 2025/2026 theory for:
- event/point-process representations of intermittent stochastic systems;
- first-passage / renewal / survival structure;
- multiscale identifiability / coarse-graining;
- information-theoretic emergence of observable macrostates.

### New offline gate

The next actual source-ranking gate must again use at least >=143 arbitrary candidate source hypotheses.

Because R0 shows encounter fields converge much faster than full path variance, a multi-realization candidate bank can be designed around encounter statistics rather than full concentration covariance.

The exact theory and gate should be frozen only after novelty/prior-art review.
