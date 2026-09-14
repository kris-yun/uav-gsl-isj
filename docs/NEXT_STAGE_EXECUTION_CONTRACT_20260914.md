# Next-Stage Execution Contract

Date: 2026-09-14

Purpose: one falsification round to decide whether **observability-first / persistent-excitation measurement design** deserves to become the paper's main innovation candidate.

This contract does not authorize posterior redesign, neural networks, new GADEN generation, or a new causal score.

---

# Phase A — explain the 5 s time-mismatch result before using it scientifically

The previous dual-UAV test found:

```text
correct same-frame signed increment = 2/4 source rank-1
5 s time mismatch                  = 3/4 source rank-1
```

Do not tune a lag around this result.

## A1. Geometry-only revisit audit

Use only frozen `FORMATION_PLUS_ROUTE.csv` and `FORMATION_MINUS_ROUTE.csv`.

For lags from -10 s to +10 s on the existing 0.2 s grid, compute:

\[
d_{geo}(\tau)
=median_t\|x_+(t)-x_-(t+\tau)\|.
\]

Also report 10th/90th percentiles.

Required fields:

```text
GEOMETRIC_OVERLAP_BEST_LAG_S
D_GEO_AT_0S
D_GEO_AT_5S
D_GEO_AT_BEST_LAG
```

No gas values or source labels may be used.

## A2. Motion-revisit timescale

Report the route-speed distribution and the baseline projected onto motion.

Reference calculation to audit, not fit:

```text
2.0 m / 0.35 m/s ≈ 5.71 s
```

## A3. Wind-advection timescale

Using the frozen baseline and deployable recorded local wind, report per wind:

- median/IQR/10th/90th percentile of `|b| / |u|`;
- signed projected advection time where well-defined;
- fraction of samples where projection is physically valid.

Classify the old 5 s improvement only as:

```text
MOTION_REVISIT_CONFOUND_SUPPORTED
ADVECTIVE_TIMESCALE_COMPATIBLE
UNRESOLVED
```

No lag-based localization algorithm is authorized.

Commit and push Phase A before Phase B.

---

# Phase B — source-observability-first route design

## B0. Hypothesis

The dominant failure is insufficient physical excitation of source-discriminating modes.

The experiment asks:

> Can measurement geometry alone, with unchanged sensor physics and unchanged source evaluator, restore a well-conditioned source-response operator and held-transport source identity?

## B1. Frozen information split

Design/selection winds:

```text
W_fast
W_slow
```

Held transport regime:

```text
W_altfast
```

`W_altfast` source scores are forbidden until exactly one route is frozen and committed.

This is an internal development holdout only because `W_altfast` has appeared historically elsewhere in the project.

## B2. Frozen physical contract

Keep unchanged:

- House02 occupancy/map;
- existing Main-V8 raw caches;
- four controlled source coordinates;
- flight altitude;
- exact FOPDT;
- 150 s duration;
- 0.2 s cadence;
- route kinematic limits;
- dual-UAV 2 m safety separation if dual formation is evaluated.

No new GADEN.

## B3. Candidate-route generation

Generate a bounded deterministic route set using only:

- map/free space;
- kinematic constraints;
- duration;
- optional source-blind deployable wind if its use is declared before source response scoring.

No gas, source response, source truth, candidate rank, posterior or held-wind score may enter route generation.

Before any source-response score is calculated, commit/push:

```text
ROUTE_GENERATOR_CONTRACT.json
ROUTE_CANDIDATE_MANIFEST.json
ROUTE_CANDIDATE_SHA256SUMS
```

The candidate budget and generator seed are frozen at this point.

## B4. Source-response operator

For every candidate route `R` and design wind `w`, query the existing four source caches with the same sensor law and build processed source responses:

\[
Y_w(R)=
\begin{bmatrix}
y_{s_1,w}^T\\
y_{s_2,w}^T\\
y_{s_3,w}^T\\
y_{s_4,w}^T\end{bmatrix}.
\]

Center across sources:

\[
C_w(R)=P_4Y_w(R).
\]

Compute:

```text
rank
sigma1 sigma2 sigma3
sigma3/sigma1
Q_energy
minimum pairwise source distance
per-source exposure count
per-source temporal-third coverage
exact collisions
```

## B5. Frozen route-selection rule

Rank candidates lexicographically:

1. number of design winds with rank 3;
2. worst-design-wind `sigma3/sigma1`;
3. worst-design-wind `Q_energy`;
4. minimum source exposure / temporal coverage;
5. route cost as final tie-breaker;
6. deterministic route ID as last tie-breaker.

Historical premise gates are reused without relaxation:

```text
rank = 3 in every design wind
sigma3/sigma1 >= 0.05 in every design wind
Q_energy >= 0.01
no exact source-pair collision
every source has useful exposure in >= 2 temporal thirds
```

If none passes:

```text
OBSERVABILITY_FIRST_ROUTE_PREMISE = NO_GO
```

Stop. Do not enlarge the search budget or relax thresholds after seeing results.

## B6. Freeze before held wind

If candidates pass, select exactly one using the frozen rule.

Commit/push before `W_altfast` is opened:

```text
OBSERVABILITY_ROUTE_FREEZE.json
FROZEN_ROUTE.csv
PRE_HELD_WIND_SHA256SUMS
```

## B7. Held-wind identity

Use the same simple source-identity evaluator already used in the dual-UAV premise. Do not invent a new likelihood or classifier.

Primary gate:

```text
W_altfast: 4/4 sources rank-1
```

If the design-wind observability gates pass but held-wind identity fails:

```text
DESIGN_OBSERVABILITY_DOES_NOT_TRANSPORT = NO_GO
```

## B8. Same-inference baseline comparison

Use exactly the same source evaluator on:

1. old frozen geometry route;
2. new observability-designed route.

At minimum compare:

```text
per-wind sigma3/sigma1
Q_energy
source exposure counts
held-wind rank1 count
minimum held-wind margin
```

A useful mechanism requires the improvement to come from the measurement design, not from a changed estimator.

---

# Phase C — novelty collision only if Phase B passes

Do not perform this as a naming exercise.

Compare against at least:

1. classic infotaxis / entropy-driven GSL exploration;
2. PMFS / model-based adaptive exploration;
3. generic optimal sensor placement / OED;
4. ICML 2026 `Online Bayesian Experimental Design for Partially Observed Dynamical Systems`;
5. NeurIPS 2025 `PhySense`;
6. multi-robot informative-region allocation / distributed GSL;
7. system-identification persistent-excitation and multi-signal informativity literature.

Candidate novelty boundary to test:

> **worst-transport source-parameter observability / persistent excitation that explicitly prevents source-response rank collapse before Bayesian assimilation.**

The following are not novel enough:

```text
maximize expected information gain
choose informative sensing locations
reduce posterior entropy
use two UAVs
fuse two robot beliefs
```

If prior GSL or active-sensing work already contains an equivalent weakest-source-mode / robust rank-conditioning objective, mark:

```text
NOVELTY_COLLISION = YES
```

and return to theory selection rather than relabeling.

---

# Phase D — secondary module trigger, not implementation

Only if the single-route study establishes the observability principle but shows that no single deployment-feasible trajectory can meet all source-mode gates, open the following candidate:

```text
COLLECTIVE_MULTI_TRAJECTORY_INFORMATIVITY = CANDIDATE
```

The next mathematical object would be

\[
C_w^{joint}=[C_w(R_1)\;C_w(R_2)]
\]

with the same worst-transport weakest-mode objective.

Do not implement it in this task.

---

# Prohibited in this round

- neural network;
- posterior tuning;
- new source likelihood;
- new GADEN generation;
- closed-loop PMFS integration;
- multiseed expansion;
- threshold relaxation;
- House-specific tuning;
- use of factual source online;
- causal-localization claim;
- cross-dataset/generalization claim.

---

# Required GitHub outputs

```text
experiments/active_observability_v1/
  TIME_MISMATCH_FORENSIC.json
  ROUTE_GENERATOR_CONTRACT.json
  ROUTE_CANDIDATE_MANIFEST.json
  DESIGN_WIND_OBSERVABILITY.csv.gz
  OBSERVABILITY_ROUTE_FREEZE.json          # only if design gate passes
  FROZEN_ROUTE.csv                         # only if design gate passes
  HELD_WIND_SOURCE_IDENTITY.json           # only after route freeze
  BASELINE_COMPARATOR.json
  FINAL_GATE.json
  SHA256SUMS

docs/
  ACTIVE_OBSERVABILITY_RESULT_20260914.md
  ACTIVE_OBSERVABILITY_NOVELTY_COLLISION_20260914.md   # only if premise passes
```

Final reply to user must contain only:

```text
branch:
starting SHA:
final SHA:
TIME_MISMATCH_FORENSIC:
DESIGN_WIND_OBSERVABILITY:
FROZEN_ROUTE_STATUS:
HELD_WIND_SOURCE_IDENTITY:
BASELINE_COMPARATOR:
NOVELTY_COLLISION_STATUS:
FINAL_VERDICT:
```

Then stop and return to GPT for review.
