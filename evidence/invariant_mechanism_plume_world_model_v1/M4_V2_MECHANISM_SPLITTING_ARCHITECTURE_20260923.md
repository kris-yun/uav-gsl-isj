# M4 v2 — Mechanism-Splitting Plume World Model for PMFS

Date: 2026-09-23
Branch: \`research/invariant-mechanism-plume-world-model-v1\`
Status: **preferred M4 implementation form; no large model training before audits**

## 1. Why v2

A direct copy of ICLR-2026 iMOOE with gas-dispersion data would be too close to "apply a recent method to a new dataset."

The PMFS-specific second derivation is therefore:

> **do not learn the composition relationship as a generic MoE fusion first; encode the composition as an explicit physical operator-splitting world model and learn only the unresolved mechanism.**

This makes the method recognizably different from a generic neural-operator mixture and keeps physical semantics fixed.

Working method name:

**Mechanism-Splitting Plume World Model (MS-PWM)**

Paper-level thesis remains:

**Invariant physical mechanisms are reused across environments.**

---

## 2. State and exogenous variables

Physical state:

\[
c^n(x) \approx c(x,t_n)
\]

or a physically related filament-density field.

Exogenous fields/parameters:

\[
e =
\{w(x,t),O(x),D(x,t),q_s(x,t)\}.
\]

The House ID is **not** an input.

The source candidate \(s\) enters only through the source forcing \(q_s\).

---

## 3. Fixed physical mechanism sequence

For one step \(\Delta t\), use a Strang-like mechanism composition:

\[
\boxed{
c^{n+1}
=
\Psi_{\theta}
\circ
\Phi_{\rm src}^{\Delta t/2}
\circ
\Phi_{\rm adv}^{\Delta t/2}
\circ
\Phi_{\rm diff}^{\Delta t}
\circ
\Phi_{\rm adv}^{\Delta t/2}
\circ
\Phi_{\rm src}^{\Delta t/2}
(c^n)
}
\]

with obstacle/boundary conditions enforced inside the transport operators.

The precise order can be changed only for numerical/physical reasons fixed before source-localization evaluation.

Do not search over operator orders using truth-source rank.

---

## 4. Known mechanisms

### 4.1 Source operator

\[
\Phi_{\rm src}^{\tau}(c;q_s)
=
c + \tau q_s
\]

for the simplest pilot.

The source support is exactly the PMFS candidate region / point source model.

### 4.2 Advection operator

\[
\partial_t c
=
-\nabla\cdot(wc).
\]

Use known GADEN/VGR wind.

For a first pilot this should be a conservative numerical transport operator, not a neural expert.

### 4.3 Diffusion operator

\[
\partial_t c
=
\nabla\cdot(D\nabla c).
\]

Begin with a scalar or simple anisotropic \(D\), selected from physical/source-blind calibration rather than source truth.

### 4.4 Boundary operator

Obstacle mask and wall flux are handled as part of each physical step.

Do not let the residual network put concentration inside occupied cells.

---

## 5. Learned unknown mechanism

After known mechanism propagation:

\[
\tilde c^{n+1}
=
\Phi_{\rm known}
(c^n;e),
\]

learn only a correction:

\[
\boxed{
c^{n+1}
=
\tilde c^{n+1}
+
R_\theta(
\tilde c^{n+1},
c^n,
w,
O,
\text{local geometry}
)
}
\]

or a positivity-preserving transformed version.

The learned mechanism is intended to capture:
- unresolved turbulence;
- filament intermittency;
- coarse-grid transport error;
- simplified boundary error;
- effective dispersion not represented by fixed \(D\).

It must not relearn source injection or mean wind advection.

---

## 6. Cross-House invariance constraint

Use the **same** \(R_\theta\) for House01/02/03.

No House embedding / House ID.

The only differences visible to the residual mechanism are physical exogenous variables:
- local wind;
- geometry;
- wall normal/distance;
- local state/gradients;
- source forcing only through the propagated physical state.

The hypothesis is:

\[
\boxed{
R_\theta^{H01}
=
R_\theta^{H02}
=
R_\theta^{H03}
}
\]

after proper physical canonicalization.

This is the central zero-shot claim.

---

## 7. Auxiliary A integration — contextual local symmetry

Before feeding a local patch to the residual mechanism:

### free-space regime

canonicalize coordinates so local wind points along +x.

### near-wall regime

canonicalize with wall normal/tangent and represent wind in that frame.

The network sees a local canonical representation rather than absolute map orientation.

Thus:

\[
\text{raw House patch}
\rightarrow
\text{physical frame canonicalization}
\rightarrow
R_\theta.
\]

Only use latent symmetry mixtures if explicit canonical frames are insufficient.

---

## 8. Auxiliary B integration — dissipativity structure

The residual is constrained not to act as an unmodeled gas source in zero-supply conditions.

For storage

\[
H(c)=\frac12 c^TMc,
\]

require in source-off/no-inflow diagnostic states:

\[
\langle Mc,R_\theta(c)\rangle
\le
\epsilon_{\rm phys}.
\]

A later structural version may parameterize a conservative/dissipative residual split.

Do not impose a naive global decay constraint while source/boundary supply is active.

---

## 9. PMFS-compatible source inference

Do not change every part of PMFS simultaneously.

### Stage M4-B0

For every PMFS candidate source \(s\):

1. generate/propagate its candidate field with MS-PWM;
2. convert the candidate concentration state to the same PMFS hit-probability representation;
3. use the **unchanged Native PMFS candidate scoring rule**;
4. keep Native movement.

Primary endpoint:

- truth-containing source candidate rank.

This isolates forward-model value.

Only after positive B0 may posterior scoring and movement be redesigned.

---

## 10. Required comparison ladder

The main scientific ablation must be:

A. Native PMFS forward model.

B. Known operator-splitting model only:
\[
M_{\rm src}+M_{\rm adv}+M_{\rm diff}+M_{\rm bnd}.
\]

C. B + one **House-specific** residual model.

D. B + one **shared invariant** residual model.

E. D + contextual symmetry.

F. E + dissipativity structure.

Interpretation:

- B vs A: value of explicit mechanism model.
- C vs D: test of mechanism invariance across Houses.
- D vs E: test of local symmetry.
- E vs F: test of physical fusion constraint.

If C consistently beats D on held-out Houses, the invariance thesis fails.

---

## 11. Stronger novelty than generic iMOOE application

iMOOE learns a bank of operator experts and a fusion relationship.

M4 v2 instead uses:

1. **physically named and partly analytic operators**;
2. **source candidate as explicit forcing/intervention field**;
3. **fixed mechanism-splitting composition**;
4. only unresolved residual is learned;
5. local wind/wall symmetry is explicit;
6. source localization rank, not PDE forecast RMSE, is the hard endpoint.

Thus ICLR-2026 invariant-operator learning is the mother idea, while the plume-specific method is independently derived.

---

## 12. I0/S0/P0 audits before training

All three use the same small GADEN multi-source time-resolved dataset.

### I0 — mechanism residual structure
Compute:

\[
R_{\rm data}
=
\partial_t c
-
M_{\rm src}
-
M_{\rm adv}
-
M_{\rm diff}.
\]

Test whether it is smaller/more structured than raw dynamics.

### S0 — symmetry
Test whether wind/wall canonicalization reduces cross-House discrepancy in \(R_{\rm data}\).

### P0 — dissipativity
Test whether the field storage/supply balance is meaningful at available spatial/temporal resolution.

**No neural network is trained until these audits pass.**

---

## 13. Data efficiency target

Because known physics handles the dominant transport, the pilot should not require a huge source grid.

Initial target after generation-cost PASS:

- 4–8 source locations per House;
- 2 stochastic plume seeds;
- 5–20 physical-time slices per realization;
- held-out source positions;
- held-out House rotation for zero-shot tests.

This is a feasibility target, not a promise.

---

## 14. Kill conditions

Kill M4 main line if any occurs:

1. I0: known mechanism subtraction does not yield a smaller/repeatable residual.
2. I1: residual law is strongly House-specific after physical conditioning.
3. S0: physically correct canonical frames do not improve cross-House alignment beyond null frames.
4. tiny shared residual model fails to improve held-out source rank.
5. House-specific residual consistently dominates shared residual.
6. positive field RMSE changes do not translate into truth-source-rank improvement.
7. the method needs House ID or truth-tuned per-House parameters.

---

## 15. Current preferred contribution structure

### Main
**Invariant mechanism-splitting plume world model**

### Auxiliary 1
**Contextual local symmetry canonicalization / mixture**

### Auxiliary 2
**Dissipativity-constrained mechanism fusion**

No generative stochastic module is required for the first paper version.

Stochastic residual modeling remains optional and must earn its place experimentally.
