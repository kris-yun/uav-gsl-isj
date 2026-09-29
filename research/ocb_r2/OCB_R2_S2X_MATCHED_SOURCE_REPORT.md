# OCB-R2 S2X matched-source dataset qualification

Decision: **OCB_R2_S2X_MATCHED_SOURCE_DATASET_PASS**

- Frozen runlist SHA256: `f89dbd78e56f8d564947bc0af24ddd647a0c31994a86c670e2bf0d166917700c`
- Frozen input manifest SHA256: `7dceb7ba29723c605714980f4bec979f4d4b7a82e8c7557846b95f389fe9f9ce`
- Frozen config SHA256: `d0a65940cb0f90b86eacc90e70aaea2e048cbf54a9a2366db322c3cb5e570837`
- Generator SHA256: `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`
- Crossed runs: 32/32; archived with 1817/1817 files per run and host SHA after copy before VM cleanup.
- Structural smoke: X00r1, X02r1, X04r1, X06r1 passed before the remaining 28 runs.
- Archive: `C:\GADEN_OCB_R2_ARCHIVE\s2x_matched_source`, 32 leaves, 58,144 files, 3,875,258,707 bytes.
- Combined S2+S2X: 8/8 matched non-source strata, each 2 configured source positions × 4 independent realizations.
- Timebase: 1803 records/run, 0 to 999.502991 s; wind-index sequence matches parent S2.
- Pre-run infrastructure event: the first smoke attempt stopped before simulator launch because VM free space fell below the inherited 1.30 GB guard. The existing system journal was rotated and vacuumed to 200 MB, freeing 96 MB. The same frozen run was then executed. No ROS build/install or experiment asset was removed.
- VM raw S2X leaves after verified archival: 0; root available after campaign: 1,359,310,848 bytes.
- House01/House02 confirmation and House03 were not accessed by this execution.
- Structural QC checked finite simulator output; no concentration maps, PMFS, source rank, M0, P/Q-time, or dependency score was calculated.
- D0A source-comparability audit is the next separate gate; this report makes no method claim.
