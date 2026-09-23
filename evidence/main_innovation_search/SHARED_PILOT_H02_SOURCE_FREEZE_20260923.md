# House02 Shared-Pilot Source Position Freeze

Date: 2026-09-23  
Parent contract: `SHARED_PILOT_M3_M4_M5_M6_DATA_CONTRACT_20260923.md`

## Status

`S1–S4 XY POSITIONS FROZEN SOURCE-BLIND`

3-D validity at source height must still be checked by Codex/GADEN before batch generation.

## 1. Input used

Only the House02 occupancy geometry from the exported PMFS grid was used.

No source-truth coordinates, source scores, gas measurements, hit probabilities, or localization outcomes were used in the selection objective.

Grid facts:

- full cells: 1053;
- layout: 27 × 39;
- free cells: 631;
- obstacle cells: 422;
- grid spacing: 0.3 m.

## 2. Eligibility rule

For every free 2-D cell, compute Euclidean distance to the nearest obstacle-cell center.

Require:

[
d_{m wall-center}ge 0.9 {m m}
]

which equals 3 PMFS grid cells.

This avoids deliberately selecting wall-adjacent source positions for the first pilot.

217 free cells satisfy the rule.

## 3. Deterministic space-filling rule

1. Compute the mean XY coordinate of all eligible cells.
2. Select the eligible cell nearest that mean as S1.
3. Iteratively select the point maximizing its minimum Euclidean distance to all already selected sources.
4. Break exact ties by smallest `cell_index`.

No random seed is needed.

## 4. Frozen XY positions

| ID | cell_index | grid_i | grid_j | x (m) | y (m) | nearest-obstacle-center distance (m) |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 523 | 10 | 19 | -2.242730 | -1.600880 | 0.900000 |
| S2 | 917 | 26 | 33 | 2.557270 | 2.599120 | 0.900001 |
| S3 | 1029 | 3 | 38 | -4.342730 | 4.099120 | 0.900000 |
| S4 | 84 | 3 | 3 | -4.342730 | -6.400880 | 0.900000 |

Pairwise XY distances:

- S1–S2: 6.3781 m;
- S1–S3: 6.0745 m;
- S1–S4: 5.2393 m;
- S2–S3: 7.0612 m;
- S2–S4: 11.3406 m;
- S3–S4: 10.5000 m.

Minimum pairwise spacing: **5.2393 m**.

## 5. Z-coordinate rule

Preferred pilot source height:

[
z=0.20 {m m}
]

to match the existing House02 source-height convention and hold source height fixed across the intervention study.

Codex must verify each ((x,y,0.20)) against the actual 3-D GADEN environment before simulation.

## 6. Predeclared invalid-point replacement rule

If a frozen XY source is not a valid free GADEN point at z=0.20:

1. search eligible PMFS free cells in increasing XY distance from the frozen location;
2. require the same 0.9 m 2-D obstacle-center margin;
3. choose the first cell that GADEN verifies free at z=0.20;
4. tie-break by smallest cell_index;
5. document old/new coordinates and reason before any plume simulation.

Do not choose a replacement using gas dispersion, hit maps, or localization performance.

## 7. One-source benchmark

Use **S1** first for the one-source GADEN-RT generation-cost benchmark unless S1 fails the 3-D validity check.

Do not launch S2–S4 until the S1 benchmark passes.

## 8. Wind conditions

W1/W2 remain unfrozen until Codex audits the House02 GADEN wind configurations.

Priority:
1. two existing physical wind configurations;
2. two distinct replayable physical wind regimes;
3. only if unavailable, a predeclared speed scaling of W1 preserving topology.

Do not rotate the indoor vector field arbitrarily.

Status:

`SOURCE FACTOR FROZEN; WIND FACTOR PENDING PHYSICAL CONFIG AUDIT`.
