# Takens / delay-manifold conjugacy transfer — NO-GO

Date: 2026-09-22
Status: **NO-GO AS MAIN LINE**

## Mother idea

Takens-style state-space reconstruction from nonlinear dynamical systems: different observables of the same underlying system can reconstruct diffeomorphic delay manifolds.

Recent scite context:
- *Stable Takens' Embedding Theorem for Non-Uniformly-Sampled Linear Systems* (2026), arXiv:2608.14001.
- *Wasserstein Geometry of Information Loss in Nonlinear Dynamical Systems* (2026), arXiv:2601.22814.
- 2025–26 work on convergent cross mapping and delay reconstruction.

Public EDM implementation:
https://github.com/SugiharaLab/pyEDM

## Transfer tested

For each source candidate:
- sample candidate simulated hit probability along the robot trajectory;
- construct delay embeddings of candidate and measured sensor traces;
- compare local neighborhood structure after rank normalization;
- subtract the same manifold similarity produced by robot-to-candidate geometry.

Natural development screen:
E=3, tau=5 samples, stride=5, 5 nearest neighbors, Theiler exclusion 5 sampled points.

## Result

Geometry-conditioned manifold-overlap score:
- pooled improvement = **21.30%**
- non-worse = **10/12**
- old = 5/6
- new = 5/6

## Mechanism failure

Final-leaf permutation, 500:
- null as good as/better than real = **62.8%**

Candidate-identity mismatch, 100:
- null as good as/better than real = **62%**

New-realization score reproducibility:
- H01: **-0.432**
- H02: 0.748
- H03: 0.906

Several truth-nearest candidates receive very low score percentile.

## Decision

Delay-manifold similarity is not source-specific enough; apparent endpoint gains are compatible with generic trajectory geometry/dynamics.

`TAKENS_DELAY_MANIFOLD_GSL_TRANSFER_NO_GO_20260922`
