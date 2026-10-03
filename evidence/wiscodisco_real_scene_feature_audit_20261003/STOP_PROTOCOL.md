# R1B postmortem: STOP current parametric front mainline and reset the scene question
Date: 2026-10-03

## Frozen decisions
Keep unchanged:
- R1 = `R1_HOLD_WEAK_OR_UNSTABLE`
- R1A = `R1A_RESIDENCE_SUFFICIENT_STOP_UPLIFT_ATTRIBUTION`
- R1B = `R1B_HOLD_MISMATCH_NOT_FRONT_LOCKED`

Do not retroactively promote any of them to PASS.

STOP for the current paper-mainline:
- elevated source-information-layer/uplift mechanism;
- front-induced source-range-compression as a lake-specific mechanism;
- R1.1 and R2;
- high-fidelity CFD launched only to rescue this failed parametric-front hypothesis.

## What R1B really proved
The 3888-realization confirmatory matrix shows a robust **model-mismatch** phenomenon:
- XF90_F1: 36.57 pp Top1 loss, +11.39 m downstream mean x bias;
- XF90_F2: 55.56 pp, +16.94 m;
- XF120_F1: 24.54 pp, +7.36 m;
- XF120_F2: 30.09 pp, +9.03 m;
- XF150_F1: 0;
- XF150_F2: 0.93 pp.

For the four affected scenes:
- errors are downstream;
- direction is 100% among errors;
- 8/8 new seeds are direction-consistent;
- all six uniform negative controls remain 100% Top1.

Therefore the effect is real inside this synthetic family, but not demonstrated to be front-locked.

## Why the front-lock gate failed
All candidate sources are at x={20,50,80} m.
All front positions are x={90,120,150} m.
Thus **every source is upstream/behind every tested front**. Moving the front never makes a different source group cross from one side of the front to the other.

The most-vulnerable source remaining x=20 is therefore not surprising. This geometry is poor for asking whether the "affected source region moves with the front".

However, this does NOT justify changing the frozen gate post-hoc. It means only that R1B is inconclusive about a front-relative causal mechanism.

## Exploratory path-relative observation
Using the frozen 300 s route at z=10:
- XF90: fraction of path with x > x_front = 1.000
- XF120: 0.493
- XF150: 0.163

Mismatch magnitude falls in the same order:
- F1: 36.57 -> 24.54 -> 0 pp
- F2: 55.56 -> 30.09 -> 0.93 pp

But front position is simultaneously coupled to matched path speed:
- F1 matched speed: 0.477 -> 0.597 -> 0.714 m/s
- F2: 0.553 -> 0.795 -> 1.029 m/s

Therefore neither "fraction of route across the front" nor "path mean speed" can be isolated from this matrix.

A post-hoc first-transect decomposition also does not yield a clean single cross-front signature. It should not be used to rescue the hypothesis.

## Another important design fact
At the primary z=10 endpoint, the "uniform" and "profile" baselines are effectively the same test: the profile control is x/y invariant and is matched at each height; at a single fixed z=10 endpoint it collapses to the same scalar horizontal wind used by the uniform control. Their identical primary results are therefore not two independent confirmations.

## Scientific interpretation
The strongest defensible statement is:

> A spatially nonuniform flow field unknown to the inference model can produce large, seed-stable, directional source-position bias even when a uniform model is matched to the measurement-path wind speed.

This is **generic model misspecification**, not yet a lake-specific novelty.

Recent GSL work already addresses changing wind, topography, and spatial context. Therefore this generic statement is not sufficient for the thesis main innovation.

## Decision: do not spend another large matrix on this exact parametric front
No more tuning:
- front location;
- w amplitude;
- source grid;
- threshold;
- candidate spacing;
to make R1B pass.

The current parametric-front branch has completed its role: it falsified uplift attribution and revealed generic spatial-wind model mismatch.

## Next scene-specific search must start from real lake observations, not another hand-built front
Before generating any new GADEN matrix, use public lakeshore observations to identify **one feature that is both:**
1. demonstrably present in real lakeshore low-altitude data at UAV-relevant scales;
2. absent from / not represented by ordinary GSL assumptions;
3. measurable online by a UAV or a small set of auxiliary sensors;
4. capable of creating a specific source-localization failure, not just a different wind field.

Priority candidate features to audit:
A. shallow lake-breeze/internal-boundary-layer height intersecting UAV operating altitude;
B. vertical directional decoupling between near-source layer and UAV layer;
C. persistent shoreline convergence/stagnation zone tied to the water-land thermal boundary;
D. humidity/temperature air-mass boundary usable as a marker of lake-air vs land-air state.

For each candidate, first use WiscoDISCO/LMOS/JGR/FastEddy evidence to quantify the actual magnitude and time/height scale. Do not simulate gas until a real-data gate is passed.

## New hard gate before any next GADEN run
A new mechanism is allowed to proceed only if public/observational evidence shows:
- it occurs on a 5–300 s UAV task-relevant spatial/temporal window, or remains quasi-steady during such a task;
- its magnitude is large enough to cross at least one planned UAV sensing altitude/trajectory;
- at least two independent profiles/events or one event plus an independent literature/LES source support it;
- the proposed UAV-observable variables can distinguish the state without access to hidden truth.

If no lake-specific feature passes this real-data gate, stop making "lake physics" the first-paper novelty. Keep lake shore as the target application/validation scenario and return the main methodological innovation to task-sufficient source localization / robust active sensing.
