# ME-ACI V11 — three concrete technical modules

This note supersedes the earlier wording of contribution 3 as merely
"fixed-prior cumulative recomputation".  The runtime V11 implementation is
unchanged.  The goal is to state the existing method as three explicit
operators/modules with independent failure modes, inputs/outputs, and
ablation targets.

## Module 1 — ACIT: Amplitude-Conditioned Inverse Transport

**Input:** completed UAV sensing events `(x_i, y_i, wind_i, hit_i)` and a
candidate source `s`.

**Operator:** compute a source-relative inverse-transport score under the
frozen 54-member nuisance family and condition on the observed hit count
`K`.  The conditioning removes an unknown additive release/sensor intercept
from the binary event ordering problem.

**Output:** two disjoint temporal-fold generalized evidence scores for every
source candidate.

**Failure mode addressed:** absolute forward-plume mismatch and unknown
source/sensor amplitude can make a physically plausible true source receive a
poor native PMFS score.

**Theory lineage:** inverse cause-from-effect assimilation (Nature
Communications 2026) and generalized Bayes under scientific-model
misspecification (JMLR 2026).  No theorem is claimed to transfer directly.

---

## Module 2 — STRI: Spatiotemporal Replication Identifiability

**Input:** the retained event history before source evidence is released.

**Operator:** permit release only if both disjoint temporal parity folds
contain hit/miss contrast and hits have occurred in at least two distinct
occupied sensing cells.

**Output:** `identifiable / abstain`.

**Failure mode addressed:** a single intermittent plume encounter, or a
pattern occurring in only one temporal realization, can look coherent while
remaining non-identifying for source location.

**Theory lineage:** split-sample relative-fit inference under misspecification
(Biometrika 2026) and algorithmic replicability (NeurIPS 2025) motivate the
principle that evidence should persist across separated data views rather than
be trusted from one unstable realization.  V11 does not inherit their
confidence or sample-complexity theorems.

**Existing offline ablation:** on held-out H02/seed825201, temporal contrast
was present at updates 1/2 but all hits occupied one sensing cell.  Removing
only the spatial replication rule forces an early top candidate about 4.79 m
from truth, while the nearest physical candidate is about 0.293 m from truth.

---

## Module 3 — R-GAF: Reversible Generalized Assimilation Filter

The previous description "fixed-prior cumulative generalized posterior" was
an implementation invariant, not a sufficiently explicit module.  The same
runtime V11 can be written exactly as a recursive generalized-evidence filter.

Let `g_t(s)` be the V11 cumulative generalized evidence score computed from
all retained observations through update `t`, after the ACIT and temporal-rank
operators.  Define the **generalized evidence innovation**

```
Delta g_t(s) = g_t(s) - g_{t-1}(s),        g_0(s)=0.
```

R-GAF then performs

```
q_t(s) proportional to q_{t-1}(s) * exp(Delta g_t(s)).
```

### Proposition 1 — telescoping sequential/batch equivalence

If

```
q_{t-1}(s) proportional to q_0(s) * exp(g_{t-1}(s)),
```

then

```
q_t(s)
  proportional to q_0(s) * exp(g_{t-1}(s)) * exp(g_t(s)-g_{t-1}(s))
  proportional to q_0(s) * exp(g_t(s)).
```

Thus the recursive innovation form is exactly equivalent to V11's full-history
fixed-prior reconstruction.  Old evidence is not double counted.

### Proposition 2 — defeasible source odds

For two candidates `s` and `r`,

```
log[q_t(s)/q_t(r)]
 = log[q_{t-1}(s)/q_{t-1}(r)]
   + Delta g_t(s) - Delta g_t(r).
```

Therefore later evidence can either strengthen or weaken the relative odds of
an earlier source basin.  A previously preferred candidate is not mechanically
protected by the previous posterior.

### Proposition 3 — support preservation under finite generalized scores

If `q_0(s)>0` and every cumulative generalized score is finite, then every
candidate retains positive analytical support at each finite update.  Hence
future evidence can in principle recover a previously demoted source.  This is
a structural property of the inference rule, not a guarantee of correct
ranking on every plume realization.

**Input:** previous generalized source state plus the newly enlarged retained
event history.

**Operator:** compute `Delta g_t` and perform the reversible generalized
assimilation step above.

**Output:** updated generalized/decision source distribution.

**Failure mode addressed:** V10 posterior lock-in after the first accepted
source basin.

**Theory lineage:**

- Deep Bayesian Filter, ICML 2025: a top-conference example in which the
  innovation is a structured recursive assimilation method with a designed
  inverse observation operator rather than a loose heuristic module;
- Fong & Yiu, Biometrika 2026, *Asymptotics for a class of parametric
  martingale posteriors*: recent predictive/sequential posterior theory built
  around one-step-ahead predictive recursion;
- Wu et al., JMLR 2026, generalized Bayes under misspecified scientific
  models: supports decision/generalized posterior semantics rather than
  pretending the rank score is an exact sampling likelihood.

R-GAF is not claimed to be the Deep Bayesian Filter or a martingale posterior.
The transfer is the sequential-assimilation design principle; the telescoping
generalized-evidence innovation above is the plume-localization construction.

### Offline numerical audit on frozen V11 evidence

For every available consecutive released-score pair in the three held-out
Houses, reconstructing `q_t` from `q_{t-1} exp(Delta g_t)` reproduces the
archived V11 `posterior_mass` to floating-point precision:

- H01 update 1->2: max abs error ~9.0e-16
- H01 update 2->3: max abs error ~1.5e-15
- H01 update 3->4: max abs error ~1.3e-15
- H02 update 3->4: max abs error ~1.4e-15
- H03 update 1->2: max abs error ~6.3e-16
- H03 update 2->3: max abs error ~1.2e-15
- H03 update 3->4: max abs error ~8.9e-16

In H02 update 3->4, the generalized-evidence innovation spans approximately
`[-2.175, +1.027]` across the 201 candidates, demonstrating that a new block
can both demote and promote source hypotheses.  The top candidate also changes
between the two releases.

---

# Recommended paper architecture

Do not present three unrelated tricks.  Present one ME-ACI framework with
three named technical modules:

1. **ACIT** — how source evidence is constructed under plume/amplitude
   mismatch;
2. **STRI** — when that evidence is identifiable enough to release;
3. **R-GAF** — how released evidence is assimilated sequentially without
   double counting and with future falsifiability.

This gives a coherent chain:

```
completed gas/wind events
        -> ACIT source-abduction scores
        -> STRI identifiability decision
        -> R-GAF reversible generalized assimilation
        -> PMFS source state
```

The three modules solve distinct structural failures and can be individually
ablated, while the frozen V11 runtime remains unchanged.
