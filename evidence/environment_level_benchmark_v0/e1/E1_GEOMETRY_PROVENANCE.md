# E1 geometry provenance

Inputs are 3D occupancy, seed-invariant PMFS pruned navigation geometry, legacy probe contract, and E0 metadata.
Validated mappings: `prepare_gate1a_bank.py` (`read_occ`, `fine_index`) and PMFS `Grid2DMetadata` (0.30 m cell centers, x + width*y).
Observation is 2×2 native-grid average at z=0.20 m and D1R iteration indices 100,150,200,250,300,350,400,450,500,550.
No plume values informed source/probe selection or E1A/B. A later technical extraction check reads one pre-existing cube per House02 wind after geometry decision is fixed.
No GADEN generation executable was called.

House candidate counts: {"House01": {"gaden_num_cells": [87.0, 114.0, 33.0], "observation_z_m": 0.2, "pmfs_grid_shape": [29, 38], "pmfs_pruned_free_count": 626, "probe_candidate_count": 1227, "source_candidate_count": 621, "source_z_m": 0.2}, "House02": {"gaden_num_cells": [83.0, 119.0, 26.0], "observation_z_m": 0.2, "pmfs_grid_shape": [27, 39], "pmfs_pruned_free_count": 631, "probe_candidate_count": 1298, "source_candidate_count": 630, "source_z_m": 0.2}, "House03": {"gaden_num_cells": [138.0, 83.0, 25.0], "observation_z_m": 0.2, "pmfs_grid_shape": [46, 27], "pmfs_pruned_free_count": 626, "probe_candidate_count": 1245, "source_candidate_count": 624, "source_z_m": 0.2}}

## Input SHA256

- `/home/zyc/e1_repo_20260925/research/causal_biorthogonal_green_v1/prepare_gate1a_bank.py`: `6c9d028933b856ae8807f9425065e49d9db60ea7c886cf1a5e80c0ba9c3eb1b6`
- `/home/zyc/e1_repo_20260925/research/causal_biorthogonal_green_v1/extract_gate1a_probe_vector.py`: `e099fe249a7f1623784b1d372c4c9fc93892d413b662c1c3fdff1ca282da0453`
- `/home/zyc/bigreen_gate1a_exact_20260924/gate1a_contract.json`: `68121bc9225646e37fcf0233e769b694d9dbaec382723f45b8e80ffc73cea334`
- `evidence/environment_level_benchmark_v0/e0/E0_ENVIRONMENT_ASSET_INVENTORY.tsv`: `5e7fd902a047fab8a1dbd303f1f41431c4acd5df6f8cccb7c34bb13392f67672`
- `/home/zyc/e1_repo_20260925/research/environment_level_benchmark_v0/E1_CROSS_HOUSE_CONTRACT_CHARTER_20260925.md`: `37f1ab628af449295b1daa6664ded7088e53b7ba36df0d76a00342803f1ec3c0`
- `/home/zyc/e1_repo_20260925/research/environment_level_benchmark_v0/E1_IMPLEMENTATION_RULES_20260925.md`: `b108cc220365733449cc3af87113c70aab1d6895797945837723f5e61da8f76c`
- `/home/zyc/e1_repo_20260925/research/environment_level_benchmark_v0/build_e1_cross_house_contract_vm.py`: `5194dbec8cb7aca31b8519c32dc8ea0fc81583d692ef10f9d8f9f204028177ac`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01/OccupancyGrid3D.csv`: `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H01_air_seed0/off/geometry_export/pruned_meta.json`: `dabf0f188fc2d1723e2ffa1d5539c2945717569e17dceae3f05d18f67101088d`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H01_air_seed0/off/geometry_export/pruned_occupancy.bin`: `697f4326ba74b2f5d5075e72dbce0924a7c0be487d3d78898737b67d0a4229aa`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H01_air_seed1/off/geometry_export/pruned_occupancy.bin`: `697f4326ba74b2f5d5075e72dbce0924a7c0be487d3d78898737b67d0a4229aa`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House02/OccupancyGrid3D.csv`: `9402690152be4568ced8f2256e9098d82691aaaa1f22a1887eeac55d0e5d098d`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H02_seed0/off/geometry_export/pruned_meta.json`: `60efd1fe681d91b189fa270ad704e2f052af6513d87ae363cff62e7af056ee3b`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H02_seed0/off/geometry_export/pruned_occupancy.bin`: `bc640b1a59cd60db7f502f6c9ddbcb949b86ab9795c8c1efb2ff6603c774cb69`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H02_seed1/off/geometry_export/pruned_occupancy.bin`: `bc640b1a59cd60db7f502f6c9ddbcb949b86ab9795c8c1efb2ff6603c774cb69`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House03/OccupancyGrid3D.csv`: `ac8c9e69e762c8941dab46cd7e804684c2aa50dc6f0912806d19b070c135c4af`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H03_seed0/off/geometry_export/pruned_meta.json`: `cdda9e893a35fb2ee3e094a5d66b23acb1503afc61210f2a038a1117b607c3e5`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H03_seed0/off/geometry_export/pruned_occupancy.bin`: `32d362e73211532547d76f699e957ca3c0f3f6f2b3f6cc4f4fa862cf4f4943d7`
- `/home/zyc/rmfe_v2_runtime_causal_20260814_a2_002/house123/runs_2seed_v4/H03_seed1/off/geometry_export/pruned_occupancy.bin`: `32d362e73211532547d76f699e957ca3c0f3f6f2b3f6cc4f4fa862cf4f4943d7`
