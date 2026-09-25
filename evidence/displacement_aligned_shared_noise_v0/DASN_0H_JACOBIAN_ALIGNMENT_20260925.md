# DASN 0H — Local Source-Sensitivity / Jacobian Alignment

Date: 2026-09-25

Status: **SOURCE-MATCHED DISPLACEMENT ALIGNMENT SIGNAL PRESENT; PHYSICAL LATENT NOT YET PROVEN**

## Construction

For each source s and each odd/even probe view:

1. use only the training 8 realizations to estimate the source mean log(1+ppm) response;
2. use the source and its available four-neighbor source cells in the frozen 168-cell panel to fit a local linear response Jacobian
   J_s = df/d(x,y);
3. standardize observation coordinates using training data only;
4. project each fresh realization residual onto the local two-dimensional source-sensitivity span;
5. interpret the resulting 2D coefficient only as an **equivalent local source displacement**, not as a proven physical displacement latent;
6. center these coefficients within source and compute odd/even same-realization cross-view shared displacement T_J.

All 168 local Jacobians have rank 2.

To reduce amplification from ill-conditioned local sensitivities, the primary calculation uses a fixed ridge term equal to 0.1 times the mean eigenvalue of J_s^T J_s. This constant is not tuned on diagnostic outcomes.

## Direction A

Train reps 1-8; diagnose reps 9-16.

Source-matched Jacobian:
- T_J = 0.05103 m^2.

200 within-source realization-pairing destructions:
- null q2.5 = -0.00747 m^2;
- null q97.5 = 0.00705 m^2;
- exceedance = 0/200.

Jacobian-source mismatch control:
- randomly permute source labels of the frozen Jacobians;
- use the same permutation for odd/even views so the control retains a coherent arbitrary 2D local basis.

Across 200 source-Jacobian permutations:
- median T_J = 0.01486 m^2;
- 95% interval = 0.00680 to 0.02766 m^2;
- maximum = 0.03421 m^2;
- observed source-matched T_J exceeds all 200 controls.

## Direction B

Train reps 9-16; diagnose reps 1-8.

Source-matched Jacobian:
- T_J = 0.07167 m^2.

Pairing-destruction null, 200 permutations:
- q2.5 = -0.01237 m^2;
- q97.5 = 0.01422 m^2;
- exceedance = 0/200.

Jacobian-source mismatch control, 200 permutations:
- median = 0.01914 m^2;
- 95% interval = 0.00955 to 0.03416 m^2;
- maximum = 0.04534 m^2;
- observed source-matched T_J exceeds all 200 controls.

## Sensitivity to inverse regularization

The same sign and pairing-null separation persist for ridge fractions 0, 0.01 and 0.1.

Unregularized pseudoinverse gives larger absolute displacement magnitudes because some local Jacobians are ill-conditioned; the fixed 0.1-ridge result is therefore used as the primary descriptive value.

## Interpretation

The shared plume-realization effect is not merely preserved by an arbitrary 2D projection.

Residuals from a source are substantially more likely to produce coherent odd/even equivalent-displacement coefficients when projected through that source's own local response Jacobian than through another source's Jacobian.

This supports a source-displacement-aligned observation-noise geometry.

However, this remains a geometric/mechanistic association, not identification of a unique physical latent Q in a covariance decomposition.

High-rank generic factors can absorb much of the same covariance, so a predictive consequence is still required before ADVANCE_MECHANISM_ONLY.

Next mini-step: **DASN-0I predictive mechanism test — does training-half displacement-aligned noise predict fresh-half localization difficulty beyond total variance/gain?**