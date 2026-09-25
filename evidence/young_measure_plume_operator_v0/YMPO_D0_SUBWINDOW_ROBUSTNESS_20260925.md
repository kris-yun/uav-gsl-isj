# YMPO D0 — Protocol-Conditioned Subwindow Robustness

Date: 2026-09-25

Status: **SUPPORTS PROTOCOL-CONDITIONED LOCAL MEASURE OBJECT; NOT STATIONARY-PDF CLAIM**

## Motivation

The ten frozen observation slices occur at simulator iteration indices

  [100,150,200,250,300,350,400,450,500,550].

The review package does not contain enough verified metadata to convert the 50-iteration spacing into physical seconds. Therefore snapshot counts are not reported as dwell seconds.

## Five-snapshot empirical-distribution tests

Using the same quantile empirical-measure summary and 6-fit / 2-calibration / opposite-8-fresh realization protocol:

- first five time indices: -2.204 / -2.328 bit;
- last five: -2.536 / -2.649 bit;
- interleaved even positions {0,2,4,6,8}: -2.090 / -2.122 bit;
- interleaved odd positions {1,3,5,7,9}: -2.134 / -2.207 bit.

The late block is less informative, so the local measure must not be described as a stationary concentration PDF independent of sampling protocol.

## Matched mean-field control on disjoint interleaved windows

Even five snapshots:
- per-probe mean field: -3.275 / -3.370 bit;
- empirical-measure field: -2.090 / -2.122 bit.

Odd five snapshots:
- mean field: -3.246 / -3.412 bit;
- empirical-measure field: -2.134 / -2.207 bit.

Thus two completely disjoint time subsets independently reproduce an approximately 1.1-1.3 bit/target advantage of the local empirical-measure representation over a point-valued mean field.

## Claim refinement

The scientifically defensible object is:

> a **protocol-conditioned spatial field of local concentration measures**,

not a universal stationary local PDF.

The measure is induced by the frozen short-window sampling distribution over simulator time/observation slices.

This claim remains compatible with the Young-measure mother theory at the representation level, while avoiding a false stationarity assumption.

## Next action

Stop further House02/W2 development.

Next gate must use a physically different canonical wind field and freeze all baselines before generation.