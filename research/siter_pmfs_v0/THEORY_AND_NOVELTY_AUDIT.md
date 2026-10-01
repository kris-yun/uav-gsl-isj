# SITER-PMFS v0 — theory and novelty audit

Date: 2026-10-01
Status: candidate main line; no closed-loop authorization.

## Core change in research strategy

The project should stop searching for one feature that is globally invariant to House, wind realization, sensor history and plume state.

That objective is too strong for gas transport: the source identity/location is the task variable we want to preserve, while wind is not a nuisance that should be removed. Wind changes the physical relationship between source and observation and therefore must remain a structured transformation variable.

The proposed thesis is:

> learn a small source-relevant specialist representation from the already robust PMFS evidence, while representing wind-conditioned transport equivariantly; use transport only as a conservative contradiction channel, not as an unconstrained second source posterior.

Working name:

**SITER-PMFS — Source-Invariant / Transport-Equivariant Specialist Representation for PMFS.**

## 2026 parent ideas

### 1. Generalist -> specialist representation

Yujia Zheng, Fan Feng, Yuke Li, Shaoan Xie, Kevin Murphy, Kun Zhang,
**From Generalist to Specialist Representation**, ICML 2026, PMLR 306.

Official:
https://proceedings.mlr.press/v306/zheng26a.html

Transfer:
PMFS is treated as the physically grounded generalist representation.
We do not replace it with a raw-data network. We derive a sparse source-localization specialist state containing only candidate evidence that is useful for source ranking.

The paper's theorem does not automatically apply to our construction; the transfer is the representation principle and sparsity motivation.

### 2. Domain-invariant structures, but not invariant dynamics

Pascal Janetzky, Tobias Schlagenhauf, Stefan Feuerriegel,
**Continual Learning of Domain-Invariant Representations**, ICML 2026,
PMLR 306.

Official:
https://proceedings.mlr.press/v306/janetzky26a.html

Transfer:
the source-evidence channel should avoid House-specific shortcuts and is tested under leave-one-House-out generalization.

### 3. Flow-equivariant dynamics

Hansen Lillemark et al.,
**Flow Equivariant World Models: Structured Memory for Dynamic Environments**,
ICML 2026, PMLR 306.

Official:
https://proceedings.mlr.press/v306/lillemark26a.html

Transfer:
wind should not be forced to disappear from the representation. Candidate-to-observation geometry is expressed in local flow coordinates so that changing wind transforms the transport channel in a structured way.

## Why this is different from earlier failed lines

- TNQC tried to quotient/canonicalize a spatial hit-logit field and failed at final source ranking. SITER does not assume the full plume field is invariant.
- M4 tried to learn the plume/field dynamics. SITER does not predict the full plume and does not optimize field MSE.
- Source-Lineage Lagrangian v2 tried to improve deterministic forward transport. Its learned residual had almost no signal over 3-D physics. SITER instead operates at the inverse source-evidence level.
- P3T-D0 tried to improve the 3-D observation representation with Gaussian support. It failed to restore positive truth evidence.
- R1/R1P5 showed that 3-D transport can strongly suppress many wrong hypotheses while not increasing the truth score. SITER turns this empirical asymmetry into the inference principle.

## Novel inference principle: one-sided transport falsification

Let the PMFS log score for candidate s be l_PMFS(s).

Let C_theta(s; W, H) >= 0 be a learned or structured transport contradiction energy derived from wind W and PMFS/history features H.

SITER uses

    l_SITER(s) = l_PMFS(s) - C_theta(s; W, H)

and therefore

    P_SITER(s) proportional to P_PMFS(s) * exp(-C_theta(s; W, H)).

The wind channel can down-weight a physically inconsistent candidate, but cannot create positive source evidence by itself.

This is deliberate: our current evidence says the transport model is better at falsifying wrong sources than positively identifying the truth.

## Minimal specialist representation

For each PMFS candidate, build two feature groups.

### Source-stable/generalist channel

Source-blind, per-update normalized PMFS descriptors:

- native PMFS log-score quantile;
- confidence-weighted measured/predicted residual quantiles;
- observed/predicted support overlap;
- confident-hit unsupported mass;
- confident-miss predicted mass;
- candidate leaf area / source-map local mass;
- tie/support coverage diagnostics.

These are not claimed individually invariant. The specialist fit is explicitly tested for leave-one-House-out stability.

### Flow-equivariant channel

For supported observation cell i and candidate s:

    d_is = x_i - s
    uhat_i = u_i / (||u_i|| + eps)
    a_is = d_is dot uhat_i
    b_is = ||d_is - a_is uhat_i||

Candidate transport descriptors are low-dimensional summaries of:

- detected-gas upwind violation mass;
- downwind confident-miss mass;
- cross-flow residual dispersion;
- along-flow residual asymmetry;
- local wind directional coherence;
- streamline/reachability contradiction when the PMFS map permits it.

The core representation is candidate-centered and wind-relative. Absolute House coordinates are not model features.

## Sparse contradiction head

Each contradiction component c_k is scaled to [0,1] using training-House statistics only.

Use

    C_theta(s) = sum_k alpha_k c_k(s)
    alpha_k >= 0
    sum_k alpha_k = 1.

This keeps the correction interpretable, non-negative and sparse.
L1/group sparsity may select a strict subset of components.

No unconstrained MLP is the primary v0 model.

## Generalization protocol

Outer test is leave-one-House-out over H01/H02/H03.

For each outer fold:
- train/freeze on two Houses only;
- tune sparsity only inside those Houses;
- never use held-out-House truth to choose features, scales, weights or gates;
- evaluate both seeds of the held-out House at the terminal <=300 s snapshot.

Training may use earlier source updates from the training Houses, but test metrics are terminal localization metrics.

## Claim boundary

Even if positive, v0 would support only:

> a PMFS-anchored, flow-conditioned specialist representation can transfer source-discriminative contradiction evidence across Houses better than a raw learned plume model or unconstrained score fusion.

It would not establish map-free localization, full 3-D inference, or final closed-loop superiority.
