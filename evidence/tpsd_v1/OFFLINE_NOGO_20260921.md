# TPSD V1 offline screen — NO-GO

Date: 2026-09-21

Status: **NO_GO_ON_NATIVE_300S_ENDPOINT**

## Data

Authoritative frozen R2 six-case archive:

`TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`

All six native runs contain 1500 sensor samples (5 Hz, 300 s), pose traces,
wind traces, five source updates, and final candidate-support exports.

Final candidate-support coverage along the native trajectory was:

- H01/s0: 98.8%
- H01/s1: 100.0%
- H02/s0: 100.0%
- H02/s1: 97.8%
- H03/s0: 99.6%
- H03/s1: 99.0%

No interpolation was needed for the screening samples.

## Endpoint parity

A local C++ clone of the original probability-only `std::sort`
`ExpectedValue(sourceProbability,0.05)` semantics reproduced the six native
endpoints to about 2e-7 m.

Therefore this screen was evaluated on the original 300-s top-5% source
endpoint, not only source rank.

## Evidence variants

All variants used the same final candidate response maps and the same native
trajectory observations.

Controls:

- native PMFS
- cumulative Bernoulli temporal likelihood
- event latency
- primacy-only early-window evidence
- generic cross-hypothesis inhibition

TPSD:

- event-locked early evidence
- delayed candidate-overlap-weighted inhibition

Sensitivity grid was fixed before evaluation:

- early window: 0.4 / 1.0 / 2.0 s
- late window: 2 / 5 / 10 s
- posterior tilt beta: 0.25 / 0.5 / 1 / 2

The invalid case where late-window end equals the early-window end
(`2.0 s early + 2.0 s late-end`) is excluded from interpretation.

## Result

Native pooled mean:

`5.555060 m`

Ordinary cumulative temporal likelihood was slightly negative:

- beta 0.25: -0.0053%
- beta 2: -0.0402%

Generic inhibition was also negative in pooled endpoint despite improving some
true-source ranks:

- beta 0.25: -0.0099%
- beta 2: -0.0877%

Primacy-only produced small positive changes. The strongest tested
primacy-only setting reached about +0.25% pooled improvement.

The valid TPSD delayed-inhibition variants were also only small corrections.
The strongest tested valid settings were approximately:

- 1.0-s early / 10-s late-end / beta=2: +0.4568%
- 2.0-s early / 5-s late-end / beta=2: +0.4816%
- 2.0-s early / 10-s late-end / beta=2: +0.5014%

These do not meet the predeclared promotion bar (~2% pooled and clear
advantage over primacy/latency controls).

## Scientific interpretation

The 2026 olfactory-bulb temporal-primacy mechanism has a detectable but weak
analogue in this dataset: early encounter evidence is modestly less harmful
than full cumulative evidence.

However, the key proposed new ingredient — delayed cross-hypothesis
decorrelation/inhibition — does not produce a sufficiently large or robust
native-endpoint gain to justify a new online method.

This result also shows why source-rank improvements alone are insufficient:
generic inhibition strongly improved average true-source rank but degraded the
actual PMFS endpoint.

## Decision

TPSD V1 is frozen as a negative screen.

Do not tune:

- early-window length;
- late-window length;
- inhibition gain;
- posterior beta;
- event threshold

on these same six cases.

Do not implement TPSD in ROS.

Proceed to a different scientific mechanism.
