# E2C-R1 pre-run freeze

This file freezes the source panel, seed matrix, roles and implementation **before the first of the 120 new simulations**. It is an asset/geometry decision, not a scientific result.

## Acquisition

- Reuse one canonical E2 wind per House: H01 `1,3-2,4_fast` (E0), H02 `3,5-1_slow` (E1), H03 `1-2,5_fast` (E5).
- Reuse the original six E1/E2 sources per House and four existing E2 seeds/source. The E2 cubes and run metadata already passed 168/168 SHA256 checks in XHOC-R0.
- Continue the E1 geometry-only farthest-anchor/adjacent-partner rule to select pair four: H01 `pmfs_2_36` / `pmfs_3_36`; H02 `pmfs_26_35` / `pmfs_25_35`; H03 `pmfs_41_1` / `pmfs_41_2`. Recomputing the first three pairs from occupancy/navigation geometry matched all E1 source IDs and xyz exactly.
- New seed formula: `2026290000 + 10000*house_index + 100*source_index + replicate_index`, with H01/H02/H03 indices 0/1/2, source indices 0–7, old-source new replicate indices 4–7 and new-source indices 0–7. All 120 seeds are unique, below 2³¹ and disjoint from the inspected E2, JTD E2 and AOD F1 seed manifests. A rerun with an old seed is not a new independent realization.
- Reuse the original E2 GADEN executable, parameters, wind files, occupancy, native concentration extractor, E1 30-probe geometry and 2×2 pooling. The ten requested records are IDs 100–550, with physical clock and active wind index specified in `evidence/e2c_r1/TIMEBASE_MAP.csv`.
- Keep 120 new cubes, per-run metadata and extracted vectors. E2C runner calls the original E2 `run_one()`; extraction applies the original E2 2×2 mean formula. The original E2 files are never overwritten.

## Frozen roles

| House | Old six | New pair |
| --- | --- | --- |
| H01 | 6×8 DISCOVERY | 2×8 SEALED_WITHIN_HOUSE_CONFIRMATION |
| H02 | 6×8 DISCOVERY | 2×8 SEALED_WITHIN_HOUSE_CONFIRMATION |
| H03 | 6×8 SEALED_EXTERNAL_HOUSE_CONFIRMATION | 2×8 SEALED_EXTERNAL_HOUSE_CONFIRMATION |

There will be 72 reused canonical E2 runs plus 120 new runs = 192 source–realization rows. The two H01/H02 new-source sets and all H03 scientific values remain sealed through benchmark construction. Source is the scientific unit; nested seeds, reextractions and probes are not extra sources.

## Historical-exposure limitation discovered before generation

`evidence/e2c_r1/PRIOR_EXPOSURE_AUDIT.json` records metadata-only overlap: **all eight H03 source IDs** were already in the prior AOD F1 truth panel, and H02's new `pmfs_26_35` was already in R0. No outcomes were read for this pre-run check. Thus the E2C observation arrays can be kept sealed, but neither H03 as a House nor all proposed confirmation source identities are historically untouched. This audit does not alter geometry-based source selection or use performance to substitute another source. Future claims must call the protected material an **E2C dataset holdout** and disclose historical House/source exposure. An entirely untouched-House confirmation would require a separate design and authorization.

## Runtime/storage boundary

The new output root is `/home/zyc/ros2_ws/e2c_r1_120_runs_20260929`. At preflight the VM root had 234,975,232 bytes free. The final cube/metadata bank is expected to be about 50 MiB from E2's measured 70 MiB for 168 retained runs, while each temporary native realization is deleted only after its concentration cube and hashes pass the original E2 checks. The runner stops if free space before a run is below 100 MiB. No old asset is deleted or overwritten.

## Frozen machine-readable files

- `evidence/e2c_r1/TIMEBASE_MAP.csv`
- `evidence/e2c_r1/TIMEBASE_PROVENANCE.json`
- `evidence/e2c_r1/SOURCE_PANEL_8x3.tsv`
- `evidence/e2c_r1/SOURCE_PANEL_SELECTION_AUDIT.json`
- `evidence/e2c_r1/SEED_MANIFEST_120.tsv`
- `evidence/e2c_r1/SPLIT_MANIFEST.tsv`
- `evidence/e2c_r1/PRE_RUN_ASSET_SHA256.tsv`
- `evidence/e2c_r1/PRE_RUN_FREEZE.json`
- `evidence/e2c_r1/PRIOR_EXPOSURE_AUDIT.json`

No Ordinal, AOD, CENTERED, TCMA, AEC or other mechanism was scored during this freeze.
