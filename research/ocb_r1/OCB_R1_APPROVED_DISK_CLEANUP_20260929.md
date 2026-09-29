# OCB-R1 approved disk cleanup, 2026-09-29

## Decision

**DISK_EMERGENCY_CLEANUP_PASS** for the limited disk operation. Root available space rose from **225,255,424 bytes** immediately before deletion to **3,306,045,440 bytes** after cleanup, a net gain of **3,080,790,016 bytes (2.87 GiB)**. The 1.5–2 GiB emergency threshold was met. This is not authorization to run OCB-R1: **OCB_R1_RUN_HOLD** remains because the House02 wind inventory still has 63 missing component files and one conflicting file. No GADEN simulation was started.

## Scope and safeguards

Nine exact directories of derived per-run output from two frozen NO-GO experiments were removed. Their parent directories, source/configuration files, final reports, aggregate results, key hashes and source bundle or frozen runtime were retained. The retained copies and 318 hashes are in `evidence/ocb_r1/retired_experiments/RETAINED_FILE_SHA256.tsv`. The nine deletion paths and branch/decision context are in `evidence/ocb_r1/RETIRED_EXPERIMENT_EVIDENCE.tsv`; all 3,581 files were enumerated before deletion in `DELETION_FILE_INVENTORY_BEFORE.tsv`. The deletion script required the unchanged manifest digest `996753450de24f06411fa9de7a7a7c2cd4abd2cafde80061edad1aa818ba2f57` and rejected an earlier attempt with a mistyped digest before any deletion. The successful execution is recorded in `DELETE_EXECUTION_EXPERIMENT.jsonl`.

- CG-PC-CTT: `CG_PC_CTT_MULTI_SEED_NOT_GO`; branch `codex/v3-orr-integrated-20260827`, source bundle head `172968b0d18d32e81f7059519f467f7b1ec5b6b6`. Deleted only `results/House01`, `results/House02`, `results/House03`, totaling **1,340,686,336 allocated bytes**. Kept `results/_batch` and source, freeze, analysis, scripts and hashes.
- MEACI V12: `V12_M_HELDOUT_GENERALIZATION_NO_GO`; exact Git commit was not recorded in the frozen VM snapshot. Deleted only six named House/seed per-case derived directories, totaling **173,215,744 allocated bytes**. Kept the final result/report, aggregate CSVs, theory, frozen runtime scripts and hashes, plus one small representative H02 ON trace.

Also deleted **69,625** ROS `.log` files older than 2026-09-27, **225,845,248 allocated bytes**. Recent ROS logs were retained. `journalctl --vacuum-size=200M` removed **80** archived journal files present in the pre-cleanup inventory, **1,191,182,336 apparent bytes**; active journals remain and journal usage was about 288 MiB afterward. `apt clean` was run (cache roughly 132 KiB before), and `pip cache purge` removed two HTTP cache entries (roughly 13 KiB). `ros2_ws/log` was left intact because the total was only 6.8 MiB and contains latest build/list provenance. No `/tmp` or `/var/tmp` contents were deleted.

`evidence/ocb_r1/CLEANED_PATHS.tsv` lists every experiment directory, ROS log and archived journal path removed. For apt/pip, the table records the operation and approximate pre-cleanup size, not an invented exact per-file byte count. `DISK_USAGE_AFTER_APPROVED_CLEANUP.tsv` contains the post-cleanup directory/file/inode audit; the immediately pre-deletion `df -B1` row and resolved paths are in `retired_experiments/PRE_DELETE_REALPATH_DU.txt`.

## Protected state

`/home/zyc/ros2_ws/src`, `build` and `install` were not targeted and were verified present afterward. The CG and MEACI final result files were verified present afterward. The deletion allowlist did not include GADEN raw plume data, original wind/occupancy/source/launch inputs, the House02 conflicting wind copies, OCB-R1 frozen files, or other historical experiment directories. This verifies the cleanup scope; it is not a new scientific integrity audit of those assets.

VMware `vmhgfs-fuse` is mounted at `/mnt/hgfs`, but currently listed shared folders are on the Windows D drive; no C-drive archive folder was configured or used. A future C-drive shared folder can provide an archive destination, but no VM setting or real experimental data was changed in this operation.
