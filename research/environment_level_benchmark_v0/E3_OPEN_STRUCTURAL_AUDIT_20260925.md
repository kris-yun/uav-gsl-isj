# E3 OPEN Discovery Structural Audit

Date: 2026-09-25

Status: **OPEN-ONLY DISCOVERY; DEV/FINAL REMAIN SEALED**

Data used:
- H01 `1,3-2,4_fast`;
- H02 `3,5-1_slow`;
- H02 `4,5-3_slow`;
- 6 frozen sources/environment;
- 4 realizations/source;
- frozen 10x30 observation contract.

## Robust low-level facts

### Within-environment source identity is strong

Source-effect fraction in globally standardized log(1+ppm) observation space:
- H01: ~0.984;
- H02/W0: ~0.956;
- H02/W2: ~0.981.

Median first2-vs-last2 source-mean cosine:
- ~0.988 / 0.994 / 0.998.

Ordinary 3-train/1-fresh six-source nearest-centroid accuracy:
- ~0.792 / 0.875 / 0.875.

### Source-mean variation is low-dimensional within each environment

Top-2 centered source-mean variance fraction:
- H01: ~0.945;
- H02/W0: ~0.910;
- H02/W2: ~0.960.

This alone is not promoted as a mechanism because only six source classes are present.

## Rejected/simple stories

### Observation geometry is not a faithful source-space manifold

Spearman between physical source-pair distance and observation-mean distance:
- H01: ~0.18;
- H02/W0: ~0.02;
- H02/W2: ~0.57.

Therefore no general geometry-preserving source-manifold claim is supported.

### Direct source prototypes are not wind invariant

House02 uses identical six sources and probes in W0/W2.

Cross-wind six-source nearest-centroid transfer:
- W0->W2 normalized full-shape accuracy: ~0.50;
- W2->W0: ~0.208;
- mass/temporal/log-full alternatives are also unstable.

Therefore simple fixed source signatures do not transfer across wind operators.

### Sparse target-context interpolation is not an obvious rescue

With four target-environment context sources and two completely held-out source locations, ordinary coordinate IDW interpolation gives weak/asymmetric query-source accuracy (~0.20 in W0, ~0.40 in W2 on average across source splits).

A common additive wind shift and simple coordinate-affine source warp are also poor.

Therefore no complex in-context model is authorized from these lower bounds alone.

## House02 source x wind variance decomposition

For log(1+ppm) full observations across the two OPEN H02 winds:
- source main effect: ~73.4%;
- wind main effect: ~6.1%;
- source x wind interaction: ~17.6%;
- seed residual: ~2.8%.

For time-integrated normalized spatial shape:
- source: ~81.0%;
- wind: ~3.4%;
- source x wind interaction: ~14.1%;
- seed: ~1.4%.

Thus source identity remains dominant, but environment interaction is much larger than seed noise and cannot be ignored.

## Candidate mechanism: reusable environment-deformation subspace

Let M_E(s) be the source-conditioned mean 300-D log observation for environment E.

For H02 W0/W2 define the source-dependent wind deformation after removing the source-common environment shift:

  C_02(s) = [M_W2(s)-M_W0(s)] - mean_s[M_W2-M_W0].

Empirical OPEN facts:
- top-2 singular modes explain ~93.1% of C_02 energy;
- across 2+2 realization splits the top-2 fraction remains about 88.4-95.0%;
- split top-2 principal angles are ~4.0 deg and ~7.6 deg;
- first-half top-2 basis captures ~90.3% of last-half deformation energy;
- last-half basis captures ~93.0% of first-half energy.

Controls:
- random two-dimensional feature subspaces capture ~0.5% median and ~1.65% at the 95th percentile;
- same-wind seed-noise subspaces capture only ~56% / ~19% in the registered cross-control.

Interpretation:

> the W0<->W2 source-dependent environment deformation is not a common shift and is not arbitrary high-dimensional noise; it occupies a reproducible low-dimensional observation subspace.

This is only an OPEN discovery mechanism, not a main innovation.

## Next gate

Consume only the H02 SEALED_DEV_HOLDOUT (`3,5-1_fast`) to test whether its source-dependent deformation is predicted by the OPEN W0/W2 deformation subspace.

H01 DEV and all House03 data remain sealed.