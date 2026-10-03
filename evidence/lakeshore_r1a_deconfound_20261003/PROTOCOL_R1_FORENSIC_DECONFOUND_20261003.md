# R1 forensic re-analysis and deconfounding gate
Date: 2026-10-03

## Status

The frozen original decision remains:

`R1_HOLD_WEAK_OR_UNSTABLE`

Do **not** retroactively promote it to PASS.

The previously proposed `R1_1_ELEVATED_LAYER_FOLLOWUP.md` is now **paused**. A deeper forensic re-analysis of the delivered 864-realization evidence found that F1/F2 simultaneously changed horizontal advection and vertical velocity, so the observed 30 m information cannot yet be attributed specifically to lake-front uplift.

The next experiment must first deconfound the mechanism.

## What the delivered data actually show

At release=10 filaments/s, threshold=0.001 ppm:

| env | hit rate 10 m | hit rate 30 m | M4 Top1 10 m | M4 Top1 30 m | median rank 30 m |
|---|---:|---:|---:|---:|---:|
| N0 | 0.3180 | 0 | 1.000 | 0.1111* | 5 |
| L1 | 0.3180 | 0 | 1.000 | 0.1111* | 5 |
| F1 | 0.6043 | 0.3239 | 1.000 | 1.000 | 1 |
| F2 | 0.5144 | 0.1756 | 1.000 | 1.000 | 1 |

`* 0.1111` is not 1/9 successful hard predictions. Every candidate has an exact equal score because all observations are misses; fractional tie credit gives 1/9 and average rank 5.

At 30 m the F1 median Brier margin (best false - true) is ~0.0775, minimum ~0.0309. F2 median is ~0.0449, minimum ~0.0075. Thus the 30 m signal is genuine within this synthetic family and not an exact-tie artifact.

The result is robust to the preregistered threshold factors 0.5/1/2 and to release=5/10; F2 release=20 has mild degradation.

## Strong source-distance structure in the elevated layer

At release=10, 30 m mean hit rates by source x are:

F1:
- x=20: 0.5285
- x=50: 0.2710
- x=80: 0.1722

F2:
- x=20: 0.2535
- x=50: 0.1856
- x=80: 0.0876

Define the simple vertical allocation ratio:
`R30 = hit30 / (hit10 + hit30)`.

For every one of the 8 plume seeds, Spearman(source_x, R30) = -1 in both F1 and F2.

Interpretation: farther-upwind sources have more time/distance for the plume to occupy the 30 m layer. This is a potentially useful physical fingerprint, but it is not yet uniquely attributable to vertical front uplift.

## Why attribution is currently confounded

Along the actual UAV path:

N0/L1:
- u(10 m) ≈ 2.0 m/s
- u(30 m) ≈ 2.0 m/s
- w = 0

F1:
- mean u(10/30 m) ≈ 0.597 m/s
- mean w(10 m) ≈ 0.055 m/s
- mean w(30 m) ≈ 0.143 m/s

F2:
- mean u(10/30 m) ≈ 0.794 m/s
- mean w(10 m) ≈ 0.110 m/s
- mean w(30 m) ≈ 0.285 m/s

Therefore F1/F2 change at least three things simultaneously:
1. horizontal residence/advection time;
2. x-dependent convergence/slowdown;
3. vertical lifting.

The 30 m gas may be caused by any combination. N0 is not a matched horizontal-speed control.

## Why the original diagnostics need reinterpretation

### M1
45-degree upwind-cone capture is 100% by construction for all gas hits because:
- v=0;
- sources are all west/upwind of the sampled transects;
- source y offsets remain within the very wide +/-45 degree cone.

M1 is therefore geometrically degenerate in this experiment and should not be used as evidence for or against the scene mechanism.

### M2
M2 preregistered the sign:
N0 low layer detectable -> front low layer suppressed -> higher layer restored.

The data show the opposite family:
front conditions increase 10 m hits and create 30 m hits.

Thus M2=0 does not imply "no vertical effect"; it implies the originally hypothesized low-level false-negative mechanism is not supported.

### M3
The +/-15 m front-band fraction is weak because the fixed ladder already contains x=130, only 10 m from the fixed x_front=120; N0 therefore has a built-in ~1/3 front-band baseline.

A more revealing exploratory diagnostic is the source_x -> peak_x mapping:

- N0/L1: monotone; median Spearman rho ~1.
- F1: compressed/shifted; median rho ~0.866, with seed variability.
- F2: ordering reverses; median rho ~-0.866 across releases.

At release=10:
- N0 source x 20/50/80 -> peak x 100/130/160.
- F2 source x 20/50 -> peak x 160, source x 80 -> peak x 130.

This suggests strong front-like flow can decouple concentration-peak position from source position, but the effect must be rechecked with matched horizontal-speed controls.

### M4
M4 contains the strongest result, but the correct statement is:

"Within the present synthetic front-like velocity family, source-discriminating hit patterns extend to 30 m, whereas N0/L1 contain no gas information at 30 m."

Do not yet state:
"lake-front uplift creates an elevated source-information layer."

## Another important limitation: current task is too easy at 10 m

At the 10 m trajectory, all environments reach Top1=100% by about the first 30 s in an exploratory prefix analysis. The full 300 s low-altitude observation is therefore already saturated.

This means the present matrix cannot demonstrate that an active vertical probe improves localization. It only demonstrates additional/relocated information at 30 m.

Also, naive equal weighting of 10 m + 30 m binary evidence can reduce Brier ranking because the weaker 30 m channel adds noise to an already perfect 10 m channel.

Therefore do not run the old R2 active-probe protocol yet.

## R1A: deconfounding experiment (must precede front-tracking R1.1)

Keep the same sources, seeds and path for the first causal decomposition. Add the following controls:

### C20
Current N0: u=2.0 m/s, w=0.

### C06
Uniform slow-advection control:
u=0.60 m/s, v=w=0.

### C08
Uniform slow-advection control:
u=0.80 m/s, v=w=0.

### S06
x-invariant vertical-shear control with path-level low-altitude u matched approximately to F1, w=0.

### S08
same, matched approximately to F2, w=0.

### H1 diagnostic ablation
Use the exact F1 u(x,z), but set w=0.
This is intentionally not a physically complete incompressible front; label it a numerical diagnostic only. It isolates horizontal convergence/residence effects from vertical displacement.

### H2
same using F2 u(x,z), w=0.

### F1/F2
unchanged full fields.

Primary analysis at release=10 first; 8 new seeds. Run release 5/20 only if the primary decomposition is interpretable.

## R1A questions

A. Do C06/C08 alone create the 30 m source-identifiability effect?
- YES -> residence time / ordinary diffusion is sufficient; stop the "front uplift" interpretation.
- NO -> continue.

B. Do H1/H2 create 30 m information without w?
- YES -> horizontal convergence/slowdown is sufficient or dominant.
- NO, but F1/F2 do -> vertical component is necessary within this model family.

C. Does full F1/F2 add a large incremental 30 m effect over H1/H2?
Measure:
- hit rate at 30 m;
- Brier margin;
- Top1 / median rank;
- vertical allocation ratio R30;
- source_x -> R30 monotonicity.

Only if F significantly exceeds both speed-matched and horizontal-only controls should the project use "vertical uplift" as the mechanism phrase.

## After R1A

Only if vertical/front structure survives the decomposition should the paused R1.1 be resumed with:
- 20/30/40/50 m heights;
- front x 90/120/150;
- w strength 0.25/0.5/1.0;
- new seeds;
- front tracking.

After that, create a genuinely ambiguous localization task before testing active sensing:
- denser candidate-source spacing and/or
- partial path budget and/or
- realistic sensor response/noise.

Do not deliberately tune difficulty to make the method win; freeze the ambiguity protocol before comparing horizontal vs vertical actions.
