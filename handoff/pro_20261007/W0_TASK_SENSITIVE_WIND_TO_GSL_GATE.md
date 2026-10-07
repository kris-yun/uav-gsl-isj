# W0 phenomenon gate — matched wind error → unequal GSL damage?

## Purpose

Before building any new wind-reconstruction or GSL model, test the one phenomenon that the candidate first-paper novelty requires:

> **Two wind-field errors with matched global magnitude can produce materially different plume/source-inference errors because their spatial/structural locations differ.**

If this is false or not reproducible, STOP the task-oriented wind route.

This is not another PMFS feature search.

---

## Stage W0-A — low-cost mechanism screen in existing House scenes

Use H01/H02 only as mechanism/stress-test environments.

### Freeze
- one qualified base 3D oracle wind field per House;
- legal equal-height source pair already validated;
- one gas type initially;
- same source, release parameters, geometry and RNG for matched perturbation comparisons;
- same UAV/source-blind observation route and sensing budget;
- no model training.

### Construct controlled wind perturbation families

Start from oracle wind U* and create delta-U fields.
Normalize every perturbation to the same free-space global vector RMSE (and report cosine/angular error).

Suggested paired perturbations:

1. **Transport-corridor local error vs off-corridor local error**
   - same affected volume;
   - amplitudes rescaled to identical global RMSE.
   - For W0 mechanism only, an oracle plume corridor may define the upper-bound sensitive region.
   - This oracle region must never be used by the final inference method.

2. **Vertical-shear destruction vs horizontal-speed error**
   - smooth/remove vertical shear while preserving comparable global error;
   - compare with a matched horizontal speed perturbation.

3. **Direction error vs speed error**
   - matched vector-RMSE energy.

4. **Near-boundary / obstacle-wake error vs open-region error**
   - matched volume and RMSE.

5. Optional: **remove w component vs matched horizontal perturbation** if base flow has meaningful vertical velocity.

Do not add more families after looking at outcomes.

### Physical propagation

For every perturbation:
- rerun GADEN using the perturbed 3D wind;
- keep RNG paired where technically possible;
- use complete plume truth only for diagnostic evaluation, never as algorithm input.

### Downstream evaluation

Layer 1 — plume/sensor response:
- 2D column concentration footprint;
- source-blind virtual UAV concentration time series;
- arrival time / detection probability;
- plume path / footprint distance.

Layer 2 — source inference:
Use at least two different inference baselines if feasible:
- PMFS / candidate-probability baseline;
- a simple Bayesian/Gaussian/source-term likelihood baseline.

Reason: the phenomenon should not exist only because PMFS is brittle.

Report:
- true-source rank;
- Top-k;
- source localization error;
- posterior NLL/Brier/calibration if defined;
- KL/JS or other posterior distortion relative to oracle-wind inference.

### Primary phenomenon statistic

For each matched-RMSE perturbation pair A/B:

- verify |E_wind(A)-E_wind(B)| is within a pre-frozen tolerance;
- test whether downstream GSL damage differs materially.

Define before scoring:
- wind-error matching tolerance;
- minimum source-rank/posterior distortion ratio or absolute difference;
- consistency requirement over seeds and both sources.

### Suggested PASS logic

Do not require every pair to pass.

W0-A SCREEN PASS if:
- at least two pre-registered structural perturbation contrasts show reproducible unequal GSL damage under matched global wind error;
- direction is consistent across both sources in one House;
- at least one contrast repeats in the second House or later FSR pilot;
- result is visible in both plume/sensor response and source inference, not source rank alone.

W0-A HOLD if:
- strong effect in only one environment or only one baseline.

W0-A STOP if:
- matched global wind error predicts downstream damage as well as the structural perturbation type, or differences are dominated by realization noise.

---

## Stage W0-B — confirmation in FSR pilot only after FSR execution preflight

Do not build the full benchmark first.

Once FSR can run qualified CFD/GADEN:
- choose a very small controlled set (e.g. 2 forcing cases, 2 sources, 4 paired realizations);
- repeat only the structural contrasts that survived W0-A;
- preserve real-site geometry + controlled meteorological labels.

If House passes but FSR fails, do not call the mechanism “lakeshore-specific”.

---

## If W0 passes: method design principle

The final method cannot know the true source or oracle plume corridor.

Convert the oracle sensitivity finding into a source-blind quantity such as:
- posterior-weighted candidate transport corridors;
- expected source-likelihood sensitivity over candidate sources;
- wind-state ensemble marginalization;
- reduced wind modes ranked by expected posterior distortion.

One generic target formulation:

p(y | s, O_w) = ∫ p(y | s, U) p(U | O_w) dU

and prioritize transport information according to its expected influence on the source posterior, not global wind RMSE.

---

## If W0 fails

Explicitly STOP:
- GSL-task-oriented wind reconstruction;
- transport-relevance mask;
- source-posterior-driven wind assimilation.

Do not rescue by switching to a larger neural network.
