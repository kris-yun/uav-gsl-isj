# Hodge / Helmholtz Plume Decomposition V1 — offline screen

Date: 2026-09-22
Status: **NO-GO AS MAIN INNOVATION**

## Hypothesis

Construct a transport field q = c * unit(wind) and ask whether source identity is specifically carried by the divergence / potential-like component while curl-like circulation is turbulent nuisance.

A load-bearing Hodge result would require the source signal to weaken materially when the true wind topology is removed.

## First screen

On the frozen 240-s VGR asset (H01/H02/H03 × SA/SB × fast/slow):

- signed divergence: 8/12
- absolute divergence: 12/12
- signed curl: 10/12
- absolute curl: 9/12
- transport magnitude: 11/12

The 12/12 absolute-divergence result initially looked positive.

## Load-bearing controls

That apparent positive result does **not** depend on Hodge physics:

- true wind absolute-divergence: 12/12
- replace each episode by its mean wind direction: 12/12
- replace all wind directions by fixed +x: 12/12
- pure concentration-gradient magnitude: 12/12
- concentration Laplacian: 11/12
- spatially shuffle wind directions, 100 deterministic source-blind seeds:
  - mean accuracy 91.08%
  - median 11/12
  - 38/100 runs remain 12/12

Thus the strong discrimination is already present in the concentration spatial shape. The vector-field decomposition is not load-bearing.

## Decision

**NO-GO.**

Do not implement a full graph-Poisson Hodge projection and do not promote Hodge/Helmholtz, divergence-vs-curl separation, or vector-field topology as the paper-level main innovation.

The correct scientific interpretation is that the 240-s asset contains strong distributed spatial source identity, not that this identity specifically lives in a potential-flow component.
