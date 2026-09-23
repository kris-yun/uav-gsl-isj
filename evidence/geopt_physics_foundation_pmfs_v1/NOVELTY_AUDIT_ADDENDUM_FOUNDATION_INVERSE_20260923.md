# M6 Novelty Audit Addendum — Foundation Models for Inverse Problems Already Exist

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## New boundary

Do NOT claim:

- first foundation model for an inverse problem;
- first pretrained foundation representation used for physical inversion.

A 2026 example is:

**Foundation Model-Assisted Full Waveform Inversion**  
Alfarhan et al., arXiv:2608.05763.

It uses a pretrained seismic foundation model encoder to define an inversion objective and reports improved full-waveform inversion behavior relative to conventional waveform losses in several experiments.

Therefore the broad pattern:

`pretrained foundation representation -> physical inverse problem`

is already occupied outside GSL.

## What remains distinctive for M6

M6 does not merely use foundation-model features in an inverse loss.

Its intended structure is:

1. use a **cross-physics geometry–dynamics foundation simulator backbone**;
2. preserve a pretraining-aligned obstacle-constrained transport representation;
3. prompt the backbone with local wind displacement;
4. inject each PMFS candidate source as a localized birth/forcing;
5. generate candidate plume/hit fields;
6. retain PMFS's candidate-source probability-map inversion shell.

Thus the target claim is closer to:

> foundation-transfer of a transport forward model *inside* PMFS candidate simulation,

not:

> foundation features improve inverse optimization.

## Current direct-collision status

No direct equivalent has yet been found in:
- robotic gas-source localization;
- odor-source localization;
- plume-source inversion;
- methane leak localization.

Final literature audit remains mandatory before “first” wording.

Status:

`M6 REMAINS OPEN-LOOKING AT THE GAS/PMFS-SPECIFIC INTERFACE`.
