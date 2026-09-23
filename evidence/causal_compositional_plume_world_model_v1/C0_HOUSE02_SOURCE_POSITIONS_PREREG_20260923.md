# M4 C0 Source-Intervention Preregistration — House02

Date: 2026-09-23  
Status: **2-D source-blind selection frozen; 3-D GADEN validation pending**

## Input

Source-blind geometry source:

`House02_seed0_off_off/context_bank/source_update_0001/measured_hit_probability.csv`

Only these columns were used:
- `grid_i`;
- `grid_j`;
- `x`;
- `y`;
- `occupancy`.

No:
- gas probability;
- source posterior;
- truth source x/y;
- candidate rank;
- endpoint result

was used.

## Frozen selection rule

Implemented in:

`reference/select_m4_c0_source_positions.py`

Parameters:
- count = 4;
- minimum 2-D clearance = 0.9 m;
- clearance = minimum of:
  - distance to obstacle-cell centers;
  - distance to map boundary;
- first point = eligible point nearest eligible-set centroid;
- subsequent points = deterministic farthest-point sampling.

Eligible free cells: **177**.

## Frozen 2-D proposals

| ID | grid_i | grid_j | x | y | 2-D clearance |
|---|---:|---:|---:|---:|---:|
| S1 | 10 | 17 | -2.242730141 | -2.200880051 | 1.341641213 |
| S2 | 3 | 34 | -4.342730045 | 2.899120331 | 0.900000095 |
| S3 | 19 | 33 | 0.457270145 | 2.599120140 | 0.900000572 |
| S4 | 3 | 3 | -4.342730045 | -6.400879860 | 0.900000095 |

## Z coordinate

Use the fixed House02 source-height plane required by the benchmark / GADEN source contract.

Do not alter x/y after truth inspection.

## Mandatory 3-D validation

Before generation, Codex must validate each proposed point against:

`House02/OccupancyGrid3D.csv`

at the frozen source-height plane.

For every S1–S4 record:
- 3-D occupancy index;
- free/occupied status;
- local clearance if available.

### Fail-closed rule

If any proposal is invalid:
1. do not manually choose a replacement;
2. rerun a deterministic geometry-only selector that includes the actual 3-D occupancy constraint;
3. commit the new selector/output before any plume generation;
4. explain why the 2-D proposal failed.

## Generation contract

For each validated source:
- same House02 occupancy;
- same canonical wind directory;
- same gas parameters;
- two predeclared independent seeds;
- only source x/y changes.

This constitutes the first controlled `do(S=s)` intervention block for M4.
