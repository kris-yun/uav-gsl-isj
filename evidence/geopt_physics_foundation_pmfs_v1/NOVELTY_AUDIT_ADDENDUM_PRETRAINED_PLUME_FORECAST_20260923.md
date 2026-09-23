# M6 Novelty Audit Addendum — Pretrained Urban Plume Prediction Is Prior Art

Date: 2026-09-23

## Near-neighbor

A 2025 PNAS Nexus paper, *Spatiotemporal predictions of toxic urban plumes using deep learning*, uses a pretrained ML model to make rapid spatiotemporal predictions of previously unseen urban plumes from limited initial observations.

Therefore M6 must not claim:
- first pretrained ML for plume prediction;
- first low-data neural plume forecasting;
- first learned plume model that generalizes to unseen plume cases.

## Distinction required for M6

M6 must remain specifically about:

1. a **cross-physics foundation backbone** pretrained without gas/plume labels;
2. geometry–dynamics particle-walk pretraining;
3. local wind-displacement prompting;
4. PMFS candidate source as a localized birth/injection condition;
5. candidate forward-map generation for **inverse source localization**;
6. truth-source rank as the downstream scientific endpoint.

The novelty is not plume forecasting itself.

## Implication

This prior art actually sharpens the M6 experiment:

the strongest control is not only scratch Transolver, but—if practical—a small plume-specific model trained from the same GADEN data.

M6 must show that cross-physics foundation pretraining adds value beyond ordinary task-specific plume learning in the scarce-data regime.

Status:

`KEEP — CLAIM BOUNDARY NARROWED`.
