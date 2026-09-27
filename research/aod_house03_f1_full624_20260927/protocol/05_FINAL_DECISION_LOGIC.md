# Final F1 labels

## Infrastructure holds

Before scientific scoring:

`AOD_F1_HOLD_TIMEBASE`
for physical-time/release-time/writer ambiguity.

`AOD_F1_HOLD_ASSET_OR_PARITY`
for candidate/source/wind/template/hash/implementation failure.

`AOD_F1_HOLD_FULL624_BUDGET`
only if the approved 54,912-candidate-forward bank cannot be completed.
If this occurs, DO NOT generate fresh GADEN and DO NOT silently shrink support
to 12.

## Nominal confirmation

Nominal full-support AOD confirmation requires BOTH:

N1. `Delta_acc_nominal >= 0.05`.

N2. nominal paired-bootstrap 95% lower bound `> 0`.

If either fails:

`AOD_F1_FULL624_NOT_CONFIRMED`.

Do not change sources, seeds, candidate support, score, blur or path and retry
the same confirmation.

## Stress interpretation, only after nominal confirmation

Let state0 stress CI be `[L0,U0]`.

### Non-inferior under the frozen stress

If:

`L0 >= -0.05`

final:

`AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR`.

### Supported negative stress effect

If non-inferiority fails AND:

`U0 < 0`

final:

`AOD_F1_FULL624_CONFIRMED_TRADEOFF`.

Interpretation:
nominal resolution improvement is confirmed, and rawu has supported negative
relative performance under the predeclared reduced-state/reduced-depth stress
condition.

Do NOT call this a pure wind-error causal effect.

### Stress uncertainty

If:

`L0 < -0.05` and `U0 >= 0`

final:

`AOD_F1_FULL624_CONFIRMED_STRESS_UNCERTAIN`.

Interpretation:
nominal improvement is confirmed, but 96 fresh plume realizations do not
establish non-inferiority or a supported negative stress effect.

This avoids converting a failed non-inferiority test into a decorative
“tradeoff” claim.
