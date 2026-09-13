# Dual-UAV House02 geometry parity and global route result

Date: 2026-09-13

Branch: `codex/dual-uav-two-point-premise-20260913`

Starting contract SHA: `ca730377c29e9518832b54b4984139d49dd42ce0`

## Decision

```text
CUSTOM_OCCUPANCY_NATIVE_PARITY = PASS
TDIAG_A_NATIVE_BLOCKED_COUNT = 270
T_DIAG_A_IS_NOT_A_DEPLOYABLE_NAVIGATION_ROUTE = TRUE
HOUSE02_2M_GLOBAL_FEASIBILITY = PASS
SOURCE_BLIND_FORMATION_ROUTE = PASS
HOUSE02_DUAL_LARGE_UAV_TESTBED = GEOMETRY_PASS
```

The earlier `r_max=1.8 m` result remains valid only for the historical `T_diag_A` path. It is invalid as a whole-House02 limit because that path contains 270 native-nonfree points and the previous custom parser also differed from native GADEN at negative outside-boundary coordinates.

## G0: authoritative parity

The native helper uses `gaden::Environment::ReadFromFile`, `coordsToIndices`, and `at`. The corrected Python reader matches it at all 3,044 deterministic probes, including 1,536 grid-cell centers. The only code correction was replacing mathematical floor with the truncation-toward-zero rule used by the native GLM integer conversion. A regression self-test fixes this boundary behavior.

Native GADEN reports 270/750 blocked samples on `T_diag_A` and 272/750 on `T_diag_B`. These are diagnostic query paths rather than deployable navigation routes.

## G1: whole-map 2 m aperture

At altitude 0.4 m, with a fixed 2.0 m receiver separation, 5 degree orientation grid, and a free centerline corridor:

- free center cells: 6,704;
- formation-feasible center cells: 4,958 (73.956%);
- connected components: 2;
- largest component: 4,942 cells, 49.42 square metres.

The result is explicitly `POINT_RECEIVER_WITH_FREE_CENTERLINE_CORRIDOR`. It proves the offline receiver geometry required by this premise test; it does not certify two full rotor footprints or real-flight separation control.

## G2: source-blind formation route

The route uses only occupancy, connectivity, fixed altitude, the pre-existing 0.35 m/s cadence, and pre-existing deployable wind columns. It never reads gas, source identity, posterior, localization error, or response features.

The deterministic largest-component DFS produces a 150 s, 750-sample center route. For each of three winds, the baseline orientation is the geometrically feasible 5 degree angle nearest the frozen cross-wind direction. Exact post-serialization validation reports:

- 5,250 center/endpoint native queries, zero non-free or parity failures;
- 2,250 receiver pairs, zero separation errors;
- 2,250 centerline corridors, zero failures.

The geometry is therefore eligible for a dedicated pre-gas freeze commit. Same-frame gas access remains forbidden until that commit is present on the remote branch.

## Pre-registered downstream decision

The primary structural representation is the signed increment `z_plus-z_minus`; squared structure is reported as a secondary diagnostic. Source observability must pass rank 3 and `sigma3/sigma1 >= 0.05` separately in every wind. Source identity uses only `W_fast` and `W_slow` to form standardized nearest-centroid prototypes and evaluates `W_altfast` as an internal development holdout. Position swap, 5 s time mismatch, collapsed baseline, and same-data ordinary D2 remain mandatory controls. These rules are frozen in `ANALYSIS_POLICY_FREEZE.json` and `tools/evaluate_two_point_premise.py` before any plume value is queried.
