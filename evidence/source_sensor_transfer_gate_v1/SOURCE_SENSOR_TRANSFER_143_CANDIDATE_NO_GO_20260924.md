# Source-to-Sensor Transfer 143-Candidate Gate — 2026-09-24

Decision: **NO_GO_143_CANDIDATE_TRANSFER_GATE**

## Frozen setup

- Development environment: House02
- Train cells only: S1-W1 A/B, S2-W1 A/B, S1-W2 A/B
- Holdout: S2-W2 A/B
- Real UAV geometry: frozen House02 TNQC/PMFS navigation seed0 and seed1 trajectories
- Times: 50,75,100,125,150,175,200,225,250,275 s
- Candidate set: 142 frozen PMFS quadtree candidates plus exact S2 reference
- Nearest actual quadtree candidate to S2:
  `quadtree_1_30_3_5`, distance 0.6708208 m
- No candidate selection from holdout truth

## Result

### Linear source-to-sensor transfer

Exact S2, nav0-A / nav0-B / nav1-A / nav1-B:
- MSE rank: **1 / 20 / 2 / 23**
- temporal-correlation rank: **2 / 2 / 15 / 17**

Nearest real quadtree candidate:
- MSE rank: **2 / 18 / 1 / 15**
- temporal-correlation rank: **3 / 3 / 5 / 5**

Median exact-S2 ranks:
- MSE: 11.0
- correlation: 8.5

### Nonlinear source-to-sensor transfer

Exact S2:
- MSE rank: **2 / 41 / 4 / 29**
- temporal-correlation rank: **3 / 6 / 11 / 5**

Nearest real quadtree candidate:
- MSE rank: **5 / 31 / 2 / 21**
- temporal-correlation rank: **8 / 8 / 6 / 3**

Median exact-S2 ranks:
- MSE: 16.5
- correlation: 5.5

No model achieved all-four Top3 for either metric, for either exact truth or the actual nearest PMFS candidate.

## Interpretation

The earlier two-source S1-vs-S2 signal was only a necessary-condition result.
It does not survive the real many-candidate inverse problem.

Failure mode: source non-identifiability.
- many distant candidates generate similar sparse temporal signatures;
- MSE can favor low-amplitude candidates;
- correlation can favor far-away candidates with similar temporal shape;
- training at only two source locations does not identify a continuous source-to-sensor transfer map over the PMFS candidate domain.

Therefore this route does NOT justify closed-loop PMFS integration or confirmatory House01/03 work.

## Stop rule

**STOP this route.**

Future candidates must pass a many-source rank gate early. Field MSE, wind-response cosine, two-source discrimination, or source-pair classification alone are not sufficient evidence.
