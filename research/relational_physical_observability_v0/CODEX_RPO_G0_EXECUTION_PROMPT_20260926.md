# CODEX TASK — RPO-G0 Relational Physical Observability

Branch:
`research/relational-physical-observability-g0-20260926`

Authoritative files:
- `research/relational_physical_observability_v0/RPO_G0_CHARTER_20260926.md`
- `research/relational_physical_observability_v0/RPO_SCIENTIFIC_BOUNDARY_20260926.md`

Upstream RIA final commit:
`bc07091152ff527fa6f02c01f50791f4af0ab7a6`.

Hard scope:
- 0 new plume;
- House02 `3,5-1_slow` W0 only;
- CENTRAL 84 pairs for all fitting/gates;
- OFFSTRIP 3 pairs stress-only;
- use exact SPX-audited occupancy and 11 W0 wind arrays;
- exact P_G1A and P_E2 probe contracts;
- use frozen RIA Y_CNR/Y_ED targets;
- no concentration/model-output feature in physical predictor;
- no neural network;
- no feature search;
- no JTD/NPG rescue;
- do not read H01 DEV or House03.

Stage A0:
1. verify all source/probe/wind/occupancy/RIA target hashes;
2. freeze occupancy slice, shortest-path convention, wind interpolation, 0.05 m/s travel-time floor, feature order, ridge grid, x-bands and bootstrap seeds;
3. write `RPO_G0_PRE_RUN_LOCK.json` before fitting any predictor.

Stage F:
1. compute SOURCE-ONLY, GEOM, SIMPLE-WIND and PHYS features for all 87 pairs without reading observed Y values;
2. save feature tables and hashes;
3. freeze feature tables before outcome-model fitting.

Stage P:
1. import frozen CENTRAL Y_CNR/Y_ED from RIA;
2. run four-band nested ridge prediction for all four predictor families;
3. generate exactly one out-of-band prediction per CENTRAL pair;
4. compute Spearman, MSE differences, sign balanced accuracy and per-band diagnostics;
5. run 10,000 pair bootstrap and apply G0-1..5 exactly.

Stage S:
Only after CENTRAL decision is frozen, fit PHYS on all CENTRAL pairs and evaluate the 3 OFFSTRIP stress pairs descriptively.

Required deliverables:
- `RPO_G0_PRE_RUN_LOCK.json`;
- `RPO_G0_ASSET_CHECK.json`;
- `RPO_G0_SOURCE_ONLY_FEATURES.csv`;
- `RPO_G0_GEOM_FEATURES.csv`;
- `RPO_G0_SIMPLE_WIND_FEATURES.csv`;
- `RPO_G0_PHYS_FEATURES.csv`;
- `RPO_G0_HELDOUT_PREDICTIONS.csv`;
- `RPO_G0_BAND_SUMMARY.csv`;
- `RPO_G0_BOOTSTRAP_10000.npz/json`;
- `RPO_G0_OFFSTRIP_STRESS.csv`;
- `RPO_G0_RESULT.json`;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `RPO_G0_PASS_PHYSICAL_RELATIONAL_CONTEXT_PREDICTS_IDENTIFIABILITY`
- `RPO_G0_STOP_PHYSICAL_CONTEXT_NOT_PREDICTIVE_BEYOND_BASELINES`
- `RPO_G0_DATA_CONTRACT_STOP`

Stop immediately after RPO-G0.