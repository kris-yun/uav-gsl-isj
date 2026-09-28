# TCMA-D0 — Target-Conditioned Model Adequacy Audit
Date: 2026-09-29
Branch: `research/tcma-d0-target-conditioned-adequacy-20260929`
Base: `65e75986f0bf0c69c5831903e9b7923f119b6632`

Status: PREREGISTERED READ-ONLY MECHANISM AUDIT

## Motivation

AEC-D0 established `AEC_D0_NO_CROSS_HOUSE_PREDICTIVE_SIGNAL`:
simulator-only self-competence does not predict whether `rawu-ABS` will beat
`u-ABS` on real/frozen target trajectories. In particular House02 reverses
strongly.

This licenses one narrower question before abandoning simulator-derived
reliability altogether:

> Is **target-conditioned model adequacy** predictive even though
> target-independent simulator self-competence is not?

This audit does not introduce a new method and does not claim conformal
coverage. It tests a source-mechanism hypothesis using existing frozen assets.

## Frozen assets

Use exactly the already frozen assets from AEC-D0 and its parent studies:

- 49 H01/H02 Native trajectories and their frozen endpoint observations;
- the AEC source-conditioned 88-member pseudo banks for the matching physical
  truth sources/routes;
- House03 full624 F1: 12 truth sources, 8 target realizations/source,
  2 frozen paths/realization, and the existing 88-member source-conditioned
  simulator bank per source/path/operator;
- operators: `u-ABS` and `rawu-ABS` only.

No CENTERED, adjacent difference, new source, new route, new wind family, new
EPS, new gain rule, or new observation operator is permitted.

## Adequacy construction

For operator e and a frozen target vector y from physical source s, let
m_{s,e,k} be the k-th source-conditioned simulator pseudo-vector on the same
route, k=1,...,K (K=88).

Target residual:

    T_e(s,y) = min_{g>=0} || y - g * mean_k(m_{s,e,k}) ||^2

Leave-one-out simulator self-residual:

    R_{e,k}(s) = min_{g>=0}
                 || m_{s,e,k} - g * mean_{j!=k}(m_{s,e,j}) ||^2

Define the frozen empirical adequacy percentile:

    A_e(s,y) =
      [1 + #{k : R_{e,k}(s) >= T_e(s,y)}] / (K + 1)

Higher A means the observed target is no more discrepant from the candidate
source model than many of the simulator's own realizations are.

This is an empirical model-adequacy diagnostic. Because observed targets are
not assumed exchangeable with simulator draws, do NOT describe A as a
distribution-free conformal p-value.

## Source-level aggregation

Scientific unit = physical source.

For each physical source, average A_e over its frozen target trajectories /
realizations and paths exactly as the parent study aggregates rank:

    bar_A_e(s) = mean_targets A_e(s,y)

Define:

    Delta_A(s) = bar_A_rawu(s) - bar_A_u(s)

Use the already frozen target outcome:

    Delta_G(s) = mean_rank_u(s) - mean_rank_rawu(s)

Positive Delta_G means rawu gives the better real target rank.

No target truth is used to construct A_e. Truth is used only after all
adequacy values are frozen, to form Delta_G and evaluate source rank.

## Required pre-outcome freeze

Before joining to `Delta_G`:

1. reproduce all source-conditioned pseudo-vector hashes from AEC-D0;
2. reproduce the target vectors / routes from the parent frozen studies;
3. compute all A_e values;
4. freeze and commit the adequacy table and its SHA256;
5. only then join the previously frozen ranks.

## Primary cross-House gate

TCMA advances only if all conditions hold:

1. Spearman(Delta_A, Delta_G) is positive in H01, H02, and H03 separately;
2. nonzero sign agreement between Delta_A and Delta_G is > 0.5 in each House;
3. no House has a strong reversal comparable to AEC-D0 House02;
4. the source-aware diagnostic selector
      choose rawu iff Delta_A > 0, else choose u
   is no worse in mean truth rank than the better fixed arm in every House,
   and strictly better in at least two Houses;
5. direction is not carried by a single physical source in any House with
   enough sources to assess this.

If these fail:
  `TCMA_D0_NO_CROSS_HOUSE_TARGET_CONDITIONED_SIGNAL`

If they pass:
  `TCMA_D0_CROSS_HOUSE_TARGET_CONDITIONED_SIGNAL`

If asset/parity requirements fail:
  `TCMA_D0_HOLD_INFRASTRUCTURE`

No result licenses ROS/VGR, probability fusion, PMFS repair, or training.

## Secondary diagnostic

For each operator separately, report whether higher `bar_A_e(s)` tends to
associate with lower real mean truth rank across physical sources within each
House. This is descriptive only and cannot rescue a failed primary Delta gate.

## Interpretation boundary

A positive result would support only this mechanism:

> the observed target's compatibility with the simulator's own variability
> contains cross-House information about representation reliability.

Only after such a result may a remote-field theory audit be opened (e.g.
data-conditional simulation calibration / model-misspecification-aware
inference). Do not attach a mother-theory label before the gate.

## Stop boundary

No new GADEN plume, PMFS scientific forward, VGR, planner change, network,
routing-weight fit, threshold tuning, TopK search, CENTERED arm, or probability
map. STOP after D0 and package all hashes/results.
