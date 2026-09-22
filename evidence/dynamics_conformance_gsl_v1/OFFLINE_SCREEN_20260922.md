# Dynamics-Conformance GSL V1 — cheap screen

Date: 2026-09-22
Status: **NO-GO AS MAIN INNOVATION**

## Remote-field anchor

ICLR 2026 — Banerjee & Gupta, *Detection of unknown unknowns in autonomous systems*.

The transferred idea was model-recovery-and-conformance: detect structural changes in underlying dynamics rather than marginal distribution shift.

## GSL screen

For each source hypothesis, construct candidate-relative state variables from:
- gas empirical rank;
- normalized source-relative radius;
- radial wind projection;
- normalized wind speed;
- source-relative radial motion.

Use a fixed low-order nonlinear library to model d(gas-rank)/dt.
For a target fast/slow trajectory, fit the source-specific model only on the opposite-wind trajectory and score target conformance by normalized prediction RMSE.

No endpoint truth is used to fit model parameters.

Tested fixed temporal strides:
- 0.4 s
- 1.0 s
- 2.0 s

and horizons 120/160/176/200/220/240 s.

## Best results

The most favorable fixed configuration (2.0-s stride) reaches:
- 220 s: 12/12
- 240 s: 11/12

Other fixed strides range mostly between 9/12 and 11/12 at late horizons.

The failure is not stable with horizon and sampling stride.

## Decisive comparison

Previously frozen candidate-relative static spatial structure reaches 12/12 at 160, 176, 180, 200, 220 and 240 s on the same controlled asset.

Therefore model-space dynamics conformance does not provide an earlier or more stable source-identity signal than the simpler static source structure.

## Decision

The ICLR-2026 unknown-unknown / model-conformance principle is scientifically relevant to GSL model validity, but the source-conditioned dynamics-conformance mechanism is **not load-bearing for localization on the available controlled asset**.

Do not promote it as the paper-level main innovation.
