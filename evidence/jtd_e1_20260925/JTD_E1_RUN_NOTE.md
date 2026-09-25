# JTD-E1 frozen fresh cross-environment gate

Decision: `JTD_E1_HOLD_ENVIRONMENT_HETEROGENEOUS_SIGNAL`.

The pre-run lock was committed as `382cac419754a83abc751a5fb986ed1688cdf723` before the first fresh plume. It fixed the 72 existing OPEN reference cubes, 18 reference source groups, 36 fresh seeds, two E1 source/probe contracts, three wind operators, 600 null base keys and all E1-G1..G7 thresholds. The three OPEN environments were H01 `1,3-2,4_fast`, H02 `3,5-1_slow` and H02 `4,5-3_slow`. The E2 DEV, House03 and reserve environments were not read.

Exactly 36 new GADEN simulations were performed, one per frozen fresh target seed. The first simulation completed but its extractor initially failed because GADEN removed an occupancy symlink from the results directory. Before any target concentration or rank was inspected, the E2-style symlink restoration and extraction resume were committed separately as infrastructure-only patch `9bb036277882432536090e5d899797c0856d8b67`. The completed first simulation was reused; its seed was not rerun. The original failure logs and code-hash attestation are retained.

All 36 complete concentration cubes and pooled 10x30 observations passed QC and SHA256 checks. `JTD_E1_FRESH_RAW_36_20260925.tar.gz` contains the 36 cube/run-metadata/pooled bundles and has SHA256 `a3cb40fb0fe689a34f8b54bc454e0d39b29df97a04ea55fee6999dc48606fe5a`. Independent re-extraction from all 36 raw cubes exactly reproduced the target tensor. Independently recomputed posteriors from the saved candidate log likelihoods and replayed all 200 nulls per environment, bootstrap draws and seven frozen gates; the decision matched.

E1-G1, G2, G4, G5, G6 and G7 passed. E1-G3 failed: 12/18 environment x source units were positive, below the frozen 13/18 requirement. Positive source counts by environment were 5/6, 3/6 and 4/6; H02 `3,5-1_slow` missed its 4/6 minimum. All three environment mean deltas were positive, and no catastrophic reversal occurred. The charter's single-environment heterogeneity rule therefore gives HOLD. No threshold, source, seed, null, PCA dimension or model was changed after scoring.

This HOLD does not authorize dense-source G1A or a claim of cross-environment mechanism confirmation. No dense expansion or closed loop was run.
