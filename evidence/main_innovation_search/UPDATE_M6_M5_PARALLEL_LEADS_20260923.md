# Parallel Lead Update — M6 + M5

Date: 2026-09-23

The search now has two active lead tracks.

## Lead A — M6 GeoPT physics foundation transfer

Branch:
`research/geopt-physics-foundation-pmfs-v1`

Next:
- complete actual `GeoPT_8layers.pt` load audit on local VM;
- run G1 low-data pretrained-vs-random-vs-scratch historical transfer pilot.

## Lead B — M5 source-agnostic generative Lagrangian transport

Branch:
`research/generative-lagrangian-filament-world-model-v1`

Next:
- execute L1 trajectory extraction and generative-necessity gate;
- do not train a large generative model unless simple Gaussian/known-physics baselines fail.

M5 gained priority because:
- source transport is source-agnostic after injection;
- one plume realization yields many local trajectory transitions;
- GADEN trajectories are recoverable from sigma-age/order invariants;
- PMFS vs GADEN source-code audit shows a real structural physics gap (2-D stop-at-wall vs 3-D buoyancy + wall deflection + evolving sigma).

M4 remains HOLD.
M3 remains secondary until dense-field data become justified.
