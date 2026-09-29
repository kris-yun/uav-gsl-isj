# Independent House02 wind staging verification

- Frozen staging plan: `RECONSTRUCTED_H02_WIND_STAGING_PLAN.tsv`, SHA256 `102ff41a87b0af5efcb369f5d60a64eb2e4a97aefc312617b7f395dd1eb3990a`.
- Staging path: `/home/zyc/ocb_r1_assets/h02_wind_reconstructed` (separate from original A and B).
- 176 planned/staged files, 701,159,809 apparent bytes: 112 copied from A, 64 from B. Every source and copied destination SHA256 passed during construction. A separate post-build pass rehashed all 176 staged files and checked that the tree has exactly the planned relative paths, 176/176 PASS. The 176 rows in `RECONSTRUCTED_H02_WIND_STAGING_SHA256.tsv` agree with the frozen plan's relative path, source tree, source path and digest.
- The 44 staged U/V/W state payloads match the corresponding historical House02 gas-run wind state hashes, 44/44. The individual comparisons are in `RECONSTRUCTED_H02_WIND_STATE_MATCH.tsv`.
- No original wind directory was edited. No GADEN run or launch change occurred. This verifies an input staging tree; it does not release `OCB_R1_RUN_HOLD`.
