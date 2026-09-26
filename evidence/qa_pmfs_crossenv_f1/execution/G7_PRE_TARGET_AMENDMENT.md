# QA-PMFS F1 — G7 pre-target amendment

Date: 2026-09-26

This amendment resolves the previously non-numeric phrase
“no catastrophic calibration failure comparable to old JTD FULL”.

It MUST be frozen before any fresh-target truth/rank/posterior metric is read.

## G7 scope

G7 applies only to the fixed-transfer main model:

- M0 = independent full-marginal Bernoulli likelihood baseline
- M3 = fixed QA transfer model, `L=T, rho=0.6`

M1 and M2 remain mechanistic/reference-selection diagnostics and are NOT part
of G7.

## Metric

For each environment `e`, compute the source-averaged true-source posterior NLL:

`NLL_e(M) = mean_s mean_{j in fresh targets of s} [-log q_M(s | y_{s,j})]`.

Posterior probabilities must be computed in log-space with the same frozen
source prior/support for M0 and M3. Do not clip posterior probabilities to
satisfy the gate.

Define

`DeltaNLL_e = NLL_e(M3) - NLL_e(M0)`.

## Numeric threshold

G7 PASS iff, for EVERY environment,

`DeltaNLL_e <= ln(10) = 2.302585092994046 nats`.

Equivalently, on the geometric-mean true-source posterior probability scale,
M3 may not make the truth more than 10x less probable than M0 in any single
environment.

If any environment has

`DeltaNLL_e > 2.302585092994046`,

then G7 FAILS and `QA_F1_CROSS_ENV_CONFIRMED` is forbidden.

A G7 failure is reported as `QA_F1_NOT_CROSS_ENV_GENERAL`, not
`QA_F1_CALIBRATION_ONLY`.

## Why this threshold

This threshold is prospective and interpretable; it is NOT tuned from the new
fresh targets. A one-order-of-magnitude loss in geometric-mean true-source
posterior is defined here as catastrophic.

The historical JTD FULL failure had environment-level NLL degradations of many
tens of nats in the failing environments, so this rule would have caught that
failure by a wide margin, without copying its observed magnitude as the new
threshold.

## Interaction with the existing gates

- G6 remains: pooled M3 posterior NLL must be lower than pooled M0.
- G7 is the environment-level anti-catastrophe guard.
- Therefore a pooled improvement cannot hide a severe failure in one
  environment.

No other F1 rule is changed by this amendment.
