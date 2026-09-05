# CSTAR M2 hard contract — sparse local wind, no hidden full-field prerequisite

Date: 2026-09-06

This document closes an ambiguity in the first CSTAR theory freeze.

## 1. Runtime wind information actually available

The deployable robot is allowed timestamped **local** wind observations at executed poses, plus geometry. It does not receive a future GADEN wind field or an oracle global wind map.

The current checked GMRF path is not promoted to a prerequisite: the archived spent-record audit showed the checked cumulative predictor still underperformed simple persistence for next-local-wind RMSE and the latest-cell variant failed to converge. Therefore CSTAR must remain scientifically valid when GMRF is absent.

## 2. CPO final API

CPO must accept directly:

`(source hypothesis, geometry, sparse stamped local-wind history, gas/sensor causal state, candidate future route)`

and output the future first-passage/committor/marked observation law.

It must **not** require a complete `u(x,y),v(x,y)` field as a mandatory runtime input.

## 3. Role of CTPIOnlineCoreV2::Transport

The conservative V2 solver remains valuable for:

- numerical/physical prior features;
- offline counterfactual data generation where a declared wind field exists;
- a baseline provider;
- parity and conservation tests.

But it is not the final M2 identity and cannot force a hidden global-wind-estimation stage.

For a causal baseline when only local wind is available, a explicitly named `LOCAL_PERSISTENCE_BROADCAST` prior may broadcast the latest local vector over the free grid for a short prediction horizon. This is intentionally coarse, truth-blind and auditable. CPO may learn a geometry/context-conditioned correction from heterogeneous offline transport data around that prior.

Any future improved wind-field provider (GMRF or otherwise) is an optional provider ablation. It must satisfy the same timestamp/geometry contract and demonstrate predictive utility independently before use.

## 4. Scientific implication

CPO's scientific object is the **conditional encounter law under sparse causal context**, not recovery of the exact global wind field. A full-field reconstruction is neither a required claim nor an excuse to delay the main M2 falsification.

The required zero-shot test therefore gives the held-out House only its geometry and the local wind/gas/pose stream available to a real robot. No held-out-House wind bank or simulated future field is exposed.
