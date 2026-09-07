# M1 route-law score V1

`m1_picr/route_law_score.py` is the shared observation-law boundary between
M2 and M1. It consumes one candidate-conditioned route law and one
source-response-masked context law per candidate, then computes a normalized
AR(1) innovation log score. Thus the M1 increment is a difference between two
fully specified conditional laws rather than an unnormalized distance or a
per-step hit product.

The validity contract is explicit: an invalid frame contributes no likelihood
factor and resets the local innovation chain; a valid zero-valued sensor sample
is scored normally. Candidate masks and priors are passed to the existing
conditional-evidence transform, preserving fixed support and rejecting empty
candidate sets.

The CPU check is:

```text
CSTAR_M1_ROUTE_LAW_SCORE_SELFTEST PASS
CSTAR_M1_M2_SHARED_LAW_SELFTEST PASS
```

The second check exercises the actual physical prior as both candidate law
and source-masked context denominator; it is still a mechanism/integration
check on a synthetic grid, not a House-data gain.

This proves only shape, normalization and validity semantics. It is not a
House-data result, a PMFS comparison, or evidence for a causal localization
gain. The observation law still requires physical-prior parity, calibration,
route intervention controls and a prospective one-shot gate.
