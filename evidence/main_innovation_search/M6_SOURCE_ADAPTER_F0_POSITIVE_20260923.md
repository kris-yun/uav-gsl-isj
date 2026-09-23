# M6 source adapter F0 positive

Date: 2026-09-23

M6's PMFS-specific source conditioning now has a concrete minimal implementation.

- adapter: 4 -> 64 -> 256;
- parameters: 16,961;
- only ~0.439% of the 8-layer GeoPT parameter count;
- zero-initialized scalar gate preserves the pretrained environment representation at initialization;
- source coordinates do not alter the official GeoPT raw input projection.

This supports the intended architecture:

`pretrained geometry/wind transport backbone + small candidate-source injection + plume head`.

Primary empirical gate remains GeoPT-vs-scratch low-data truth-source rank.
