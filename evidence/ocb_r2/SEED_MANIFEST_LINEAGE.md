# OCB-R2 master-seed lineage

Source: `evidence/ocb_r1/SEED_MANIFEST_96.tsv`, SHA256 `49e80377b0882c11dd7a42cf828e98d537b9600e22429aff835f5bb8cc396e51`.
Audited command contract: `evidence/ocb_r1/RUNNER_COMMAND_CONTRACT.json`, SHA256 `138a18ce03217f731867cfdc3419b5048a4817b48a9ea60bfb417c41daa24c83`.

All 96 `requested_seed` integers were copied one-to-one into `master_seed`.
No seed was drawn, replaced, or selected from plume outcomes. The S1 rule is
replicate index 1 (the first frozen seed) for each H01/H02 configuration
index 0 through 7. Replicates 1-4 retain DISCOVERY status; replicates 5-8
remain CONFIRMATION for H01/H02. All H03 rows remain SEALED_CONFIRMATION and
SEALED_NOT_RUN. No H03 simulation is authorized in S1.

The master manifest hashes are frozen separately; `run_id` is a deterministic
identifier only. House02 wind_asset points to the approved reconstructed
staging (not the conflicted raw copy). Runtime uses a layout-only conversion
of these frozen wind values for the current GADEN v3 loader.
