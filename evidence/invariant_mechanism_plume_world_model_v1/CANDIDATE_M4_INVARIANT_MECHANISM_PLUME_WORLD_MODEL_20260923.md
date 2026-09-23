# Candidate M4 — Invariant-Mechanism Plume World Model

Date: 2026-09-23  
Branch: \`research/invariant-mechanism-plume-world-model-v1\`  
Status: **LEAD BIG-IDEA CANDIDATE — theory + data gate, not yet method PASS**

## 1. Main scientific thesis

Do not frame this as "another neural operator for GSL."

The proposed scientific change is:

> **A plume should be modeled as a composition of reusable physical mechanisms whose laws remain invariant across environments, rather than as one monolithic source-to-field mapping.**

For gas-source localization, the environment changes:
- House geometry;
- wind field;
- source position;
- stochastic plume realization;
- possibly transport coefficients.

But the causal/physical mechanisms do not become new physics in each House.

The same families remain:
1. source injection;
2. advection by wind;
3. diffusion / dispersion;
4. obstacle / wall interaction;
5. unresolved turbulent-intermittent transport.

The world model should therefore factor the plume dynamics into these mechanisms and reuse them across Houses.

Working name:

**Invariant-Mechanism Plume World Model (IM-PWM)**

Alternative:
**Compositional Physical World Model for PMFS**

---

## 2. Remote-field mother idea

### P1 — Physics-guided invariant operator composition, ICLR 2026

Li et al., *Towards Generalizable PDE Dynamics Forecasting via Physics-Guided Invariant Learning*, ICLR 2026.

The paper formalizes a **two-fold PDE invariance principle**:

1. **operator invariance** — elementary operators representing distinct physical processes remain invariant across domains;
2. **compositionality invariance** — the relationship that combines those operators with parameters/forcing remains invariant.

It implements the idea using an Invariance-aligned Mixture Of Operator Experts (iMOOE).

This is the closest technical mother idea.

### P2 — Context-dependent causal world models, NeurIPS 2025

Zhao et al., *Curious Causality-Seeking Agents in Open-ended Worlds*, NeurIPS 2025.

They model an environment through multiple causal subgraphs whose activation/composition changes with a latent meta-state.

Transferable principle:

> environmental context may change which mechanism is active or how strongly it acts without requiring the agent to relearn one monolithic world model.

Do **not** copy their causal-discovery/intervention algorithm into GSL. A UAV moving its sensor does not intervene on plume physics strongly enough to justify that transfer.

Use this only as a world-model representation principle.

---

## 3. Why this is different from existing GSL neural forward models

Existing GSL already includes:
- physics-guided NNs for source-conditioned gas dispersion;
- publicly listed 2026 IROS physics-informed neural operator GSL;
- neural / FNO-based gas-dispersion surrogates in adjacent fields.

Those primarily learn a monolithic mapping such as

\[
(s,w,O) \mapsto c(x,t)
\]

or source-conditioned concentration.

M4 instead assumes a structured dynamical factorization:

\[
\boxed{
\partial_t c
=
\mathcal M_{\rm src}
+
\mathcal M_{\rm adv}
+
\mathcal M_{\rm diff}
+
\mathcal M_{\rm bnd}
+
\mathcal M_{\rm res}
}
\]

or, more generally, a fixed composition

\[
\boxed{
c_{t+\Delta t}
=
\Phi_{\rm comp}
(
\Phi_{\rm src},
\Phi_{\rm adv},
\Phi_{\rm diff},
\Phi_{\rm bnd},
\Phi_{\rm res};
\ w,O,p
)
}
\]

where the mechanism families and composition rule are shared across environments.

The source candidate changes the forcing of the source mechanism; House/wind change exogenous context.

---

## 4. Physics-grounded mechanism roles

The experts are **not** free MoE slots that are allowed to discover arbitrary semantics.

### Msrc — source injection

For candidate source \(s\),

\[
q_s(x,t)
=
Q_s(t)\,\kappa_s(x)
\]

with \(\kappa_s\) supported only in the candidate source region.

This mechanism is known / fixed in the first version.

### Madv — wind advection

\[
\boxed{
\mathcal M_{\rm adv}(c,w)
=
-\nabla\cdot(wc)
}
\]

Wind is a physical field, not merely a learned feature channel.

This can be implemented analytically / numerically and need not be learned.

### Mdiff — diffusion / subgrid dispersion

\[
\mathcal M_{\rm diff}(c)
=
\nabla\cdot(D(x,t)\nabla c).
\]

Start with a simple fixed or low-dimensional \(D\).

Only promote a learned diffusion expert if data demonstrate systematic departures.

### Mbnd — geometry / wall interaction

Obstacle geometry \(O\) defines:
- invalid concentration support inside solids;
- boundary normal \(n(x)\);
- approximate no-through-wall flux.

A first constraint is

\[
n\cdot(wc-D\nabla c)\approx0
\]

at solid walls.

Do not assume exact no-flux where the GADEN contract disagrees.

### Mres — unresolved turbulent/intermittent residual

\[
\mathcal M_{\rm res}
=
R_\theta(c,w,O,\xi).
\]

This is the main learned unknown mechanism.

It should explain only residual dynamics not accounted for by the known source/advection/diffusion/boundary mechanisms.

---

## 5. Why this is closer to a causal world model

A useful structural view is:

\[
S \rightarrow q_s
\]

\[
(W,O,p,C_t) \rightarrow
\{
M_{\rm adv},M_{\rm diff},M_{\rm bnd}
\}
\]

\[
(q_s,C_t,W,O,p,\xi)
\rightarrow C_{t+1}
\]

and finally

\[
C_t,X_t
\rightarrow Y_t
\]

for the robot observation.

The intended invariance is not "statistical correlation stays the same."

It is:

> changing House/wind/source changes exogenous variables and mechanism inputs, but not the semantic identity of the physical mechanisms.

This makes cross-House generalization a test of the main hypothesis rather than an extra benchmark.

---

## 6. PMFS integration

Keep the recognizable PMFS outer shell.

For each PMFS candidate source \(s\):

1. create candidate source forcing \(q_s\);
2. propagate the same invariant mechanism world model under current wind/geometry;
3. convert predicted concentration / filament density to hit probability;
4. score/update candidate source belief;
5. keep PMFS-style candidate probability map and closed-loop movement initially.

Native:

\[
s\rightarrow h_s(x).
\]

M4:

\[
s
\rightarrow
q_s
\rightarrow
\{\text{shared invariant mechanisms}\}
\rightarrow
p(H_s(x,t))
\rightarrow
\pi(s).
\]

Do not train an end-to-end network that directly outputs the source coordinate.

---

## 7. Main novelty boundary

The claim is **not**:

- first neural operator for gas;
- first physics-informed GSL;
- first MoE;
- first causal model for physics;
- first advection-diffusion surrogate.

The defensible contribution, if supported, is narrower:

> **factorizing PMFS-style source-conditioned plume prediction into physically named invariant mechanisms and demonstrating that this mechanism-level representation transfers source identity across unseen geometries/wind domains better than monolithic learned or hand-designed forward models.**

A final systematic audit is still required before using "first."

---

## 8. Auxiliary innovation candidate A — Clifford / Geometric-Algebra physical representation

Parent:

Pepe et al., *Fengbo: a Clifford Neural Operator pipeline for 3D PDEs in Computational Fluid Dynamics*, ICLR 2025.

Do not make Clifford Algebra the paper thesis.

Use it only if it solves a real interface problem:

the plume world contains heterogeneous geometric quantities:
- scalar concentration \(c\);
- vector wind \(w\);
- vector concentration gradient \(\nabla c\);
- wall normal \(n\);
- bivector / pseudoscalar vorticity in 2-D/3-D.

A geometric-algebra representation can encode these in one multivector while preserving grade meaning and rotation relationships.

For a 2-D pilot:

\[
z(x)
=
c(x)
+
w_x e_1+w_y e_2
+
\omega e_{12}
+
\cdots
\]

This could make the residual/boundary expert geometry-aware without treating all channels as unrelated scalars.

**Promotion gate:** it must improve cross-rotation / cross-House transfer or data efficiency over ordinary channel concatenation.

Otherwise drop it.

---

## 9. Auxiliary innovation candidate B — stochastic residual world mechanism

Parent candidates:
- Operator Flow Matching, NeurIPS 2025;
- physics-constrained flow matching, NeurIPS 2025/ICLR 2026 lines.

The unresolved transport mechanism should be stochastic if the data support it:

\[
R_\theta(c,w,O,\xi)
\]

rather than a deterministic residual mean.

This is secondary to mechanism invariance.

Required comparison:

1. invariant deterministic residual mechanism;
2. invariant stochastic residual mechanism.

If stochasticity does not improve source rank or predictive calibration on independent plume realizations, drop it.

Do not use generative modeling merely because it is fashionable.

---

## 10. Why M4 may need less data than M3

M3's pure stochastic world model must learn an entire source-conditioned field distribution.

M4 fixes or strongly constrains several mechanisms:

- source injection: known;
- advection: known wind operator;
- obstacle support: known;
- much of boundary physics: known;
- only residual/unresolved mechanism must be learned.

Thus learning target becomes

\[
\boxed{
R_{\rm unknown}
=
\partial_t c
-
M_{\rm src}
-
M_{\rm adv}
-
M_{\rm diff}
-
M_{\rm bnd}
}
\]

rather than the whole field.

This is potentially much more data-efficient and scientifically interpretable.

---

## 11. Offline falsification before neural training

### I0 — mechanism residual audit

Using time-resolved GADEN slices, estimate

\[
\partial_t c
\]

by finite differences.

Compute the known mechanistic terms:

\[
M_{\rm adv}=-\nabla\cdot(wc),
\qquad
M_{\rm diff}=\nabla\cdot(D\nabla c),
\]

plus source mask / obstacle handling.

Then calculate residual:

\[
R
=
\partial_t c
-
M_{\rm src}
-
M_{\rm adv}
-
M_{\rm diff}.
\]

No neural network yet.

Report:
- fraction of dynamics energy explained by known mechanisms;
- residual spatial autocorrelation;
- residual dependence on wind shear / obstacle distance;
- cross-realization reproducibility;
- cross-source / cross-House similarity.

### Hard interpretation

If known mechanisms explain almost nothing and residual is completely unstructured:
- the proposed mechanism factorization is poor -> kill/redesign.

If known mechanisms explain nearly everything:
- a learned world model is unnecessary -> demote.

The ideal positive regime is:
- known physics explains the dominant structure;
- residual is smaller but non-random and repeatable.

---

## 12. I1 — mechanism invariance test

This is the key test of the big idea.

Without training a large model:

1. estimate residual descriptors / small local regressors separately in House01/02/03;
2. test whether the same residual law predicts held-out House/source better than House-specific correlations;
3. compare normalized residual distributions after conditioning on:
   - local wind;
   - wall distance / normal;
   - local concentration/gradient.

If mechanism-conditioned residual laws align across Houses substantially better than raw plume fields, that is a positive signal for invariant-mechanism modeling.

A destructive null:
- shuffle mechanism labels or wind/geometry context between Houses.

Alignment/generalization should collapse.

---

## 13. I2 — tiny learned mechanism prototype

Only after I0/I1 positive.

Do **not** start with iMOOE-scale architecture.

Fit a tiny residual mechanism predictor:

\[
\hat R
=
f_\theta(
c,\nabla c,
w,\nabla w,
d_{\rm wall},n_{\rm wall}
).
\]

Shared weights across Houses.

Compare against:
1. no residual;
2. House-specific residual model;
3. monolithic source+wind+geometry→next-field model;
4. shared invariant residual model.

Hard metric for this research project:
- truth-source candidate rank after forward replay.

Field RMSE alone is insufficient.

---

## 14. I3 — cross-House zero-shot gate

Train/freeze mechanisms using two Houses.

Test the third House with:
- no fine-tuning;
- no truth-driven parameter changes.

Rotate held-out House.

This is the defining experimental test.

If the method needs House-specific retraining to work, the invariant-mechanism thesis fails.

---

## 15. Relation to the current baseline-recovery result

The corrected R1 result already shows that source ranking changes strongly with the forward contract.

That motivates, but does not prove, a mechanism-level model.

M4's response is not to average over arbitrary models.

It asks:

> can the forward model be made transferable by preserving reusable physical mechanisms while allowing environment-specific exogenous inputs?

This is a different hypothesis from the previously killed generic multi-model / "many wrong models" line.

---

## 16. Direct risks

### R1 — too close to iMOOE

If we simply copy iMOOE and replace its benchmark PDE with gas dispersion, novelty is weak.

Our second innovation must be PMFS/source-localization specific:
- named source/advection/boundary mechanisms;
- partial mechanisms are analytic, not all learned experts;
- source candidate is an intervention/forcing term;
- final hard endpoint is source identity.

### R2 — gas-PINO collision

Generic operator learning is already crowded.

The paper must demonstrate mechanism factorization and zero-shot mechanism reuse, not only lower field RMSE.

### R3 — insufficient multi-environment field data

Needs W0.5-style GADEN field generation.

### R4 — mechanism decomposition not identifiable

Multiple terms may compensate each other.

Fix known mechanisms wherever possible rather than letting learned experts permute roles.

### R5 — turbulence residual not invariant

If unresolved turbulence changes qualitatively with House geometry, a single residual expert may fail.

Possible remedy only if data support it:
- a small bank of physically named residual regimes with context-dependent gating.

Do not add arbitrary MoE experts after seeing truth.

---

## 17. Current verdict

**Big-idea level:** high.  
**Physics meaning:** very high.  
**Cross-domain/source idea:** invariant/causal-mechanism world modeling + PDE operator invariance.  
**Direct GSL collision found so far:** none for explicit invariant mechanism composition.  
**Generic neural-GSL collision:** strong, therefore claims must stay mechanism-level.  
**Data risk:** moderate-high but lower than full stochastic OFM because most physics is fixed.

Status:

\`KEEP — STRONGER SCIENTIFIC THESIS THAN A MONOLITHIC GENERATIVE WORLD MODEL; PENDING I0/I1 MECHANISM AUDIT\`.
