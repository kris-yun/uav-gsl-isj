# Codex Execution Contract — TPT Reactive-Path Premise V1

Date: 2026-09-14
Starting evidence SHA: `1be4363959fcf7909e935568bb74d0a0dbd4328b`
Suggested execution branch: `codex/tpt-reactive-path-premise-20260914`

## Objective

Test exactly one big-science hypothesis before any PMFS integration:

> Conditioned on successful finite-time source-to-sensing transport, does the **transition-path / reactive-current geometry** preserve source identity across transport regimes beyond what is available from scalar hit probability, first-entry statistics, or unconditional plume occupancy?

This is an offline physics premise only.

Do not implement a planner, posterior, network, or closed loop.

## Authoritative theory / collision files

Read first:

1. `docs/TPT_COLLISION_SCREEN_V3_20260914.md`
2. `docs/TPT_THEORY_FREEZE_V1_20260914.md`
3. `docs/TPT_DATA_SEMANTICS_AUDIT_V1_20260914.md`
4. `docs/TPT_REACTIVE_PATH_GATE_V1_20260914.json`

Broad novelty claims for scalar committor / hitting probability or generic TPT source inversion are explicitly forbidden.

---

# Phase 0 — Exact stochastic-semantics audit

Audit the **actual VM GADEN build used by the project**, not only upstream public GADEN.

Record:

- GADEN source-tree / git identity;
- simulator and player SHA256;
- build/compiler flags;
- OpenMP/threading settings;
- RNG engine and initialization path;
- whether explicit RNG seed already exists;
- whether seed reproducibility depends on thread count;
- raw-frame serialization schema;
- whether stable filament IDs exist across frames;
- whether per-filament center/radius/moles are saved;
- whether an individual filament's contribution to a concentration query can be reconstructed exactly.

Outputs:

```text
experiments/tpt_reactive_path_v1/GADEN_STOCHASTIC_SEMANTICS_AUDIT.json
docs/TPT_GADEN_SEMANTICS_AUDIT_20260914.md
```

Set:

```text
TPT_TRAJECTORY_ENSEMBLE_ESTIMABLE = YES/NO
```

If NO, commit/push `D. TPT_TRAJECTORY_ENSEMBLE_NOT_IDENTIFIABLE` and STOP.

Do not infer a probability from the existing one-realization R3B cache.

---

# Phase 1 — Research-only RNG / filament instrumentation, only if required

If the exact frozen simulator already supports reproducible independent seeds and stable filament histories, do not modify it.

If it does not, an isolated research build may add only:

- explicit RNG seed;
- stable emitted-filament ID;
- read-only per-filament trajectory/contribution logging;
- deterministic single-thread execution if necessary for seed reproducibility.

It must not change transport physics, release physics, wind, noise distribution, collision handling, source parameters, map, FOPDT, or PMFS.

Use a distinct build tag and record binary SHA256.

Qualification requirements:

1. same seed repeated twice -> bitwise-identical saved filament trajectory log;
2. different seed -> different stochastic trajectory;
3. deterministic drift/collision/release contract matches frozen code;
4. stochastic displacement distribution matches the frozen Gaussian law (report N, mean, std, expected std, relative error);
5. no localization metric is used for qualification.

If qualification fails: commit/push and STOP.

---

# Phase 2 — Precommit ensemble and resource contract

Use exactly these 48 seed IDs for every source/wind:

```text
41001..41048
```

The same seed list is used across sources/winds as a controlled exogenous replicate list. Within each source×wind, the 48 seeds are the stochastic replicates used for probability intervals.

Design winds only:

```text
W_fast
W_slow
```

Sources:

```text
S_truth
S_k01
S_k10
S_k22
```

Frozen sensing design:

```text
route = AO_00 / historical geometry route
horizon = 150 s
cadence = 0.2 s
hit floor = 0.1 ppm
House = House02
```

Before running source results, commit and push:

```text
experiments/tpt_reactive_path_v1/ENSEMBLE_PRECOMMIT.json
experiments/tpt_reactive_path_v1/SEED_LIST.txt
experiments/tpt_reactive_path_v1/ANALYSIS_POLICY_FREEZE.json
```

Benchmark exactly 2 seeds of one source-wind only to report wall time / disk / projected total cost. If the frozen 384-run design ensemble is infeasible, STOP and return to GPT. Do not lower N post hoc.

Do not generate/read `W_altfast` yet.

---

# Phase 3 — Generate design ensemble and path logs

Generate:

```text
4 sources × 2 winds × 48 seeds = 384 independent seeded simulator realizations
```

For every realization save enough information to reproduce:

- emitted filament ID;
- emission time;
- filament center through time;
- radius / amount needed for contribution calculation;
- route query time/position;
- raw total concentration at the route;
- per-filament concentration contribution at every hit query;
- first route hit time / route index;
- exact simulator / wind / source / seed identity.

The seed-level trajectory log is the stochastic unit. Do not treat time samples or filaments as independent simulator replicates.

Store compressed Git-trackable derived trajectory/path records; if full raw simulator output is too large, retain it externally with committed SHA256, path, generation command and environment identity. All decision-critical extracted path records must be in Git.

---

# Phase 4 — Mission-level scalar reachability diagnostic

For each source×design-wind:

```text
q_detect = (# seeds with >=1 raw 0.1 ppm route hit by 150 s) / 48
```

Report:

- successes / 48;
- q_detect;
- 95% Wilson interval;
- first-hit time distribution.

Historical failure-linked groups on AO_00:

```text
EXPOSED = {S_truth, S_k10}
ZERO_EXPOSURE = {S_k01, S_k22}
```

Strict per-wind gate:

```text
max upper95(q_ZERO_EXPOSURE) < min lower95(q_EXPOSED)
```

If either design wind fails this separation:

```text
C. TPT_DOES_NOT_EXPLAIN_SUPPORT_FAILURE
```

commit/push and STOP.

Important: even if this gate passes, `q_detect` is not the innovation. It is a collision baseline / failure-mechanism diagnostic.

---

# Phase 5 — Build transition-path representations

For every **successful seed realization**, identify all filaments contributing to the first route hit.

Weight each contributing filament path by:

```text
instantaneous filament concentration contribution / total concentration at first hit
```

No top-K, percentile cutoff or learned weight.

Reconstruct each contributing filament path back to emission.

## Global anti-triviality mask

Construct once from geometry only:

- robot-accessible connected free-space sensing layer at the frozen sensing altitude;
- remove every cell within `2 × gas-grid spacing` of **any of the four candidate source coordinates**.

This is one global mask, not a different source-specific visible region.

Commit mask hash before computing source identity.

Representations:

### Q_ONLY

Scalar `q_detect`. Collision baseline only.

### ENTRY_ONLY

Nonnegative normalized histogram of first-hit route position/time using fixed bins declared in `ANALYSIS_POLICY_FREEZE.json` before evaluation.

### UNCONDITIONED_VISIT

Nonnegative normalized accessible-cell occupancy of **all** filament trajectories in the seeded simulations, without conditioning on successful source-to-route hit.

### REACTIVE_CURRENT

On the global masked accessible grid, accumulate contribution-weighted **directed adjacent-cell transitions** from successful contributing filament histories.

Flatten `(cell, outgoing_direction)` directed-edge counts and L1-normalize.

Call this an **empirical finite-time reactive-current fingerprint**. Do not claim exact continuum TPT current unless a validated Markov/TPT estimator is separately implemented.

---

# Phase 6 — Cross-wind source-identity premise

Metric is frozen cosine distance:

```text
d(x,y) = 1 - cosine(x,y)
```

No learning, whitening, fitted metric or coordinate weighting.

For each source representation in `W_fast`, rank the four source representations in `W_slow`; then reverse `W_slow -> W_fast`.

Eight source-identity cases total.

For each case report:

- true-source rank;
- same-source distance;
- best-false source/distance;
- margin = best_false_distance - same_source_distance.

Primary gate for `REACTIVE_CURRENT`:

```text
8/8 rank-1
all 8 margins > 0
minimum margin strictly > ENTRY_ONLY minimum margin
minimum margin strictly > UNCONDITIONED_VISIT minimum margin
```

If `ENTRY_ONLY` or `UNCONDITIONED_VISIT` equals/exceeds the current result:

```text
B. SCALAR_OR_MARGINAL_TRANSPORT_EXPLAINS_RESULT_NO_PATH_GAIN
```

STOP.

If current fails 8/8:

```text
E. TPT_PATH_FINGERPRINT_NO_CROSS_TRANSPORT_IDENTITY
```

STOP.

---

# Phase 7 — Destructive mechanism controls

Only if Phase 6 passes.

Run without refitting:

1. `EDGE_DIRECTION_ROTATE_90`: at every accessible cell, cyclically rotate the outgoing direction labels by +90 degrees while preserving total cell occupancy / edge mass;
2. `UNCONDITIONED_VISIT`: already defined;
3. `ENTRY_ONLY`: already defined;
4. `UNMASKED_CURRENT`: diagnostic only and cannot count toward PASS.

The correctly directed, conditioned, masked current must have a strictly larger minimum cross-wind identity margin than `EDGE_DIRECTION_ROTATE_90` and the marginal baselines.

If direction destruction does not degrade rank count or minimum margin:

```text
TPT_PATH_DIRECTION_NOT_LOAD_BEARING = FAIL
```

STOP.

---

# Phase 8 — Freeze before held transport

Only after Phases 4–7 pass, commit/push:

```text
TPT_REPRESENTATION_FREEZE.json
GLOBAL_MASK_SHA256
DESIGN_WIND_RESULTS.json
PRE_HELD_WIND_SHA256SUMS
```

Freeze per-source prototype as the arithmetic mean of the L1-normalized `W_fast` and `W_slow` reactive-current fingerprints followed by L1 renormalization.

Only now authorize generation of:

```text
W_altfast × 4 sources × seeds 41001..41048
```

No re-selection of bins, mask, metric or current definition.

---

# Phase 9 — Internal held-wind gate

For each `W_altfast` source fingerprint rank the four frozen prototypes.

Required:

```text
4/4 rank-1
all margins > 0
minimum REACTIVE_CURRENT margin > ENTRY_ONLY minimum margin
minimum REACTIVE_CURRENT margin > UNCONDITIONED_VISIT minimum margin
```

Label result only:

```text
INTERNAL_DEVELOPMENT_HOLDOUT
```

It is not cross-House or independent paper confirmation.

---

# Final decisions

Return exactly one main scientific verdict:

```text
A. TPT_REACTIVE_PATH_PREMISE_PASS
B. SCALAR_OR_MARGINAL_TRANSPORT_EXPLAINS_RESULT_NO_PATH_GAIN
C. TPT_DOES_NOT_EXPLAIN_SUPPORT_FAILURE
D. TPT_TRAJECTORY_ENSEMBLE_NOT_IDENTIFIABLE
E. TPT_PATH_FINGERPRINT_NO_CROSS_TRANSPORT_IDENTITY
F. RNG_INSTRUMENTATION_NOT_QUALIFIED
G. PRECOMMITTED_ENSEMBLE_RESOURCE_INFEASIBLE
```

`A` still does **not** authorize PMFS integration or novelty claim. Return to GPT first.

---

# Hard prohibitions

Do not:

- modify PMFS;
- implement an online planner;
- train a neural committor/current model;
- use source truth as an online feature;
- tune hit floor, horizon, seed count or route after seeing results;
- generate `W_altfast` before design freeze;
- use House-specific fitted weights;
- call scalar hit probability a novel committor module;
- call this causal localization;
- claim stochastic independence from individual filaments;
- claim cross-dataset generalization.

---

# Required GitHub deliverables

```text
experiments/tpt_reactive_path_v1/
  GADEN_STOCHASTIC_SEMANTICS_AUDIT.json
  RNG_INSTRUMENTATION_QUALIFICATION.json        # if needed
  ENSEMBLE_PRECOMMIT.json
  SEED_LIST.txt
  ANALYSIS_POLICY_FREEZE.json
  RESOURCE_BENCHMARK.json
  DESIGN_ENSEMBLE_MANIFEST.json
  Q_DETECT_WILSON.json
  GLOBAL_ACCESSIBLE_MASK.json
  FIRST_ENTRY_FINGERPRINTS.npz
  UNCONDITIONED_VISIT_FINGERPRINTS.npz
  REACTIVE_CURRENT_FINGERPRINTS.npz
  DESIGN_CROSS_WIND_IDENTITY.json
  DESTRUCTIVE_CONTROLS.json
  TPT_REPRESENTATION_FREEZE.json                # only if design pass
  HELD_WIND_IDENTITY.json                       # only if authorized
  FINAL_GATE.json
  SHA256SUMS

tools/
  audit_gaden_stochastic_semantics.py
  qualify_seeded_gaden.py                       # if needed
  extract_tpt_path_ensemble.py
  build_reactive_current_fingerprint.py
  evaluate_tpt_reactive_path_premise.py

docs/
  TPT_GADEN_SEMANTICS_AUDIT_20260914.md
  TPT_REACTIVE_PATH_PREMISE_RESULT_20260914.md
```

Every freeze must be committed/pushed **before** the evidence it governs is opened.

## Final reply to user

Reply only with:

```text
branch:
starting SHA:
final SHA:
TRAJECTORY_ENSEMBLE_ESTIMABLE:
RNG_QUALIFICATION:
DESIGN_ENSEMBLE_STATUS:
FAILURE_LINK_GATE:
REACTIVE_CURRENT_8WAY_IDENTITY:
MARGINAL_BASELINE_COMPARATOR:
DIRECTION_CONTROL:
HELD_WIND_STATUS:
FINAL_VERDICT:
```

Then stop and return to GPT.
