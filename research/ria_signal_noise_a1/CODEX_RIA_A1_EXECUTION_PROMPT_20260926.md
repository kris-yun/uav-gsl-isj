# CODEX TASK — RIA-A1 Signal vs Variability Decomposition

Branch:
`research/ria-signal-noise-decomposition-a1-20260926`

Authoritative charter:
`research/ria_signal_noise_a1/RIA_A1_CHARTER_20260926.md`

Upstream:
- RIA-A0 final commit `bc07091152ff527fa6f02c01f50791f4af0ab7a6`;
- RPO-G0 STOP final commit `844b18ef89b5ceef6e187b8bbaf7f28f1702c19b`.

Hard scope:
- 0 new plume;
- CENTRAL 84 House02/W0 pairs only for diagnosis;
- exact frozen RIA folds and formulas;
- no new predictor;
- no wind/occupancy features;
- no model tuning;
- no H01 DEV/House03/H02 W2.

Execute:
1. independently recompute fold-level S, W, D_CNR from frozen tensors;
2. compute exact log signal/noise decomposition;
3. independently recompute B, W_E, ED and D_ED components;
4. verify algebra/tensor hashes before importing Delta_A/Delta_B;
5. compute 10,000 pair-bootstrap intervals;
6. apply the three frozen diagnostic labels exactly;
7. stop.

Required deliverables:
- `RIA_A1_PRE_RUN_LOCK.json`;
- `RIA_A1_FOLD_DECOMPOSITION.csv`;
- `RIA_A1_PAIR_DECOMPOSITION.csv`;
- `RIA_A1_ENERGY_COMPONENTS.csv`;
- `RIA_A1_ASSOCIATIONS.json`;
- `RIA_A1_BOOTSTRAP_10000.npz/json`;
- `RIA_A1_RESULT.json`;
- independent recomputation JSON;
- code/input/output SHA256 manifests;
- final branch commit;
- review package path/bytes/SHA256.

Final label exactly one:
- `RIA_A1_SIGNAL_SEPARATION_DOMINANT`
- `RIA_A1_WITHIN_VARIABILITY_DOMINANT`
- `RIA_A1_MIXED_SIGNAL_AND_VARIABILITY`