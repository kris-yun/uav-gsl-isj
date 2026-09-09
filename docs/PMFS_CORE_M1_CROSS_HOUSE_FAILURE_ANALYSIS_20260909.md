# CORE-M1 cross-House failure attribution

## Executive conclusion

The House123 NO_GO is not explained by a map, wind, or runtime alignment
failure. The implementation and environment contract were satisfied, but the
causal residual used by M1 does not obey the same transport-invariance
assumption in all Houses.

M1 assumes that transport-member variation is mostly candidate-independent
nuisance. Centered log-odds should then remove that common nuisance before the
source posterior is updated. The H02/H03 evidence indicates that the remaining
transport mismatch is candidate-dependent. It therefore survives centering and
appears as a systematic pseudo-causal source signal.

## Evidence that the environment contract was satisfied

- H01, H02, and H03 used the same environment preflight and geometry-manifest
  contract.
- The algorithm commit and binary hash were fixed within the M1H House123
  experiment (`a633673`, `2ccfd3c95d78a73d8a1833b5c23ff9999cb3f24540b4c4aab5702d0f83b6fce3`).
- `sensor_seed=12`, `stepsSourceUpdate=1`, warmup `(max,min)=(3,1)`, and the
  240 s horizon were fixed.
- Every M1H window used eight new events and the logs reported
  `transport_pool=robust_log_variance`.
- All four House123 seed4 arms reached the independent
  `time_budget_timeout` terminal status.

The repeated ROS warning about a publisher already being registered also
appears in H01 and H02 logs and is not specific to the H03 failure.

## House-specific closed-loop evidence

| House | M1H posterior/trajectory behavior | V3 paired outcome |
|---|---|---|
| H01 | Posterior gradually moved toward the source; closest error 1.018 m at about 210.5 s. | Final +5.707 m; AUC +359.819 m s |
| H02 | Posterior entropy collapsed to 0.104 and the endpoint improved, but the route was worse for much of the horizon. | Final +1.010 m; AUC −44.549 m s |
| H03 | The first post-warmup update moved the route away from the source; the final MAP was `(9.5,0.39)` while the true source was `(-0.45,1.9)`. | Final −2.008 m; AUC −67.676 m s |

H03 is the clearest counterexample. Around 50 s, A0 reached 0.45 m from the
true source, while M1H diverted to the right. The M1H route subsequently had
54.3% of sensor samples above 0.5 ppm, compared with 68.6% for A0. The causal
update therefore changed the sensing regime in the wrong direction.

## Why M1H did not fix it

M1H uses the fixed robust score

```
ell_H(c) = mean_u ell_u(c) - 0.5 Var_u[ell_u(c)]
```

This discounts disagreement between transport members. It does not remove a
shared House-specific bias. If all three members make a similar candidate-
dependent error, their variance is small and the wrong evidence can still
receive high confidence. This explains why H02/H03 can show entropy collapse
without reliable source localization.

## Scientific interpretation

The results establish four separate claims:

1. The M1 event-time causal chain is implemented and auditable.
2. M1 can produce real closed-loop gains in an individual environment.
3. The transport-invariance assumption is not valid uniformly across House123.
4. M1 cross-House closed-loop utility is not validated: the seed4 V3 joint gate
   has only 1/3 same-world final-and-AUC improvements.

Thus the failure should not be described as “the code did not run” or as a
generic lack of information. It is a falsification of the stronger claim that
the current causal residual is transport-invariant across Houses.

The next principled direction is a new preregistered mechanism that detects or
blocks candidate-dependent transport bias. Further changes to arithmetic,
geometric, or variance pooling alone would not address the observed failure
mode.

## Evidence files

- `evidence/cstar_core_m1h_h01_seed4_20260909_R4/`
- `evidence/cstar_core_m1h_h02h03_seed4_20260909_R1/`
- `docs/PMFS_CORE_M1G_M1H_SEED5_SEED4_RESULT_20260909.md`
