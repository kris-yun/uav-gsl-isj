# OCB-R1 disk audit and historical-output triage

Date: 2026-09-29. Baseline: `c56da218a4aa43488a3c46ea4850a42838285a0b` on
`research/original-config-common-benchmark-r1-20260929`.

## Decision and scope

**DISK_CLEANUP_HOLD** and **OCB_R1_RUN_HOLD**. This pass was read-only after
the user's latest instruction to classify the 20–30 largest directories and
return them for review before deleting anything. No GADEN simulation, ROS
build, cache purge, journal vacuum, file deletion, file move on the VM, or
shared-folder reconfiguration occurred. The earlier House02 wind-asset blocker
(63 missing component files and one conflicting file) remains independent of
disk space.

The 30 largest immediate children of `/home/zyc` are classified in
`evidence/ocb_r1/OLD_EXPERIMENT_DELETE_MANIFEST.tsv`. Every proposed cleanup
entry has action `HOLD_USER_REVIEW_NO_DELETE`. The full before and no-deletion
checkpoint inventories are `DISK_USAGE_BEFORE.tsv` and
`DISK_USAGE_AFTER.tsv`; `CLEANED_PATHS.tsv` contains only its header because
no paths were deleted. `JOURNAL_FILES_BEFORE.tsv` records the 100 current
journal files for a later, separately authorized vacuum audit.

## Space accounting

| Measurement | Before | No-deletion checkpoint |
| --- | ---: | ---: |
| Root `/dev/sda3` available | 233,754,624 B (223 MiB) | 233,730,048 B (223 MiB) |
| Root inodes available | 2,272,500 | 2,272,500 |
| Space freed by this task | 0 B | 0 B |

The 24,576-byte drift between snapshots is ordinary background filesystem
activity, not cleanup. `df -h` still reports the 49 GiB root as 100% used.
`/home/zyc` occupies about 25 GiB, `/var` 7.1 GiB, `/usr` 10 GiB, and
`/home/zyc/ros2_ws` 2.8 GiB. The current user-level low-risk pool is much
smaller than the 3–5 GiB target: `.ros/log` is 226 MiB, `ros2_ws/log` 6.8 MiB,
pip cache 68 KiB, apt archives 132 KiB, and systemd journal about 1.3 GiB.
The latter would require an authorized journal vacuum; none was run.

## Largest-directory provenance check

The top 30 are in the manifest with byte sizes, classification, rationale,
reconstruction status, retained evidence, and proposed action. The most
material distinctions are:

- **KEEP_SOURCE_ASSET:** `ros2_ws` source/build/install and independent
  simulator/PMFS builds; `.local` Python runtime; the CESS D1R 168×16
  concentration reference; HCMC seeded GADEN data; C0.5 raw GADEN bank;
  PMFS sidecar raw runs and wind snapshots; repositories and GADEN source.
  A method's later NO-GO does not invalidate its original plume realizations.
- **Confirmed derived-output review candidate:**
  `CG_PC_CTT_V3_ORR_FULL60_PACKAGE_20260827` is 1,368,621,056 B, of which
  `results` is 1,340,706,816 B. Its runtime files are largely context-bank
  CSV and logs; `MULTISEED_VERDICT.json` says
  `CG_PC_CTT_MULTI_SEED_NOT_GO`. The exact review target is its `results`
  child after preserving freeze, configuration, aggregate verdict and
  essential small evidence. SHA256 of the existing verdict JSON:
  `ca2c3f3898f52863880561a528bf0f7a903f5cda84c155098a27a8a48ea063e4`.
- **Confirmed derived-output review candidate:**
  `meaci_v12_generalization_20260825_r1` is 174,534,656 B, mostly
  per-case context-bank CSV/log output. Its report says
  `V12_M_HELDOUT_GENERALIZATION_NO_GO`. Preserve the result JSON, report,
  freeze protocol and runtime manifests before considering any removal.
  SHA256 of its result JSON:
  `edd64fecb74ac7e1e92c419c0e0e587731abbea830c40fe9dcfcbebab254b812`.
- **UNKNOWN_HOLD:** The 2,317,451,264-byte AOD F1 directory includes
  2,041,757,696 B of derived `candidate_forward`, but its frozen F1 decision
  is `AOD_F1_FULL624_CONFIRMED_STRESS_NONINFERIOR`. This is a current positive
  asset, so it is not on the proposed deletion list. Likewise, native
  candidate replay traces, marked-encounter forward files, and wind-alignment
  replay evidence have potential parity or later-method dependencies. Size
  alone is insufficient to delete them.
- **SAFE_LOG pending review:** `.ros/log` is 235,941,888 B by `du`. All
  69,800 regular files examined there have `.log` extension. Files modified
  before 2026-09-27 account for 69,625 files and 193,748,204 apparent bytes;
  2026-09-27/28 logs include recent validation activity and remain protected.
  `ros2_ws/log` has about 6.8 MiB of colcon/list provenance and was left
  intact. No log cleanup was performed in this read-only pass.

The two clearly failed large derived-output directories total only about
1.54 GiB **before** retaining evidence. Adding old ROS logs still does not
establish a safe 3–5 GiB release, let alone 10–20 GiB. More space may be
recoverable, but it would require a separate provenance and dependency review.
This audit does not infer removability from directory names or method status.

## Large ordinary files and system storage

The full `find /home/zyc -xdev -type f -size +100M` inventory is included in
both disk-usage TSVs. Examples that must be retained are the 442 MB PyTorch
runtime library, the 375 MB `fixed_source.tar.gz` of unresolved provenance,
Git object packs, raw wind snapshot binaries, and PMFS/ROS executables.
`/var/log/journal` accounts for about 1.4 GiB on disk, while
`journalctl --disk-usage` reports 1.3 GiB active plus archived journals.

## Windows storage and shared-folder check

Windows C: had 139,287,953,408 B available and D: 2,316,251,136 B when
checked. The live VMware VMX is on `D:\Ubuntu`; all five configured hgfs
host paths in that VMX point to D:, and `/mnt/hgfs` is mounted read/write but
has only about 2.2 GiB available. There is no configured C: shared folder,
so no C: write-test file was created. VM configuration was not changed.

## Next decision boundary

The user should review the candidate rows in
`OLD_EXPERIMENT_DELETE_MANIFEST.tsv`, starting with CG-PC-CTT `results` and
MEACI per-case runtime outputs. Before any future delete, preserve each
route's source/commit, frozen decision, key metrics, configuration and scripts,
essential small evidence, and a directory-level file inventory with hashes of
key files. No large per-file SHA sweep is required for a demonstrably
reproducible derived tree. Raw GADEN inputs/plumes, current OCB-R1 evidence,
all ROS2 source/build/install trees, and both House02 wind copies remain
protected. OCB-R1's 96 GADEN runs remain on HOLD regardless of any later
disk cleanup.
