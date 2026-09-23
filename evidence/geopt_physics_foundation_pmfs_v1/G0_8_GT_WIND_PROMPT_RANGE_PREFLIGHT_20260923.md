# M6 G0.8 — Ground-Truth-Wind Dynamics-Prompt Range Preflight

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`G0.8 = POSITIVE RANGE CHECK`

A recovered-Native ground-truth wind field was used to test whether the proposed GeoPT-aligned gas dynamics prompt is grossly out of the pretraining step-length range.

This is an interface/range check only, not a source-localization result.

## Data provenance

Source:

`research/native-pmfs-baseline-recovery-v1`

R0 House01 seed0 ground-truth-wind recovery.

The R0 audit already established:
- GADEN ground-truth wind branch active;
- 626/626 free-cell internal PMFS vectors match the wind service at float32 storage precision.

Thus this check does not use the invalid old R2 GMRF forward wind.

## Ground-truth wind distribution

Across 626 free cells at the first recovered source update:

- min: ~8.73e-6 m/s
- Q25: ~0.03023 m/s
- median: ~0.05972 m/s
- Q75: ~0.09702 m/s
- Q90: ~0.17905 m/s
- Q95: ~0.26265 m/s
- max: ~0.45102 m/s

## GeoPT geometry scale

House01 PMFS x extent:

`8.4000001 m`

GeoPT-style target x extent:

`5`

Source-blind coordinate scale:

`scale_geo = 5 / 8.4000001 = 0.5952381`

## Pretraining-aligned dynamics prompt

Define:

`step_length = scale_geo * wind_speed * tau_ref`

For the first range preflight use:

`tau_ref = 1 s`

Reason:
1 s is a natural simulator/wind timescale and is not chosen from source truth.

Resulting normalized advective step length:

- min: ~5.20e-6
- median: ~0.03555
- Q90: ~0.10657
- Q95: ~0.15634
- max: ~0.26846

Fraction above GeoPT pretraining `max_step=2`:

`0 / 626 = 0%`

## Comparison to tau=0.1 s

Using 0.1 s:

- median: ~0.00355
- Q95: ~0.01563
- max: ~0.02685

This is also inside the pretraining range, but is much more concentrated near zero.

## Interpretation

The physically derived 1 s wind-displacement prompt is:

- inside the released GeoPT synthetic step-length support;
- not numerically extreme;
- source-blind;
- tied to a physical displacement interpretation.

It is still concentrated in the lower part of GeoPT's uniformly sampled [0,2] step-length range.

Do **not** rescale it upward merely to resemble the pretraining histogram.

If a different `tau_ref` is used later, it must come from a fixed protocol/physical horizon and be declared before truth evaluation.

## Next requirement

Codex G0.5 House02 token export should reproduce the same statistics with recovered GADEN ground-truth wind:

- wind-speed quantiles;
- normalized step-length quantiles;
- fraction outside [0,2].

If House02 remains inside support, proceed to frozen-backbone G1.

Status:

`PASS RANGE CHECK — NO OBVIOUS DYNAMICS-PROMPT OOD BARRIER`.
