# Critical M6 interface correction — exact GeoPT contract

Date: 2026-09-23

The exact released GeoPT contract is:

- `space_dim=3`: explicit positional argument `pos3=[x,y,z]`;
- `fun_dim=11`: `fx11=[x,y,z,SDF,dir3,dynamics4]`;
- the model concatenates them internally;
- pretrained `preprocess` therefore sees **14 dimensions**.

For gas:

`pos3=[x,y,z]`

`fx11=[x,y,z,wall_SDF,wall_dir_x,wall_dir_y,wall_dir_z,wind_dir_x,wind_dir_y,wind_dir_z,wind_speed]`

Candidate source does **not** add raw channels. It enters after the pretrained projection through the Source Injection Adapter.

This supersedes any earlier shorthand saying “11-D total input.”

M6 feasibility conclusion is unchanged: `space_dim=3` and `fun_dim=11` can be preserved exactly.
