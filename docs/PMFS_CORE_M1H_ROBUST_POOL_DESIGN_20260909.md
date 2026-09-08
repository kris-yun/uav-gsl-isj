# CORE-M1H: transport-disagreement-robust causal evidence

## Motivation from the frozen failures

M1F fixed the retrospective-rescoring error by committing one event-time
window at a time. M1G then replaced the arithmetic transport-member mixture
with a geometric log pool. The H01 seed5 screen improved (4.258 m final,
298.367 m s AUC), but the preregistered H02/H03 seed5 expansion worsened in
both houses. The logs show the contract was obeyed (three native transport
members and eight new events per window); the failure is therefore
overconfident concentration under member disagreement, not an environment or
cadence mismatch.

## Fixed estimator

For candidate source region `c`, let `ell_u(c)` be the event-window
Bernoulli log-likelihood under native transport member `u`, after the frozen
centered-log-odds causal residual correction. M1H uses

```
ell_H(c) = mean_u ell_u(c) - 0.5 * Var_u[ell_u(c)]
L_H(c)   = exp(ell_H(c))
```

The coefficient 0.5 is fixed (no data-dependent tuning): it is the standard
second-order entropic-risk penalty for a unit risk-aversion bound. Thus a
candidate must have both high causal evidence and cross-transport agreement.
The sequential event-time commit, warmup exclusion, three-member native
transport, map/wind certificate, and A0 pairing are unchanged.

This is a robustness layer on the causal residual, not a new planner or a
post-hoc distance rescue. M1G remains frozen as an independently auditable
negative result.

## Theory anchors (2026)

- Madaleno et al., *Bayesian Hierarchical Invariant Prediction*, CLeaR 2026:
  partial invariance across environments motivates explicit uncertainty over
  environment-specific mechanisms.
- Asiaee, *Certified Interventional Fidelity*, UAI 2026: interventional
  claims require fidelity checks under distribution shift.
- Kim et al., *On Causal Representation Learning with Internal Auxiliaries*,
  UAI 2026: auxiliary environment variation can identify causal structure only
  when nuisance variation is controlled.
- Moran & Aragam, JASA 2026: causal representations should be evaluated by
  interpretable, mechanism-level identifiability rather than latent fit alone.

These papers support the design principle (separate invariant causal signal
from environment nuisance); they do not constitute gas-specific proof. The
closed-loop V3 paired gate remains the required empirical test.

## Falsification gate

First screen only H01 seed4 against A0 under the frozen House/environment
certificate and sensor seed12. If H01 fails either final error or exact
0--240 s ZOH AUC, stop and preserve M1H as NO_GO. Only a joint H01 pass permits
the preregistered H02/H03 seed4 expansion. Algorithm seeds under fixed sensor
seed12 are not independent plume realizations.
