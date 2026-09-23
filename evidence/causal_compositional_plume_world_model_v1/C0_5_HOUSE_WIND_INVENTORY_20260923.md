# C0.5 House and same-geometry wind inventory

Date: 2026-09-23
Branch: `research/causal-compositional-plume-world-model-v1`
Audit type: source-blind read-only inventory on the VM

## Decision

The hard stop is **not triggered**. House02 has two complete, finite, physically
stored GADEN wind fields under the same occupancy geometry. The selected pair
is:

- `W1 = 3,5-1_fast`
- `W2 = 3,5-1_slow`

No wind rotation or numerical speed scaling was applied. The two fields are
read directly from their canonical GADEN `wind/` directories.

The complete machine-readable audit, including every iteration hash, is
[`C0_5_HOUSE_WIND_INVENTORY_20260923.json`](C0_5_HOUSE_WIND_INVENTORY_20260923.json)
(SHA-256
`dec3b877783b606fc3bd1fceaa06acb32e6616b2cae2d2f2e2f7f52fc4ed71fb`).

## 1. Source-blind House audit

All three Houses were inspected before any C0.5 plume result or source-rank
metric was read. The occupancy files and canonical wind directories were read
from:

`/mnt/hgfs/workspace/GADEN_files/scenarios/`

| House | Occupancy dimensions (x × y × z) | Occupancy SHA-256 | Complete canonical wind configurations | Cells per wind field |
|---|---:|---|---|---:|
| House01 | 87 × 114 × 33 | `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb` | `1,3-2,4_fast`, `1,3-2,4_slow`, `2,4-1_fast`, `2,4-1_slow` | 327,294 |
| House02 | 83 × 119 × 26 | `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d` | `3,5-1_fast`, `3,5-1_slow`, `4,5-3_fast`, `4,5-3_slow` | 256,802 |
| House03 | 138 × 83 × 25 | `ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af` | `1-2,5_fast`, `1-2,5_slow`, `5-3_fast`, `5-3_slow` | 286,350 |

Every listed configuration contains `wind_iteration_0` through
`wind_iteration_10` (11 files). Each House's binary field size is exactly
`3 × cell_count × sizeof(double)`, which matches GADEN's legacy triple-array
reader. All decoded values are finite. House02 was selected by the predeclared
geometry-only cost rule because it has the smallest complete field among the
three eligible Houses; this did not use a source, truth, plume, or PMFS score.

## 2. Selected W1/W2 physical fields

| ID | Canonical wind directory | Iterations | Bytes/iteration | Min speed (m/s) | Median (m/s) | Max (m/s) | P95 (m/s) | Nonzero fraction | Mean speed-weighted direction |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W1 | `House02/gas_simulations/3,5-1_fast/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind` | 11 | 6,163,248 | 0 | 0.0359376 | 1.13357 | 0.319220 | 0.684329 | −118.464° |
| W2 | `House02/gas_simulations/3,5-1_slow/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20/wind` | 11 | 6,163,248 | 0 | 0.0145863 | 0.990601 | 0.146744 | 0.684329 | −120.900° |

Both directories use the same House02 occupancy hash, grid dimensions, gas
type, and source metadata. The field comparison over all 11 iterations gives:

| Check | Result |
|---|---:|
| Common iterations | 11 |
| Byte-identical iterations | 1 (the initial field only) |
| Max absolute component difference | 1.032032 m/s |
| Mean absolute component difference | 0.0214427 m/s |
| Components differing by >1e−12 | 62.2115% |
| Component correlation over all iterations | 0.914010 |

The initial equality is retained as evidence; it is not relabeled as an
independent difference. Iterations 1–10 are byte-distinct. All individual
iteration SHA-256 values for W1 and W2 are in the JSON audit.

## 3. Predeclared source interventions

The source positions were frozen by the earlier geometry-only deterministic
selector and were validated against the actual House02 3-D occupancy before
generation:

| ID | x (m) | y (m) | z (m) | GADEN cell index (x,y,z) | Cell state | Nearest nonfree distance |
|---|---:|---:|---:|---|---|---:|
| S1 | −2.242730141 | −2.200880051 | 0.20 | (31, 52, 12) | Free (0) | 0.50 m |
| S2 | −4.342730045 | 2.899120331 | 0.20 | (10, 103, 12) | Free (0) | 0.80 m |

The source-to-source distance is 5.515433 m. The validation JSON is
[`C0_5_SOURCE_VALIDATION_20260923.json`](C0_5_SOURCE_VALIDATION_20260923.json)
(SHA-256
`75ea97b3260d1fbbfd794f1db290361c3f90912a5fdcbd092c5dc810040bc332`).

## 4. Gate boundary

The same-geometry physical-wind prerequisite is satisfied for House02. The
next authorized step is the one-source 30/120/300 s generation-cost benchmark.
No 8-realization bank, model fitting, or PMFS source-rank evaluation is
included in this inventory checkpoint.
