# M6 G1 High-Fidelity Target Contract — House02

Date: 2026-09-23  
Status: **FROZEN BEFORE NEW GADEN FIELD GENERATION**

## Purpose

Define exactly what high-fidelity field M6 is trained to predict.

M6 replaces the PMFS candidate **hit-probability / hit-frequency forward map**.

Therefore the first target is not arbitrary concentration MSE and not a transient video field.

It is a GADEN-derived time-averaged hit-frequency map at the robot sensor plane.

## 1. Source plane

House02 source interventions:

`z_source = 0.20 m`

This is the fixed House02 source plane for the 2-D PMFS target.

See:

`G1_HOUSE02_FIXED_SOURCE_PLANE_20260923.md`

## 2. Observation plane

Historical and recovered runner contract:

`flight_height = 0.30 m`

Therefore all G1 high-fidelity target samples are queried at:

`z_sensor = 0.30 m`

for each PMFS free x/y cell.

Do not sample the target on the source plane.

## 3. Gas HIT threshold

Official GSL code:

`thresholdGas = getParam<double>("th_gas_present", 0.1)`

The recovered launch does not override `th_gas_present`.

Thus the frozen first-pilot detection rule is:

[
Y(x,t)=mathbf 1[C(x,z_{sensor},t)>0.1].
]

Use the same concentration units returned by the GADEN runtime query.

No threshold tuning is allowed.

## 4. Simulation horizon

Physical simulation horizon:

`300 s`

matching the existing benchmark timeout/evaluation contract.

## 5. Burn-in / recording window

Primary burn-in:

`50 s`.

Reason:

Official Native PMFS forward settings use:

- `maxWarmupIterations = 500`;
- `deltaTime = 0.1 s`.

Thus the maximum Native PMFS warmup horizon is:

[
500	imes0.1=50 {m s}.
]

This gives a PMFS-native, source-blind warmup reference.

Primary recording window:

[
tin[50,300) {m s}.
]

## 6. Temporal sampling

Sample concentration once per physical second.

Primary field therefore uses 250 temporal samples:

[
t=50,51,ldots,299 {m s}.
]

If the RunningSimulation internal time step is 0.1 s, advance ten steps between exported field samples.

Do not change the sample cadence after inspecting source rank.

## 7. High-fidelity target

For source intervention (s), free PMFS cell (x):

[
oxed{
H_s^{HF}(x)
=
rac{1}{250}
sum_{t=50}^{299}
mathbf 1[
C_s(x,z=0.30,t)>0.1
]
}
]

Obstacle cells are masked and are not training targets.

This is the primary deterministic target for M6 G1.

## 8. Independent plume seeds

Generate two independent stochastic realizations per source.

### Training target
For training sources, the primary field target may average the two seed-specific hit-frequency maps:

[
ar H_s^{HF}
=
rac12(H_{s,11}^{HF}+H_{s,12}^{HF}).
]

Keep both seed-specific maps separately.

### Hard replay
At least one seed-specific realization must remain available for sparse-observation replay without using the averaged field as the observation source.

The exact seed split must be declared before training.

## 9. Required exported artifacts per source/seed

- source xyz;
- source split (train/val/test);
- GADEN random seed;
- environment/wind config ID and hash/path;
- grid x/y;
- sensor z;
- occupancy mask;
- concentration threshold;
- burn-in start/end;
- sampling frequency;
- raw or compact per-time hit samples if storage permits;
- final hit-frequency field;
- SHA256 of generated field and metadata.

## 10. Diagnostics — not model-selection targets

Also report:
- mean concentration field;
- concentration variance;
- hit-frequency map for windows [20,300) and [100,300) **only as source-blind stability diagnostics**.

The primary [50,300) target may not be replaced after truth/source-rank inspection.

## 11. Fairness to Native PMFS

For hard candidate replay:
- same source-candidate geometry;
- same sparse observation locations;
- same HIT threshold 0.1;
- same source update/evidence rule across learned forward arms;
- PMFS quadtree candidates integrated with fixed 2×2 source quadrature.

Only the candidate forward field changes.

## 12. Kill signal

If the two independent GADEN seeds for the same source yield hit-frequency maps whose disagreement is so large that the 250-s target is unstable relative to source-to-source differences, M6 deterministic G1 may be insufficient.

In that case:
- first quantify the stochasticity;
- do not silently average it away;
- M3 stochastic world modeling may become the justified extension.

Status:

`HOUSE02 G1 HIGH-FIDELITY TARGET CONTRACT FROZEN`.
