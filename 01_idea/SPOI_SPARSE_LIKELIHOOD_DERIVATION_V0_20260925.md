# SPOI Sparse-Observation Likelihood Derivation V0 — 2026-09-25

Status: **THEORY FREEZE FOR D1; FULL DLL NOT YET AUTHORIZED**

## 1. Conditional stochastic plume representation

For candidate source/context a_s, represent the plume observation function as

C = mu_s + Phi_s xi,

where:
- mu_s is the context-conditioned mean plume function;
- Phi_s is an input-conditioned low-rank basis over the plume function domain;
- xi is a low-dimensional stochastic coefficient vector.

Full DLL learns a non-Gaussian conditional law p_theta(xi | a_s).

D1 first tests the Gaussian coefficient lower bound:

xi | a_s ~ N(0, Lambda_s).

## 2. UAV sparse observation operator

Let H_T select/interpolate the space-time points measured by the UAV up to time T.

With sensor noise eta ~ N(0,R_T):

y_T = H_T C + eta
    = H_T mu_s + B_s xi + eta,

where B_s = H_T Phi_s.

The crucial implementation point is that the full plume field does not need to be reconstructed online. Only the basis evaluated at observed coordinates is required.

## 3. Analytic DLL-lite source likelihood

For Gaussian coefficients:

y_T | s ~ N(
  H_T mu_s,
  K_s
),

K_s = B_s Lambda_s B_s^T + R_T.

Thus the source log likelihood is

log L_s = -1/2 [
  e_s^T K_s^{-1} e_s
  + log |K_s|
  + m log(2 pi)
],

e_s = y_T - H_T mu_s.

The PMFS source posterior update is

P_T(s) proportional to P_0(s) L_s.

All candidates remain on the original PMFS source grid.

## 4. Low-rank Woodbury evaluation

When m observations are larger than coefficient rank r, avoid an m x m inverse.

Let A_s = Lambda_s^{-1} + B_s^T R_T^{-1} B_s.

Then

K_s^{-1} = R_T^{-1} - R_T^{-1} B_s A_s^{-1} B_s^T R_T^{-1}.

and

log |K_s| = log |R_T| + log |Lambda_s| + log |A_s|.

For r << m, per-candidate evidence can therefore be evaluated using an r x r solve.

This makes a 168-candidate PMFS update plausible without Monte-Carlo plume simulation.

## 5. Coefficient-space posterior

The same sparse observations update the latent plume coefficients:

Sigma_xi,s = A_s^{-1},

m_xi,s = Sigma_xi,s B_s^T R_T^{-1} e_s.

So each source hypothesis maintains not only source evidence but a low-dimensional posterior over its compatible stochastic plume realization.

This is a useful auxiliary object for sequential sensing and uncertainty-aware prediction.

## 6. Sequential update

As new UAV measurements arrive, H_T and y_T grow.

Candidate evidence can be updated by:
- recomputing the small r x r information matrix;
- or applying rank-one/rank-k matrix updates in coefficient space.

This is fundamentally different from re-running GADEN/filament transport for every source hypothesis.

## 7. Full DLL extension

For non-Gaussian p_theta(xi|a_s):

L_s(y_T) = integral p_eta(y_T - H_T(mu_s+Phi_s xi)) p_theta(xi|a_s) dxi.

At D1 this integral is NOT approximated with outer-target-tuned Monte Carlo.

After Gaussian DLL-lite ADVANCE, admissible full-DLL evidence approximations include:
- low-dimensional importance sampling in coefficient space;
- Laplace/variational evidence using the DLL coefficient score/density;
- flow-ODE density evaluation if computationally justified.

The approximation must be frozen and calibrated before any closed-loop test.

## 8. Difference from 2026 DGSE-S

DGSE-S learns inverse distributions from sparse observations and predicts concentration uncertainty with independent per-cell diagonal Gaussians before source inference.

SPOI instead learns a forward source-conditioned correlated random-function law and derives the sparse measurement likelihood through H_T.

Thus source posterior updates retain an explicit observation model:

source context -> stochastic plume law -> sparse sensor evidence -> PMFS posterior.

## 9. D1 scientific question

The first question is not whether full coefficient diffusion is expressive.

It is:

> Does a context-conditioned correlated low-rank plume law provide source-identification information under sparse observations that a deterministic mean model, diagonal heteroscedastic model, and ordinary direct inference model do not?

If no, full DLL is stopped before training.