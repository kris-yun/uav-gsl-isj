# ATC V1 implementation compatibility audit

Date: 2026-09-22

## Question

Can the existing PMFS source simulator be treated as the callable substep map required by Alternating Neural Integrators?

## Source audit

The native candidate path calls:

`simulateSourceInPosition(source, hitMap, true, settings.iterationsToRecord, settings.deltaTime, settings.noiseSTDev, ...)`.

Inside `simulateSourceInPosition`:

- new filament vectors are created on every call;
- a fresh warm-up releases/moves filaments until stabilization/max warm-up;
- recording then runs for the requested number of timesteps;
- `hitMap` is accumulated and divided by `timesteps`;
- no final filament ensemble or dynamical state is returned.

Although `timesteps` and `deltaTime` are parameters, the interface is a source-to-stationary-field generator, not an advance operator from one plume state to the next.

## Consequence

The existing PMFS routine cannot be inserted directly as `P_tau(u)` in a Strang/ANI composition without changing its semantics.

Calling it twice for half as many timesteps is not equivalent to advancing one persistent state through two half-steps, because both calls restart/warm up independent filament ensembles.

## Decision

- Direct ANI transfer: **NOT SEMANTICALLY VALID ON THE CURRENT PMFS INTERFACE**.
- Terminal field residual correction: still testable, but must be described as discrepancy correction, not ANI.
- Stateful filament refactor: possible future research route, but intrusive and not authorized by this branch.

The existing `reference/atc_v1_stage_a_offline_gate.py` remains a diagnostic falsification screen only.
