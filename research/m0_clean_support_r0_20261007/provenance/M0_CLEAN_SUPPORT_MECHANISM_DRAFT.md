# M0 clean-support matched-error mechanism experiment — draft contract

## Purpose

Obtain a clean causal answer to the phenomenon blocked by W0C Stage 0:

> With equal global wind-field error, can different spatial/structural error patterns cause reproducibly different plume/source-inference damage?

M0 is a **mechanism screen**, not a paper benchmark.
FSR remains the intended main lakeshore benchmark.

## Scene construction

Use a new, simple, large 3D GADEN scene with no legacy House boundary limitations.

Architecture:
- inner analysis ROI contains both candidate sources and the entire virtual-UAV route;
- outer simulation domain adds a guard band on every horizontal side;
- source placement is frozen before any perturbation run;
- equal source height;
- sufficient obstacle/domain clearance.

Preferred initial scene:
- obstacle-free or minimally obstructed box;
- one controlled base wind with material horizontal advection and nonzero vertical shear;
- if GADEN allows direct wind-field generation, use an analytically specified smooth field;
- no OpenFOAM required for M0.

Do not claim M0 is lakeshore.

## Clean-support qualification

Before perturbations:
- run 4 unperturbed realizations;
- use a pre-frozen 100–700 s or other task window chosen *before* looking at plume outcomes;
- require plume support well inside the simulation-domain boundary;
- use a direct guard-domain criterion rather than selecting an edge by mean wind;
- record full all-side outer-band mass, centroid clearance and source clearance;
- 4/4 baseline realizations must pass.

If baseline fails, enlarge the simulation domain under a new predeclared build revision; do not move only the favorable source or shorten the window after seeing data.

## Perturbation pairs

Only after baseline qualification.

Start with two pairs:

A. **on-transport-region directional error vs same-volume off-region directional error**
- same amplitude / support volume;
- matched global vector RMSE.

B. **vertical-shear distortion vs matched horizontal-vector error**
- global vector RMSE matched.

Freeze:
- support masks;
- amplitude;
- RMSE tolerance;
- physical consistency checks;
- all metrics before running perturbed plumes.

Do not add new perturbation families after results.

## Paired simulations

For each perturbation:
- same source;
- same gas;
- same RNG;
- same release parameters;
- same geometry;
- same clock;
- only wind differs.

Use 2 candidate sources × 4 paired realizations initially.

## Source observations

Use a deterministic source-blind sparse UAV route fixed from ROI geometry only.
No oracle plume route.

## Inference baselines

At least:
1. simple Bayesian / source-term likelihood;
2. PMFS-compatible or candidate-forward probability baseline if low-cost;
3. transport-ensemble / many-wrong-models baseline only as prior-art comparison, not proposed novelty.

No neural network.

## Primary gate

For every matched-error pair:
1. global wind RMSE difference within frozen tolerance;
2. plume/sensor damage differs materially;
3. source-posterior/localization damage differs materially;
4. direction consistent in >=3/4 paired realizations.

M0_PASS:
- both preregistered structural contrasts show task-anisotropic downstream damage, or one strong contrast repeats for both sources with both inference families.

M0_PARTIAL_HOLD:
- effect appears only for one source or one inference family.

M0_STOP:
- equal global wind error produces no reproducible structural difference in GSL damage.

Stop automatically after verdict.

## After M0

PASS -> repeat only the surviving contrast(s) in FSR pilot.
HOLD -> Pro review before any expansion.
STOP -> abandon task-sensitive wind/transport mainline.
