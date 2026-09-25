# CODEX TASK — JTD-B1 Source-Specific OAS Reference-Depth Audit

Branch: `research/jtd-cross-environment-v0`

Authoritative charter:
`research/jtd_cross_environment_v0/JTD_B1_REFERENCE_DEPTH_CHARTER_20260925.md`

Use the audited R0/JTD-G0 canonical 18x16 dataset only.

Hard restrictions:
- 0 new plume;
- no E2 OPEN/DEV/House03 reading;
- no dense-source expansion;
- no model/feature changes;
- restore the exact G0 source-specific OAS likelihood;
- do not reuse B0 pooled covariance.

Evaluate K={3,4,6,8,10,12} exactly as frozen.
For K<12, precompute and save the three deterministic reference subpanels before any scoring.
Use 200 deterministic marginal-preserving nulls per fold/subpanel.

Deliver:
- `JTD_B1_RESULT.json` with decision and K_min;
- depth summary CSV;
- fold/subpanel summary CSV;
- source summary by depth;
- target metrics by depth;
- subpanel lock JSON;
- input/code/output SHA256 manifests;
- independent recomputation of all reliability gates;
- branch/final commit;
- review package path/bytes/SHA256.

Final decision exactly one:
- `JTD_B1_PASS_REFERENCE_DEPTH_IDENTIFIED`
- `JTD_B1_HOLD_REQUIRES_G0_DEPTH`
- `JTD_B1_FAIL_IMPLEMENTATION_OR_CONTRACT_DRIFT`

Stop after B1.