# House02 wind asset lineage R1

Date: 2026-09-29. Read-only audit; no simulator was started and no original asset was changed.

## Decision

| Gate | Result |
| --- | --- |
| `missing_63_status` | **RECOVERABLE** (`H02_MISSING63_RECOVERABLE`) |
| `conflict_1_status` | **B_SUPPORTED** (`H02_CONFLICT_B_SUPPORTED`) |
| `asset_provenance` | **PASS** |
| Overall | **`H02_WIND_ASSET_LINEAGE_PASS`** |

This is an **asset-lineage** decision only. `OCB_R1_RUN_HOLD` remains: no reconstructed staging tree has been created, the historical 2,000 versus pinned 1,803 writer-record issue is separate, and an output volume for 96 retained runs is not approved. No GADEN run is authorized by this report.

## Trees and exact set comparison

- **A**, the original House02 ROS1/ROS2 launch `wind_data` path: `/mnt/hgfs/workspace/GADEN_files/scenarios/House02/wind_simulations`. `realpath` is identical to this path. `du -sh`: 428 MiB; **113 files**, 447,701,435 apparent bytes.
- **B**, nested House02 scenario copy: `/mnt/hgfs/workspace/GADEN_files/scenarios/House02/House02/wind_simulations`. `realpath` is identical. `du -sh`: 669 MiB; **176 files**, 701,159,809 apparent bytes.

Files were matched by full path **relative to the wind root**, with SHA256 of the complete bytes. A has **0 unique** files; B has **63 unique** files; **112 common files are identical**; **one common file differs**. All 63 missing A paths exist in B, with no other B-only paths. They form a coherent 11-state, four-file-per-state wind family: all 44 `4,5-3_slow` files (`0..10`, `.csv` and `_U/_V/_W`), plus 19 `4,5-3_fast` files (state 5 `_U/_V/_W` and states 6–9 all four files). B has four House02 wind families × 11 states × four files = 176 files. The A/B inventory and set tables are in `evidence/ocb_r1/h02_wind_asset_lineage/`.

## Stronger historical provenance check

The original House02 gas-simulation directories contain saved binary `wind_iteration_0..10` for all four original wind configurations. For every state, SHA256 of the three B component payloads (`.csv_U`, `.csv_V`, `.csv_W`, with each four-byte file header omitted) is **identical** to the SHA256 of the corresponding historical saved wind. This passed **44/44** states. All **28** states for which A has a complete component trio also match. The outer and nested copies of the historical saved winds match **44/44**. See `HISTORICAL_WIND_MATCH.tsv` and the reproducible verifier `verify_h02_historical_wind_vm.py`.

This establishes that B's complete **numeric wind fields**, including all missing states, are the same fields embedded in historical House02 gas runs. It is materially stronger than a filename or timestamp match. It supports using B as the source for missing files without changing the House02 wind realization. The saved binary does not independently archive the original CFD text `.csv`; that file's special case is analyzed in `CONFLICT_FILE_FORENSICS.md`.

The nested House02 copy also contains `gas_simulations` and occupancy files. Outer and nested `OccupancyGrid3D.csv`, `occupancy.pgm`, and `occupancy.yaml` are byte-identical. House03 has the same outer/nested layout pattern, with all four wind families present in both locations. Original House02 launch XML references A through `vgr_dataset/scenarios/House02/wind_simulations/...`; the preserved 2022 gas runs contain B-identical wind bytes. The ROS1 and ROS2 launch files are dated 2023, whereas B's CFD text is dated 2021 and components 2022. A's wind root and truncated file have July 2026 mtimes. These dates and structure are consistent with an incomplete later outer copy, but the actual copy command or operator log was not found. The scenario asset tree has no Git history, and the bounded shell-history/script search found no documented A/B copy operation. The decision relies on byte identity with historical run snapshots, not a guess from mtimes.

The searched third-copy scopes were exact raw wind filenames under `/home/zyc`, bounded House02 paths under `/mnt/hgfs/workspace/GADEN_files/scenarios`, known PMFS/HCMC/CESS/C0.5 directories, launch XML, repository history, and shell history. No third same-format CFD wind directory was established. `THIRD_COPY_CANDIDATES.tsv` records the outer and nested historical gas-run wind snapshots as **binary-format** witnesses; these are not mislabeled as additional CFD-text copies or treated as independent experimental realizations.

## Future reconstruction plan only

If separately authorized, create a **new** `RECONSTRUCTED_H02_WIND_STAGING` tree while leaving A and B unchanged. The frozen plan `RECONSTRUCTED_H02_WIND_STAGING_PLAN.tsv` selects A for 112 byte-identical paths and B for 63 absent paths plus the one truncated path. The planned result is byte-for-byte identical to B's 176-file tree. Each planned source path and SHA256 is recorded. A later stage must verify all 176 staged hashes and explicitly bind the launch to that new tree before any smoke run. **No staging directory, copy, move, launch edit, or simulator run occurred in R1.**
