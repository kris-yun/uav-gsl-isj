# Standalone Native candidate replay — H01_R2026092201

Status: **STATIC_PARITY_PASS_152_OF_152; OFFLINE_TRACE_FULL_MAP_PARITY_PASS_152_OF_152**. This is an information-recovery result, not a transfer-operator or localization-method result. No ROS node or live PMFS callback was run for replay.

## Frozen input and the effective seed

The accepted run is `H01_R2026092201`, navigation seed 2, source update 1. Its runtime manifest binds the accepted launch SHA-256 `0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9` and Native algorithm SHA-256 `b06c2036da91ef22285d1cb5d4d08172e828956fc5844d8a2044a4221a8c2cce`. The launcher passes `random_seed` to the algorithm (`vgr_gsl_pmfs_pfdi.launch.py:214` in the frozen VM launch); `Algorithm.cpp:23` and `PMFS.cpp:211` read `seed`. Since `seed` is absent on the algorithm node, the effective Native candidate transport/source-point seed is **0**, even though the navigation seed in `runtime_manifest.json` is 2. The first multi-cell candidate's Native sampled point exactly matches the event-keyed draw for seed 0 and not seed 2. The replay tool refuses other launch hashes/navigation seeds rather than guessing this mapping.

The remaining frozen contract comes from `reference/run_hcmc_v1_independent_gate_20260922.sh`: 200 recording steps, 0.2 s/step, noise standard deviation 0.5, warmup 1–3 steps, five injected filaments/step, source discrimination power 1, no blur, and transport substream `0x4E4154495645504D`. It uses the complete exported measured 29×38 occupancy/probability grid and Free-cell 2D estimated wind grid. All six accepted input artifacts in the local verified package have SHA-256 matching the VM originals:

| Input | SHA-256 |
|---|---|
| `candidate_manifest.csv` | `86a2323909519390a03bc00ddd933e457c008a86653ae56fc749d8f87f331026` |
| `candidate_support_alignment.csv` | `8acd9b4b3aaf66bb7ff88e4b509922879c87d81f67c367850cf6b462bb74771f` |
| `measured_hit_probability.csv` | `7ae011f966e2749c36964aac6c21eb870dc8eb5aaeb3bc4470504f22881d9142` |
| `estimated_wind.csv` | `8f899eff73769150af2729baa44966182bc0712beb5ccc36d08b847313b20ad7` |
| `source_update_timing.csv` | `e2de3d7e88e01e64cda08f4b45c8b3cff7f859626f2639937f93ee12ccb20f84` |
| `runtime_manifest.json` | `153a22b4501982fa7832b89a7007986219a0fdacb0eb0e01ed432dc72fe0fd3c` |

## Hard gates and results

The offline C++ tool links the existing compiled `PMFS` library and calls its protected `simulateSourceInPosition` method with a Quadtree-mode `SimulationSource`. The existing point-replay entrypoint cannot be used: Native re-samples a point within the candidate leaf for every injected filament; the manifest contains only the first point. The tool never reads source truth, GADEN oracle wind/gas, or future robot pose.

The sequence was 1 source-blind multi-cell candidate, then 10, then all 152 evaluated candidates. For every candidate, the first sampled source point matched bitwise, all 212 observed-support float hit probabilities matched bitwise, and the exported Native score matched as a double bit pattern. Total observed-support comparisons: **32,224**, maximum absolute difference **0**. Candidate ID and rectangle are checked against the manifest. The 152 evaluations include ancestor regions; **121 terminal leaves** exactly partition all 626 Free cells with no overlap or gap. See `H01_R2026092201/parity_1.csv`, `parity_10.csv`, and `parity_all.csv`.

Only after the full 152/152 static gate passed, an offline-only mirrored recording loop collected step states while calling the same compiled PMFS filament movement, collision/visibility, and keyed-RNG functions. For each candidate, its resulting **full** final hitMap and first source point matched the untouched compiled PMFS kernel bitwise before the trace was written. This is stronger than the historical bank's observed-support check, but the historical Native full maps were not retained, so unobserved historical cells cannot be independently compared to a saved Native map.

`H01_R2026092201/parity_trace_all.csv` records this second pass. `H01_R2026092201/step_summary.csv` has 30,400 rows (152 × 200) of active counts, unique hit-cell counts, filament centroids and 2D covariance, plus offsets into the binary positions. `occupied_cells.csv.zst` contains 1,579,830 source-conditioned `(candidate, internal_step, cell)` events. The full package also contains 15,474,729 pre-move filament XY positions (float32 pairs) and aligned from/to cell transitions (int32 pairs, `-1` on exit). The step index is **candidate-internal time**, not synchronized with GADEN time or a future robot trajectory. `trace_manifest.json` hashes every full-package trace file. The integrity verifier passed shape, offset, uniqueness, and binary-size checks; the first candidate's trace was byte-identical in separate one-candidate and all-candidate runs.

## Package and reproduction

Full immutable data package (297,635,840 bytes uncompressed; 127,998,403 bytes compressed; compressed SHA-256 `46bbfd8aff2d6203dd4046c754b2885273b8f5b94e4643a9dec0946279e2b71f`):

- Windows: `D:\ZYC\A-gas\_staging\STANDALONE_NATIVE_CANDIDATE_REPLAY_20260923\H01_R2026092201_native_candidate_dynamics_v2.tar.zst`
- VM: `/home/zyc/native_candidate_replay_results_20260923/H01_R2026092201_native_candidate_dynamics_v2.tar.zst`

The branch contains the compact step summary, compressed sparse occupancy, parity records and integrity manifest. The 128 MB compressed binary-position/transition package is kept outside Git history. An earlier `v1` package in the same staging folder is preliminary; **use `v2`**.

Build the isolated `gsl_server` package with `-DCMAKE_BUILD_TYPE=Release -DPFDI_LOW_MEMORY_BUILD=ON -DBUILD_TESTING=OFF`. The only package changes are the offline tool in `ros2_package/tools/native_candidate_replay.cpp` and its CMake target. No file under `ros2_package/src/gsl_server/algorithms/PMFS/` was changed. With the usual ROS/GADEN overlays sourced, run:

Offline executable SHA-256: `c86486cb6a6fc5740d93032f1cad9c5ba162e799338f97ca95dd335496aab45d`. Linked PMFS static library SHA-256: `9b9e23df9129002087f95add0ad2cf17031788af08fed7492744af9a8a045fae`. `Simulations.cpp` source SHA-256: `d8b7c3d8a3799192719cbbf3abbcc1d421d0acfe3b23f3e8822f5cd3474c30ed`.

```bash
native_candidate_replay <H01_R2026092201_run_dir> parity_1.csv 1
native_candidate_replay <H01_R2026092201_run_dir> parity_10.csv 10
native_candidate_replay <H01_R2026092201_run_dir> parity_all.csv all
native_candidate_replay <H01_R2026092201_run_dir> parity_trace_all.csv all <new_trace_dir>
python3 reference/verify_native_candidate_trace.py <new_trace_dir> parity_trace_all.csv trace_manifest.json
```

The tool aborts on the first failed static or full-map check. Results here establish one accepted run's deterministic model-internal replay; they do not establish source identity across plume realizations, transport conditions, or real turbulent flow. No transfer-operator/PF, large-deviation, or Mori–Zwanzig algorithm was tested.
