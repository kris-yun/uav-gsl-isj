# Sparse-event source-pooling exploratory screen

This diagnostic uses a fixed causal event-weighted pool: measured log-gas is
used as a non-learned attention weight so long zero-gas prefixes do not dilute
plume-bearing frames. It preserves the same causal mask and does not inspect
future frames, source truth, or banks.

Command:

```text
D:\Anaconda\python.exe -X utf8 experiments/ctpi_cstar/controlled_screen.py --out evidence/cstar_controlled_screen_20260907_geometry_event_pool --geometry-normalized --coordinate-equivariant --event-weighted-source-pool
```

Result: `M1_CONTROLLED_SCREEN_NO_GO`.

| held-out House | PICR NLL | context-only NLL | unconstrained NLL | mechanism gate |
|---|---:|---:|---:|---|
| H01 | 8.067 | 8.122 | 8.049 | fail |
| H02 | 8.935 | 8.826 | 9.573 | fail |
| H03 | 10.483 | 10.896 | 10.555 | fail |

The H02 score improved, but context-only still wins; no fold passes all
causal controls. The option remains exploratory and does not authorize a
closed loop.
