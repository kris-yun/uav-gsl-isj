# HOLD — source-position contract must be audited before E2C acquisition

Date: 2026-09-29

Status: **HOLD BEFORE SIMULATION — ZERO NEW GADEN RUNS**

The 144-run freeze selected previously unexposed PMFS free cells such as
`pmfs_2_36`, `pmfs_25_35`, and eight new House03 cells using an E1
geometry-only rule.

That is acceptable only if the authoritative GADEN dataset/scenario contract
explicitly permits source position to be freely parameterized at arbitrary
valid free cells.

The project owner has now clarified a stricter dataset constraint: source
locations may be defined by existing scenario/configuration assets rather than
freely selectable PMFS cells.

Therefore:
- DO NOT execute `SEED_MANIFEST_144.tsv`;
- DO NOT create the E2C 144-run data directory;
- DO NOT generate any new plume at a newly selected PMFS cell;
- preserve the 144-run freeze only as an audit record;
- first inventory the authoritative configured source positions for H01/H02/H03
  and determine which of those can support the common E2 acquisition operator.

If the configured source catalog is too small for a clean held-out source split,
report that limitation rather than inventing new source locations.

No scientific mechanism or innovation claim is changed by this HOLD.
