# DASN 0H — Training-Half Jacobian / Displacement-Projection Test

Date: 2026-09-25

Status: **STRONG DISPLACEMENT-LIKE SHARED SIGNAL; SPECIFICITY NOT YET ESTABLISHED**

## Construction

For each source and each disjoint probe view, estimate the source-response Jacobian J_s = df/d(x,y) from training-half mean log(1+ppm) profiles using the frozen 0.30 m source grid.

Central differences are used where both neighboring source cells exist inside the complete 168-cell rectangle; one-sided differences are used at the rectangle edge.

For each fresh realization residual r = y - mean_train(s), compute a regularized local least-squares pseudo-displacement:

delta_theta = (J^T J + lambda I)^(-1) J^T r,

with lambda = 1e-3 times the local average diagonal scale of J^T J.

Odd/even probe views estimate independent Jacobians and independent pseudo-displacements.

## Direction A

Train reps 1-8; diagnose reps 9-16.

- shared pseudo-displacement T_J = 0.24425 m^2;
- centered x correlation = 0.6478;
- centered y correlation = 0.5158;
- paired pseudo-displacement cosine median = 0.8903;
- cosine mean = 0.5264;
- 83.9% of sources have positive source-wise shared trace;
- median Jacobian condition number: odd 15.7, even 26.0.

Pairing-destruction null, 300 permutations:
- q2.5 = -0.03298 m^2;
- median = -0.00055 m^2;
- q97.5 = 0.03513 m^2;
- exceedance = 0/300.

## Direction B

Train reps 9-16; diagnose reps 1-8.

- T_J = 0.50227 m^2;
- centered x correlation = 0.8059;
- centered y correlation = 0.5790;
- paired pseudo-displacement cosine median = 0.8799;
- cosine mean = 0.5115;
- 85.7% of sources have positive source-wise shared trace;
- median Jacobian condition number: odd 14.4, even 34.6.

Pairing-destruction null:
- q2.5 = -0.09920 m^2;
- median = 0.00549 m^2;
- q97.5 = 0.10274 m^2;
- exceedance = 0/300.

## Current interpretation

Independent probe views map the same fresh plume realization into strongly aligned local source-displacement-like perturbations.

This is the first DASN result that directly uses source-response sensitivity rather than only decoder error covariance.

However, it is NOT YET displacement-specific evidence.

A generic shared plume fluctuation projected through an arbitrary or variance-optimal 2D observation subspace could potentially produce a similar paired pseudo-displacement statistic.

Next mini-step: **DASN-0I equal-dimensional arbitrary/generic observation-subspace specificity control**.