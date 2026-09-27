# House03 source-panel freeze

## Existing geometry anchors

House03 already has three E1 geometry-selected 0.30 m neighbour pairs that
were selected without House03 gas outcomes:

- `pmfs_24_13` / `pmfs_24_14`
- `pmfs_1_4` / `pmfs_2_4`
- `pmfs_44_26` / `pmfs_43_26`

These six sources are retained as anchors.

## Add exactly three new pairs

Locate the canonical House03 source bank / geometry table containing all free
PMFS source candidates at `z=0.20 m`.

Required per source:
- source_id
- pmfs_i, pmfs_j
- x_m, y_m, z_m
- free-space status
- clearance_m if already available.

If no canonical source bank can be hash-verified, STOP:
`AOD_H03_F0_HOLD_SOURCE_BANK`.

Eligible pair:
- both sources are free;
- both z=0.20 m;
- PMFS grid indices differ by exactly one cell in x OR y and zero in the other;
- Euclidean center distance is 0.30 m within numeric tolerance;
- clearance for both >=0.30 m;
- neither source is already used by another selected pair.

The three existing E1 pairs are fixed first.

Select the next pair greedily by maximizing the minimum Euclidean distance from
its pair center to all already selected pair centers.

Tie-break:
ascending SHA256 of
`AOD_H03_F1_20260927|<canonical_source_a>|<canonical_source_b>`.

Repeat until 6 pairs total.

Do NOT use:
- gas data;
- forward score;
- rawu/u contrast;
- expected plume mass;
- hit probability;
- source rank;
- wind response.

After selection verify:
- 12 unique sources;
- 6 unique pairs;
- all pair distances 0.30 m;
- minimum pair-center separation >=1.50 m.

If fewer than six pairs satisfy all conditions, STOP:
`AOD_H03_F0_HOLD_PANEL_GEOMETRY`.

Freeze:
`HOUSE03_F1_SOURCE_PANEL_12.tsv`
plus source-bank SHA256 and selection log.
