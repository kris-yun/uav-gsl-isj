# CODEX TASK — RIA-A0 Relational Identifiability Audit

Branch:
`research/relational-identifiability-a0-20260926`

Authoritative charter:
`research/relational_identifiability_a0/RIA_A0_CHARTER_20260926.md`

Upstream SPX final commit:
`666e7996b5b060516e32b2d93df0679171981745`.

Hard scope:
- 0 new plume;
- House02 `3,5-1_slow` only;
- use SPX frozen crossed tensors and target metrics;
- 84 CENTRAL pairs primary;
- 3 OFFSTRIP pairs descriptive only;
- no wind-derived predictor yet;
- no occupancy-derived predictor yet;
- no neural model;
- no JTD/NPG/RSC rescue;
- do not read H01 DEV or House03.

Stage A:
1. verify SPX crossed-tensor and pair-definition hashes;
2. freeze four 12-reference/4-heldout folds;
3. compute reference-only D_CNR and normalized energy distance D_ED for every CENTRAL pair×protocol×fold;
4. freeze pair/protocol averages before importing heldout bounded/risk metrics.

Stage B:
1. compute median-across-reader bounded operational metrics Delta_A and Delta_B from frozen SPX heldout accuracy/Brier;
2. compute estimator-risk summaries and probe-switch changes;
3. compute all A0-Q1/Q2/Q3 associations;
4. use 10,000 pair bootstrap resamples only;
5. run leave-one-pair-out influence sign audit.

Stage C:
1. issue exactly one RIA-A0 diagnostic label;
2. only after label is frozen, compute the OFFSTRIP descriptive stress table.

Required deliverables:
- `RIA_A0_PRE_RUN_LOCK.json`;
- `RIA_A0_REFERENCE_IDENTIFIABILITY.csv`;
- `RIA_A0_BOUNDED_OPERATIONAL.csv`;
- `RIA_A0_ESTIMATOR_RISK.csv`;
- `RIA_A0_ASSOCIATIONS.json`;
- `RIA_A0_BOOTSTRAP_10000.npz/json`;
- `RIA_A0_LOO_INFLUENCE.csv`;
- `RIA_A0_OFFSTRIP_STRESS.csv`;
- `RIA_A0_RESULT.json`;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final label exactly one:
- `RIA_A0_PHYSICAL_IDENTIFIABILITY_TARGET_SUPPORTED`
- `RIA_A0_MODEL_RISK_DOMINANT_NO_PHYSICAL_TARGET_YET`
- `RIA_A0_MIXED_OR_UNRESOLVED`

Stop immediately after RIA-A0.