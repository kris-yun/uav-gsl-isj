# M6 G0.7 — Pretraining-Semantics Alignment for Indoor Gas Tokens

Date: 2026-09-23  
Branch: `research/geopt-physics-foundation-pmfs-v1`

## Decision

`G0.7 = PRETRAINING SEMANTICS IDENTIFIED`

M6 should preserve not only GeoPT input dimensions but also the meaning of the pretrained channels as closely as possible.

## 1. Exact pretraining geometry channels

GeoPT pretraining builds interior volume features:

`[x, y, z, SDF, dir_x, dir_y, dir_z]`

where the direction is computed as:

`closest_boundary_point - volume_point`

normalized by the distance.

Therefore the pretraining-aligned direction points **from the free-space point toward the nearest surface/boundary**.

For M6 use the same sign convention:

`wall_dir(x) = (closest_wall(x) - x) / distance_to_wall(x)`

Do not silently use the opposite direction.

## 2. Exact pretraining dynamics channels

GeoPT pretraining condition:

`[move_dir_x, move_dir_y, move_dir_z, step_length]`

The move direction and step length are sampled per point.

Thus the pretrained backbone already supports **spatially heterogeneous pointwise dynamics conditions**.

This is important for GSL because indoor wind is a spatial vector field, not one global flow direction.

## 3. Gas dynamics mapping

For local wind vector `w(x)`:

If `||w|| > eps`:

`move_dir(x) = w(x) / ||w(x)||`

else:

`move_dir(x) = [0,0,0]`

Define:

`advective_step(x) = scale_geo * ||w(x)|| * tau_ref`

where:
- `scale_geo` converts world metres into the normalized GeoPT geometry coordinates;
- `tau_ref` is fixed from an experiment/simulation protocol, not truth-tuned.

The primary G1 prompt is:

`dynamics4 = [move_dir_x, move_dir_y, move_dir_z, advective_step]`.

Raw speed may be reported only as an ablation.

## 4. Coordinate-axis convention

GeoPT pretraining treats one axis as vertical/ground-normal after geometry alignment.

For a 2-D PMFS floor plane embedded in 3-D, use a deterministic y-up mapping.

Recommended convention:

- GeoPT X <- House world X;
- GeoPT Y <- physical vertical height;
- GeoPT Z <- House world Y.

Then a horizontal 2-D wind `[w_x, w_y]` maps to:

`w_geo = [w_x, 0, w_y]`.

The same rotation/permutation must be applied consistently to:
- coordinates;
- wall direction;
- wind vector;
- source coordinates.

Do not rotate geometry without rotating wind/source.

## 5. Geometry normalization

GeoPT normalizes geometries into a common scale.

For the first House pilot:
- use one fixed source-blind geometry scaling transform for the entire House;
- save the affine transform;
- apply it identically to all source positions and all plume realizations.

The advective step length must use the same spatial scale.

## 6. fx11 and pos3

After alignment:

`pos3 = [X_geo,Y_geo,Z_geo]`

`fx11 = [
 X_geo,Y_geo,Z_geo,
 wall_SDF,
 wall_dir_X,wall_dir_Y,wall_dir_Z,
 wind_dir_X,wind_dir_Y,wind_dir_Z,
 advective_step
]`

GeoPT then concatenates `pos3 + fx11` internally, giving the exact 14-D pretrained projection input.

## 7. Source injection

Candidate source remains outside raw inputs.

The source position is transformed by the same House affine map, then used by the post-projection Source Injection Adapter.

## 8. Required source-blind audits before training

Export distributions for House02:

- wall SDF;
- pretraining-aligned wall-direction components;
- wind direction;
- advective step length.

Compare advective step lengths against the GeoPT pretraining range.

If House values are far out of distribution:
- do not tune `tau_ref` using truth;
- report the mismatch;
- test a protocol-derived rescaling or mark M6 HOLD.

## 9. Important code discrepancy in GeoPT downstream preprocessing

Some released downstream preprocessing (e.g. DrivAerML) uses the opposite SDF direction sign from the pretraining generator.

Therefore:
- the checkpoint's pure pretraining semantics and downstream fine-tuning semantics are not perfectly identical;
- G1 should predeclare the **pretraining-aligned sign** as primary;
- the opposite sign may be included as a source-blind interface ablation, not selected by truth rank.

## 10. Current consequence

M6 is now defined by **semantic transfer**, not merely dimensional compatibility:

- boundary-aware volume geometry;
- pointwise directional displacement;
- candidate-source injection.

Status:

`READY FOR CODEX G0.5 ACTUAL LOAD + HOUSE TOKEN EXPORT`.
