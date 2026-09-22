# HCMC V1 independent-validation execution attempts

The following attempts are execution failures and are excluded from scientific evaluation. They are retained on the VM under `/home/zyc/hcmc_v1_native_runs_20260922/failed_attempts/`:

- `H01_R2026092201_attempt1_runner_replaced_midrun`
- `H01_R2026092201_attempt2_missing_r2_result_anchor`
- `H01_R2026092202_attempt1_missing_r2_result_anchor`
- `H02_R2026092211_attempt1_wrong_discovery_max_iteration`
- `H02_R2026092211_attempt2_missing_shadow_occupancy_yaml`
- `H02_R2026092211_attempt3_missing_r2_result_anchor`
- `H02_R2026092212_attempt1_missing_r2_result_anchor_partial`
- `H03_R2026092221_attempt1_wrong_discovery_max_iteration`
- `H03_R2026092221_attempt2_missing_shadow_occupancy_yaml`
- `H03_R2026092221_attempt3_missing_r2_result_anchor`
- `H03_R2026092222_attempt1_missing_r2_result_anchor_partial`

The final six accepted runs were generated only after source-blind smoke validation of the execution-only R2 correction. They pass the frozen trace, provenance, final-bank, terminal-status, and linked-native endpoint-parity checks documented in `NATIVE_RUN_INTEGRITY_20260922.json`.

The terminal HCMC failure is separate: `H01_R2026092201` is a valid accepted Native run, but the frozen HCMC transform yields zero valid candidates. That failure is classified as scientific NO-GO rather than execution failure.
