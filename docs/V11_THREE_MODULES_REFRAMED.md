# ME-ACI V11 — authoritative three-module contribution contract

> **Status: AUTHORITATIVE PAPER-METHOD POSITIONING**  
> Branch: `meaci-v11-paper-three-contributions`  
> Frozen runtime method: ME-ACI V11 on `meaci-v11-reversible-cumulative`  
> Runtime code status: **UNCHANGED by this document**  
> Purpose: define exactly what the three scientific/technical contributions are, what each module computes, what evidence supports it, and what must not be claimed.

This document supersedes weaker descriptions such as **“fixed-prior cumulative recomputation”** as an innovation by itself.  The frozen V11 implementation is one integrated inference framework with three explicit modules:

```text
completed gas / wind / pose events
        |
        v
[1] ACIT  -- construct source-abduction evidence
        |
        v
[2] STRI  -- decide whether evidence is identifiable enough to release
        |
        v
[3] R-GAF -- assimilate released evidence sequentially and reversibly
        |
        v
PMFS source state / final source estimate
```

The three modules answer three different questions:

1. **How is source evidence constructed under plume-model and amplitude mismatch?**
2. **When is that evidence sufficiently reproducible to be source-identifying?**
3. **How can later evidence revise or falsify an earlier accepted source hypothesis without double counting history?**

They are not three unrelated tricks.  Together they form the ME-ACI V11 inference pipeline.

---

# Module 1 — ACIT
## Amplitude-Conditioned Inverse Transport
## 幅值条件化逆输运模块

### Scientific problem

Native PMFS is fundamentally a forward simulator-based estimator.  Under intermittent turbulent transport and simulator mismatch, a physically plausible source can receive a poor absolute forward fit.  A second problem is unknown source-release / sensor-response amplitude: absolute hit rate can vary even when source-relative transport geometry is informative.

### Input

For completed event `i`:

```text
position x_i
hit/miss y_i
wind direction / speed w_i
candidate source s
```

plus the frozen 54-member transport-discrepancy family.

### Operator

For candidate source `s` and nuisance member `m`, construct a source-relative inverse-transport propensity `psi_im(s)` in the local wind frame.  For one temporal fold, condition on the observed total hit count `K` and compute

```text
ell_m(s)
 = sum_i y_i psi_im(s)
   - log e_K(exp(psi_1m(s)), ..., exp(psi_nm(s))),
```

where `e_K` is the elementary symmetric polynomial evaluated by the stable dynamic program in the frozen code.

The 54 nuisance members are marginalized, producing one candidate-relative conditional inverse-transport score per temporal view.

### Output

Two disjoint temporal-fold source-abduction score fields:

```text
ell_even(s), ell_odd(s)
```

which are later transformed to candidate-relative normal ranks before release.

### What ACIT solves

- absolute forward-plume mismatch;
- unknown release/sensor amplitude in the binary event-ordering comparison;
- wrong-source ranking caused by treating one imperfect simulator realization as an exact observation model.

### Theory lineage (2025–2026 and foundational)

1. **Andreou, Chen & Bollt, “Assimilative causal inference,” Nature Communications 17, 1854 (2026), DOI 10.1038/s41467-026-68568-0.**  
   Transferable principle: causes can be inferred backward from observed effects in intermittent dynamical systems using an inverse/assimilation viewpoint.  
   Non-transferable claim: V11 does **not** inherit their causal-identification theorem or implementation; their method is not UAV gas-source localization and does not use conditional hit-count inverse transport.

2. **Wu et al., “Adaptive Nonparametric Perturbations of Parametric Models with Generalized Bayes,” JMLR 27 (2026).**  
   Transferable principle: when a scientific/parametric model is misspecified, task-specific generalized updating can be safer than pretending an exact sampling likelihood is correct.  
   Non-transferable claim: their consistency results do not automatically apply to V11’s dependent plume sequence or rank-normalized score.

### Correct terminology

Use:

- `conditional inverse-transport score`;
- `source abduction` / `inverse cause-from-effect inference`;
- `generalized/decision posterior` after rank aggregation.

Do **not** call the final normal-rank aggregate an exact Bayesian likelihood or Bayes factor.

---

# Module 2 — STRI
## Spatiotemporal Replication Identifiability
## 时空复现可辨识模块

### Scientific problem

A single intermittent plume encounter can be spatially coherent but still non-identifying for the source.  Likewise, a pattern that appears in only one temporal realization may be turbulent transport noise rather than stable source evidence.

### Input

The retained completed-event history before source evidence is released.

### Operator

Release is permitted only when all three truth-blind conditions hold:

```text
0 < K_even < N_even
0 < K_odd  < N_odd
number_of_distinct_hit_cells >= 2
```

The first two conditions require hit/miss contrast in two disjoint temporal parity folds.  The third requires spatial replication across at least two occupied sensing cells.

### Output

```text
IDENTIFIABLE -> pass ACIT evidence to R-GAF
ABSTAIN      -> retain events and wait for more observations
```

### Why this is an inference module, not a performance gate

STRI does not read:

- true source location;
- source-distance error;
- candidate truth rank;
- final PMFS metric;
- posterior entropy threshold;
- House-specific tuning information.

Its role is **identifiability control**, not post-hoc performance rescue.

### Theory lineage

1. **Park, Balakrishnan & Wasserman, “Robust universal inference for misspecified models,” Biometrika 113(2), 2026, DOI 10.1093/biomet/asaf070.**  
   Transferable principle: under misspecification, separated data views and relative-fit comparisons can be safer than one absolute-model score.  
   Non-transferable claim: V11’s dependent plume events and rank score are not their test statistic, so their finite-sample confidence theorem is not inherited.

2. **Replicable Distribution Testing, NeurIPS 2025.**  
   Transferable principle: conclusions should be stable/replicable across independent or separated random realizations rather than hinge on one unstable sample.  
   Non-transferable claim: V11 does not inherit their sample-complexity result; the transfer is the replicability design principle.

### Existing offline ablation

Held-out H02 / seed `825201` gives a direct counterfactual mechanism test:

- update 1: 32 retained events; each parity fold contains 2 hits / 16 events;
- update 2: 56 retained events; each parity fold contains 2 hits / 28 events;
- all observed hits still occupy only one sensing cell;
- frozen V11 therefore correctly abstains with `single_hit_site_no_spatial_replication`.

When only the spatial-replication requirement is removed offline, while preserving the same event history, 201 physical candidates, ACIT score family and nuisance members, the forced early top candidate lies about **4.79 m** from truth.  The nearest available physical candidate is about **0.293 m** from truth.

Interpretation: the multi-site spatial replication criterion blocks a temporally coherent but spatially non-identifying early commitment.

This is a mechanism ablation, not a new held-out qualification result.

---

# Module 3 — R-GAF
## Reversible Generalized Assimilation Filter
## 可逆广义同化滤波器

### Why the earlier wording was insufficient

“Retain all observations and rebuild from the fixed prior” is an implementation invariant.  By itself it is not a sufficiently explicit scientific module.

The exact same frozen V11 computation has a strict recursive representation as a **generalized-evidence innovation filter**.  This representation exposes the actual sequential operator and its mathematical properties.

### Input

- previous released generalized source state `q_{t-1}(s)`;
- cumulative generalized source score `g_{t-1}(s)`;
- enlarged retained event history after the new observation block;
- newly recomputed cumulative score `g_t(s)`.

`g_t(s)` is the actual frozen V11 released score after nuisance marginalization and even/odd candidate-normal-rank aggregation:

```text
g_t(s) = [z_even,t(s) + z_odd,t(s)] / sqrt(2).
```

### Generalized evidence innovation

Define

```text
Delta g_t(s) = g_t(s) - g_{t-1}(s),
g_0(s) = 0.
```

This is the incremental source evidence supplied by the newly enlarged history relative to the previous released state.

### Assimilation operator

R-GAF performs

```text
q_t(s) proportional to q_{t-1}(s) * exp(Delta g_t(s)).
```

This is a recursive filter over candidate-source decision weights.

### Proposition 1 — Sequential/batch equivalence by telescoping

Assume

```text
q_{t-1}(s) proportional to q_0(s) * exp(g_{t-1}(s)).
```

Then

```text
q_t(s)
 proportional to q_0(s)
              * exp(g_{t-1}(s))
              * exp(g_t(s)-g_{t-1}(s))
 proportional to q_0(s) * exp(g_t(s)).
```

Therefore the recursive innovation form is **exactly equivalent** to frozen V11’s full-history fixed-prior reconstruction.

Consequence: old evidence is not counted twice.

### Proposition 2 — Defeasible source odds

For candidates `s` and `r`,

```text
log[q_t(s)/q_t(r)]
 = log[q_{t-1}(s)/q_{t-1}(r)]
   + Delta g_t(s) - Delta g_t(r).
```

If later observations favor `r` relative to `s`, then

```text
Delta g_t(s) - Delta g_t(r) < 0,
```

and the relative weight of `s` decreases even if `s` was previously preferred.

Consequence: an accepted source basin remains **falsifiable by future evidence**.

### Proposition 3 — Support preservation under finite scores

If

```text
q_0(s) > 0
```

and all generalized scores remain finite, then

```text
q_t(s) > 0
```

at every finite update.

Consequence: a candidate that was previously demoted is not mechanically eliminated and can in principle recover when future observations support it.

This is a structural property, not a guarantee that every plume realization will be correctly ranked.

### What R-GAF solves

V10 cleared accepted evidence and could carry an accepted posterior unchanged when a later all-miss window was non-identifying by itself.  This created a posterior lock-in mechanism.

R-GAF instead makes the sequential state explicitly depend on the **evidence innovation**.  New observations may create positive or negative source-relative increments.

### Theory lineage

1. **Tarumi et al., “Deep Bayesian Filter,” ICML 2025.**  
   Transferable principle: a filtering contribution should be stated as an explicit recursive assimilation operator with defined state, observation/inverse operator and update, rather than as a loose bookkeeping rule.  
   Non-transferable claim: R-GAF is not Deep Bayesian Filter and uses no claimed theorem from it.

2. **Fong & Yiu, “Asymptotics for a class of parametric martingale posteriors,” Biometrika 113(2), 2026, DOI 10.1093/biomet/asag007.**  
   Transferable principle: modern posterior-like sequential inference can be organized around predictive/sequential recursion rather than only a conventional fixed likelihood model.  
   Non-transferable claim: R-GAF is not a martingale posterior and does not inherit its asymptotic theorem.

3. **Wu et al., JMLR 2026, generalized Bayes under scientific-model misspecification.**  
   Transferable principle: decision/generalized posterior semantics are appropriate when updating uses a task-specific score under model misspecification.

### Offline numerical verification on frozen V11 data

The repository script

```text
analysis/verify_rgaf_telescoping.py
```

reconstructs

```text
Normalize[q_{t-1}(s) * exp(g_t(s)-g_{t-1}(s))]
```

and compares it with archived V11 `posterior_mass`.

Across every available consecutive released-score pair in the three held-out Houses, the recursive reconstruction matches frozen V11 to floating-point precision:

```text
H01 update 1->2: max abs error ~9.0e-16
H01 update 2->3: max abs error ~1.5e-15
H01 update 3->4: max abs error ~1.3e-15
H02 update 3->4: max abs error ~1.4e-15
H03 update 1->2: max abs error ~6.3e-16
H03 update 2->3: max abs error ~1.2e-15
H03 update 3->4: max abs error ~8.9e-16
```

For H02 update 3->4, the generalized-evidence innovation spans approximately

```text
-2.175 <= Delta g_t(s) <= +1.027
```

across the 201 candidates.  Thus the same update simultaneously demotes some candidate causes and promotes others.

### Same-seed V10 -> V11 mechanism regression

Development seed H02 / `824201` is not held-out evidence, but it directly diagnoses the structural repair:

```text
V10 final ME-ACI error: 3.6017 m
V11 final ME-ACI error: 2.5407 m
V10 update3 -> update4 max posterior change: 0
V11 update3 -> update4 max posterior change: ~0.01739
V11 update3 -> update4 L1 posterior change: ~0.4673
```

The 24 newly acquired update-4 events are identical between archived V10 and V11 for position, hit flag, concentration and wind direction.  Therefore the changed posterior is attributable to the sequential inference rule rather than a different observation sequence.

The V11 realization is still worse than native PMFS on this already-inspected seed, so this result is **not** universal accuracy evidence.  It establishes the module-level claim that later evidence is no longer mechanically prevented from revising an accepted source basin.

---

# Current frozen empirical status

ME-ACI V11 has already passed the current preregistered three-House unseen-seed qualification:

```text
H01 / seed825101: 7.3619 m -> 5.7601 m  (+21.76%)
H02 / seed825201: 2.4220 m -> 1.4232 m  (+41.24%)
H03 / seed825301: 7.5100 m -> 6.8596 m  (+8.66%)
pooled:            17.2938 -> 14.0429 m (+18.80%)
```

All three Houses improved; there was no frozen-definition catastrophic regression and no newly introduced false-confident collapse.

This qualifies V11 as a **frozen positive main-inference candidate**.  It does not yet establish population-level statistical generalization from only three held-out pairs.

---

# Correct paper architecture

Use **one method** with three explicit modules:

```text
ME-ACI V11
  |
  +-- ACIT: Amplitude-Conditioned Inverse Transport
  |     -> how source evidence is constructed
  |
  +-- STRI: Spatiotemporal Replication Identifiability
  |     -> when evidence is identifiable enough to release
  |
  +-- R-GAF: Reversible Generalized Assimilation Filter
        -> how future evidence revises the released source state
```

The modules map to three observed failure modes:

| Failure mode | Module |
|---|---|
| forward simulator / amplitude mismatch | ACIT |
| one intermittent encounter masquerading as source evidence | STRI |
| early wrong basin becoming mechanically persistent | R-GAF |

This is the intended paper contribution structure.

---

# Claim boundary — mandatory

## Claims supported now

- a physics-informed online source-inference module integrated with PMFS;
- inverse source abduction from gas/wind effects under amplitude nuisance;
- truth-blind spatiotemporal evidence identifiability;
- reversible generalized evidence assimilation with exact telescoping sequential/batch equivalence;
- three unseen House/seed pairs all improved the official final PMFS source-location metric, with 18.80% pooled reduction.

## Claims NOT supported now

Do not claim:

- exact Bayesian likelihood / Bayes factor for the normal-rank aggregate;
- calibrated posterior probability or frequentist coverage;
- Pearl-style interventional causal-effect identification;
- universal convergence / consistency theorem for R-GAF;
- universal planner-mediated improvement across all Houses;
- guaranteed posterior variance reduction;
- guaranteed <1 m final localization;
- statistical population generalization from only three held-out pairs.

The next experiment should freeze all three modules and add independent seeds.  Do **not** tune ACIT, STRI or R-GAF after looking at those new outcomes.

---

# Reproducibility pointers

- Frozen runtime branch: `meaci-v11-reversible-cumulative`
- Paper/analysis branch: `meaci-v11-paper-three-contributions`
- R-GAF identity verifier: `analysis/verify_rgaf_telescoping.py`
- Earlier three-contribution positioning: `docs/V11_THREE_CONTRIBUTION_POSITIONING.md`
- Auxiliary 2025–2026 module screen: `docs/AUXILIARY_2025_2026_SCREEN.md`

**Important:** this paper-positioning branch must not modify the qualified V11 runtime equations or planner.  Any future conformal calibration or active-planning extension is a separate treatment and requires its own frozen study.
