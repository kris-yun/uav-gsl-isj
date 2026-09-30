# OCB-R2 R3A — geometry-only prospective multi-source design

Status: **DESIGN COMPLETE; NO GADEN AUTHORIZATION**. This document freezes a proposed custom-source extension for human review. No new plume, PMFS forward, confirmation, House03, model, or closed-loop run was performed.

Base: R2A evidence `e5393356f15f78340939ba959de71ba6cc4189da`; theory pivot was copied from `cd96b52910302a52ee65928184b0cf3890733145` without changing the R2A result. The matched-window MZ gate remains HOLD. R0/R1/R2 Gate B motivates a prospective source test; it does not itself establish a formal PID synergy decomposition.

## Input boundary

The selector reads only H01/H02 original 3D occupancy, their legal 2D candidate masks, S2/S2X context metadata, the OCB-R2 master seed manifest, and the frozen historical source-exposure union. No concentration, path tensor, effect size, ranking, or score is read by either R3A script. House03 and H01/H02 confirmation assets were not opened.

Verified occupancy SHA256: H01 `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb`; H02 `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`. Exposure-union SHA256: `9b6995bdcdffbdc99f593982b77a4b966ae84d33c45dfa45734a203131053527`. Generator binary SHA256 inherited from S2X: `ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`.

These four positions are **new custom simulation source configurations** in the existing House geometries. They are not historical source locations from the original fixed two-source-per-House dataset. Any future publication must label this panel accordingly.

## Geometry census and rule

The legal 2D masks have 626 H01 and 631 H02 free cells. Each candidate is a 0.30 m PMFS cell center and must also occupy a free voxel in the raw 0.10 m 3D occupancy at its proposed source height. One new point is anchored to each old physical source and inherits that old source's z coordinate. Historically exposed PMFS source IDs and the old source coordinates are excluded.

The census showed that a 0.20 m minimum 3D obstacle clearance and a 0.42 m minimum 2D clearance leave no unexposed H02 source-2 candidate within 1.50 m, but two within 1.80 m. The geometry-only selection band was consequently frozen as old-anchor distance **0.90–1.80 m**, with other-old-source distance ≥0.90 m and new-to-new distance ≥0.90 m. Among eligible two-point sets, choose the smallest total deviation from 1.00 m anchor distance, then the smallest maximum deviation, then greater minimum 2D clearance, then greater new-to-new distance, then source IDs. This avoids picking distant corners simply to make the original two-source task easy. The 1.00 m target is about three 0.30 m grid steps and was fixed after the spacing census, before any plume outcome was consulted.

| House | Old anchor | New source | xyz (m) | Old-anchor 3D distance (m) | 2D clearance (m) | 3D clearance (m) |
|---|---|---|---|---:|---:|---:|
| H01 | configured 1 | `pmfs_21_35` | (−1.10000, 2.77000, 0.40) | 0.960 | 0.424 | 0.316 |
| H01 | configured 2 | `pmfs_20_15` | (−1.40000, −3.23000, −0.30) | 1.053 | 0.424 | 0.447 |
| H02 | configured 1 | `pmfs_19_24` | (0.45727, −0.10088, 0.20) | 1.009 | 0.900 | 0.806 |
| H02 | configured 2 | `pmfs_22_22` | (1.35727, −0.70088, −0.10) | 1.639 | 0.600 | 0.520 |

The H02 fourth source is 1.639 m from its anchor because nearer unexposed cells lacked the frozen 3D clearance. A free-voxel-only candidate at 1.261 m had just 0.10 m clearance and was rejected. H01's two old sources are already 4.904 m apart; R3A retains this intrinsic easy cross-cluster contrast but adds one approximately 1 m hard neighbor to each. H02's four-source pairwise 3D separations span 1.009–2.285 m. None of these geometric properties guarantees ranking headroom; that is a future data result.

## Proposed prospective bank

Eight unchanged S2/S2X House–wind–gas contexts × two new sources × four independent seeds = **64 proposed runs**. Each context would then contain its two old sources plus these two new sources, each at four realizations. Within each context, wind, gas, occupancy, generator, timebase and observation contract remain matched; only source xyz and seed differ. The 64-line manifest uses `seed = 2026920000 + 100*context_index + 10*new_source_index + replicate`, with context 0–7, new-source index 1–2, replicate 1–4. All 64 seeds are unique and disjoint from the frozen OCB-R2 master-96 and S2X seeds. No common random-number source pairing is introduced.

The proposed VM output root is `/home/zyc/ocb_r2_r3_multisource`; the proposed host archive root is `C:\GADEN_OCB_R2_ARCHIVE\r3_multisource`. These are plans only. Each future run must be copied, inventoried and hash-verified on the host before its VM raw copy is removed. The original S2/S2X/confirmation/H03 assets remain intact.

Source panel SHA256: `11952617610c4b50d789ac73a5a05e8302a0f570f55eca504598872844e9017e`. Prospective runlist SHA256: `15f2121eae2772989c7cff7f292825a31efe94c24efedc34f2a9ccd681f947d0`.

## Resource estimate, not execution approval

The completed S2X campaign stored 3,875,258,707 bytes for 32 similar runs (121,101,834 bytes/run, 1,817 files/run). Linear projection for 64: **7,750,517,414 bytes (7.22 GiB)** and roughly 116,288 files on the host, before package/metadata overhead. Current observed Windows free space at design time was C: 128,829,300,736 bytes and D: 7,643,590,656 bytes. The C archive is suitable by capacity; D is below the projected payload and must not be the sole destination.

The 32 saved S2X simulator logs report 5.84–9.87 s per GADEN process, median 8.765 s. Multiplying their total by two gives about **540 s of simulator-core time** for 64 comparable runs. This excludes ROS startup, 116k-file archival, hashing, QC, transfers and possible failures, so it is not an end-to-end ETA. The S2X report recorded 1,359,310,848 bytes of VM root space after its campaign; this is historical and requires a fresh preflight `df -h`. Any later execution should use the established one-run archive/verify/cleanup cadence and the inherited free-space guard, not batch 64 raw outputs on the VM.

## Future R3 scoring preplan

After separate approval and structural qualification, evaluate **M-FULL** and the already frozen candidate-wise broad-memory `E_BM` as two separate four-source scores on the same `10×30` observation contract. Report full four-source truth rank, unique Top-1, MRR, truth-versus-best-wrong margin, and the hard neighbor separately by context, source and seed. Keep K=3 fair-U reference parity by leaving a target's own realization out and using three references for every candidate; repeat the four alternative-reference omissions as robustness. Do not introduce a fusion weight, softmax, tuned lag weights, calibration or new model in R3A. The eventual scientific gate must be separately preregistered before reading R3 targets.

**STOP here.** Human review of geometry, source configuration scope, manifest, resource plan and R3 scoring gate is required before any R3 GADEN call.
