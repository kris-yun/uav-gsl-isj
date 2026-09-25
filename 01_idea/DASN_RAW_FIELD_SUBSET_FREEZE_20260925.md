# DASN/Meandering Raw-Field Subset Freeze — 2026-09-25

Status: **RAW-FIELD RETRIEVAL ONLY; NO NEW GADEN RUN**

Purpose:
test whether the reproducible shared localization error left by DASN is better explained by a coherent spatial plume-deformation/meandering mode.

The current 10x30 pooled probe contract cannot identify a spatial deformation field.
Therefore retrieve a small pre-frozen subset of existing D1R full concentration cubes.

## Selection rule

Only the 143 non-boundary D1R sources were eligible.

Sources were selected deterministically by farthest-point sampling in standardized:

- source x;
- source y;
- log(1+median total mass);
- first8/last8 raw-mean relative L2;
- median zero fraction.

Start point = source nearest the multivariate feature center.
Then repeatedly add the point maximizing minimum squared standardized distance to the already selected set.

No cube outcome was inspected for this selection.

## Frozen 8 sources

| panel_index | source_id | pmfs_i | pmfs_j | x_m | y_m | split raw rel-L2 | median mass | zero frac |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
|114|pmfs_17_14|17|14|-0.14273|-3.10088|0.157215|119.5600|0.786667|
|156|pmfs_23_14|23|14|1.65727|-3.10088|0.992740|53.3586|0.821667|
|131|pmfs_19_17|19|17|0.45727|-2.20088|0.027101|941.9911|0.695000|
|35|pmfs_6_12|6|12|-3.44273|-3.70088|0.645229|80.6295|0.803333|
|159|pmfs_23_17|23|17|1.65727|-2.20088|0.218024|531.1556|0.821667|
|20|pmfs_3_18|3|18|-4.34273|-1.90088|0.269615|118.0521|0.821667|
|164|pmfs_24_15|24|15|1.95727|-2.80088|0.639190|124.1498|0.841667|
|107|pmfs_16_14|16|14|-0.44273|-3.10088|0.191095|189.4645|0.663333|

Retrieve all 16 existing D1R realizations/source:

8 x16 = **128 full cubes**.

Each expected cube shape:
`(10,83,119)`.

No simulation regeneration is permitted.

## What this subset may answer

A future raw-field mechanism screen may test:

- coherent spatial translation/deformation across time;
- plume-centroid/meandering modes;
- low-dimensional spatial deformation versus amplitude-only changes;
- whether deformation parameters predict the odd/even shared localization error.

It must NOT be used to retrospectively choose the eight sources.

If the existing VM files are unavailable, do not rerun GADEN automatically.
Report missing raw assets first.
