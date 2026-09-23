# M6 G1-B compact sampler proof — one source, two plume seeds

Date: 2026-09-23  
Protocol commit: `2d894a0` (sampler fixes `adda39b`, `157476b`, `7b7c9a8`,
`f10c965`)  
Status: **ENGINEERING PROOF PASS; FULL PILOT NOT YET STARTED**

## Scope

Before expanding to the frozen 12-source bank, the compact sampler was run for
the first pre-registered training source (`train1`, source
`(-1.942730188369751,-1.300879955291748,0.20)`) with two process-level seeds:
`2026092311` and `2026092312`. No model, truth-source rank, or closed-loop
output was read. The second run is therefore an independent realization check,
not a model-selection result.

## Runtime and provenance

- Host: `zyc-virtual-machine`, ROS2 Humble.
- Occupancy: House02 `OccupancyGrid3D.csv`, SHA256
  `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`.
- Wind: House02 `3,5-1_fast`, `wind_iteration_0` SHA256
  `35c2b2d3f5d059f8f219befb75bc51c6154bb573d9a298d9a75c4c7e03d8e88f`.
- Free-token grid: `G1_HOUSE02_GRID_GEOMETRY_20260923.csv`, SHA256
  `F30C7DE2EA892120B70411EDB7187F2769246896152F9BB9B8181E15F749A397`,
  1053 rows / 631 free rows.
- Seeded filament binary SHA256:
  `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`.
- Seeded `libgaden.so` SHA256:
  `aca55af4e39831f97c1480bb31c014eb06294ced8a71329c3aa216e6cf7991a8`.
- Audited source patch SHA256:
  `50f04ec609157189d3f9fed72a87e6729c0b66691fcaee8da6864d9194575278`.
- `GADEN_RNG_SEED` was set before each process; no in-process reseeding.

## Fixed field contract and output dimensions

The sampler used the frozen source/sensor planes (`z=0.20/0.30`), strict
`C>0.1`, 300 s horizon, 50 s burn-in, and 1 Hz samples `50,...,299`.
Both seeds returned `G1B_SAMPLER_OK`, 250 primary samples, and 631 free tokens.
Each case writes a 157,750-byte `(250,631)` `hit_samples_u8.bin`, six compact
float32 maps, and metadata; no filament or full-volume files are produced.
The first two runs took 2.35 s and 2.31 s wall time respectively (about 73.6
MiB peak RSS); each retained the full compact output manifest.

## Seed-control evidence

Primary `hit_frequency_f32.bin` hashes:

| run | SHA256 |
|---|---|
| seed `2026092311` | `e470eb07ecc1f08f7f28aeb3bfc5af982ad1806e8e8ca236ae79850efd63eae9` |
| seed `2026092312` | `a49742ecbc080df6a07e763317fac0ffe2a569491a816383363b3b6fc7c2b037` |
| same-seed replay `2026092311` | `e470eb07ecc1f08f7f28aeb3bfc5af982ad1806e8e8ca236ae79850efd63eae9` |

The same-seed replay is byte-identical for both `hit_frequency_f32.bin` and
`hit_samples_u8.bin` (the latter hash is
`621b684e9cf307246e6a1e3e6aba65aea1ece9f47120126b3170f130963f494`). The
second seed differs (`hit_samples_u8.bin` hash
`f0bf975e3169753cf7ca7db23aa5aa5b2f0f2d18ee8e4ced87e62efb6dcb841f`). This
satisfies the process-level
same-seed reproducibility / different-seed divergence requirement.

The two primary maps are nontrivial runtime outputs (means 0.2338 and 0.2648,
with 264 and 278 nonzero tokens respectively); these values are descriptive
only and are not a source-rank result.

## Decision

`G1-B COMPACT SAMPLER PROOF = PASS` for engineering, dimensions, fixed
contract, compact storage, and seed control. This authorizes expansion to the
pre-registered 12 sources × 2 seeds. It does **not** authorize G1-C training,
truth-source rank inspection, or any closed-loop run until the complete bank
manifest is frozen and committed.
