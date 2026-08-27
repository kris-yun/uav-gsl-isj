# CG-PC-CTT V3 geometry-information addendum — 2026-08-27

Status: theory refinement; no frozen V2 threshold or evidence is changed.

## 1. Do not equate observation count with source information

The sparse-support diagnostics use random feature subsets only to expose rank loss. They do **not** define a rule such as `Q>=16 => identifiable`.

Actual UAV samples are spatially correlated along a trajectory. The online object must therefore be the information matrix computed on the actual causal observation support `H_t`, not raw visit count.

A repeated StopAndMeasure block can enrich the sensor outcome `Y` but does not create new independent spatial source directions by itself.

## 2. Intrinsic source-support dimension

The nominal source coordinate is `(x,y)`, but local feasible source support can become nearly one-dimensional near narrow corridors, obstacles, or irregular candidate boundaries.

Let local physical displacements around source class `s` be rows of `DX_s`. Define

`d_geo(s) = rank(DX_s)`

with a frozen numerical geometry tolerance independent of outcomes.

The response should be judged against this physical dimension. A future refined criterion is:

- if `d_geo=2`, require two replicated positive source-information directions;
- if `d_geo=1`, require the single feasible tangent direction, and do not manufacture an impossible transverse requirement;
- if the local geometry itself is numerically degenerate or poorly conditioned, report `GEOMETRY_LIMITED` rather than `TRANSPORT_UNIDENTIFIABLE`.

This is conceptually aligned with geometry-aware inverse imaging: infer only directions supported by the physical source manifold.

## 3. Geometry-conditioning audit

For a local source neighborhood define

`G_s = DX_s^T DX_s`.

Record `cond_geo(s)=lambda_max(G_s)/lambda_min_positive(G_s)`.

High `cond_geo` means the fitted local response Jacobian is sensitive to candidate-layout anisotropy. The tangent-information statistic must not silently attribute that instability to plume physics.

On the recovered House02 V12 201-carrier grid:

- all Delaunay local neighborhoods have geometry rank 2;
- median `cond_geo` is approximately `1.89`;
- 90th percentile approximately `4.45`;
- 95th percentile approximately `13.63`;
- 99th percentile approximately `35.76`;
- maximum approximately `117.44`.

Therefore most source neighborhoods are well-conditioned, but a small boundary/irregular tail needs an explicit geometry audit.

## 4. Binding interpretation of the OSDR-inspired block marker

The within-stop dynamic marker is an **outcome-richness** mechanism:

`Y_e = [logc_mean, logc_sd, hit_fraction, temporal_slope]`.

It can improve sensor/bridge adequacy with few spatial stops, but it does not by itself repair a missing second spatial source direction. Spatial resolution remains governed by `H_t` and local source geometry.

## 5. Runtime rule

Never use a fixed minimum number of visits as the primary identifiability gate. Use:

`actual trajectory/event support -> H_t response ensemble -> local geometry audit -> replicated tangent information -> quotient/abstain`.
