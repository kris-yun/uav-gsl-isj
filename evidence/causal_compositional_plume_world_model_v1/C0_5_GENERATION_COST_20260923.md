# C0.5 real-GADEN generation-cost benchmark

Date: 2026-09-23

## Contract and provenance

The benchmark used the frozen House02 source intervention `S1`, wind `W1`, and
plume seed `2026092301`:

- source: `(-2.242730141, -2.200880051, 0.20) m`;
- wind: canonical `3,5-1_fast` field;
- occupancy SHA-256:
  `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`;
- `wind_iteration_0` SHA-256:
  `35c2b2d3f5d059f8f219befb75bc51c6154bb573d9a298d9a75c4c7e03d8e88f`;
- simulator SHA-256:
  `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`.

The ROS and HCMC overlays were sourced before execution. The command used the
standalone filament simulator with `writeConcentrations=false` and a 0.5 s
result interval. Each run ended with the literal success message
`Filament simulator finished correctly!`; the compact raw logs are under
[`c0_5_generation_cost_benchmark_20260923/`](c0_5_generation_cost_benchmark_20260923/).
The full generated realization files remain at the immutable VM root
`/home/zyc/c0_5_cost_benchmark_20260923` and are not copied into Git.

## Measurements

| Simulated time | Wall time | User CPU | System CPU | CPU utilization | Peak RSS | Iteration files | Realization bytes |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 s | 0.89 s | 4.41 s | 0.19 s | 512% | 89,560 KB | 58 | 34,005,248 |
| 120 s | 0.88 s | 5.12 s | 0.21 s | 604% | 89,656 KB | 209 | 35,186,904 |
| 300 s | 1.89 s | 16.49 s | 0.29 s | 886% | 89,524 KB | 566 | 42,961,851 |

The simulator completed all three cases without an error. Active-filament count
was not emitted by this benchmark script, so no active-count claim is made.

## Duration decision

`300 s` is selected for C0.5. It is inexpensive on the verified binary and
matches the project's evaluation horizon while producing 566 saved snapshots.
This choice was made before any model or source-rank result and uses no plume
truth. The benchmark is a cost/infrastructure gate only; it is not a spatial
plume or M4 model result.

Machine-readable measurements are in
[`C0_5_GENERATION_COST_20260923.json`](C0_5_GENERATION_COST_20260923.json).
