# SPX-G0 House02/W0 crossed diagnosis

Frozen label: `SPX_G0_SOURCE_PROBE_INTERACTION`. This is a diagnostic label, not a main-innovation PASS. JTD-E2 and NPG-G0 remain STOP.

A0 found and numerically verified all 2,688 CENTRAL and 96 OFFSTRIP raw cubes, both 30-probe contracts, the House02 occupancy grid, and all 11 W0 wind arrays. CENTRAL×P_G1A and OFFSTRIP×P_E2 reproduce their historical 10×30 tensors with maximum absolute difference 0.0. The same raw cube was then extracted under both protocols. No new plume was generated.

The primary score is a uniform-prior two-source conditional likelihood on the 84 CENTRAL and three OFFSTRIP fixed 0.3 m pairs. It does not compare 168-way with 6-way posteriors. The H02 W2 distant-aliasing cases are outside this diagnosis.

For FULL versus BP, 39/84 CENTRAL pairs are positive under both probes, 31/84 reverse sign on probe switch, and 1/3 OFFSTRIP pairs are non-positive under both probes. The corresponding FULL versus MBD counts are 49/84, 24/84 and 0/3.

Neither frozen SOURCE_REGIME_DOMINANT nor PROBE_PROTOCOL_DOMINANT inequalities hold for both comparators. Therefore the charter assigns SOURCE_PROBE_INTERACTION by exclusion. This label does not itself establish a physical relational mechanism; the source/probe effects may also include Gaussian model instability and severe NLL tails. Median CENTRAL paired probe effects are near zero, while target-level tails are large. The reference-only rank audit found 29/3480 PCA2 blocks with fewer than two varying raw dimensions, affecting 11 pairs. All pairs remain in the result.

An independent verifier refit all 16704 target/model scores, recomputed pair/probe effects, all 10,000 pair bootstrap draws and the frozen diagnosis. The maximum truth NLL difference was 2.91e-11. No model, feature, pair, probe, threshold or interpretation rule was changed after the full score was observed.
