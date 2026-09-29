# E2C-R1 source-unseen confirmation pre-run freeze

Status: **AUDIT AND FREEZE ONLY — ZERO NEW GADEN RUNS.** This document supersedes
the 120-run source panel and seed manifest, while preserving the original freeze
and pause decision as historical records.

## Exposure precedes selection

The prior-source union was committed at `674da79f`, before the replacement
selector ran. Its SHA256 is
`9b6995bdcdffbdc99f593982b77a4b966ae84d33c45dfa45734a203131053527`.
It contains 6 House01, 192 House02 and 12 House03 source IDs from executed
truth/source/validation panels and metadata-only case records. The 55 local Git
branch heads were independently scanned for small source-panel and target
manifests; no additional `(House, source_id)` pair was found. Full candidate
support banks were intentionally excluded: merely being a hypothetical
candidate is not source-location exposure.

The selection code reads occupancy, Native navigation mask, E1 geometry code,
the old E1 source panel and the frozen union. It reads no concentration, score,
rank, posterior, Top-1 or model outcome. The first three E1 source pairs and
coordinates reappeared exactly under the original geometry code.

## Replacement confirmation panel

The H01/H02 discovery sources remain the original six per House. They reuse
four E2 realizations and receive four new realizations each. The source-unseen
confirmation cells are:

| House | New adjacent source pairs |
| --- | --- |
| H01 | `pmfs_2_36`, `pmfs_3_36` |
| H02 | `pmfs_25_35`, `pmfs_25_34` |
| H03 | `pmfs_40_1`, `pmfs_40_2`; `pmfs_12_26`, `pmfs_12_25`; `pmfs_15_1`, `pmfs_14_1`; `pmfs_30_26`, `pmfs_30_25` |

All 12 confirmation source IDs are absent from the committed exposure union.
Each pair has adjacent 0.30 m PMFS cells, a valid Native navigation cell and a
free House-specific 3D occupancy voxel at `z_source=0.20 m`.

The H03 selection starts from the three old E1 geometric anchors and chooses
four new pairs sequentially using the E1 farthest-anchor and adjacent-partner
rule, with exposed cells excluded. The old H03 six-source E2 assets stay sealed
as historically exposed auxiliary data; none enters the revised eight-source
confirmation panel.

## Data and execution contract

- H01: 24 new discovery runs + 16 new source-unseen confirmation runs = 40.
- H02: 24 + 16 = 40.
- H03: 8 new source-unseen cells × 8 realizations = 64.
- Total: **144 new runs**, plus 48 existing H01/H02 E2 discovery runs, yielding
  192 common-contract source–realization rows.
- Seed: `2026290000 + 10000*house_index + 100*source_index + replicate_index`,
  with House indices H01/H02/H03 = 0/1/2. Discovery uses new replicate indices
  4–7; confirmation uses 0–7. The 144 seeds are unique and do not overlap the
  inspected E2, JTD E2 or AOD F1 seeds.
- Execution output root, if separately authorized later:
  `/home/zyc/ros2_ws/e2c_r1_144_runs_20260929`.
- House-specific canonical wind, E1 30 source-blind probes, 2×2 footprint,
  original E2 extractor and ten writer record IDs remain fixed. Record ID is
  **not** physical seconds; see `TIMEBASE_MAP.csv` and provenance.
- H01/H02 confirmation and all H03 scientific values remain sealed. H03 as a
  House has been studied historically, so the eventual claim is source-unseen
  House03 common-contract confirmation, not a wholly unseen environment.

`SOURCE_PANEL_8x3.tsv`, `SOURCE_PANEL_SELECTION_AUDIT.json`,
`SEED_MANIFEST_144.tsv`, `SPLIT_MANIFEST.tsv`,
`CONFIRMATION_SOURCE_UNSEEN_AUDIT.tsv`, `PRE_RUN_ASSET_SHA256.tsv` and
`PRE_RUN_FREEZE.json` are the machine-readable freeze. The old
`SEED_MANIFEST_120.tsv` remains archived in Git history and is not executable
under the revised 144-run runner.

**Stop here.** This freeze does not authorize a GADEN run or any scientific
mechanism analysis.
