# Invariance screening checkpoint — 2026-09-20

## Decision boundary

This screen asks a narrower question than closed-loop localization:

> Is there a source-identifying representation that removes nuisance variability by physics-derived symmetries, rather than learning a black-box correction?

The candidate came from the recent invariance/quotient-space line:
- Yao et al., *Unifying Causal Representation Learning with the Invariance Principle*, ICLR 2025.
- Kim et al., *Sufficient Invariant Learning for Distribution Shift*, CVPR 2025.
- Xu et al., *Quotient-Space Diffusion Models*, ICLR 2026.

The transfer is deliberately non-causal: we test whether plume observations admit a physically justified nuisance group whose quotient retains source identity.

## Exact affine nuisance hypothesis

For a spatial concentration vector c in R^m,

c = b 1 + Q h_s + epsilon,

where b is spatially uniform background/sensor offset, Q>0 is unknown release/sensor gain, and h_s is the source-dependent transport signature.

Define the nuisance group

G = { g_(a,b)(c) = a c + b 1 : a>0, b in R }.

With P = I - (1/m) 11^T, the normalized centered field

q(c) = Pc / ||Pc||_2

is exactly invariant to the affine nuisance group:

q(a c + b 1) = q(c), for a>0.

Source identifiability in the quotient requires distinct sources to have non-collinear centered signatures.

This is stronger than “normalization as preprocessing”: the scientific claim would require the nuisance group, maximal invariant, identifiability condition, and a source-inference rule on the quotient.

## Real-data screen 1 — Orebro 3D gas dataset

Dataset: jburgues/Orebro3DSEN.

The useful natural experiment is that Exp01, Exp02, Exp06, Exp08, and Exp09 use the same source position (2.70, 0.50, 0.90) while changing release apparatus and/or fan condition. Exp03/04/05/07/10 use other source positions.

Evaluation:
- use the authors' steady interval 40–90 min;
- non-overlapping 2, 5, and 10 minute windows;
- 27-sensor field;
- compare raw amplitude, affine-quotient shape, multiscale temporal statistics, and low-order ARX probes;
- separately regress representations on wind summary statistics and test the residual representation.

### Result

Raw amplitude does not identify the common source:
- AUC about 0.489;
- leave-one-condition-out source recognition about 0.20.

Wind alone is worse:
- AUC about 0.26;
- leave-one-condition-out recognition 0.00.

Affine-quotient spatial shape survives:
- 2 min, plain: AUC 0.891, LOO 0.808;
- 5 min, plain: AUC 0.880, LOO 0.820;
- 10 min, plain: AUC 0.880, LOO 0.800.

After wind residualization:
- 2 min: AUC 0.980, LOO 0.944;
- 5 min: AUC 0.957, LOO 1.000;
- 10 min: AUC 0.963, LOO 1.000.

Exact compactness permutation over all C(10,5)=252 five-experiment groups:
- 2 min plain: true same-source group rank 1/252, exact lower-tail p=0.003968;
- 2 min wind-residualized: 1/252, p=0.003968;
- 5 min plain: 2/252, p=0.007937;
- 5 min wind-residualized: 1/252, p=0.003968;
- 10 min plain: 2/252, p=0.007937;
- 10 min wind-residualized: 1/252, p=0.003968.

Low-order temporal probes do not carry the effect:
- ARX plain AUC only about 0.50 / 0.55 / 0.62 for 2/5/10 min;
- temporal multiscale statistics are also weak;
- adding ARX or temporal statistics to spatial quotient shape does not beat the shape representation.

### Interim verdict

The data reject ARX/operator dynamics as the main scientific idea and demote the TimeBridge-style temporal branch. The strongest signal is a source-specific spatial equivalence class after removing additive/multiplicative nuisance.

## Real-data screen 2 — moving-UAV CO2 dataset

Dataset: salman786hossain/Gas-Source-Localization.

The three field days use the same documented CAR ground-truth source:
- UTM-like coordinates (695325.0811199092, 5912837.280386977);
- geographic coordinates in the code comments (53.32860045464625, 5.933187224731924).

The three days strongly change wind. Example median wind speeds in the filtered flight data:
- 100 m acquisition: about 3.32 / 7.37 / 5.34 m/s;
- 200 m acquisition: about 3.20 / 9.02 / 6.44 m/s;
- 300 m acquisition: about 2.72 / 10.85 / 7.39 m/s.

A deliberately hard test was run:
1. retain measurements near the nominal 10/19/29 m flight levels;
2. rotate candidate-relative coordinates into each day's median-wind frame;
3. spatially bin CO2;
4. use centered normalized field correlation as the affine-quotient consistency score;
5. scan a 21 x 21 candidate grid, ±100 m around the true source.

Results:
- 100 m: true source rank 29/441 (top 6.6%); best offset (-20,-20) m;
- 200 m: true source rank 439/441; failure;
- 300 m: true source rank 272/441; failure;
- combined: true source rank 407/441; failure.

### Falsification consequence

The affine quotient is not invariant to arbitrary wind/transport regime changes. At larger spatial scales, changing wind changes plume geometry rather than merely applying a global gain/offset. Therefore we must not claim a universal wind-invariant plume shape.

This is a useful negative result, not a reason to force the method:
- exact quotient symmetry remains valid for release-rate/background nuisance;
- transport variables such as wind speed/direction must be conditioned, marginalized, or handled by a physically derived similarity/equivariance law;
- any next version must separate exact nuisance symmetries from transport transformations that alter the source signature.

## Current branch status

- ARX / dynamic-operator main idea: REJECTED.
- TimeBridge-style temporal nonstationarity as main idea: DEMOTED.
- Simple “normalize the plume” method: REJECTED AS NOVELTY CLAIM.
- Physics-derived quotient representation: SURVIVES ONLY AS AN EXACT SUBMECHANISM.
- Next search target: a recent top-tier framework for combining exact quotient invariance with condition-dependent/equivariant transport variation, preferably with an identifiability or sufficiency theorem.

Do not enter closed-loop until that stronger formulation survives a second moving-sensor/source-localization screen.
