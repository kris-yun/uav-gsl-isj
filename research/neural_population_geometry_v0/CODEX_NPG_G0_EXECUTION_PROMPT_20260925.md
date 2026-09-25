# CODEX TASK — NPG-G0 Task-Relevant Neural Population Geometry Falsification

Branch:
`research/neural-population-geometry-g0-20260925`

Authoritative charter:
`research/neural_population_geometry_v0/NPG_G0_REFERENCE_ONLY_CHARTER_20260925.md`

Scientific boundary note:
`research/neural_population_geometry_v0/NPG_SCIENTIFIC_BOUNDARY_20260925.md`

Hard scope:
- 0 new plume;
- use only the frozen 168x16 House02 `3,5-1_slow` bank;
- do not use E2 fresh-target outcomes;
- do not read H01 DEV or House03;
- no dense-bank source filtering;
- no neural network;
- no learned interaction subspace;
- no closed loop;
- no JTD rescue.

Stage A0:
1. verify the 24x7 source-strip ordering and all 84 disjoint horizontal nearest-neighbor pairs;
2. freeze four x macro-bands and both 8/8 realization directions;
3. freeze all preprocessing, interaction formula, ridge grids, bootstrap seeds and G0-1..G0-5 before utility scoring.

Stage G0:
1. for each direction, fit block scalers/PCA on DESIGN only;
2. construct base z and fixed bounded 40-D cross-block interaction j(z);
3. evaluate held-out pair Delta_log with identical ridge-logistic reader family for base and interaction;
4. compute the frozen neural-geometry vector from DESIGN only;
5. run leave-one-macro-band-out geometry utility prediction;
6. run INNER_CV and all ordinary predictors;
7. bootstrap pair units and apply G0-1..G0-5 exactly.

Required deliverables:
- `NPG_G0_PRE_RUN_LOCK.json`;
- `NPG_G0_RESULT.json`;
- pair definition CSV;
- per-split per-pair utility CSV;
- per-pair neural-geometry feature CSV;
- held-out prediction CSV for GEOMETRY and all ordinary predictors;
- macro-band summary CSV;
- bootstrap outputs;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `NPG_G0_PASS_TASK_GEOMETRY_PREDICTS_INTERACTION_UTILITY`
- `NPG_G0_HOLD_INSUFFICIENT_UTILITY_HETEROGENEITY`
- `NPG_G0_STOP_GEOMETRY_NOT_BETTER_THAN_ORDINARY_SELECTION`

Stop immediately after G0.