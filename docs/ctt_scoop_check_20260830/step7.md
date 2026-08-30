# Step 7 — Delta and verdict

Timestamp: 2026-08-30

## Verdict

**Level 3 — Medium Overlap** for the narrowed M2 main innovation.

PMFS already covers candidate-source online dispersion simulation and Bayesian
GSL. Classical plume/occupancy work already covers hidden state versus
detection. Recent robotics papers already cover learned plume models and
physics-guided neural GSL. These components cannot be claimed independently
new.

No reviewed GSL paper was found that exactly maintains one native stochastic
plume-response member jointly with source across all completed mobile-robot
stops and PMFS source updates, then marginalizes it only after sequential
accumulation under a persistent sensor while replacing the native source
channel once. This is a bounded search result, not a universal nonexistence
claim.

## Delta

Unlike PMFS, which constructs candidate hit evidence without retaining one
native stochastic plume realization as a joint latent state across the whole
robot run, CTT maintains and marginalizes a persistent
source–transport–sensor atom across completed stops, aiming to prevent mutually
incompatible per-stop plume explanations from reversing source evidence.

## Research decision

- M1: KEEP_AS_SUPPORTING_COMPONENT.
- M2: KEEP_AS_MAIN_INNOVATION.
- M3: KEEP_AS_SUPPORTING_COMPONENT.
- neural scientific module: REJECT_COLLISION.
- sparse-wind hidden-field model: REJECT_NO_EVIDENCE.
- neural M1 compression: engineering-only eligibility after exact parity.
