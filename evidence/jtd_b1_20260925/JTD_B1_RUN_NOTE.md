# JTD-B1 frozen reference-depth audit

Decision: `JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED` with `K_min=4` reference realizations/source.

The index-only subpanels were locked in commit `09fd90ac8b0d36b963e6a2c19c0a0c816a03ae17` before scoring. The source-specific OAS scorer was frozen in commit `b12e0c998302afe29a88b5d23c4ed38d836716de` before any B1 result was opened. The original audited R0/G0 18 x 16 bank was the only input. No new plume was generated, and no E2 environment, sealed data, dense-source bank or closed loop was read or run.

The four original G0 target folds, 64 locked fold/subpanel evaluations, 200 marginal-preserving nulls per evaluation, and K={3,4,6,8,10,12} completed. K=3 failed R5, the pre-frozen largest-positive-5%-removal test. K=4,6,8,10,12 passed all six reliability gates. K=12 reproduced the archived G0 FULL and each null truth-source NLL: maximum absolute differences were about 8.3e-13 and 4.2e-12, respectively.

The independent verifier recomputed every reliability gate from the target-level CSV, checked all 64 saved per-panel null score arrays, and checked the K=12 G0 comparison. It returned the same decision and K_min.

This is an R0 estimator-depth result, not cross-environment confirmation. If the later E2 OPEN design keeps four reference and at least two fresh targets per source, it would require six realizations/source; the current four would imply two additional realizations/source, or 36 across the three six-source OPEN environments. No E2 fill-in was run in B1.
