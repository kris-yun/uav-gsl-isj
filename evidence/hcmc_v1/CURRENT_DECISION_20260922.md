# HCMC V1 — CURRENT DECISION CHECKPOINT

Date: 2026-09-22
Branch: `research/hypothesis-conditioned-multiscaling-v1`

## Decision

**HCMC V1 is the current primary main-innovation candidate.**

It has passed the Stage-1 discovery/falsification screen on the frozen native 300-s R2 six-case archive.

It has **not** yet passed an independent validation set and is **not** authorized for closed-loop ROS integration.

## Paper-level thesis

Gas-source hypotheses should not be judged primarily by pointwise agreement with one turbulent plume realization.

Instead, a physically compatible source hypothesis should reproduce the measured turbulent scalar field's **cross-scale increment laws**.

HCMC therefore ranks each source hypothesis by measured-vs-simulated conformity of a fixed multi-order structure-function slope spectrum.

The scientific mother idea is:

**turbulent intermittency / anomalous multiscaling / cross-scale universality of transported scalar statistics.**

This is a paper-level physics thesis, not an engineering fusion trick.

## Frozen discovery result

Native 300-s ExpectedValue endpoint:

- native mean: 5.5551 m
- HCMC mean: 2.4488 m
- mean reduction: 55.92%
- improved cases: 6/6

Destructive controls:

- final-leaf rank permutation: null mean 4.4958 m; only 1/300 as good as real HCMC;
- simulated-field spatial shuffle: null mean 4.9613 m; 0/30 as good as real HCMC;
- cross-seed source-blind score reproducibility exceeds permutation null in H01/H02/H03.

## Robustness already frozen

- fixed p=1..4 family;
- leave-one-order-out remains 6/6 for every omitted order;
- p=2 alone remains 6/6 but is not promoted post hoc;
- full fixed scale family 1/2/4/8 cells remains the V1;
- coarse 2/4/8 family also gives 6/6, but is not substituted post hoc;
- removing the numerical confidence floor still retains 6/6 and a large gain.

## Important negative diagnostics

HCMC is **not** claimed to be immediately informative at every time.

Source-update progression:
- early updates can be neutral or harmful;
- update 3 is 5/6 improved;
- final update is 6/6.

HCMC is **not** claimed to be transport-invariant under arbitrary low-signal conditions.

On the separate controlled 240-s fast/slow asset:
- H01: 4/4;
- H02: 2/4;
- H03: 4/4;
- total: 10/12.

The two failures are H02-SA, where both wind realizations contain essentially no resolvable gas excitation (>0.01 ppm samples = 0).

HCMC is also **not** a local redundant cue:
- x-only and y-only are weaker than full x+y;
- two disjoint spatial folds are weaker and their candidate rankings correlate poorly;
- broad spatial support is load-bearing.

## Safe scientific claim

> A source hypothesis can be evaluated by whether its simulated plume reproduces the observation's multi-order, cross-scale turbulent-scalar increment structure, rather than by requiring pointwise instantaneous plume agreement.

## Claims currently prohibited

Do not claim:

- a universal Kolmogorov exponent in the indoor data;
- a formal multifractal spectrum theorem;
- arbitrary wind-regime invariance;
- local spatial redundancy;
- independent generalization;
- closed-loop superiority;
- that intermittency itself is new to OSL.

## Literature lineage

Modern anchors:

- PRL 2025: onset of intermittency and multiscaling through Eulerian/Lagrangian structure functions;
- JFM 2025: dual scaling of second-order transported-scalar structure functions;
- PRL 2026 Editors' Suggestion: anomalous turbulent-transport exponents from cross-scale Kolmogorov multiplier statistics, including arbitrary-order structure functions.

Targeted OSL/GSL collision searches found temporal intermittency, burst statistics, intensity/timing learning, Bayesian inference and plume-tracking methods, but no direct candidate-conditioned measured-vs-simulated multi-order structure-function exponent conformity method.

This is a targeted collision screen, not an exhaustive patent/literature novelty opinion.

## Next and only promotion gate

Generate genuinely new VGR/GADEN stochastic realizations not used during discovery.

No seed2/seed3 R2 evidence was found in the repository or the frozen release.

Keep HCMC V1 unchanged.

Independent offline promotion bar:
- >=10% pooled error reduction;
- majority non-worse, at least 4/6 for a six-case matrix;
- no new false-confident collapse;
- provenance and final-leaf scope checks pass;
- destructive controls remain separated from real HCMC.

Only after that PASS may a closed-loop HCMC V2 branch be created.

## Key files

- `evidence/hcmc_v1/OFFLINE_SCREEN_20260922.md`
- `evidence/hcmc_v1/HCMC_V1_REPRO_CONTROL_SCREEN_20260922.json`
- `evidence/hcmc_v1/POWER_ORDER_ABLATION_20260922.md`
- `evidence/hcmc_v1/SCALE_FAMILY_ABLATION_20260922.md`
- `evidence/hcmc_v1/UPDATE_PROGRESSION_20260922.md`
- `evidence/hcmc_v1/CROSS_ASSET_MECHANISM_DIAGNOSTIC_20260922.md`
- `evidence/hcmc_v1/SPLIT_SUPPORT_DIAGNOSTIC_20260922.md`
- `evidence/hcmc_v1/PRIOR_ART_COLLISION_SCREEN_20260922.md`
- `evidence/hcmc_v1/CODEX_HANDOFF_20260922.md`
- `reference/hcmc_v1_screen.py`
