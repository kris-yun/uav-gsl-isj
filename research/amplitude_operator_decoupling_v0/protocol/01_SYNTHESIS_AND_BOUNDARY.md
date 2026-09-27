# Synthesis

## What is now supported on OPEN data

Using the SAME ordinary B2 positive-scale SSE score:

- H01:
  blurred `u`: mean rank 1.3333 / Top1 75%
  raw `rawu`: 1.3333 / 75%

- H02 W0:
  `u`: 1.5000 / 58.33%
  `rawu`: 1.2917 / 79.17%

- H02 W2:
  `u`: 1.4583 / 58.33%
  `rawu`: 1.2083 / 79.17%

Across 72 OPEN targets:
- rawu obtains 10 additional Top1-correct targets relative to frozen B2;
- it harms 0 targets that frozen B2 already classified correctly.

The 2x2 diagnostic shows:
- `rawu_nearest == rawu_footprint` in ranking metrics;
- `u_nearest == u_footprint` in ranking metrics.

Therefore **removing the extra hit-map blur is the isolated current mechanism**.
The probe-area average is not the isolated source of gain.

## What is NOT established

- blur is not universally bad;
- rawu is not calibrated ppm;
- unblurred amplitude is not yet confirmed on a new House;
- this is not yet a calibrated source posterior;
- improvement is concentrated in 4/18 environment-source units;
- no claim of wide cross-source generalization is permitted.

## Main scientific question that remains

The real question is no longer “is amplitude useful?” but:

> When numerical smoothing is introduced to make a binary occurrence model
> robust, should the same smoothing also be imposed on the amplitude observation
> channel when the task is to distinguish nearby source locations?

The candidate method direction is therefore **observation-operator
decoupling**, not generic marked-process modeling.
