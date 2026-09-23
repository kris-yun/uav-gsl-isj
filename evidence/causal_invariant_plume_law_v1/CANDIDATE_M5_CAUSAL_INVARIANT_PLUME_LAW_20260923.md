# Candidate M5 — Causal Invariant Plume-Law Discovery for PMFS

Date: 2026-09-23  
Branch: \`research/causal-invariant-plume-law-v1\`  
Status: **BIG-IDEA CANDIDATE — competes with M4; no neural training before invariant-law audit**

## 1. Paper-level thesis

The main scientific idea is not:
- symbolic regression;
- turbulence closure;
- a neural operator;
- an end-to-end source localizer.

It is:

> **Indoor plume dynamics contain an intrinsic transport law shared across environments, while House/wind/source-specific effects are environment-dependent mechanisms. Multi-environment causal invariant-function learning can disentangle the shared law from those environment-specific dynamics and turn it into a transferable PMFS forward mechanism.**

Working name:

**Causal Invariant Plume Law (CIPL)**

Alternative:

**Invariant-Law PMFS**

The scientific question is:

> What part of plume dynamics remains the same when House geometry, wind realization and source position change?

---

## 2. Remote-field mother idea

### ICML 2025 — Disentanglement of Invariant Functions (DIF)

Gui, Li & Ji,  
*Discovering Physics Laws of Dynamical Systems via Invariant Function Learning*, ICML 2025.

Their problem is stronger than ordinary domain generalization.

They observe dynamical systems in multiple environments where environment-specific mechanisms may change not only coefficients but even **functional form**.

Example from the paper:
- ideal pendulum intrinsic law;
- damped environment adds one mechanism;
- powered environment adds another mechanism.

They formulate a causal graph and disentangle:

\[
\text{invariant intrinsic function}
+
\text{environment-specific dynamics}.
\]

An information-based independence principle separates the learned invariant function from environment identity.

They then use symbolic regression to expose the recovered invariant physics law.

### Transferable principle

Do not assume every observed term is part of the intrinsic system.

Use environmental heterogeneity to discover which law persists.

---

## 3. Gas/plume translation

Define an environment index

\[
E
=
(\text{House}, \text{wind configuration}, \text{plume seed/source context})
\]

only for training/audit.

Let the physical concentration/density state be \(c(x,t)\).

Known coarse physics:

\[
\partial_t c
=
-\nabla\cdot(wc)
+
q_s
+
\text{unknown transport}.
\]

Move the unquestionably known terms to the left:

\[
\boxed{
r_E(x,t)
=
\partial_t c
+
\nabla\cdot(wc)
-
q_s
}
\]

The unresolved term may include:
- effective diffusion/dispersion;
- wall interaction;
- turbulent/intermittent transport;
- numerical/coarse-grid effects.

The M5 hypothesis is that this unresolved dynamics can be decomposed as

\[
\boxed{
r_E
=
f_{\rm inv}(z)
+
g_E(z)
+
\epsilon
}
\]

where:
- \(f_{\rm inv}\): intrinsic plume law shared across environments;
- \(g_E\): environment-specific mechanism;
- \(z\): local physical state/geometry variables;
- \(\epsilon\): stochastic/noise remainder.

---

## 4. Physical variables, not House labels

Candidate local state:

\[
z=
\{
c,\nabla c,\nabla^2c,
w,\nabla w,
d_{\rm wall},n_{\rm wall},
\text{local source indicator}
\}.
\]

The invariant law should be expressed in physical quantities.

The House ID is used only as an environment label for the invariance criterion.

It must **not** become a predictor input to \(f_{\rm inv}\).

If the final forward model needs a House embedding, the invariant-law thesis has failed.

---

## 5. Causal interpretation

A conceptual structural model is

\[
E
\rightarrow
\{
W,O,G_E
\},
\]

\[
S\rightarrow Q_s,
\]

\[
(C_t,W,Q_s,O)
\rightarrow
F_{\rm inv},
\]

\[
(F_{\rm inv},G_E)
\rightarrow C_{t+\Delta t}.
\]

The scientific assumption is:

\[
\boxed{
F_{\rm inv}\perp E
\mid Z_{\rm phys}
}
\]

in the sense that its functional law does not change with environment once expressed in the correct physical coordinates.

This is not causal discovery from robot motion.

The environmental variation comes from:
- different Houses;
- different wind configurations/realizations;
- different source positions generated offline.

That heterogeneity supplies the quasi-interventional contexts.

---

## 6. Why this is different from M4

### M4
We predefine the mechanism family:

- source;
- advection;
- diffusion;
- boundary;
- residual.

Then share the residual mechanism across Houses.

### M5
We do **not** assume the unresolved mechanism has one preselected form.

We ask the data to disentangle:

\[
\text{intrinsic invariant law}
\quad\text{vs}\quad
\text{environment-specific dynamics}.
\]

Symbolic interpretation is optional after the separation.

Thus:

- M4 = **mechanism composition prior**;
- M5 = **causal invariant-law discovery**.

They should be tested separately first.

---

## 7. Why this is not ordinary symbolic turbulence closure

2025 CFD literature already contains:
- symbolic turbulence closures;
- neural-network-to-symbolic-model extraction;
- solver-in-the-loop closure learning;
- generalizable symbolic closures.

Therefore do **not** claim:
- first symbolic gas/turbulence closure;
- first data-driven plume residual;
- first interpretable fluid closure.

The distinctive scientific role must be:

> **multi-environment causal disentanglement of invariant plume dynamics from environment-specific mechanisms, followed by source-localization use of the recovered invariant law.**

Symbolic regression is only an explanation/export layer.

---

## 8. Local PDE-to-learning reduction

DIF is demonstrated on ODE systems.

Gas dispersion is a PDE.

For a first falsification, convert field snapshots into local dynamical samples.

At cell \(x_i\) and time \(t_n\):

\[
y_{i,n,E}
=
r_E(x_i,t_n).
\]

Input:

\[
z_{i,n,E}
=
[
c,
\nabla c,
\nabla^2c,
w,
\nabla w,
d_{\rm wall},
n_{\rm wall},
\ldots
].
\]

Then learn:

\[
y
=
f_{\rm inv}(z)
+
g_E(z)
+
\epsilon.
\]

This is a local closure/law representation.

Only after it passes should a nonlocal/operator form be considered.

---

## 9. Invariance objective

Do not directly copy DIF architecture before the audit.

Conceptually require:

### Fit

\[
\mathcal L_{\rm dyn}
=
\|y-f_{\rm inv}(z)-g_E(z)\|^2.
\]

### Environment independence of invariant component

\[
\boxed{
I(
F_{\rm inv};
E
)
\rightarrow0
}
\]

or a practical adversarial/MMD/HSIC independence surrogate.

### Environment-specific branch remains allowed

Do not force the entire dynamics to be invariant.

That would simply average different Houses.

The decomposition must permit \(g_E\) to absorb genuinely environment-specific effects.

---

## 10. Strong physical identifiability restriction

A dangerous trivial solution is:

\[
f_{\rm inv}=0,\qquad g_E=y.
\]

Another is an over-powerful \(f_{\rm inv}\) that memorizes all environments.

Therefore M5 requires explicit controls.

### C1 — capacity asymmetry

The environment-specific branch must be intentionally low-capacity / regularized.

### C2 — cross-environment necessity

Train on multiple environments and evaluate the invariant branch alone or with source-blind adaptation on unseen environment.

### C3 — intervention consistency

Changing source position should modify source forcing \(q_s\), not change the recovered intrinsic law.

### C4 — wind consistency

Changing wind must change known advection input, not cause a new intrinsic law.

### C5 — environment-label null

Randomly permuting environment labels should destroy the meaningful decomposition.

---

## 11. Pre-network audit L0

Before implementing DIF/hypernetworks, ask whether an invariant law is even plausible.

Use the M4 extraction pipeline on H01/H02/H03.

For each field sample compute candidate physical descriptors \(z\) and residual \(r_E\).

### Test A — conditional cross-House alignment

Partition/match local samples by physical state/context:
- concentration scale;
- wind speed;
- wind-relative gradient;
- wall distance/regime.

Then compare residual distributions across Houses.

Positive signal:

\[
D(
P(r|z,E_i),
P(r|z,E_j)
)
\ll
D(
P(r|E_i),
P(r|E_j)
).
\]

### Test B — leave-one-House simple predictor

Fit a small source-blind regressor

\[
\hat r=f(z)
\]

on two Houses.

Test the third.

Compare:
- shared predictor;
- House-specific predictor;
- no-physics/raw-coordinate predictor.

If physical state variables expose a common law, shared \(f(z)\) should retain useful zero-shot skill.

### Test C — wrong-context nulls

- shuffle wind;
- shuffle wall geometry;
- random House labels;
- omit known advection subtraction.

A real invariant law should weaken under these nulls.

---

## 12. L1 — minimal causal invariant decomposition

Only if L0 is positive.

Use:
- small shared \(f_{\rm inv}\);
- small environment-specific \(g_E\);
- environment-independence regularizer on invariant representation/function output.

No transformer/hypernetwork initially.

Compare against:

1. pooled single model;
2. separate House-specific models;
3. M4 shared residual model;
4. invariant + environment-specific decomposition.

Primary forward metrics:
- held-out House residual prediction;
- multi-step field error;
- physical consistency.

Hard project metric:
- PMFS truth-source candidate rank after replay.

---

## 13. L2 — symbolic law export

Only if the invariant branch is:
- stable across seeds;
- useful cross-House;
- lower-dimensional/structured enough.

Use symbolic regression to approximate:

\[
f_{\rm inv}(z)
\approx
\hat f_{\rm sym}(z).
\]

Required tests:

- symbolic expression reproduces neural invariant branch on held-out environments;
- its coefficients are stable across training seeds;
- dimensional/physical sanity;
- inserting it into the forward solver preserves source-rank benefit.

If symbolic export loses the benefit, keep the learned invariant mechanism and do not force a white-box claim.

---

## 14. PMFS integration

For every candidate source \(s\):

1. source candidate defines \(q_s\);
2. known advection uses current wind;
3. propagate coarse field using recovered invariant law;
4. optionally add a tightly controlled environment-specific component available from source-blind local context;
5. convert field to PMFS hit probability;
6. use unchanged Native PMFS candidate scoring first.

No end-to-end source-coordinate predictor.

Hard metric:

\[
\boxed{
\text{truth-source candidate rank}
}
\]

on independent plume realizations.

---

## 15. Strong novelty tests

M5 only survives as main thesis if all are true:

1. the invariant branch is measurably more transferable across Houses than a monolithic model;
2. the effect cannot be explained by ordinary normalization / coordinate canonicalization alone;
3. environment-specific branch captures distinct residual structure rather than arbitrary fitting;
4. recovered law improves source identity, not only field RMSE;
5. the same invariant mechanism survives unseen source positions;
6. final literature audit finds no GSL work already doing invariant-law discovery.

---

## 16. Relation to causal representation learning 2026

Baumgartner et al., CLeaR 2026,
*Disentangling Dynamical Systems: Causal Representation Learning Meets Local Sparse Attention*,
shows a related emerging trend:

- system parameters can be disentangled from trajectory data;
- local state-dependent causal structures can be necessary for identifiability.

This strengthens the broader scientific direction but is not copied directly.

Possible future connection:
- wall/free/corner regimes may have local causal structures, tying M5 to contextual local mechanisms.

Do not add sparse-attention machinery unless L0 shows such regime dependence.

---

## 17. Data requirements

M5 requires fewer source locations than a monolithic generative world model because every spatial-temporal cell becomes a local law sample.

But independence is not guaranteed:
- cells from the same plume realization are strongly correlated.

Therefore evaluation splits must be by:
- plume realization;
- source position;
- House,

not random cells.

Pseudo-replication is forbidden.

---

## 18. Kill conditions

Kill M5 main line if:

- L0 shows no conditional cross-House alignment;
- pooled/shared physical predictor fails completely on held-out House;
- invariant decomposition collapses to trivial branch allocation;
- House-specific models are consistently required;
- symbolic/invariant law does not improve PMFS source rank;
- environment labels/source contexts are too few to identify the decomposition;
- direct prior-art collision is found.

---

## 19. Current comparison with M4

### M4 strengths
- safer;
- stronger physical prior;
- lower identifiability risk;
- easier to implement.

### M5 strengths
- larger scientific idea;
- causal/invariant law discovery rather than fixed architecture;
- can potentially reveal an explicit transferable plume law;
- more clearly remote from existing GSL neural surrogates.

### M5 risks
- identifiability;
- multi-environment data sufficiency;
- PDE-to-local-law approximation;
- turbulence closure prior art.

Status:

\`KEEP — HIGH-RISK / HIGH-SCIENTIFIC-UPSIDE BIG-IDEA CANDIDATE; RUN L0 BEFORE ANY MODEL\`.
