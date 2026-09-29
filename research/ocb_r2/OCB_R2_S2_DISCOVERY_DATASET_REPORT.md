# OCB-R2 S2 discovery dataset qualification

**Decision: OCB_R2_S2_DISCOVERY_DATASET_PASS.**

- Runlist: 32 rows, frozen before S2 plume generation in commit `63935e8090b694851b899e468c2987fd793e2301`; SHA256 `f1d8604b49a74ba3ab698f445a2c1e381d84164c809e1bcf8b0f08beddf40974`.
- Frozen configuration SHA256: `72969373811ace0d30ba64d9227d429136680ce2d34449c4cc3bbd7f868eaa47`.
- Generator binary SHA256: `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`.
- House01 16/16 and House02 16/16 discovery runs passed. Eight original source/wind configurations have four frozen seeds each.
- Every run has 1803 native records from 0 to 999.502991 s, 1802 nonempty filament records, all 11 legal wind states, finite parsed filament values, and complete asset/seed provenance.
- The eight replicate-1 scientific output hash lists exactly match their S1 runs, 1803/1803 records for every configuration.
- Each 1817-file raw run was archived at `C:\GADEN_OCB_R2_ARCHIVE\s2_discovery` and SHA256-verified after copy before deleting its VM raw leaf. Small evidence and inventories remain in Git.
- House01/House02 confirmation replicates 5-8 were not generated or opened. House03 remains `SEALED_NOT_RUN`.

This is dataset qualification only. No PMFS, localization rank, dependence score, method evaluation, or main-innovation result was computed.
The 32 discovery runs may be used in a separate, explicitly scoped discovery analysis; confirmation and H03 remain sealed.
