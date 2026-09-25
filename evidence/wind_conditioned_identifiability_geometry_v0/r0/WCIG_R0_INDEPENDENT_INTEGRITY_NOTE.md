# WCIG R0 independent integrity note

Decision remains `WCIG_R0_FAIL_STOP_WIND_GEOMETRY_MAINLINE`.
The upstream frozen decision remains
`LSC_CROSSWIND_D0_FAIL_STOP_MAINLINE_GENERALITY`.

Scope: 8 frozen sources, 10 frozen edges, 3 discovery wind operators,
0 new plume realizations. W3 `4,5-3_fast` wind was read only; the LSC
plume data directory contains no W3 run.

Integrity checks after the frozen analysis:

1. All 44 canonical 3D wind files matched the prior inventory SHA256.
2. A second existing reader
   (`audit_c05_house_winds.read_wind`) and independent linear-index
   calculation reproduced every one of the 1320 saved local wind vectors
   exactly after the validated float32 export conversion.
3. The saved 4×10×11×3×3 wind-sample tensor independently reproduced
   all 40 rows of primary `A_parallel`, `A_perp`, and `U` features.
4. Independent ordinary least-squares leave-one-wind-out calculations
   reproduced all three held-out Spearman values and pooled
   Spearman `-0.008231368186874304` to numerical tolerance.

The first attempt stopped at input SHA preflight because the code copied one
character incorrectly into the frozen LSC result hash. Commit
`817f7a7bc5cdf12b86f62bfaf8b66eae98b03364` corrected only that
literal, before any local wind sample was read. No physical feature,
regression formula, threshold, or W3 prediction rule changed after reveal.
