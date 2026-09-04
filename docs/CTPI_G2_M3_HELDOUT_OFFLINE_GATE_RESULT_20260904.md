# CTPI-G2 M3 proper H2 held-out offline gate result

Date: 2026-09-04
Verdict: `CTPI_G2_M3_HELDOUT_OFFLINE_GATE=NO_GO`

## Observation law qualification

H01-only unpenalized MLE produced the monotone Bernoulli adapter:

`P(Y=1|S,a) = sigmoid(-0.3140391523 + 4.2809302349 * C_norm(S,a))`.

It passed the frozen held-out gate before policy evaluation:

| House | event rate | model NLL | constant NLL | model Brier | constant Brier |
|---|---:|---:|---:|---:|---:|
| H02 | 0.432257 | 0.659603 | 0.684045 | 0.233529 | 0.245462 |
| H03 | 0.360518 | 0.633365 | 0.666572 | 0.220632 | 0.236769 |

Therefore the negative M3 result is not caused by a failed observation-law
precondition.

## Proper H2 result

The gate used 128 paired worlds: 8 deterministic source carriers × 8 GADEN
transport members in each held-out House, a 32-action frozen spatial cover, and
10 acquisitions. H2 branched exactly over `Y=0,1`; no expected-observation
shortcut, discount, posterior multiplier, distance penalty, or tuned weight was
used.

Primary H2-minus-myopic source-risk AUC:

- pooled: 22 wins / 106 losses / 0 ties; mean delta `+0.0021204` (worse);
- H02: 13 / 51 / 0; mean delta `+0.0029891`;
- H03: 9 / 55 / 0; mean delta `+0.0012517`.

Localization-error AUC also worsened: 41 wins / 87 losses, mean delta
`+0.270792 m`. H2 did not stably beat exploit (57/71) or random (51/77).

The three pre-registered M3 PASS conditions therefore fail. Per contract, this
route is frozen as `CTPI_G2_M3_PROPER_H2_NO_GO_NO_RESCUE_TUNING`. Do not proceed
to runtime integration, H3, planner-weight tuning, or closed-loop claims from
this result.

The scope is static max-over-300s acquisition. This is a decisive falsification
of this H2 mechanism under that qualified law, not a universal impossibility
theorem for every future M3 design.

Raw result SHA-256:
`786661af5674b8dc12a4d98fb06aa6c77010e3be43d8a71fd368de321200b721`
