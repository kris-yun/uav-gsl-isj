# Current research state

## What is already learned
The project repeatedly found that adding a new dynamic feature to PMFS or learning a generic plume latent does not reliably improve source discrimination across contexts.

### Recent decisive experiments
- **R0-C1**: equal-height independent confirmation. 32/32 new simulations valid. Vertical-spread temporal signal passed only 2/4 contexts. Verdict: `R0C1_VERTICAL_SIGNAL_HEIGHT_CONFOUNDED_OR_UNSTABLE_STOP`.
- **R0-D**: full wind × gas factorial completion with another 32 runs. Local context dependence exists, but H01 is mainly gas-sensitive while H02 is mainly wind-sensitive; no repeated unified mechanism. Verdict: `R0D_CONTEXT_EFFECT_HOLD`.
- **P0**: transport predictability audit. The generic transferable plume-dynamics/world-model route did not meet the frozen transfer gates. Treat that route as stopped unless a fatal design flaw is demonstrated.

## Consequence
Do **not** preserve Task-Sufficient Source–Plume World Model merely because it is conceptually new.
The latest opening report still contains that route and therefore needs scientific restructuring.

## Current candidate hypothesis (not yet accepted)
A promising candidate is a **GSL-task-oriented 3D wind / transport constraint**:
global wind reconstruction accuracy may not equal GSL utility; errors near the source, shoreline, dominant transport corridor, vertical shear or recirculation may damage plume/source inference disproportionately.

This is only a candidate.
Before proposing a new algorithm, verify:
1. the literature gap is real;
2. controlled wind errors with similar global RMSE can produce materially different GSL consequences;
3. the downstream chain wind error → plume error → source-posterior/localization error is reproducible.

If not, STOP this route too.

## Required outcome of first paper
The paper remains UAV gas source localization:
- source-coordinate localization error;
- source posterior/probability map;
- true-source rank / Top-k / MAP or equivalent success metrics;
- uncertainty/calibration when appropriate.

Plume path/shape/forecast and wind-field metrics may be supporting outputs, not substitutes for GSL success.
