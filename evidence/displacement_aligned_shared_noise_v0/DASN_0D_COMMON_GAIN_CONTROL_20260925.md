# DASN 0D — Common-Gain Control

Date: 2026-09-25

Status: **COMMON_GAIN_DOES_NOT_EXPLAIN_SHARED_LOCALIZATION_ERROR**

This is a lightweight control using the same D1R bank and the same odd/even probe localization construction as DASN 0A-0C.

## Gain nuisance

For each source s and fresh plume realization r, define one scalar common-amplitude variable:

g_sr = log(1 + total ppm over all 10 times x30 probes).

Center g within source.

For each probe-view readout and each coordinate x/y:

1. center localization error within source;
2. fit one pooled OLS slope from centered error to centered g;
3. subtract the fitted gain component;
4. recompute paired odd/even shared localization error on the residuals.

This deliberately tests the simplest common-amplitude explanation. It does not claim to remove arbitrary nonlinear plume-scale effects.

## Direction A

Train reps 1-8; diagnose reps 9-16.

Unified reimplementation gives:
- pre-control T = 0.02957 m^2;
- gain-residualized T = 0.02981 m^2;
- relative change = +0.8%.

Residual pairing-destruction null, 300 permutations:
- q2.5 = -0.00874 m^2;
- median = -0.00036 m^2;
- q97.5 = 0.00875 m^2;
- exceedance = 0/300.

## Direction B

Train reps 9-16; diagnose reps 1-8.

- pre-control T = 0.023995 m^2;
- gain-residualized T = 0.024069 m^2;
- relative change = +0.3%.

Residual pairing-destruction null, 300 permutations:
- q2.5 = -0.00746 m^2;
- median = 0.00020 m^2;
- q97.5 = 0.00705 m^2;
- exceedance = 0/300.

## Note on numerical difference from 0A-0C

The absolute pre-control T values in this control come from a unified small reimplementation of the ridge readout/CV pipeline and differ slightly from the earlier exploratory 0A-0C values (0.0267 and 0.0215 m^2).

The localization errors themselves reproduce the earlier magnitudes closely. The 0D scientific conclusion depends on the within-implementation before/after gain comparison, not on mixing the two implementations.

## Decision

The simple common-gain hypothesis is rejected as an explanation for the shared localization-error signal.

Established after 0D:

> same-realization shared localization error persists after removing a source-centered global plume-amplitude nuisance.

Not yet established:
- rejection of generic low-rank shared factors;
- readout-family invariance;
- boundary independence;
- source-displacement/Jacobian alignment;
- information-limiting correlation.

Next mini-step: **DASN-0E generic low-rank factor control only**.