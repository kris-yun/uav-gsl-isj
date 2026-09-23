# M6 GeoPT checkpoint availability — parallel-search update

Date: 2026-09-23

Official GeoPT release exposes a pretrained 8-layer checkpoint, `GeoPT_8layers.pt` (~15.6 MB).

The released downstream configuration retains the audited 11-D pointwise contract:

- xyz;
- SDF / boundary distance;
- 3-D boundary direction;
- 4-D dynamics condition.

This preserves a near-direct indoor-gas mapping:

- free-space position;
- distance/direction to nearest wall;
- local wind direction and speed.

Next hard gate is a real runtime load/forward test. No plume training before:
- checkpoint parameter-load coverage is measured;
- one real House geometry+wind token set runs through the frozen backbone;
- runtime/memory are recorded.

M6 remains `ADVANCE TO G0.5`, not yet a validated main innovation.
