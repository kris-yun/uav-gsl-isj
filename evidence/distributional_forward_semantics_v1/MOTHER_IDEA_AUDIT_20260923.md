# Distributional / measure-valued forward semantics for PMFS — mother-idea audit

Date: 2026-09-23  
Branch: `research/distributional-forward-semantics-v1`

## 1. Scope

PMFS is treated only as the outer shell:

- a spatial probability map over source candidates;
- a candidate/source partition;
- an online loop that updates belief and chooses motion.

The following Native internals are **not** protected:

- one deterministic/mean hit-probability map per candidate;
- cell-wise independent agreement;
- the product-form Native source score;
- the current Bayesian evidence semantics.

The proposed mother idea is therefore not a small likelihood patch. It is a replacement of the source-conditioned forward evidence object.

## 2. 2026 mother idea

### 2.1 Statistical computation of chaotic fluids

Raonić et al., *Nature Communications* 17, 9846 (2026), “Generative AI for efficient statistical computation of fluids”, argues that for sensitive/chaotic fluid systems the scientifically stable object is the conditional distribution / push-forward measure over possible fluid states rather than a single deterministic trajectory or a conditional mean.

DOI: 10.1038/s41467-026-76390-x  
Published: 2026-08-17.

The paper explicitly shows that deterministic mean-square surrogates collapse toward average behavior and lose variance and higher-order statistics, while conditional diffusion models recover distributions and higher-order statistics.

### 2.2 Function-space generative modeling

Wang et al., *Nature Communications* 17, 5749 (2026), “FunDiff: diffusion models over function spaces for physics-informed generative modeling”, gives a 2026 framework for learning probability distributions over continuous physical fields rather than fixed-grid point predictions.

DOI: 10.1038/s41467-026-72292-0  
Published: 2026-04-27.

### 2.3 Turbulence perspective

Eyink & Goldenfeld, *Philosophical Transactions A* 384 (2026), “Beyond chaos: fluctuations, anomalies and spontaneous stochasticity in fluid turbulence”, reviews the statistical-hydrodynamic viewpoint that fully developed turbulence may require intrinsically stochastic/statistical descriptions rather than a single deterministic realization.

DOI: 10.1098/rsta.2025.0022.

## 3. PMFS failure mechanism that this idea targets

Current Native PMFS reduces a candidate source to a marginal hit-probability field

`candidate source -> one hitMap p_i(sim | s)`

and then independently compares the map cells to the measured probability map.

The cumulative R2 evidence shows that changing the cell-wise score does not fix source identity reliably. This motivates a deeper hypothesis:

> the source-conditioned object should be a distribution over stochastic plume fields, not a single mean field.

A candidate would therefore represent a measure

`P_s(U)`

over plume / occupancy fields `U`, and the source evidence should compare the observed effect against that predictive distribution. The source-probability map can remain as PMFS’s outer representation.

## 4. R2 cross-seed source-blind preaudit

Before using truth labels, candidate simulated fields from seed0 and seed1 were compared on the intersection of their observed-support grids.

For the truth-nearest candidate, Hellinger field-distance retrieval across the independent seed was:

- House01: 4 / 148 (seed0 -> seed1), 2 / 152 (seed1 -> seed0)
- House02: 1 / 144, 2 / 148
- House03: 1 / 199, 1 / 197

Full results: `R2_CROSS_SEED_FIELD_IDENTITY_PREAUDIT_20260923.csv`.

Interpretation:

- the simulator-internal mapping from source candidate to plume statistics is not completely structureless;
- in H02/H03 especially, the field generated near the true source is highly recognizable across the two independent Native runs;
- this **does not yet establish localization utility**, because it may still be simulator self-consistency rather than reality-to-simulator conformance.

Therefore this result is a positive mechanism preaudit only.

## 5. H01 full 200-step distributional test

A stronger test used the frozen standalone Native candidate replay for H01_R2026092201:

- 121 terminal source candidates;
- 212 observed-support cells;
- 200 candidate-internal stochastic transport steps;
- full source-conditioned occupancy events.

No neural model was trained.

For each candidate, the 200 stochastic occupancy fields were treated as an empirical multivariate forecast distribution. A confidence-weighted multivariate Energy Score was evaluated against H01’s all-miss observation.

Destructive null:

- preserve each candidate’s per-cell occupancy probabilities `q_i` (the information carried by the current mean hitMap);
- replace the joint field by the product of Bernoulli marginals;
- thereby remove all cross-cell dependence.

Result:

- Native truth rank: 76 / 121
- marginal occupancy truth rank: 20.5 / 121
- mean-field L2 truth rank: 20.5 / 121
- actual joint Energy Score truth rank: 20.5 / 121
- independent-marginal Energy Score null truth rank: 27.5 / 121

The truth candidate itself has **zero occupancy on all 212 support cells over all 200 replay steps**, so its empirical joint distribution degenerates to the all-zero field. Its actual Energy Score and the independence-null Energy Score are both exactly zero.

Conclusion:

**H01 is not capable of proving that higher-order plume dependence is load-bearing.**  
It shows again that Native’s product score is poor in this all-miss case, but distributional joint structure cannot improve on the marginal field because the truth candidate has no stochastic variation on the evaluated support.

Machine-readable result:
`H01_ENERGY_PREAUDIT_20260923.json`.

## 6. Current status of the mother idea

Status: **PROMISING BUT NOT VALIDATED AS MAIN INNOVATION**.

It is not a small PMFS patch. If it survives, the architecture would be conceptually:

`source candidate s -> conditional stochastic plume measure P_s(U) -> distributional observation compatibility -> source probability map`

rather than:

`source candidate s -> one mean hitMap -> independent cell likelihood product -> source probability map`.

The main idea is therefore **measure-valued / distributional forward semantics for turbulent plume source inference**, with conditional diffusion / function-space generative modeling as a possible implementation only after the mechanism passes.

## 7. Required next knife

Do **not** train GenCFD/FunDiff yet.

The decisive test is a full standalone candidate replay on hit-bearing H02 and H03 accepted runs, preserving the exact Native kernel and exporting the 200-step occupancy fields.

Required gate:

1. freeze a source-blind multivariate distributional score before using truth;
2. evaluate truth-source candidate rank;
3. compare against the current mean-field/marginal score;
4. destroy cross-cell dependence while preserving all per-cell hit probabilities;
5. require the truth-rank improvement to disappear or materially weaken under that destructive null;
6. repeat across independent plume realizations.

Only if that gate passes should a learned conditional generative model be built.

## 8. Second 2026 idea audited: Assimilative Causal Inference

Andreou, Chen & Bollt, *Nature Communications* 17, 1854 (2026), “Assimilative causal inference”, reframes causal discovery as a Bayesian inverse problem: future effect observations reduce uncertainty in reconstructing present candidate causes, quantified by filter-to-smoother information gain.

DOI: 10.1038/s41467-026-68568-0.

This is scientifically attractive, but it is **not promoted to the main line here** for two reasons:

1. ACI’s theoretical cause variables are time-evolving stochastic state variables, whereas source location in the current GSL problem is primarily a static latent parameter. Direct application risks collapsing to ordinary parameter smoothing / data assimilation.
2. Data-assimilation-based gas source-term estimation is already an established neighboring literature, including 2025–2026 particle-filter, EnKF/variational, and reduced-order adjoint work. Merely re-labeling static source inversion as ACI would not provide the required remote-domain novelty.

ACI may later contribute an auxiliary online attribution or observation-value mechanism, but it should not displace the distributional-forward main test.

## Decision

For the current batch:

- **keep**: distributional / measure-valued forward semantics;
- **not yet validated**: H01 is structurally inconclusive for higher-order dependence;
- **next required data**: H02/H03 standalone stochastic candidate replay;
- **demote**: ACI as main innovation;
- **do not** design auxiliary modules or a three-module architecture yet.
