# OCB-R2 S1 H01/H02 structural smoke result

Decision: **OCB_R2_S1_H12_STRUCTURAL_PASS**.

- Frozen generator binary SHA256: ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688
- S1 runlist frozen in commit 2e4c8b7a4bcb82db66fd5361a80015c1858a68ff before the first S1 plume.
- H01 4/4, H02 4/4 configurations passed; all 8/8 passed record, asset, provenance and minimal scientific sanity checks.
- Each configuration produced 1803 native records, from 0 to 999.502991 s, with all 11 wind states represented. Wind transition sequence was checked independently for each configuration; no cross-House equality assumption was used.
- The first native record is empty; the remaining 1802 have parseable, finite, nonempty filament states and finite positive filament-center concentration values. This is only a structural output sanity check, not a localization or method result.
- Each 1817-file raw run was copied to C:\GADEN_OCB_R2_ARCHIVE\s1, all copied files were checked against its VM SHA256 inventory, and only then was the VM raw leaf removed. VM logs, manifests, timelines, QC and inventories remain in the evidence directory.
- House03 status: **SEALED_NOT_RUN**. Its four configurations received static launch/input/hash auditing only. No House03 prospective plume was generated or opened.

This phase does not authorize remaining H01/H02 seeds, House03, PMFS, source ranking, or any main-innovation analysis. The generator remains benchmark-frozen; binary changes require new A(S1) -> B(S2) -> C(S1) qualification.

Detailed per-run checks are in evidence/ocb_r2/OCB_R2_S1_STRUCTURAL_SMOKE_RESULTS.tsv and the eight QC/manifests in evidence/ocb_r2/s1_runs/.
