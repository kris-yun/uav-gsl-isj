# CTAER theory and collision audit

Date frozen: 2026-09-13

## Observed failure that the mechanism addresses

TAORL improved the H03 fixed-trajectory MAP error from the contextual native
PMFS endpoint of 8.584 m to 4.985 m and ranked the true source 3,089 / 7,258.
It still failed the preregistered top-decile requirement.  The post-result
diagnosis found that the wrong TAORL MAP candidate had a higher median
within-window rank correlation than the true candidate.

TAORL used reverse time only as a method-level negative control.  Candidate
ranking still used forward fit alone.  Consequently, a candidate can win by
matching reversible route geometry or slowly varying concentration shape even
when that match is not specific to the physical time direction.

## One mechanism

For candidate source `c`, hardware-allowed time constant `tau`, measured rank
trajectory `r(y)`, forward candidate rank trajectory `r(x_F(c,tau))`, and its
within-completed-window time-reversed sensor response `r(x_R(c,tau))`, define

`L_F(c,tau) = mean[(r(y)-r(x_F(c,tau)))^2]`

`L_R(c,tau) = mean[(r(y)-r(x_R(c,tau)))^2]`.

Select the sensor nuisance with the already frozen TAORL rule:

`tau*(c) = argmin_tau L_F(c,tau)`.

CTAER then scores the candidate by

`J(c) = L_F(c,tau*(c)) - L_R(c,tau*(c))`,

where lower is better.  Equivalently, `-J(c)` is an unscaled ordinal
log-evidence ratio in favour of forward over reverse response.  A common
positive likelihood temperature would not change source rank, so none is fit
on H03.

The same `tau*(c)` is used in both directions.  This prevents the reverse null
from choosing a separate nuisance value and makes the contrast paired.  The
score is computed at the end of each completed 30 s window; reversing samples
inside an already completed window does not request future online data.

CTAER changes candidate-relative evidence before any Bayesian accumulation.
It does not alter the planner, posterior after accumulation, candidate map, or
sensor hardware.

## 2026 distant-field transfer

Nonequilibrium statistical physics defines trajectory irreversibility through
the log probability ratio between forward and time-reversed trajectories.  We
transfer one narrow design principle: evidence for a directional physical
mechanism should be measured relative to its reversed counterpart for the same
hypothesis.  CTAER applies that principle to source-conditioned ordinal sensor
responses.

CTAER is not an entropy-production estimator.  Rank-MSE is a deliberately
coarse observation statistic, the reverse response is a constructed null, and
the gas-source hypotheses are not thermodynamic microstates.

## Collision decisions

- LMBT backward transport is retired: chronological full wind lost to reversed
  wind on H03.  CTAER does not backtrack parcels or create source footprints.
- CTT dynamic transport and fixed-member coherence are retired: transport
  member persistence did not add stable source ordering.  CTAER has no member
  ensemble or latent transport state.
- OC-SLA cross-stop consensus already handles predictive adequacy and
  abstention.  CTAER instead constructs a candidate-wise forward/reverse
  contrast; it does not select a consensus component.
- M1R contrasts a source response with a source-agnostic context.  CTAER
  contrasts the same candidate response under forward and reversed sensor time.
- The original TAORL forward score and reverse control remain comparators.
  CTAER's exact paired subtraction has not appeared elsewhere in this repo.

## Scientific boundary

This is a post-TAORL mechanism proposed after inspecting an exposed H03
failure.  The one-shot H03 run is therefore development evidence only.  No
threshold or formula may be changed after the result.  Passing would nominate
CTAER for a future independent confirmation; failing retires this route.

