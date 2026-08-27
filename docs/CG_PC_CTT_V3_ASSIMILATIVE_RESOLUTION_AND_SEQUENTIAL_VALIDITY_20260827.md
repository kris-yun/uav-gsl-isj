# CG-PC-CTT V3 — assimilative source resolution and sequential-validity boundary

Date: 2026-08-27  
Status: **THEORY / DIAGNOSTIC DESIGN, BEFORE H02_RECONSTRUCTED_CHALLENGE outcomes**

## 1. Why add an assimilative view

The current V3 local tangent matrix answers whether the actually observed support contains replicated sensitivity to the two physical source-coordinate directions. A further question is needed:

> How much did the current observations reduce uncertainty about the latent source location at the local physical scale?

This maps directly to the 2026 **Assimilative Causal Inference (ACI)** idea from applied mathematics / geophysical-style data assimilation:

Andreou, Chen & Bollt, *Assimilative causal inference*, Nature Communications 17, 1854 (2026), DOI `10.1038/s41467-026-68568-0`.

ACI treats causal inference as an inverse problem: observed effects are assimilated into a dynamical model, and causal information is quantified through how much uncertainty in candidate causes is reduced. The paper explicitly targets short/incomplete observations and time-evolving causal structure.

We do **not** copy the full ACI causal theorem. We borrow the inverse-cause uncertainty-reduction principle and apply it to a local source-location inverse problem.

## 2. Local source displacement model

Around a physical source hypothesis `s`, let

`delta s = [delta x, delta y]^T`.

On the causally available observation support `H_t`, linearize the candidate/member predictive response:

`delta z_m ~= J_{s,m} delta s`.

Let the full transport-member nuisance covariance be

`Sigma_tr = mean_{source,m<n} 0.5 (z_sm-z_sn)(z_sm-z_sn)^T`.

V3 uses the Moore-Penrose nuisance precision `Sigma_tr^+`, not diagonal feature whitening.

The replicated 2-D source information is

`F_s = sum_{m!=n} J_{s,m}^T Sigma_tr^+ J_{s,n} / [M(M-1)]`.

This excludes same-member self-squares and aligns the information dimension with the physical source parameter `(x,y)`.

## 3. Assimilative local resolution gain

Let `P_s^-` be a local 2-D source-displacement covariance representing the physical uncertainty scale before the current observation support is assimilated.

For a Gaussian local inverse approximation, the information-form update is

`P_s^+ = [(P_s^-)^{-1} + F_s^+]^{-1}`,

where `F_s^+` is the positive-semidefinite part of the finite-sample replicated information matrix. Negative finite-sample directions are interpreted as unsupported information, never as negative variance.

Define the dimensionless local information matrix

`G_s = (P_s^-)^(1/2) F_s^+ (P_s^-)^(1/2)`.

Let its eigenvalues be

`kappa_1 >= kappa_2 >= 0`.

Then the local posterior variance shrink factors are

`rho_i = 1 / (1 + kappa_i)`.

The weakest-direction information `kappa_2` directly answers whether both source-coordinate directions are being resolved at the current physical scale.

The total Gaussian information gain is

`I_s = 0.5 log det(I + G_s)`

`    = 0.5 [log(1+kappa_1) + log(1+kappa_2)]`.

This is a continuous diagnostic and introduces no empirical release threshold.

## 4. Choice of local physical scale

A default diagnostic scale can be defined from the physical source neighbourhood, before any outcome is inspected:

`P_s,geom = mean_{j in N(s)} (x_j-x_s)(x_j-x_s)^T`.

Then `kappa_i` measures information relative to approximately one local candidate-mesh scale.

This has two useful properties:

1. it is dimensionless;
2. if the source grid is refined, the required physical distinction becomes smaller and the scale-aware information changes accordingly rather than pretending grid density is irrelevant.

For final runtime use, a more physically exact cell/region covariance may replace `P_s,geom` if the quadtree leaf geometry is available. That substitution must be frozen before confirmatory outcomes.

## 5. Relationship to the observational quotient

The quotient and assimilative metrics have different roles.

### Quotient / pair graph

Answers:

> Which local physical alternatives are currently not reproducibly distinguishable?

It produces coarse observational equivalence classes.

### Assimilative gain

Answers:

> How much source-location uncertainty is reduced in each local physical direction?

It provides a continuous resolution diagnostic inside/between those classes.

The method should not collapse these into one arbitrary scalar threshold.

## 6. Sequential-validity problem discovered before runtime

An offline exact member sign-flip diagnostic can be useful for one frozen evaluation. It is **not automatically valid** to recompute an ordinary `p<=0.01` test at every online source update and release whenever it first passes. Repeated peeking creates a false-release risk.

Therefore V3 currently imposes the following boundary:

- sign-flip p-values are **offline qualification diagnostics**;
- the current runtime code is not authorized to treat repeated unadjusted sign-flip p-values as anytime-valid evidence;
- even/odd fold agreement is a reproducibility guard, not a proof of sequential type-I-error control.

This boundary is motivated by 2026 work in another inverse-problem domain:

Cumitini, Barletta & Simeone, *Anytime-Valid Quantum Tomography via Confidence Sequences*, arXiv:2601.20761 (2026).

The transferable idea is that a state estimate that is repeatedly inspected while measurements arrive should be accompanied by uncertainty sets/evidence processes whose coverage remains valid at any stopping time.

## 7. Future online release options

Three scientifically clean options exist; no choice is frozen yet.

### Option A — fixed decision checkpoints

Evaluate statistical release only at preregistered source-update indices. This is simplest but may waste available early evidence.

### Option B — anytime-valid confidence/e-value process

Construct an e-process or confidence sequence for source-vs-rival evidence so optional stopping is controlled. This is the strongest inferential route but needs a defensible bounded/conditional increment model.

### Option C — deterministic runtime resolution + offline inferential audit

Use only deterministic model-side conditions online (physical quotient, positive leave-one-member-out source information, observation adequacy, fold-consistent ordering) and reserve sign-flip p-values for frozen offline evaluation.

Given current project time pressure, Option C is the lowest-risk engineering path unless an anytime-valid process can be derived and self-tested without adding tunable parameters.

## 8. Binding code alignment

Canonical V3 implementation is now in:

`experiments/cg_pc_ctt/v3_math.py`

It includes:

- full pair-difference nuisance covariance;
- Moore-Penrose nuisance precision;
- 2-D cross-member tangent information;
- replicated pair separation;
- `assimilation_resolution_gain(F, prior_cov)`.

Formula-level invariance/rank tests are in:

`experiments/cg_pc_ctt/selftest_v3_math.py`.

No H02 replacement-challenge outcome may be used to change these definitions after manifest freeze.
