# Coordinate-equivariant exploratory M1 screen

This is a diagnostic follow-up to the geometry-normalized screen. In addition
to map-extent normalization, the candidate scorer uses a fixed radial
compatibility kernel around a source location predicted from the source latent;
the candidate path cannot independently memorize House coordinates. The
implementation is in `experiments/ctpi_cstar/m1_picr/model.py` and is not
enabled by the production configuration.

Command:

```text
D:\Anaconda\python.exe -X utf8 experiments/ctpi_cstar/controlled_screen.py --out evidence/cstar_controlled_screen_20260907_geometry_equivariant --geometry-normalized --coordinate-equivariant
```

Result: `M1_CONTROLLED_SCREEN_NO_GO`.

| held-out House | PICR NLL | context-only NLL | label-permutation NLL | mechanism gate |
|---|---:|---:|---:|---|
| H01 | 8.033 | 8.122 | 8.854 | fail |
| H02 | 9.538 | 8.826 | 8.892 | fail |
| H03 | 10.716 | 10.896 | 11.795 | fail |

H01 and H03 show partial gains, but H02 is beaten by context-only and the
source-latent/uncertainty controls do not all pass in any fold. This is useful
failure attribution, not evidence that M1 is valid. No closed-loop run,
multiseed claim, or gate relaxation is authorized by this directory.
