# M4 Auxiliary A — Contextual Local Symmetry for Cross-House Plume Mechanisms

Date: 2026-09-23  
Branch: \`research/invariant-mechanism-plume-world-model-v1\`  
Status: **AUXILIARY CANDIDATE — must pass pre-network symmetry audit**

## 1. Parent idea

Haoran Li et al.,
*Latent Mixture of Symmetries for Sample-Efficient Dynamic Learning*,
NeurIPS 2025.

Key parent insight:

> one global symmetry group is often too restrictive; complex dynamical systems can contain a mixture of locally relevant symmetries.

We do not copy the architecture immediately.

First test whether the gas-transport data actually contains useful local equivalences.

---

## 2. Exact physical symmetry in free space

Consider the local advection-diffusion-source operator

\[
\mathcal L[c;w,q,D]
=
-\nabla\cdot(wc)
+
\nabla\cdot(D\nabla c)
+
q.
\]

Let a rigid 2-D transformation be

\[
x'=Rx+a,\qquad R\in SO(2).
\]

Transform fields consistently:

\[
c'(x',t)=c(x,t),
\]

\[
w'(x',t)=Rw(x,t),
\]

\[
q'(x',t)=q(x,t),
\]

and for anisotropic diffusion,

\[
D'(x',t)=R D(x,t) R^T.
\]

Then the local transport law is equivariant under the joint transformation.

Therefore absolute room orientation is not fundamental physics.

A monolithic network can waste data relearning the same plume dynamics at many orientations.

---

## 3. Wind-canonical local frame

For a free-space patch centered at \(x_0\), let

\[
\theta_w=\operatorname{atan2}(w_y,w_x).
\]

Translate to the patch center and rotate by

\[
R(-\theta_w).
\]

Then the local wind is canonicalized to the +x direction.

Local inputs become:

- canonical concentration patch;
- wind magnitude \(|w|\);
- local velocity gradients / shear;
- source offset in the wind frame;
- local physical parameters.

Hypothesis:

> after wind canonicalization, residual transport laws from different absolute orientations and Houses should align better.

This is testable before neural training.

---

## 4. Wall-canonical local frame

Global rotation symmetry is broken by obstacles, but local boundary physics has its own geometric frame.

For a patch near the nearest wall, estimate:
- wall normal \(n\);
- tangent \(t\);
- signed/free-space wall distance \(d_w\).

Canonicalize such that the wall normal is a fixed axis.

The physically relevant context becomes:
- wind-normal component \(w_n=w\cdot n\);
- wind-tangent component \(w_t=w\cdot t\);
- wall distance \(d_w\);
- local curvature/corner indicator;
- concentration gradients in normal/tangent coordinates.

Hypothesis:

> wall-interaction dynamics from different rooms become comparable when expressed in the local boundary frame.

This is a contextual/local symmetry, not global SE(2) invariance.

---

## 5. Candidate symmetry regimes

Do not let an unconstrained gating network invent arbitrary regimes in the first version.

Predeclare physically named contexts:

1. **free-advection regime**
   - far from walls;
   - non-negligible local wind.

2. **wall-interaction regime**
   - within a specified geometric distance of a wall.

3. **corner / multi-boundary regime**
   - two or more nearby boundary normals.

4. **low-wind diffusion/intermittency regime**
   - wind magnitude below a source-blind threshold tied to the wind-field distribution.

These are diagnostic buckets first.

Only if different canonical frames demonstrably reduce cross-House discrepancy should a learned latent mixture be considered.

---

## 6. Pre-network symmetry audit S0

Requires time-resolved GADEN field slices from the W0.5 data-generation pipeline.

For each local free-space patch:

1. compute a raw feature/residual descriptor;
2. compute the same descriptor after wind-frame canonicalization;
3. compare cross-House discrepancy.

Possible source-blind metrics:
- Maximum Mean Discrepancy;
- Wasserstein distance;
- covariance distance;
- cross-House nearest-neighbor prediction error.

Primary criterion is relative:

\[
\boxed{
D_{\rm canonical}
<
D_{\rm raw}
}
\]

consistently across held-out Houses and plume seeds.

---

## 7. Wall symmetry audit S1

Repeat using wall-normal canonicalization.

Compare:

- global/raw coordinates;
- wind-only canonical frame;
- wall-normal + relative-wind frame.

Expected:

- free-space patches benefit most from wind frame;
- wall patches benefit from boundary frame;
- one global frame should not dominate every context.

This context-dependent signature is what justifies a mixture-of-symmetries auxiliary.

---

## 8. Destructive controls

### N1 — random rotation

Rotate each patch by a random angle unrelated to wind/walls.

Cross-House alignment should not improve equally.

### N2 — wrong-House wind pairing

Use a wind direction from another spatial point/House.

Benefit should collapse.

### N3 — shuffled wall normals

Preserve normal-vector distribution but break its pairing with geometry.

Wall-frame benefit should collapse.

---

## 9. If S0/S1 pass

Only then implement a lightweight symmetry-aware mechanism encoder.

Two options:

### A. explicit canonical frames
Preferred first:
- deterministic wind/wall canonicalization;
- shared mechanism model.

### B. Latent Mixture of Symmetries
Only if patches demonstrably contain multiple symmetry regimes not handled by the explicit frames.

The latent model can choose/interpolate locally relevant equivariant factors.

Do not start with B merely because it is a NeurIPS architecture.

---

## 10. Relation to M4

M4 main thesis:
- mechanisms are invariant across environments.

Aux A adds:

> the *coordinate expression* of a mechanism may differ, but equivalent local dynamics can be exposed through context-dependent symmetries.

Thus:

\[
\text{House-specific field}
\rightarrow
\text{local physical canonicalization}
\rightarrow
\text{shared invariant mechanism}.
\]

This is scientifically coherent rather than an unrelated network module.

---

## 11. Novelty boundary

Search so far found:
- gas dispersion neural surrogates;
- cellular/local gas models;
- wind-conditioned GSL;
- generic neural operators/PINNs.

No direct GSL/gas-dispersion work was found that explicitly learns or exploits a **mixture of local physical symmetries** for cross-environment source-conditioned plume modeling.

Do not claim first until final systematic audit.

---

## 12. Kill rule

Demote immediately if:
- canonicalization does not reduce cross-House residual discrepancy;
- improvement is explained only by trivial spatial smoothing;
- random/wrong physical frames work equally well;
- benefit appears only for one House.

Status:

\`KEEP FOR S0/S1; NO NETWORK IMPLEMENTATION YET\`.
