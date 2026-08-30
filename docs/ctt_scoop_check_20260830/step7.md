# Step 7 — Delta and verdict

Timestamp: 2026-08-30

## Verdict

**Provisional Level 2–3 — High-to-Medium Overlap** for the narrowed M2 main
innovation.

PMFS already covers candidate-source online dispersion simulation and Bayesian
GSL. Classical plume/occupancy work already covers hidden state versus
detection. Recent robotics papers already cover learned plume models and
physics-guided neural GSL. These components cannot be claimed independently
new.

No reviewed GSL paper was found in this bounded search that exactly maintains one native stochastic
plume-response member jointly with source across all completed mobile-robot
stops and PMFS source updates, then marginalizes it only after sequential
accumulation under a persistent sensor while replacing the native source
channel once. This is a bounded search result, not a universal nonexistence
claim.

## Delta

Unlike PMFS and mobile source-term estimators that retain candidate hit maps
or low-dimensional plume parameters, CTT retains the identity of one native
stochastic transport realization across completed stops while holding the
other whole-run nuisance variables fixed in both the method and its
transport-only ablation, aiming to prevent incompatible per-stop plume
realizations from reversing source evidence.

## Research decision

- M1: KEEP_AS_SUPPORTING_COMPONENT.
- M2: KEEP_AS_MAIN_INNOVATION.
- M3: KEEP_AS_SUPPORTING_COMPONENT.
- neural scientific module: REJECT_COLLISION.
- sparse-wind hidden-field model: REJECT_NO_EVIDENCE.
- neural M1 compression: engineering-only eligibility after exact parity.
