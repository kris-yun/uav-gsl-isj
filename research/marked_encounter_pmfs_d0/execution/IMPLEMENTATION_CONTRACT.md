# Outcome-blind implementation contract

Base: audited historical Native R1 C-arm replay at
`d3afac6488a9ee797f7e8d3289b485729fc5da31`, with original VM library/source hashes
validated against its recorded build provenance.

- Reuse the E1 seed-invariant PMFS pruned navigation masks and metadata for
  House01/02. Source xyz and pooled-probe centers come literally from the supplied
  E1 contracts. Source mode is Point at the six frozen cell centers.
- Sample each canonical CSV wind by its nearest 3D row at each PMFS free-cell
  center and z=0.20 m, using the historical wind adapter convention. Preserve
  Cartesian map-frame downwind U,V without angle conversion. Float32 winds.
- Native C settings: min/max warmup 200/500, recording 200, dt=0.1,
  Gaussian velocity noise std=0.5, five emitted filaments/step, blur sigma=1.5
  in both grid axes, maxRegionSize=5, sourceDiscriminationPower=0.3.
- Replicas use fresh processes, native minstd_rand0 initial seeds 1..8; seed 1
  is the native default. A seed setter executes before any Gaussian table or
  distribution use. Original draw functions, Gaussian cache/table and movement
  code are unchanged. Shared initial streams across candidates/state; this is
  not a claim of identical event-indexed draws after paths diverge.
- Count every active filament at its pre-movement recording cell, before the
  unchanged `updated` suppression. No warmup count. Normalize both counts by
  the same native 200 recording steps.
- Preserve native blurred p exactly. Apply the same occupancy-corrected Gaussian
  linear blur to u, with no upper probability clamp on filament counts. Also
  retain raw unblurred p/u full maps for audit. At each probe use its containing
  PMFS cell. These are the simulator's 0.30 m cells, not new GADEN pooled values.
- Average p and u over 11 states x 8 replicas before dividing u/p. Zero p maps
  to conditional mean 0; supplied evaluator handles its fixed epsilon.
- Supplied evaluator is unchanged. U is specified by U_PRE_TARGET_AMENDMENT.md.
  B2 is the supplied single nonnegative scale least-squares diagnostic on u.
  Save all candidate scores; do not interpret proper scores as calibrated
  deployment posteriors. Targets are previously OPEN development data.
- Native parity: full 87 maps and original CSV scores, counter OFF and ON,
  versus frozen R1. Repeat all 1584 forwards and all evaluation outputs.
- No GADEN, ROS node, network training, closed loop or protected data access.
