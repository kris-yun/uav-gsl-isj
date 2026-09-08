# CORE-M1F closed-loop result

Status: **H01 CONFIRMATORY PASS; HOUSE123 SEED6 NO-GO**.

Binary SHA256:
`a2f639a623980f16893e8b96abea061d8814e1d570c408385579ac0b718c7a34`.
All paired arms reached the 240 s terminal contract.  Every M1F source update
contained exactly eight new observation blocks from one post-warm-up physical
stop.

## Seed7 H01 diagnostic

The V1 evaluator rejected the run because the last posterior update occurred
at 232.329 s during a navigation action that continued to 239.73 s.  This
exposed the evaluator's incorrect assumption that the final trace row itself
must be after 235 s.  After the symmetric full-horizon V2 repair, seed7 showed
diagnostic improvements of `+3.1403674509 m` final error and
`+321.7131607953 m s` AUC.  It is not confirmation because the evaluator repair
was made after this trace was visible.

## Seed6 prospective H01 and House123

V2 was frozen before seed6.  H01 passed strongly:

| House | Final improvement (m) | 0--240 s AUC improvement (m s) | Both positive |
|---|---:|---:|:---:|
| H01 | +4.0532227919 | +336.7562020456 | yes |
| H02 | +1.3660985115 | -90.8848194136 | no |
| H03 | -1.9237897592 | +95.3291045558 | no |

The first aggregate V2 JSON incorrectly reported PASS because its code counted
the final-error and AUC majorities separately.  That contradicted the written
rule requiring the same 2/3 Houses to improve both metrics.  V3 repairs the
gate and gives the correct verdict: only 1/3 Houses improves both, therefore
**HOUSE123 SEED6 NO-GO**.  The positive mean improvements
(`+1.1651771814 m`, `+113.7334957293 m s`) are retained but do not override the
joint-success rule.

## Failure attribution

- H02 ends closer to truth but accumulates more early error: event-time repair
  is eventually useful, but the evidence arrives too slowly.
- H03 accumulates less error overall, then its last update jumps from
  `(3.5,-1.413)` to `(9.2,3.387)`, worsening final error.  Arithmetic mixing of
  absolute member likelihoods allows a transport member's evidence scale to
  dominate the mixture even though that scale is nuisance.

The next revision must make the causal source contrast invariant to
member-specific likelihood scale.  No planner weight, threshold, truth-based
stopping, or failed-seed rescue is permitted.

All runs still use certified sensor/replay seed12.  These algorithm-seed tests
are not independent plume realizations and cannot support a big-data claim.
