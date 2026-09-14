# TPT Data / Stochastic-Semantics Audit V1

Date: 2026-09-14
Status: PRE-EXECUTION REQUIREMENT

## Existing R3B cache is not a committor estimator

The existing `tools/audit_dual_uav_raw_cache.py` records:

```text
4 sources × 3 winds = 12 source-wind caches
physical_realizations = 1
stochastic_robustness_claim = false
```

Therefore the frozen R3B concentration cache can support single-realization support / first-hit diagnostics, but it cannot by itself estimate a probability such as

`q = P(source material reaches sensing domain before T)`.

Any implementation that divides filament counts from one saved realization and labels the result a committor probability is forbidden unless independence and sampling semantics are explicitly established.

## GADEN stochasticity is physically real but seed semantics must be audited

Current public GADEN core uses stochastic filament motion: Gaussian random displacements are generated through internal `std::mt19937`-based random utilities / precomputed Gaussian draws. The public code inspected does not expose a user-facing RNG seed in that utility.

The user's frozen VM build may differ. Codex must inspect the exact build actually used for the R3B/Main-V8 evidence.

Required audit:

- exact GADEN repository/source identity or source-tree hash;
- simulator/player binary SHA256;
- compiler/build flags;
- OpenMP / thread count and whether random streams depend on thread scheduling;
- RNG engine and initialization;
- whether a deterministic seed can already be supplied;
- raw-frame serialization fields;
- whether individual filaments have stable IDs across frames;
- whether per-filament center/radius/moles are stored and recoverable;
- whether concentration contribution of individual filaments at a sensing query can be reconstructed exactly.

Output must declare one of:

```text
A. SEEDED_INDEPENDENT_RUNS_ALREADY_SUPPORTED
B. STABLE_FILAMENT_PATHS_RECOVERABLE_BUT_SEED_LEVEL_PROBABILITY_NOT_AVAILABLE
C. RESEARCH_ONLY_SEED_INSTRUMENTATION_REQUIRED
D. TPT_TRAJECTORY_ENSEMBLE_NOT_IDENTIFIABLE
```

## Research-only seed instrumentation — allowed only under strict conditions

If exact frozen GADEN has stochastic filament dynamics but no explicit seed interface, a research-only instrumented build is allowed **only** to expose reproducible stochastic realizations.

It may:

- add an explicit RNG seed;
- add a stable emitted-filament ID if absent;
- force deterministic single-thread execution if needed to bind a seed to a repeatable realization;
- add read-only trajectory/contribution logging.

It may not change:

- wind;
- filament equations;
- stochastic distribution;
- noise standard deviation;
- release rate;
- filament growth;
- collision handling;
- source parameters;
- grid / occupancy;
- sensor law;
- PMFS.

A separate build tag and binary SHA must be recorded. The original binary remains frozen.

## Instrumentation qualification

Before scientific ensemble generation, demonstrate:

1. same explicit seed + same build gives bitwise-identical saved filament trajectories on two independent runs;
2. changing the seed changes stochastic trajectories;
3. deterministic drift / collision / source-release contracts match the frozen simulator;
4. empirical stochastic increments over a large sample have mean and standard deviation consistent with the unmodified Gaussian displacement law;
5. no PMFS or localization result is used in qualifying the RNG interface.

If these fail, STOP.

## Ensemble size frozen in advance

For the first premise experiment use:

`N = 48 independent simulator seeds per source × wind`.

Rationale: if the true mission-level hit probability were `q=0.10`, the probability of seeing zero hits in 48 independent realizations is

`(1-0.10)^48 ≈ 0.00636`.

Thus 48 gives useful resolution for distinguishing a practically zero support case from a support probability on the order of 0.1 without choosing N after seeing results.

Design phase only:

`4 sources × 2 design winds × 48 seeds = 384 runs`.

`W_altfast` must not be generated/read for this premise until the design gate passes and all analysis hashes are pushed.

Before launching all 384 runs, benchmark exactly one source-wind with 2 seeds and report wall time, disk volume and projected total resources. If the precommitted ensemble is infeasible, STOP and return to GPT; do not silently lower N after seeing costs or partial results.

## Frozen sensing design for the premise

Use the already frozen `AO_00` / historical geometry route at:

- 150 s horizon;
- 0.2 s cadence;
- existing House02 map / source coordinates / design winds;
- existing raw hit floor `0.1 ppm` where a concentration hit is needed.

Reason: this is the route on which the observed source-support imbalance was established. The first TPT experiment is a **mechanism test**, not route optimization.

## Path extraction semantics

For each successful seed-level realization (at least one raw concentration hit along AO_00 by 150 s):

- identify the first hit time and sensing position;
- identify all filaments contributing to that query if exact per-filament contribution is available;
- contribution-weight each contributing filament by its instantaneous concentration contribution divided by total concentration contribution;
- reconstruct the contributing filament history backward to emission using stable IDs.

Do not introduce an arbitrary `top-k` or `90% contribution` cutoff in V1.

If exact contributing filaments cannot be identified from simulator state/logging, `REACTIVE_CURRENT` is not estimable and the experiment must return `TPT_TRAJECTORY_ENSEMBLE_NOT_IDENTIFIABLE` rather than approximating paths from concentration images.

## Statistical reporting

For scalar mission-level hit probability report:

- successes / 48;
- point estimate;
- 95% Wilson interval.

For path fingerprints report bootstrap uncertainty over **seed-level realizations**, not over individual time samples or filaments as if independent.

The seed is the primary stochastic replicate.
