# ORDINAL-BRIDGE D0 — Cross-House Rank-Evidence Substrate
Date: 2026-09-29
Branch: `research/ordinal-bridge-d0-20260929`
Base: `05d038552b563a46b0ab087e0bb6732c885dceac`

Status: PREREGISTERED READ-ONLY BRIDGE TEST
No new plume / no PMFS scientific forward / no VGR / no planner change / no training.

## Why this test exists

AEC-D0 and TCMA-D0 both failed to find a cross-House simulator-derived
reliability variable. R0.75 CENTERED improved H01/H02 but failed on House03.
Therefore do not launch another router, calibration statistic, or representation
selector.

Before looking for a new mother theory, test whether there is a simpler
cross-House observable substrate that is already known to be robust to
measurement-scale mismatch: **relative concentration rank**.

This is NOT proposed as our innovation. A 2026 ICRA GSL paper by Jin et al.
already introduced an EDF-based gas-rank feature for calibration-free source
localization. We use that published idea only as a diagnostic bridge.

If even ordinal evidence is not stable across our Houses, stop the
monotone-invariance / relative-coding family and move to a different scientific
object.

## Frozen assets

H01/H02:
- use exactly the 49 frozen Native trajectories from DS-PMFS Identity D1;
- same completed source-update prefixes;
- same full Native legal supports (596 / 630);
- same target observations and candidate template sampling;
- same physical-source aggregation as D1/R0.75/TCMA.

H03:
- use exactly the frozen AOD House03 F1 full624 amendment;
- 12 truth sources × 8 realizations/source × 2 fixed paths;
- same 624 candidate support;
- nominal condition is primary; state0 stress is secondary robustness;
- no new path or target.

## EDF-rank transform

For a target vector y=(y_1,...,y_n), define

  M_i = (1/n) * sum_j 1[y_j <= y_i].

For candidate source s with template c_s=(c_{s,1},...,c_{s,n}), define

  E_{s,i} = (1/n) * sum_j 1[c_{s,j} <= c_{s,i}].

The candidate score is

  S_rank(s) = sum_i (E_{s,i} - M_i)^2.

Lower is better.

This is rank-equivalent to the EDF gas-rank likelihood in Jin et al. (2026)
because the paper's n/(n+1) and fixed variance denominator are common across
candidate sources at a fixed update and therefore do not alter candidate
ordering.

Tie contract:
- use the <= EDF definition exactly;
- zeros are retained, never removed;
- no jitter, random tie breaking, threshold, smoothing, or EPS is added.

## Operator contract

Primary arm:
  `rawu-EDF`

Reason fixed before scoring: rawu is the unblurred amplitude/concentration
template and is the closest analogue of the modeled concentration sequence in
the published gas-rank formulation.

Secondary diagnostic only:
  `u-EDF`

Do not choose between u/rawu after seeing results. The D0 decision is based on
the preregistered rawu-EDF primary.

Existing comparators:
- u-ABS
- rawu-ABS
- best fixed ABS arm per House, for descriptive reference only

No CENTERED, CD, HD-PLF, AEC, TCMA, learned router, or posterior fusion.

## Scientific unit and endpoints

Scientific unit = physical source.

For each trajectory / realization / path:
- truth rank;
- normalized truth rank = (rank-1)/(support-1);
- unique Top1;
- Top3;
- MAP error where the parent asset supports it.

Aggregate within physical source first, then House.

H02 winds sharing a physical source are aggregated within source before House
statistics. H03 two paths are not independent plumes.

## Primary gate: cross-House substrate

Decision `ORDINAL_D0_CROSS_HOUSE_SUBSTRATE` requires all:

1. rawu-EDF mean normalized truth rank is no worse than the better fixed ABS
   arm in H01, H02, and H03 nominal;
2. rawu-EDF is strictly better than the better fixed ABS arm in at least two
   Houses;
3. among non-tied physical sources, improved sources >= harmed sources in every
   House;
4. pooled source-balanced normalized rank across H01/H02/H03 is strictly lower
   than the pooled better-ABS reference;
5. H03 nominal unique Top1 is not lower than the better ABS Top1 by more than
   one target-path observation (1/192);
6. state0 stress does not show a supported catastrophic reversal (report only;
   do not tune on it).

If any primary condition fails:
  `ORDINAL_D0_NO_CROSS_HOUSE_SUBSTRATE`

If frozen asset/parity requirements cannot be satisfied:
  `ORDINAL_D0_HOLD_INFRASTRUCTURE`

## Required parity

Before reading ordinal outcomes:
- reproduce parent ABS ranks and source aggregates exactly;
- reproduce H03 nominal/state0 AOD F1 ABS Top1 effects exactly;
- freeze the ordinal scorer implementation and output schema;
- then execute once and repeat byte-identically.

## Interpretation boundary

PASS means only:

> a monotone-scale-free ordinal concentration representation is a stable
> cross-House evidence substrate in this project.

It does NOT mean:
- ordinal ranking is novel;
- Jin et al. is our mother theory;
- the main innovation is solved;
- a probability map or closed loop is authorized.

Only after PASS may we search for a novel mechanism that adds information on
top of this stable ordinal substrate, with temporal/dependence structure as one
candidate.

FAIL means:
- stop CENTERED/rank/monotone-invariance as a mainline family;
- do not rescue by changing tie rules, mixing ABS+EDF, or tuning weights on
  these same targets.

## Stop boundary

STOP after this read-only D0. No new GADEN, PMFS forward, VGR, PMFS-Clean,
network, route selection, threshold tuning, or probability fusion.
