# W0C matched transport error → source-posterior causal gate

## Status

Run only after reading:
- W0_PRE_EXISTING_DATA_SCREEN_20261007.md
- W0_PRE2_CONTEXT_COLLAPSE_20261007.md
- STOP_HOLD_REGISTER.md

No world model. No new neural network. No full candidate-grid sweep.

## Scientific question

After controlling source, gas, geometry, RNG, observation route and global wind-error magnitude:

> Do structurally different 3D wind errors cause reproducibly different plume and source-posterior damage?

This is the phenomenon required by a source-task-oriented transport method.

## Stage 0 — choose a clean base case before perturbation scoring

Use existing unperturbed runs only.

A base source/wind pair is eligible only if:
- source is legal/equal-height under the R0C contract;
- baseline plume has adequate transport support;
- outer 3 footprint bins on the dominant outflow side do not contain excessive mass over 100–700 s;
- centroid/path is not obviously truncated by domain boundary;
- the same source can be used for all perturbation families.

Freeze the quantitative boundary-support threshold before perturbation outcomes are inspected.

Prefer at least one eligible source in H01 and one in H02.
If H02 has no clean source under the selected wind, do not force H02 into the causal gate.

## Stage 1 — construct perturbations from one oracle wind

For each eligible base wind U* construct pre-registered pairs with matched global vector-RMSE:

A. task-region directional perturbation vs same-volume off-region perturbation;
B. vertical-shear destruction vs matched horizontal-speed perturbation;
C. near-boundary/wake directional perturbation vs open-region perturbation, only where geometry supports a clean definition;
D. optional remove-w vs matched horizontal perturbation only if native w has material magnitude.

Do NOT add perturbation families after viewing results.

For every A/B pair:
- same perturbed volume when applicable;
- global vector RMSE matched within a frozen tolerance;
- report cosine, speed MAE, direction error, divergence change;
- avoid nonphysical obstacle penetration if the wind representation permits checking it.

## Stage 2 — paired GADEN rerun

For each perturbation:
- exact same source;
- exact same gas;
- exact same RNG realization;
- exact same release parameters;
- exact same geometry;
- exact same simulation clock/output cadence;
- only wind changes.

Use 4 paired realizations if feasible.

Start small:
- 2 sources total if clean;
- 2 perturbation-pair families;
- 4 paired realizations.

Do not run the full 626-source PMFS grid.

## Stage 3 — plume/sensor damage

Frozen outputs:
- 2D column footprint trajectory;
- fixed source-blind virtual UAV concentration route;
- arrival/detection timing;
- plume centroid/path and spread as secondary diagnostics.

Compare each perturbed wind against U*.

## Stage 4 — source inference damage

At least two source-inference families:

1. PMFS or closest reproducible candidate-probability forward-simulation baseline.
2. Simple Bayesian / source-term likelihood baseline.

Also include a transport-ensemble / “many wrong models” style baseline where feasible, because generic model blending is prior art and cannot be claimed as novelty.

Primary source metrics:
- localization error;
- true-source rank;
- Top-k;
- posterior NLL/Brier/calibration if defined;
- posterior distortion vs oracle-wind result.

## Primary matched-error test

Before scoring freeze:
- allowed global wind-RMSE mismatch between perturbation pair;
- minimum material difference in source-posterior damage;
- repetition requirement across seeds;
- harm/rescue reporting rule.

Required logic:

Matched wind error:
|Ewind(A)-Ewind(B)| <= tolerance

but:
damage_source(A) / damage_source(B) >= frozen ratio
or equivalent frozen absolute difference,

with direction consistency in >=3/4 paired realizations.

Do not rescue a failed primary pair with secondary features.

## Verdicts

W0C_TASK_ANISOTROPY_PASS:
- >=2 preregistered structural perturbation contrasts show unequal source-inference damage under matched global wind error;
- result is not explained by domain-boundary truncation;
- effect appears in plume/sensor response and source inference;
- at least one contrast is reproduced in a second source/House or later FSR pilot.

W0C_PARTIAL_HOLD:
- strong signal but restricted to one source/environment or one inference baseline.

W0C_GLOBAL_ERROR_SUFFICIENT_STOP:
- matched global wind error predicts downstream source damage as well as perturbation structure, or result is not reproducible.

Regardless of outcome, stop automatically after verdict. No neural-model rescue.

## If PASS

Only then design the paper method.

The preferred direction is not generic multi-model blending. It is:

**sparse-meteorology-conditioned, source-task-sensitive transport uncertainty for probabilistic UAV GSL**

where transport states/regions are represented according to expected effect on source posterior.

Then confirm in FSR as the main lakeshore benchmark.
