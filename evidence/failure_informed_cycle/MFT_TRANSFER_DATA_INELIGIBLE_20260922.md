# Macroscopic Fluctuation Theory transfer — DATA-INELIGIBLE

Date: 2026-09-22
Status: **NO HONEST OFFLINE SCREEN WITH CURRENT DATA**

## Mother idea

Macroscopic Fluctuation Theory (MFT) is a nonequilibrium statistical-physics framework in which macroscopic dynamics and rare fluctuations are formulated jointly in terms of density and current fields, with an action determined by diffusion and mobility constitutive laws.

Recent scite anchors:
- *Macroscopic fluctuation theory of interacting Brownian particles* (2025), arXiv:2512.15569.
- *A shortcut through macroscopic fluctuation theory: a generalised Fick law*, J. Stat. Mech. 2026, DOI 10.1088/1742-5468/ae76fe.
- *Macroscopic fluctuation theory and the absorption of Brownian particles by partially reactive targets*, J. Phys. A 2025, DOI 10.1088/1751-8121/ae26ff.

## Why current GSL data are insufficient

The new independent-plume package provides:
- one source-conditioned candidate probability field per run;
- one measured hit-probability snapshot;
- an estimated wind field;
- a 1500-step scalar sensor/pose/wind trajectory.

It does not provide:
- a time-resolved measured spatial density field;
- a measured spatial probability-current field;
- source-conditioned time-resolved density/current trajectories;
- a frozen diffusion/mobility constitutive model.

Setting J=q*u would reduce the method to wind-weighted static field matching rather than MFT.
Adding an unfrozen diffusive term -D grad(q) would introduce a free constitutive parameter after seeing development results.

## Decision

No pseudo-MFT score was fabricated.

Status:
`MFT_GSL_TRANSFER_DATA_INELIGIBLE_20260922`

Revisit only if a future data contract exports time-resolved candidate scalar fields and a pre-specified transport/mobility model.
