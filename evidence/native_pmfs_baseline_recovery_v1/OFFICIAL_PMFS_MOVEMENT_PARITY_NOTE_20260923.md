# Official PMFS movement parity note — distanceWeight is computed but not used

Date: 2026-09-23
Purpose: baseline-integrity note only. **Do not treat as research innovation.**

## Verified on MAPIRlab/GasSourceLocalization humble

File:
`gsl_server/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp`

The ordinary PMFS implementation computes:

```cpp
double evaluation =
    interest /
    std::pow(pmfs->hitProbability[i].distanceFromRobot + 0.1f,
             pmfs->settings.movement.distanceWeight);
```

but then inserts:

```cpp
evaluations.insert({.indices = indices, .evaluation = interest});
```

Therefore the computed distance-penalized `evaluation` is not used by the ordering set.

This is not rendered moot by a zero parameter:
the official `Environment_config/PMFS/launch/main_simbot_launch.py` sets

```python
{"distanceWeight": 0.15},
```

and `PMFS.cpp` has a non-zero fallback default (0.1).

## Strong internal control

The SemanticPMFS counterpart,
`gsl_server/src/gsl_server/algorithms/Semantics/SemanticPMFS/MovingStateSemanticPMFS.cpp`,
computes the same distance-adjusted variable and inserts:

```cpp
evaluations.insert({.indices = indices, .evaluation = evaluation});
```

This makes the ordinary-PMFS line look like a likely implementation omission rather than an intended zero-weight behavior.

## Another movement detail relevant to parity

`MovingStatePMFS::chooseGoalAndMove()` calls `calculateMutualInformationGas()`, but the current
`informationValue()` implementation does not use `mutualInformationGas`.
The MI line is commented:

```cpp
// double varianceTerm = mutualInformationGas[...];
```

and the active term is the simulation-derived candidate hit-probability variance times hit-map uncertainty.

Therefore strict Native-PMFS parity must reproduce the actual code path, not an inferred/intended information-gain path.

## Required handling in baseline recovery

1. **Strict Native arm:** preserve ordinary PMFS humble behavior exactly.
   Do not silently change `.evaluation = interest` to `.evaluation = evaluation`.

2. Record this line/file/blob in the runtime/code provenance.

3. Only after strict Native results are frozen may a separate diagnostic arm test:
   `distanceWeight bugfix`.

4. Any such arm must be labelled an implementation bugfix ablation, not an algorithmic novelty.

5. Do not conflate this with the previous wind-path issue:
   - wind-path mismatch was caused by our VGR/R2 adaptation departing from the official launch contract;
   - this distanceWeight omission is present in the upstream ordinary-PMFS source itself.

This note does not alter the baseline-recovery charter's scientific gates.
