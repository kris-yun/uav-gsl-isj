# Gate 1A Preflight — 2026-09-24

Status: **PREFLIGHT PASS; EXACT-PHYSICS BATCH NOT YET EXECUTED**

Branch: `research/causal-biorthogonal-green-v1`

## Frozen checks completed

### W2 target provenance

The development targets are the frozen real-GADEN cells:

- `S2_W2_A`: source `(-4.342730045, 2.899120331, 0.20)`, W2
  `3,5-1_slow`, RNG seed `2026092301`;
- `S2_W2_B`: same source and wind, RNG seed `2026092302`.

Both contain 10 exact GADEN spatial slices of shape `[10,83,119]`.

### Existing HCMC trajectories are NOT W2

The two HCMC House02 replay logs
`H02_R2026092211` and `H02_R2026092212` explicitly load
`wind_simulations/3,5-1_fast`.

They are therefore W1 evidence and are excluded from the W2 Gate-1A decision.
This prevents mixing a W1 trajectory contract with W2 plume claims.

### Arbitrary-source bank

Frozen PMFS manifest:
`H02_R2026092212/context_bank/source_update_0001/candidate_manifest.csv`.

Verified counts:

- quadtree leaves: **164**;
- deduplicated 0.30 m PMFS support cells before occupancy filtering: **631**;
- free support cells at z=0.20 m: **630**;
- occupied rejected support cells: **1**;
- exact S2 support cell: **(3,34)**;
- exact S2 support coordinate:
  `(-4.342730000..., 2.899120000..., 0.20)`;
- corresponding GADEN fine-grid cell: **(10,103,12)**.

Thus the first physical source-rank test is over 630 arbitrary source
coordinates, not the two S1/S2 training interventions.

### Source-blind observation bank

The frozen 5x6 equal-area closest-free probe layout contains 30 unique points.
Together with the 10 frozen W2 snapshots this yields exactly 300 observations
per independent target realization.

Probe construction uses occupancy only and is source/plume blind.

## Frozen exact-physics predictor

Prediction seeds are fixed before running any rank:

- `2026092401`;
- `2026092402`.

They are distinct from target A/B seeds.

For every one of the 630 free source cells, the verified GADEN binary will run
the exact same W2 physics and frozen simulator parameters. Only the source
coordinate and prediction RNG seed change.

Raw realizations are streamed through the verified spatial extractor; only the
300-point probe vector and provenance hashes are retained.

## Decision rule already frozen

Primary source score:
raw-ppm normalized SSE, with no amplitude or offset fitting.

Gate 1A PASS requires on **both** S2_W2_A and S2_W2_B:

- mean(C,D) truth rank <= 3;
- C-only truth rank <= 10;
- D-only truth rank <= 10.

Otherwise:

`GATE1A_FAIL_STOP_SOURCE_TO_SENSOR_GREEN_FAMILY`.

No parameter may be altered after seeing ranks.
