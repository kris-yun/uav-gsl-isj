# Measure-Valued Lagrangian Plume World Model — Source-Intervention Bank B0

Date: 2026-09-24
Branch: `research/measure-valued-plume-world-model-v1`
Status: **DATA GATE ONLY — NO METHOD ADVANCE CLAIM**

## Scientific reason for a new bank

Existing House02 full-field GADEN evidence has only two physical source positions (S1/S2).

The frozen M4-v3 experiments established:
- wind is learned at coarse scale, but high-dimensional intervention geometry is wrong;
- source×wind interaction is order-one: the interaction norm is comparable to the wind effect itself;
- the same W1→W2 intervention produces nearly orthogonal plume changes for S1 vs S2;
- improvements in field MSE repeatedly fail to imply source-identification improvement.

Therefore two source positions are insufficient to validate any model claiming generalization in source coordinate.

This B0 bank adds only the minimum source interventions required to test unseen-source path generalization. It is **offline GADEN only**: no ROS, PMFS, planner or closed loop.

## Parent scientific candidates screened by the same bank

The bank is deliberately model-agnostic and can kill all of these with one dataset:

1. **Measure-valued Lagrangian plume state**
   - plume represented as a probability measure / particle ensemble rather than a single Eulerian concentration field.

2. **Gaussian particle state/operator**
   - scientific anchor: ICML 2026, *From Basis to Basis: Gaussian Particle Representation for Interpretable PDE Operators*.
   - GADEN itself represents gas as Gaussian filaments, making this representation physically aligned but not automatically novel.

3. **Measure-to-measure observation analysis**
   - scientific anchor: JCP 2026, *Learning enhanced ensemble filters* / Measure Neural Mapping Enhanced Ensemble Filter.
   - novelty cannot be "ensemble filtering"; ensemble filters were already used in odor-source localization long before 2026.
   - the candidate novelty is a learned analysis operator acting on the hidden plume measure while PMFS retains the source-probability map.

## Existing development sources

- S1 full-grid cell [31,52], xyz [-2.242730141,-2.200880051,0.20]
- S2 full-grid cell [10,103], xyz [-4.342730045,2.899120331,0.20]

The existing C0.5 S1/S2 data remain development data.

## Four new sources

Coordinates use the same House02 occupancy grid:
- env_min = [-5.39273,-7.45088,-1.00095] m
- cell = 0.1 m
- xyz is the center of a verified free cell.

### Development source U1 — strongest historical confounder
- pooled diagnostic cell: [1,40]
- full-grid free cell: [3,81]
- xyz: [-5.042730000, 0.699120000, 0.20]
- distance to nearest obstacle: about 0.30 m

### Development source U2 — second historical confounder
- pooled diagnostic cell: [9,48]
- full-grid free cell: [18,97]
- xyz: [-3.542730000, 2.299120000, 0.20]
- distance to nearest obstacle: about 1.40 m

### Sealed holdout source U3 — near-wall extrapolation
- pooled diagnostic cell: [3,58]
- full-grid free cell: [7,116]
- xyz: [-4.642730000, 4.199120000, 0.20]
- distance to nearest obstacle: about 0.20 m

### Sealed holdout source U4 — open-region extrapolation
- pooled diagnostic cell: [33,37]
- full-grid free cell: [66,75]
- xyz: [1.257270000, 0.099120000, 0.20]
- distance to nearest obstacle: about 0.70 m

U1/U2 deliberately target the two strongest false-source regions exposed by the frozen 20-candidate M4 audit.
U3/U4 are geometrically different holdouts; one is near a wall and one lies in a more open region.

## Minimal generation

New simulations only:
- U1 × W1/W2 × seedA
- U2 × W1/W2 × seedA
- U3 × W1/W2 × seedA
- U4 × W1/W2 × seedA

Total: **8 new 300 s GADEN realizations**.

Use exactly the frozen C0.5 simulator contract:
- time step 0.1 s
- save interval 0.5 s
- 7 filaments/s
- variable rate true
- ppm filament center 10
- initial std 10
- growth gamma 15
- filament noise std 0.01
- gas type 10
- T=298 K
- pressure=1
- looping wind iterations 1..10
- seedA = 2026092301
- same occupancy and exact W1/W2 dynamic wind assets.

Do not generate seedB yet.

## Blinding

Development:
- U1/U2 spatial concentration slices may be exported immediately.

Holdout:
- U3/U4 raw realization directories are generated, hashed, archived and removed from the open development tree.
- no U3/U4 concentration.npy is exported before model/protocol freeze.
- holdout archive SHA-256 is recorded.
- unlocking requires a committed freeze document naming architecture, training split, metrics and thresholds.

## Development gate B0-D

Use S1/S2/U1/U2 only.

Required before holdout unlock:
1. source-coordinate leave-one-source-out validation, not random snapshot split;
2. W1/W2 are both present for each source;
3. absolute source→plume path error is reported, not field MSE alone;
4. source×wind interaction geometry is reported;
5. inverse candidate rank is primary:
   - each held development source is ranked against all available source hypotheses under the same observation budget;
6. compare against:
   - frozen M4-v3;
   - matched monolithic field predictor;
   - a concentration-map state model;
   - any proposed measure/particle model.
7. no truth-coordinate tuning.

If the proposed measure/particle state cannot improve source rank under leave-one-source-out development:
**STOP before U3/U4 unlock.**

## Sealed unseen-source gate B0-H

Only after B0-D freeze.

For U3 and U4, each W1/W2 realization is untouched.

Required:
1. no target-source fine-tuning;
2. candidate set includes S1,S2,U1,U2,U3,U4;
3. truth source rank = 1 on both U3 winds and both U4 winds under full-field diagnostic;
4. sparse geometry-only probes must also be reported:
   - fixed 30 and 50 probes;
   - random-probe robustness;
5. absolute plume-path error must improve vs M4-v3;
6. source×wind interaction direction must improve vs M4-v3;
7. improvements may not depend on simulator-only source truth or future observations.

Fail any source-rank requirement:
**STOP MEASURE-VALUED MAINLINE.**

## Replication gate B1

Only if B0-H passes:
- generate seedB for U1/U2/U3/U4;
- repeat frozen tests.

Only after B1 may House01/House03 confirmatory generation be considered.

## Real-UAV boundary

The eventual deployable hidden plume state may consume only:
- source hypothesis;
- occupancy/map;
- estimated/downwind wind belief;
- past gas/wind/pose observations;
- frozen learned parameters.

GADEN filament IDs, true concentration fields, true source coordinates, future wind and future observations are forbidden at deployment.
