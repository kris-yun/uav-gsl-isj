# Exact-source posterior-consistency exploratory screen

This diagnostic adds symmetric KL consistency between the final source
posteriors of each exact-source transport pair. The existing latent-distance
penalty is retained; the new term prevents a nonlinear candidate head from
reintroducing transport-specific variation after the latent representation.

Command:

```text
D:\Anaconda\python.exe -X utf8 experiments/ctpi_cstar/controlled_screen.py --out evidence/cstar_controlled_screen_20260907_geometry_pair_consistent --geometry-normalized --coordinate-equivariant --paired-posterior-consistency
```

Result: `M1_CONTROLLED_SCREEN_NO_GO`. The H01/H02 PICR scores were still not
better than the required controls; H03 improved only partially. This term is
not enabled by the production configuration and does not authorize a closed
loop.
