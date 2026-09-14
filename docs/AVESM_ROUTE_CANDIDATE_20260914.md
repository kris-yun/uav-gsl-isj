# AVESM candidate: Anytime-Valid E-process Source Map

Date: 2026-09-14

## Why PE-WHRM stopped

PE-WHRM found positive ordered-history source evidence on the VGR factorial
development set, but its empirical ratio moment missed the calibration gate
(maximum absolute error 0.106). The missing property is not more expressive
representation; it is a sequential evidence object whose meaning survives
adaptive observation and optional stopping.

## Main innovation

**Anytime-Valid E-process Source Map (AVESM)** replaces the PMFS update kernel
with a source-grid map built from candidate-wise test martingales. For source
candidate s, define the null predictive distribution for the next gas
observation, `p_s(y_t | H_{t-1}, c)`, and a predictable alternative mixture
`q_s(y_t | H_{t-1}, c)` over the other source candidates. The update is

`e_{s,t} = q_s(y_t | H_{t-1}, c) / p_s(y_t | H_{t-1}, c)` and
`E_{s,t} = product_{tau<=t} e_{s,tau}`.

Under the null that s generated the history, `E_{s,t}` is a nonnegative
martingale (or supermartingale after safe calibration), so its expectation is
bounded at every stopping time. The probability-map interface is the normalized
test-inversion map

`pi_t(s) proportional to pi_0(s|c) / E_{s,t}`.

The fixed-rival evidence increment is
`delta_t(s*,r) = log E_{r,t} - log E_{s*,t}`. Positive values favor the true
source while retaining a finite-sample, anytime-valid evidence interpretation.

## What makes this a main mechanism

The contribution is not “use e-values” in isolation. It changes the map's
semantic object from an uncalibrated posterior-like score to a source-grid
test-inversion process whose evidence can be audited under arbitrary stopping,
history-dependent sensing, and source/time permutation controls. No online
candidate-response provider or dense field target is required.

## Falsification gate

1. Held-out null e-process expectation must remain at or below 1 under each
   source and under random stopping rules.
2. Intact true-versus-fixed-rival cumulative log-inverse-e-process margin must
   exceed direct pointwise `q0`.
3. Time-position and source-history permutations must collapse the margin and
   must not create false e-process threshold crossings.
4. Candidate-list permutation must exactly reorder the map.

Failure of the null expectation or optional-stopping gate is a hard NO-GO; no
closed-loop claim is opened by a positive rank result alone.

## Scope boundary

This is a development candidate. The existing VGR factorial source evidence is
explicitly diagnostic-only and its nominal seeds are pseudoreplicates. A PMFS
confirmation requires a genuinely independent source-by-transport asset after
the AVESM mechanism gate passes.

## Small transfer audit (2026-09-15)

Two cross-wind fits and one physical-distance fit were tested offline; none
passed the predeclared control/null gates. A route-protocol transfer from VGR
factorial episodes to eight R3C replays was also run. It produced a positive
mean inverse-e margin (`283.82`) and a reduced shuffle control (`3.16`), but
the true source was not reliably top-ranked (mean rank `2.5`) and every
episode crossed the log-20 e-process threshold. The R3C package explicitly
reuses the frozen R3B physical realization, so this is not independent
cross-simulation evidence. AVESM therefore remains an unproven candidate for
cross-data validity; no main-result claim is opened.
