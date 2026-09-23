# CRITICAL GeoPT interface correction — pos3 + fx11, not 11 total dimensions

Date: 2026-09-23

## Exact released contract

The released GeoPT fine-tuning path uses:

- `space_dim = 3`;
- `fun_dim = 11`.

The downstream loader provides a 7-D geometry feature

`[x,y,z,SDF_or_0,dir_or_normal_x,dir_or_normal_y,dir_or_normal_z]`

and `GeoPT_finetune.py` appends the 4-D dynamics field, producing **fx11**.

Then the model is called as:

`model(x[:, :, :3], fx11)`

and `Transolver.forward()` concatenates them again before `preprocess`.

Therefore the pretrained input projection sees:

`pos3 + fx11 = 14 dimensions`.

The xyz coordinates intentionally appear:
1. once as the explicit positional input;
2. again inside the 7-D geometry part of fx11.

## Correct gas mapping

Use:

- `pos3 = [x,y,z]`
- `fx11 = [x,y,z, wall_SDF, wall_dir_x, wall_dir_y, wall_dir_z, wind_dir_x, wind_dir_y, wind_dir_z, wind_speed]`

Then call the unchanged pretrained projection with:

`cat(pos3, fx11)` -> 14 dimensions.

## Consequence

This correction does **not** weaken the M6 transfer argument.

It strengthens the implementation rule:

> preserve both `space_dim=3` and `fun_dim=11` exactly as released.

Do not add source coordinates to either raw input.

Candidate source still enters only through the post-projection Source Injection Adapter.

Any earlier branch wording that says “GeoPT total input is 11-D” is superseded by this file.
