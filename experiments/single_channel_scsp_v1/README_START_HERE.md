# Single-channel metric-consistent source-safe projection (MC-SCSP)

## Decision being tested

The earlier candidate-conditioned CCDE wind-moment method is a held-out NO-GO.
Its physical wind association did not consistently beat matched-source filtering
or candidate-shuffled controls. The immutable negative package is retained in
`evidence/source/CCDE_HELDOUT_EVIDENCE_V3_20260807.tar.gz`.

This package tests one narrower correction to the existing GW-MAIN mechanism:
construct the source and nuisance subspaces in the **same confidence-weighted
observation metric**, use a rank-revealing basis for the source subspace, and
remove only the nuisance component orthogonal to all source contrasts. The
posterior rule and attribution weight remain frozen:

`p_A4 = (1-rho) p_structured(B_perp_source) + rho p_prior`.

No extra sensor, source shut-off, source library, learned network, new House,
new seed, planner change, or truth-selected threshold is introduced.

## Why this is a legitimate correction

The earlier code described both source and mismatch subspaces as whitened by
the observation covariance, but only whitened the source contrast. It also used
an unpivoted full QR basis even though the prior-centred source contrasts are
rank deficient by construction. Those two code/theory contradictions make the
reported overlap `rho` and projection geometry metric-inconsistent.

`code/metric_subspaces.py` repairs exactly those two contradictions. The legacy
implementation is retained as a control.

## One-shot development gate

Only the already-captured H03 seed11 first three source updates are used. This
is a development diagnostic because these data appeared in the previous CCDE
held-out package. It is not a new held-out or cross-House claim.

1. Verify `python code/test_metric_subspaces.py`.
2. Extract only H03 seed11 with `python code/prepare_h03_seed11.py`.
3. Run once with `python code/run_h03_seed11_gate.py`.
4. Accept the mechanism for a future untouched confirmation only if every
   preregistered condition in `PREREGISTRATION_H03_SEED11.json` passes.

The real-flight primary channel is one VOC scalar for evaporated ethanol. A
smoke cake is reserved for a separate PM2.5 robustness experiment because it
is principally an aerosol source rather than the gas represented by the PMFS
forward model. See `SINGLE_CHANNEL_REALFLIGHT_CONTRACT.md`.

