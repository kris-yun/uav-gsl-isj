# M4 Auxiliary B — Dissipativity-Constrained Mechanism Fusion

Date: 2026-09-23  
Branch: \`research/invariant-mechanism-plume-world-model-v1\`  
Status: **AUXILIARY CANDIDATE — structure audit before implementation**

## 1. Parent idea

Roth et al.,
*Stable Port-Hamiltonian Neural Networks*,
NeurIPS 2025.

Parent principle:

> learn unknown dynamics inside a structure that separates conservative flow, dissipation and external ports, so physically meaningful stability/dissipativity follows from the architecture.

Supporting physical backdrop:

- port-Hamiltonian formulations are established for open fluid systems;
- recent infinite-dimensional formulations explicitly include advection–diffusion systems with boundary control.

We do not claim port-Hamiltonian theory itself as novel.

---

## 2. Why it fits M4

M4 decomposes plume evolution into:

- source injection;
- advection;
- diffusion;
- boundary exchange;
- learned residual.

Without an additional structure, a learned fusion network can make those mechanisms compensate arbitrarily and inject unphysical concentration dynamics.

Aux B adds a global physical accounting law:

> in the absence of source/boundary supply, the learned plume state should not create stored scalar-field content from nowhere.

This is stronger than a soft PDE residual.

---

## 3. Starting plume equation

Use the coarse transport form

\[
\partial_t c
=
-\nabla\cdot(wc)
+
\nabla\cdot(D\nabla c)
+
q
-
\lambda c
+
r_\theta.
\]

Here:
- \(q\): source injection;
- \(w\): known wind;
- \(D\succeq0\): dispersion;
- \(\lambda\ge0\): loss/removal;
- \(r_\theta\): unresolved learned mechanism.

---

## 4. Storage functional

Do not call gas concentration itself "energy."

Use an energy-like nonnegative storage functional:

\[
\boxed{
H[c]
=
\frac12
\int_\Omega c(x)^2\,dx
}
\]

or, after spatial discretization,

\[
H(c)
=
\frac12 c^T M c
\]

with positive mass matrix \(M\).

The purpose is mathematical dissipativity / stability, not literal thermodynamic energy.

---

## 5. Balance structure

Under an incompressible/divergence-controlled wind discretization and appropriate boundary treatment:

### Advection

The interior advection operator should be approximately skew with respect to the mass inner product:

\[
\langle c,A_{\rm adv}c\rangle_M
\approx0,
\]

apart from explicit boundary transport.

Thus advection redistributes the scalar field; it should not be the interior source of \(H\).

### Diffusion/loss

\[
\langle c,A_{\rm diff}c\rangle_M
\le0.
\]

Diffusion and decay dissipate the storage functional.

### External ports

Source injection and open-boundary flux provide/extract storage through explicit input/output ports.

Thus

\[
\boxed{
\dot H
\le
s_{\rm source}
+
s_{\rm boundary}
}
\]

for the unmodeled-free system.

This is the plume analogue of a dissipativity inequality.

---

## 6. Semi-discrete port-Hamiltonian form

After spatial discretization, target a structure of the form

\[
\boxed{
\dot c
=
[J(c,w,O)-R(c,w,O)]
\nabla H(c)
+
G(c,O)u
+
r_\theta
}
\]

where:

- \(J=-J^T\): conservative transport;
- \(R=R^T\succeq0\): diffusion/loss;
- \(u\): source/boundary inputs;
- \(G\): input coupling.

Known numerical operators should populate as much of \(J,R,G\) as possible.

Do not ask a neural network to relearn known advection/diffusion structure.

---

## 7. Learned residual constraint

The residual is allowed to model unresolved plume physics but should not become an arbitrary hidden source.

In a no-source / no-inflow test condition:

\[
u=0,
\]

require

\[
\boxed{
\langle \nabla H(c),r_\theta(c,w,O)\rangle
\le
\epsilon_{\rm phys}
}
\]

with \(\epsilon_{\rm phys}\) tied to numerical/model mismatch, not tuned on source-localization truth.

A stronger architecture can parameterize residual dynamics as:

\[
r_\theta
=
[J_\theta-R_\theta]\nabla H
\]

with

\[
J_\theta=-J_\theta^T,
\qquad
R_\theta\succeq0.
\]

Only use this if a simple residual audit indicates enough data to learn such structure.

---

## 8. Boundary warning

Indoor plume domains are open systems.

Therefore do **not** impose

\[
\dot H\le0
\]

blindly during normal source release / boundary flow.

The correct statement is a supply inequality with:
- source injection;
- advective outflow/inflow;
- diffusive boundary flux.

Failing to account for boundary supply would turn a physical constraint into a wrong one.

---

## 9. Structure audit P0 before neural implementation

Using GADEN field slices:

1. compute \(H_t=\frac12\int c_t^2\);
2. estimate \(\dot H_t\);
3. compute source-on/source-off periods if available;
4. estimate boundary advective flux from \(c,w,n\);
5. estimate diffusion dissipation for a plausible \(D\) panel.

Check whether the empirical balance

\[
\dot H
-
s_{\rm source}
-
s_{\rm boundary}
\]

is predominantly nonpositive / consistent with unresolved dissipation after numerical uncertainty.

This is source-blind.

---

## 10. Stronger controlled test

If easy in GADEN, run one short simulation:

1. source ON until time \(T_0\);
2. source OFF after \(T_0\);
3. keep wind/environment unchanged.

After source-off, account for boundary flux and test whether storage decays consistently.

This directly tests whether a dissipativity constraint is appropriate.

Do not infer the constraint only from localization trajectories.

---

## 11. Destructive checks

### N1 — time shuffle

Shuffle concentration snapshots.

Estimated balance should break.

### N2 — wrong wind

Pair concentration with another wind field.

Boundary/advection accounting should worsen.

### N3 — sign-reversed diffusion

A deliberately anti-diffusive operator should violate the storage inequality.

These controls verify that the diagnostic is detecting physical structure rather than smoothness alone.

---

## 12. If P0 passes

Aux B can constrain M4's mechanism fusion.

Expected benefits:
- prevents learned residual from acting as hidden gas injection;
- stabilizes multi-step rollouts;
- improves extrapolation to unseen Houses/winds;
- gives interpretable decomposition of conservative vs dissipative dynamics.

Required comparison:

1. M4 without dissipativity structure;
2. M4 + soft balance penalty;
3. M4 + structural dissipativity parameterization.

Hard project metric:
- held-out truth-source candidate rank.

Physical balance and field RMSE are supporting metrics.

---

## 13. Novelty boundary

Do not claim:
- first port-Hamiltonian fluid model;
- first stable physics-guided NN;
- first dissipative gas model.

The auxiliary contribution, if retained, is:

> using a dissipativity/port-structured fusion to prevent physically named plume mechanism experts from compensating through unphysical hidden source terms in a PMFS-compatible source-localization world model.

No direct GSL work with this structure has been found in the current audit.

---

## 14. Kill rule

Drop Aux B if:
- GADEN field evolution does not admit a useful storage/supply accounting at the available resolution;
- boundary terms dominate so strongly that the constraint is non-informative;
- structural parameterization hurts source identity and generalization;
- a simple conservation/balance penalty performs equally well.

Status:

\`KEEP FOR P0 STRUCTURE AUDIT; NOT YET PART OF FINAL METHOD\`.
