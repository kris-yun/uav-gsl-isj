# RR-MVSI D0 Mechanism Audit — 2026-09-25

Status: **MECHANISM SUPPORT FOR D1, NOT FINAL IDENTIFIABILITY PROOF**

## 1. Source-dependent heteroscedasticity is real

Use D1R log(1+ppm) features.

For each source, compute realization residual energy around the source-half mean.

First8 vs last8 source residual-energy ordering:
- Spearman rho = **0.5844**.

Across the 168 sources, average split residual energy:
- minimum about **0.494**;
- median about **3.914**;
- 10th percentile about **1.228**;
- 90th percentile about **10.014**;
- maximum about **21.257**.

Therefore plume realization nuisance is strongly source dependent and a global homoscedastic noise assumption is not appropriate.

## 2. Independent-view residual cross covariance is near finite-sample null

Center reps 1..8 by their own source-half mean and reps 9..16 by their own independent source-half mean.

Compute cross-half residual covariance under eight replicate-index shifts.

Frobenius norm relative to the pooled within-source covariance:
- observed mean ratio: **0.0710**;
- observed range: approximately **0.0573 to 0.1149**.

Finite-sample null obtained by randomly permuting source identities in the second half:
- median ratio: **0.0682**;
- 5-95% range: approximately **0.0556 to 0.0865**.

Thus there is no systematic second-moment cross-realization residual covariance far above the finite-sample null.

One shifted pairing is above the null 95% range, so this is not a proof of full conditional independence.

## 3. What this supports

The D1R data are compatible at the second-moment level with the RR-MVSI decomposition:

Y_sr = mu_s + epsilon_sr,

where Sigma_s may vary strongly by source while independently seeded realizations do not share a large systematic residual covariance.

Under this condition, cross-view covariance preferentially isolates source-shared content covariance.

## 4. What this does not support

- full statistical independence of plume realizations;
- a nonlinear content/style identifiability theorem;
- source-independent nuisance;
- cross-environment transfer.

These boundaries must remain explicit.