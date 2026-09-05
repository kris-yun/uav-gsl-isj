# CSTAR current-code alignment at base 2387668

Date: 2026-09-06
Purpose: prevent scientific-identity drift during implementation.

## 1. Current M1 is not the new causal M1

File: `ros2_package/src/gsl_server/algorithms/PMFS/CPIR.cpp`

### `recordCPIRRawSample`

Keep the causal timestamp intent: gas is bound to the latest pose with timestamp `<= gas time`; future poses are rejected.

Do **not** keep `cpirObservedCellPeak` as the primary M1 statistic. It destroys event time, transport history and much of the sensor-memory evidence by retaining only a per-cell maximum.

### `applyCPIRPosterior`

Current scientific calculation:

1. select visited cells;
2. normalize observed cell peaks by the largest observed peak;
3. for each candidate source, build a Gaussian plume under historical or latest wind direction;
4. normalize predicted plume shape by its maximum;
5. calculate SSE between normalized observed/predicted shapes;
6. score with `-100*SSE/N`;
7. exponentiate and normalize to `sourceProbability`.

This is the legacy/negative-control M1 after CSTAR is introduced. It is not causal representation learning and it does not explicitly separate source strength, transport nuisance or sensor memory.

## 2. Current V2 online core is useful infrastructure

File: `ros2_package/src/gsl_server/algorithms/PMFS/CTPIOnlineCoreV2.hpp`

### Keep

- `Transport`: shared-face conservative advection/diffusion, CFL substeps, nonnegative convex update, source injection, mass-balance guard.
- `Fopdt`: explicit sensor memory with tau/dead time and causal history.
- `ObservationStream`: predict-before-observe, no future wind, monotone 0.2 s samples and non-overlapping observation blocks.

### Do not overclaim

The `Transport` API requires full `u/v` arrays. A reliable full online wind field is not currently established. Therefore it is a prior/baseline component for M2, not a hidden prerequisite for deployable CPO. See `CTPI_CSTAR_M2_SPARSE_WIND_CONTRACT_20260906.md`.

## 3. Current M3 must be replaced scientifically

File: `ros2_package/src/gsl_server/algorithms/PMFS/CTPI.cpp`
Function: `PMFS::evaluateCTPIActionInformation`

Current calculation:

1. marginalize cell posterior to carrier blocks;
2. replace each carrier region by one center coordinate;
3. predict one action-cell plume response from historical/latest wind;
4. convert plume scalar to soft binary hit probability;
5. calculate one-step binary mutual information;
6. multiply by `(1 + 20 * posteriorMassAtAction)`.

CSTAR PHS must remove:

- carrier-centroid replacement;
- one-point future observation as the whole horizon;
- direct dependence on current plume scalar as the sole M2 law;
- the `20x` posterior exploitation factor.

The old function remains a required baseline for M3 falsification.

## 4. Current controller contains M1 heuristics that must not define F00

File: `ros2_package/src/gsl_server/algorithms/PMFS/MovingStatePMFS.cpp`
Function: `chooseGoalAndMove`

Current CPIR path can:

- modulate native PMFS scores by a posterior-guidance weight;
- in search phase, chase the posterior MAP inside the open move set;
- when CTPI is enabled, re-rank open-set cells by `evaluateCTPIActionInformation`.

For the CSTAR incremental experiment:

- F00 must not use MAP chase or a fitted posterior-guidance coefficient;
- instead map PICR posterior mass deterministically to the source-hypothesis weights consumed by the existing native `calculateMutualInformationGas()` calculation;
- add parity: if injected weights equal native weights, the native score vector and goal are unchanged.

This gives M1 a downstream consumer without introducing a hidden M3-like controller.

## 5. Navigation-distance field is not a path

File: `ros2_package/src/gsl_server/algorithms/PMFS/PMFSLib.cpp`
Functions: `EstimateHitProbabilities`, `PropagateProbabilities`.

`distanceFromRobot` is initialized locally and then propagated through free cells as a shortest/low-distance field. `originalPropagationDirection` is copied as propagation metadata. No predecessor chain is retained for each destination.

Therefore `(goal cell, distanceFromRobot)` is insufficient to supply the 0.2 s route sequence required by CPO/PHS. Production PHS needs one of:

1. an actual planner path API exposed from the same navigation stack; or
2. a scientifically frozen endpoint+dwell horizon that does not claim to observe along an unknown route.

Never linearly interpolate current pose to goal through obstacles and call it the planned route.

## 6. Existing V3-ORR research code

File: `ros2_package/src/gsl_server/algorithms/PMFS/internal/ObservationResolvedV3.hpp` and `experiments/cg_pc_ctt/`.

It contains useful machinery for estimating nuisance covariance and whether adjacent source hypotheses are resolvable on actual observation support. It is **not** CSTAR M1. Reuse only as:

- an offline source-resolution evaluator;
- a destructive/control comparison;
- possible diagnostic for representation adequacy.

Do not reintroduce its predictive members as a deployment bank.

## 7. New scientific insertion boundaries

### Ingress -> M1

Existing strict stamped ingress remains the owner of raw observation legality. PICR receives the complete ordered causal history/stream; no peak aggregation occurs before PICR.

### M1 -> native planner / M3

PICR produces normalized candidate source mass. One adapter maps that mass to native PMFS source weights for F00. PHS consumes the same posterior directly for F10/F11.

### history + route + source -> M2

CPO is source-conditioned and route-conditioned. It is called independently for each source/route pair and never sees the M1 posterior as an input to its conditional law.

### M1 posterior + M2 laws -> M3

PHS is a pure planner over already-computed conditional laws. It has no learnable exploration/exploitation coefficient.

## 8. Required production mode isolation

When offline gates pass, create a new `cstar_v1` mode. Legacy `cpir`, old CTPI M3, V3-ORR and protected bank paths must remain reproducible and unchanged. New code should be added under a versioned CSTAR directory instead of modifying old scientific formulas in place.
