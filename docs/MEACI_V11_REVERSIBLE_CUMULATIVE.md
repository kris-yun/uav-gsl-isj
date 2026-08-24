# ME-ACI V11 — Reversible Cumulative Conditional Inference

## Status

This branch is an **experimental successor** to frozen ME-ACI V10.  It does not
rewrite or invalidate the V10 evidence on `main`.

V10 held-out full-300 s confirmation exposed one structural failure:

- H01: 4.284 m -> 2.072 m (+51.62%)
- H02: 2.265 m -> 3.602 m (-59.04%, catastrophic regression)
- H03: 5.557 m -> 1.983 m (+64.31%)

The H02 diagnostic is especially informative because OFF and ON trajectories
were identical.  The error therefore cannot be blamed on planner divergence.
At update 3 V10 injected a posterior that improved the truth-candidate rank
(152 -> 76) but moved even more mass into a wrong western basin.  The following
update contained later evidence but the injected posterior was carried forward
unchanged.

## Root cause

V10 solves the **first-identifiable-release** problem but not the full
sequential correction problem.

Its contract was:

1. retain incomplete events in a reservoir;
2. wait until both temporal folds contain hit/miss contrast and hits occupy at
   least two spatial cells;
3. compute the exact conditional inverse-transport likelihood;
4. inject the resulting posterior;
5. clear the evidence reservoir.

After step 5, a later all-miss window is non-identifying by itself, so V10
abstains and simply restores the previous accepted posterior.  Such later
negative evidence can never refute the accepted basin.

This makes V10 effectively **confirm-only** after its first release.

## V11 hypothesis

Keep the validated V10 likelihood and identifiability principle, but make the
Bayesian state reversible.

Let the cumulative completed-event history at source update t be

`R_1:t = R_1:t-1 union new_events_t`.

Once `R_1:t` has become identifiable, retain it after every accepted update.
For every later source update recompute the exact conditional likelihood on the
**entire cumulative history**:

```
log L_t(s)
  = log p(Y_1:t | K_1:t, do(S=s))
```

with the same frozen 54-member inverse-transport nuisance family and the same
conditional-on-hit-count dynamic program.

The posterior is always recomputed from the fixed geometry-only prior:

```
q_t(s) proportional to q_0(s) exp(log L_t(s)).
```

It is **not** computed as

```
q_t(s) proportional to q_t-1(s) exp(log L_t(s)),
```

because `log L_t` already contains all earlier events.  Multiplying by
`q_t-1` would double-count the retained history and recreate posterior lock-in.

## Why later all-miss evidence now matters without introducing amplitude

For one nuisance member, V10 conditions on the observed hit count K:

```
log L(s) = sum_i y_i psi_i(s) - log e_K(exp(psi_1), ..., exp(psi_n)).
```

Appending a later miss does not change the observed-hit term, but it enlarges
the elementary-symmetric-polynomial denominator.  A candidate that assigns a
large propensity to a newly observed miss therefore loses relative evidence.

This is exactly the missing falsification mechanism in H02.  No release-rate,
sensor-gain, temperature, or House-specific threshold is introduced.

## What is frozen from V10

V11 does **not** change:

- the inverse-transport propensity family;
- 54 nuisance members;
- conditioning on total hit count;
- even/odd temporal replication;
- minimum two distinct hit cells for the initial identifying anchor;
- PMFS planner;
- source-update cadence;
- PMFS top-5% expected-location evaluation metric;
- truth-blind online execution.

Only sequential bookkeeping changes:

1. accepted evidence history is retained;
2. the full cumulative conditional likelihood is recomputed;
3. the posterior is rebuilt from the fixed geometry prior every time.

## Scientific interpretation

V10:

> evidence-release gate + one-shot posterior replacement

V11:

> sequentially falsifiable conditional causal inference

The main principle becomes:

> **A source hypothesis is accepted only after spatiotemporal replication, but
> it remains defeasible: every later observation can change its relative
> conditional evidence.**

## Experiment sequence

### Phase 0 — source patch / build audit

```bash
git checkout meaci-v11-reversible-cumulative
python3 tools/apply_meaci_v11_reversible_patch.py
git diff -- ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp
python3 reference/verify_meaci_v11_source.py
```

Build an isolated V11 binary.  Record source and binary SHA-256.

### Phase 1 — H02 held-out counterexample becomes development-only

Re-run seed `824201` only as a **mechanism regression test** because its outcome
has already been inspected and used to design V11.

Required structural checks:

- update 3 may establish the identifying anchor;
- update 4 must no longer copy update-3 posterior byte-for-byte;
- cumulative event count at update 4 must exceed update 3;
- later misses must alter candidate log evidence;
- no truth or distance enters the online decision.

Do not tune anything if H02 remains wrong.  Report V11 current realization
NO-GO instead.

### Phase 2 — freeze

If Phase 1 shows the expected reversible mechanism, freeze:

- source SHA;
- binary SHA;
- run contract;
- cadence;
- 54-member nuisance family;
- 300 s budget;
- evaluator.

### Phase 3 — new truth-blind qualification

Use new seeds not used in V10/V11 design.  At minimum one new seed per House:

- H01 OFF vs V11 ON, full 300 s;
- H02 OFF vs V11 ON, full 300 s;
- H03 OFF vs V11 ON, full 300 s.

No early stopping at the first accepted update.

Primary metric remains PMFS `ExpectedValue(sourceProbability, 0.05)` final
localization error.

Qualification target:

- at least 2/3 Houses improve;
- pooled improvement >= 10%;
- no catastrophic regression (>= 1 m absolute regression and <= -25% relative);
- no post-injection posterior persistence when new evidence arrives unless the
  recomputed conditional posterior is numerically identical by coincidence.

## Prohibited rescue operations

Do not tune after seeing Phase-1 or Phase-3 truth:

- gate thresholds;
- temperature;
- alpha/fusion weights;
- nuisance-member ranges;
- planner parameters;
- House-specific rules;
- source-specific fallback;
- truth-rank acceptance gates.

A failure is evidence about the realization, not a prompt to tune the seed.
