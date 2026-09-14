# TROQL main-innovation terminal audit

Date: 2026-09-14

## Verdict

`TROQL_MAIN_INNOVATION_PREMISE_NOT_ESTABLISHED`

The work reached a bounded stop rule. The conclusion is not promoted to a main
innovation because the untouched external confirmation gate failed one frozen
effect-size requirement and no second qualifying, untouched public dataset was
located.

## Implementation → observed failure → missing property → one next mechanism

### Implementation

TROQL/OQIC was implemented as a pre-Bayesian evidence gate. It forms
candidate-relative margins from transport-replicated observations and releases
evidence only when a different-source edge separates from a same-source nuisance
edge. V1 used a pointwise conformal threshold; V2 replaced only that statistic
with a direction-matched distributional-dominance certificate.

### Observed failure

- V1 development: safe null abstention, but different-source replication counts
  were `14/20` and `16/20` versus the frozen `18/20` requirement.
- V2 development: both directions passed.
- V2 untouched confirmation: `a_to_b` passed; `b_to_a` had AUC `0.75` versus the
  frozen minimum `0.80`, although p=`0.00356` and all 20 source margins were
  positive.

The asymmetric failure cannot be repaired by lowering the post-confirmation AUC
threshold or pooling directions after observing the result.

### Missing theoretical property

The current certificate lacks session-conditional directional calibration. A
whole experiment carries acquisition-specific nuisance, while source identity
and transport are not factorially replicated across independent sessions. The
method therefore cannot yet guarantee that a direction-specific margin is source
evidence rather than a stable experiment fingerprint.

### One next mechanism

`CROSS_FITTED_TRANSPORT_STRATIFIED_E_VALUE`

Within each transport stratum, source-blind folds would construct candidate
prototypes and emit a per-direction e-value against the same-source acquisition
nuisance null. Only a product of e-values that remains valid across independently
replicated transport strata may become a candidate-relative likelihood factor
before Bayesian accumulation; otherwise the candidates remain merged in the
observation quotient.

This is the only next mechanism nominated. It must not be evaluated on the now
spent Orebro confirmation pair. Its decisive test requires a new, certifiably
untouched factorial asset with at least two source positions, at least two
transport conditions per source, and multiple independent acquisition sessions
per cell.

## Asset boundary

- Red:Vapor: real and transport-rich, but fixed-source; source-contrast NO-GO.
- Chasing Ghosts: reports two-room real repetitions, but raw flight sensor logs
  are not present in the current public repository.
- UCI turbulent mixtures: source position is confounded with gas identity.
- VGR/GSL-Bench: simulated and not a fresh real-sensor confirmation asset.
- Orebro3DSEN: qualifying and fully auditable, but its untouched V2 confirmation
  has now been consumed and failed.

Therefore the next action is data acquisition/release for the single frozen
mechanism above, not another posterior repair or a third threshold revision.
