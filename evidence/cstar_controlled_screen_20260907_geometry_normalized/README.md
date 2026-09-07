# Geometry-normalized exploratory M1 screen

This directory is a diagnostic rerun of the bounded M1 screen. It normalizes
history poses and candidate coordinates by each frozen House map extent from
`cstar_environment_20260906/maps_v1/geometry_manifest.json`. The original
`evidence/cstar_controlled_screen_20260907` result is unchanged and remains the
formal screen authority.

Command:

```text
D:\Anaconda\python.exe -X utf8 experiments/ctpi_cstar/controlled_screen.py --out evidence/cstar_controlled_screen_20260907_geometry_normalized --geometry-normalized
```

Result: `M1_CONTROLLED_SCREEN_NO_GO`. Proper NLL improved relative to the
previous coordinate convention, but the mechanism checks still failed. This is
not a closed-loop authorization and was not used to lower any gate.
