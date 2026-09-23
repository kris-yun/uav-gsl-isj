# Candidate M7 — Test-Time Compositional Plume Operators

Date: 2026-09-23  
Branch: \`research/testtime-compositional-plume-operators-v1\`  
Status: **KEEP — top-tier main-thesis candidate pending PMFS/GADEN mechanism gate**

## 1. Mother idea

Transfer the 2026 **test-time compositional neural-operator / physics-mechanism library** paradigm into PMFS.

Do not learn one monolithic mapping

\[
F_\theta(S,W,O)\rightarrow C.
\]

Instead represent plume dynamics as a composition of physically meaningful operators:

\[
\boxed{
\mathcal F_{\rm plume}
=
\mathcal B_O
\circ
\mathcal D
\circ
\mathcal A_W
\circ
\mathcal J_S
}
\]

where:

- \(\mathcal J_S\): source injection;
- \(\mathcal A_W\): wind-conditioned advection;
- \(\mathcal D\): diffusion / unresolved turbulent spreading;
- \(\mathcal B_O\): obstacle/boundary handling.

A new House/source/wind regime is handled by **test-time composition of reusable physics operators**, rather than retraining one gas-specific forward network.

Working name:

**Test-Time Compositional Plume Operators (TCPO)**

Alternative paper-facing name:

**Mechanism-Compositional Plume World Model**

---

## 2. Remote-field 2026 parent ideas

### P1 — Neural Operator Splitting, ICML 2026

Serrano, Han, Oyallon, Ho & Morel,  
*Test-time Generalization for Physics through Neural Operator Splitting*, ICML 2026.

Core transferable principle:

- learn a dictionary of operators representing distinct dynamics;
- freeze learned operators;
- at test time search/compose operators to represent unseen dynamics;
- no gradient update is required at test time;
- demonstrated on parameter extrapolation and unseen combinations of physics;
- official main experiment includes advection–diffusion.

Important official code fact:

\`configs/config.yaml\` has

\`mixed_physics: False\`

so the model can be trained on separated pure-physics regimes and later evaluated on combinations.

### P2 — Learning Physical Operators using Neural Operators, AISTATS 2026

Gopakumar et al., AISTATS 2026.

Core transferable principle:

- decompose a PDE using operator splitting;
- learn separate neural operators for physical operators;
- represent linear operators with fixed numerical convolutions where appropriate;
- combine them in a neural-ODE formulation;
- improve interpretability and unseen-physics generalization.

### P3 — Compositional Neural Operators, 2026

Recent 2-D CompNO work uses a library of pretrained foundation blocks for elementary physics such as:

- convection;
- diffusion;
- nonlinear convection;
- Poisson solve.

This reinforces the broader 2026 trend toward **mechanism-level reusable physics blocks** instead of monolithic operator surrogates.

These papers are parent ideas. Their PDE benchmarks are not GSL.

---

## 3. Why this is a stronger PMFS fit than direct Zebra-style ICL

Zebra, ICML 2025, is an important nearby idea:
- in-context generative PDE adaptation;
- no gradient adaptation at inference.

But the released Zebra 2-D path:
- uses regular-grid physical-state tokens;
- identifies an environment primarily through context trajectories;
- does not explicitly provide a continuous source-injection forcing in its core ICL input;
- does not encode indoor obstacle geometry or local wind fields.

A PMFS candidate source is a **persistent forcing/intervention**, not simply a new initial condition.

Therefore M7 uses the more natural mechanism-composition route.

Zebra remains conceptual context for test-time adaptation, not the implementation base.

---

## 4. PMFS-specific physics factorization

A continuous gas-density/concentration model can be written schematically as

\[
\partial_t c
=
-\nabla\cdot(Wc)
+
\nabla\cdot(D\nabla c)
+
q_S
-
\lambda c
\]

with obstacle/boundary constraints.

Define four mechanisms.

### J — source injection

\[
\mathcal J_S
\]

is tied explicitly to PMFS candidate source \(S=s\).

This module should preferably be **analytic/deterministic**, not learned:

\[
q_s(x)
=
Q\,K(x-s).
\]

Candidate source identity enters here and nowhere else unless justified.

### A — advection

\[
\mathcal A_W
\]

transports gas according to the measured/estimated vector wind field.

Wind is a true control field:

\[
W(x,t)
\]

not a metadata token.

For a first version, use known semi-Lagrangian / finite-volume advection if practical.

A learned operator is justified only for unresolved wind-conditioned transport.

### D — diffusion / stochastic residual

\[
\mathcal D
\]

models:
- molecular/eddy diffusion;
- turbulent spreading;
- unresolved random dispersion.

This is the strongest candidate for a learned neural operator.

### B — boundary/obstacle operator

\[
\mathcal B_O
\]

enforces:
- free-space support;
- wall interaction;
- no-through-wall or PMFS-consistent obstacle semantics.

Prefer a deterministic projection / boundary operator before learning one.

---

## 5. Initial splitting rule

Do not start by searching arbitrary operator strings.

Use a physics-declared splitting.

A Strang-like first version:

\[
c_{t+\Delta t}
=
\mathcal B_O
\circ
\mathcal D_{\Delta t/2}
\circ
\mathcal A_{W,\Delta t}
\circ
\mathcal D_{\Delta t/2}
\left(
c_t+\mathcal J_{S,\Delta t}
\right).
\]

This gives:
- a clear physical interpretation;
- a strong baseline;
- no truth-tuned operator ordering.

Only if evidence supports it should test-time search choose among a small predeclared family of compositions.

---

## 6. What the 2026 test-time idea adds

Classical operator splitting itself is old.

The paper-level novelty cannot be:

> “we split advection and diffusion.”

The transferred modern idea is:

> **learn/retain reusable physical operator blocks and construct the gas forward model at test time by composing those blocks for the current environment, without retraining a monolithic plume model.**

For PMFS, every candidate source query reuses the same environment mechanism library.

Only \(\mathcal J_S\) changes across source candidates.

This is potentially computationally efficient and scientifically interpretable.

---

## 7. PMFS integration

Native PMFS:

\[
s
\rightarrow
\text{fresh filament simulation}
\rightarrow
h_s(x).
\]

TCPO:

\[
s
\xrightarrow{\mathcal J_S}
c_0/q_s
\xrightarrow{
\mathcal A_W,\mathcal D,\mathcal B_O
}
C_s
\rightarrow
h_s(x).
\]

Then preserve:
- candidate-source probability map;
- native source-update shell initially;
- native movement initially;
- closed-loop localization.

The first scientific test changes only the candidate forward model.

---

## 8. Why this is not generic PINO

A generic gas PINO learns:

\[
F_\theta(S,W,O)\rightarrow C
\]

as one coupled task-specific operator.

TCPO instead requires:

1. identifiable/reusable mechanism blocks;
2. physical interfaces between blocks;
3. test-time composition;
4. cross-regime reuse without full retraining;
5. module-wise ablation and interpretation.

If the final implementation becomes a single source/wind-conditioned FNO/PINO, M7 is a NO-GO.

---

## 9. Why this is not merely a learned PMFS simulator

The hypothesis is not only speed.

The scientific hypothesis is:

> **plume forward mismatch can be reduced by modularizing transport physics so that known mechanisms remain explicit and only unresolved mechanisms are learned; this should generalize across source/wind/geometry combinations better than an equally sized monolithic gas surrogate.**

The source-localization consequence must be tested directly.

---

## 10. Direct GSL novelty audit — current result

Searches were performed for combinations of:

- neural operator splitting + gas dispersion;
- neural operator splitting + source localization;
- operator splitting + plume inversion;
- compositional neural operator + pollutant/gas plume;
- test-time neural operator + gas source localization.

No direct work was found implementing the M7 structure for robotic GSL.

Important existing boundaries:

- generic numerical advection–diffusion/operator splitting is old;
- generic PINN/PINO GSL already exists;
- obstacle-aware learned gas-dispersion surrogates such as PHOENIX-UNet exist;
- operator-splitting inversion networks exist in other inverse-problem domains.

Therefore do not claim operator splitting itself.

The open claim is the **test-time reusable mechanism composition inside PMFS source inference**.

A final systematic literature audit is still required before any “first” wording.

---

## 11. Data strategy — lower burden than M3

M7 does not require learning every physical mechanism from GADEN.

Preferred hierarchy:

### Known analytic blocks
- source injection;
- wall/free-space projection;
- as much advection as can be trusted.

### Learned block
Start with only:

\[
\mathcal D_{\theta}
\]

or a transport residual block.

This can be trained on synthetic/simple transport data and adapted/selected using limited GADEN evidence.

This is materially lower-data than learning a full source-conditioned stochastic world model from scratch.

---

## 12. First hard gate — O0: splitting adequacy on real plume data

Before neural training, test whether the declared physical split is even a useful representation.

Use high-fidelity GADEN trajectories/fields.

For a fixed source and wind:

1. reconstruct one-step or short-horizon concentration/hit fields;
2. apply a low-fidelity split model:
   - source injection;
   - wind advection;
   - diffusion;
   - obstacle projection;
3. measure residual structure.

PASS signal:

- residual is smaller/more structured than the full PMFS forward error;
- error localizes to physically interpretable mechanisms, especially turbulent spreading/recirculation;
- destructive shuffles of wind/obstacle destroy the fit.

If splitting does not isolate a reusable residual, kill M7 before neural operators.

---

## 13. O1 — mechanism-transfer test

Train only the unresolved mechanism on a small subset.

Example:

\[
\mathcal D_\theta
\]

using selected source/wind conditions.

Hold out:
- source position;
- wind condition;
- plume seed.

Compare:

A. analytic split only;  
B. split + learned residual mechanism;  
C. equal-capacity monolithic learned forward model.

Hard requirement:

B must generalize better than C on unseen combinations.

Otherwise modular composition has no demonstrated value.

---

## 14. O2 — test-time composition gate

Only after O1.

Prepare a small library:

\[
\{\mathcal A^{(k)},\mathcal D^{(j)}\}
\]

or latent operator codes corresponding to different transport regimes.

At test time:
- freeze all blocks;
- choose/compose from a predeclared search space using source-blind context;
- no gradient update.

Compare against:
- fixed split;
- monolithic model;
- per-environment fine-tuned model.

The M7 thesis only survives if test-time composition provides useful unseen-physics adaptation without retraining.

---

## 15. O3 — PMFS truth-source rank — HARD GATE

Freeze all mechanisms and selection rules.

For each held-out Native/GADEN case:

1. preserve exact PMFS source candidate set;
2. generate candidate forward maps using M7;
3. use one fixed source update;
4. compare against Native PMFS and monolithic learned baseline.

Primary endpoint:

**truth-containing source-candidate rank.**

No field-MSE-only pass.

Required:
- multiple independent plume realizations;
- no House-specific truth tuning.

---

## 16. Destructive mechanism nulls

### N1 — wind permutation
Pair \(\mathcal A_W\) with the wrong wind field.

Source-rank advantage should drop.

### N2 — obstacle removal/shuffle
Destroy \(\mathcal B_O\) geometry while preserving free-cell fraction.

### N3 — operator-order shuffle
Use an invalid composition ordering.

A claimed splitting advantage should degrade.

### N4 — source-injection shuffle
Apply the wrong \(\mathcal J_S\) to candidate labels.

### N5 — monolithic-capacity control
Match parameter count and training data.

If monolithic forward performs equally or better, M7 loses its main claim.

---

## 17. Potential auxiliary innovations — not approved yet

Only after O1/O2 pass.

### Aux A — stochastic transport operator
Use M5/M3 ideas to make the unresolved diffusion/turbulence block generative.

### Aux B — hard boundary-constrained operator
Use projection/manifold-constrained generative or neural-operator methods to enforce obstacle physics.

Do not add these to rescue a failed M7.

---

## 18. Relationship to M6

### M6 — physics foundation representation
One pretrained geometry–dynamics backbone transferred to gas.

Scientific question:
- can cross-physics pretraining reduce gas-specific data demand?

### M7 — mechanism-compositional physics model
A library of interpretable physics operators composed at test time.

Scientific question:
- can reusable elementary physical mechanisms generalize to unseen plume dynamics better than one monolithic gas model?

They are genuinely different hypotheses.

Do not merge them before each independently passes its first hard gate.

---

## 19. Current assessment

Mother-idea strength: **very high**.  
Recency/venue: **very high — ICML/AISTATS 2026**.  
Physical meaning: **exceptionally high**.  
Wind role: **explicit operator, not feature token**.  
PMFS interface fit: **high**.  
Data burden: **moderate, potentially lower than M3/M6 full fine-tuning**.  
Direct GSL collision found so far: **none**.  
Main risk: **may reduce to a learned-simulator engineering decomposition unless unseen-regime composition demonstrably beats a monolithic control**.

Status:

\`KEEP — TOP-TIER MAIN-INNOVATION CANDIDATE, ADVANCE TO O0\`.
