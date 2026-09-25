# CODEX TASK — RSC-G0 Relational Sensory Contingency Gate

Branch:
`research/relational-sensory-contingency-g0-20260926`

Authoritative files:
- `research/relational_sensory_contingency_v0/RSC_G0_CHARTER_20260926.md`
- `research/relational_sensory_contingency_v0/RSC_SCIENTIFIC_BOUNDARY_20260926.md`

Upstream SPX final commit:
`666e7996b5b060516e32b2d93df0679171981745`.

Hard scope:
- 0 new plume;
- House02 `3,5-1_slow` only;
- CENTRAL 84 pairs are the sole fitting/gating panel;
- OFFSTRIP 3 pairs stress-test only;
- exact P_G1A and P_E2 probe contracts;
- actual 11 audited W0 wind arrays and occupancy grid;
- do not read H01 DEV or House03;
- no neural net;
- no feature search;
- no JTD/NPG rescue.

Stage A0:
1. verify all wind/occupancy/probe/source hashes against SPX asset audit;
2. freeze occupancy slice, 8-neighbor path convention, interpolation, 0.05 m/s travel-time floor, feature order, four x-bands, ridge grid and bootstrap seeds;
3. freeze a pre-run lock before reading SPX utility targets into the predictor.

Stage C:
1. compute target-blind C_i(P_G1A), C_i(P_E2) and DeltaC for all 87 pairs;
2. compute geometry-only DeltaG;
3. compute reference-only DeltaR from references only;
4. export all raw feature tables before outcome-model fitting.

Stage U:
1. recompute robust 20%-trimmed pair utility from SPX target-level metrics for BP and MBD;
2. form robust probe-switch E;
3. retain untrimmed E sensitivity table.

Stage P:
1. run grouped four-band nested ridge prediction for GEOM, REF, PHYS, PHYS+REF;
2. produce out-of-band prediction for every CENTRAL pair;
3. run 10,000 pair bootstrap for all frozen comparisons;
4. apply RSC-G0-1..5 exactly;
5. only after decision, fit all CENTRAL pairs and run OFFSTRIP stress predictions.

Required deliverables:
- `RSC_G0_PRE_RUN_LOCK.json`;
- `RSC_G0_ASSET_CHECK.json`;
- `RSC_G0_PHYSICAL_CONTEXT_FEATURES.csv`;
- `RSC_G0_GEOMETRY_FEATURES.csv`;
- `RSC_G0_REFERENCE_DIAGNOSTICS.csv`;
- `RSC_G0_PAIR_UTILITY.csv`;
- `RSC_G0_HELDOUT_PREDICTIONS.csv`;
- `RSC_G0_BAND_SUMMARY.csv`;
- `RSC_G0_BOOTSTRAP_10000.npz/json`;
- `RSC_G0_OFFSTRIP_STRESS.csv`;
- `RSC_G0_RESULT.json`;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `RSC_G0_PASS_RELATIONAL_PHYSICAL_CONTEXT_PREDICTS_PROBE_EFFECT`
- `RSC_G0_STOP_RELATIONAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES`
- `RSC_G0_DATA_CONTRACT_STOP`

Stop immediately after RSC-G0.