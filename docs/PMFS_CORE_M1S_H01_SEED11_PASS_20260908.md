# CORE-M1S H01 seed11 early-screen result

Status: **H01_SEED11_EARLY_SCREEN_PASS; NOT_CROSS_HOUSE_PASS**.

## Frozen comparison

Both arms used binary SHA256
`31db663d5a0db9a379deed8bb40927dcca14152ced2e6f3be4835790b533b8f8`,
the same certified H01 realization and map, algorithm seed 11, sensor seed 12,
and a 240 s horizon.  Both ended with `time_budget_timeout` after reaching the
full horizon.

| Arm | Final error (m) | Distance AUC (m s) |
|---|---:|---:|
| A0 | 6.7250947949 | 1736.2323860 |
| M1S | 1.0004498988 | 1546.9054425 |
| A0 minus M1S | +5.7246448961 | +189.3269435 |

The preregistered early gate requires positive improvement in both final error
and 0--240 s distance AUC.  It passed.

## Causal-chain evidence

The runtime committed 104 completed sensing events in four disjoint windows:
32, 24, 24 and 24.  The logged starts were 0, 32, 56 and 80, proving that no
completed event was retrospectively rescored.  The analytic gate separately
showed exact cancellation of a candidate-common additive log-odds nuisance and
non-equivalence to retrospective rewriting.

This establishes a real trajectory-changing causal chain for one world:

```text
executed sensing intervention
  -> event-time nuisance-invariant source evidence
  -> sequential posterior
  -> changed PMFS planning trajectory
  -> lower final error and lower trajectory-wide error
```

It does not establish cross-House or big-data effectiveness.  The next gate is
the untouched H02/H03 pair at the same algorithm seed; extra seeds are
forbidden if that gate fails.
