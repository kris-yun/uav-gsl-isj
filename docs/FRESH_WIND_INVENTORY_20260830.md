# CTT H01 FRESH WIND INVENTORY — 2026-08-30

Status: **FRESH_WIND_AVAILABLE** (not `FRESH_WIND_INPUT_BLOCKED`)

This document records the authoritative inventory of House01 wind realizations
available in the VMware shared dataset. It is metadata/provenance only; no
source-ranking or test performance has been computed from any fresh field.

---

## 1. VMware shared-mount resolution

| item | value |
|---|---|
| Windows host path (authoritative) | `D:\ZYC\A-gas\workspace` |
| VM guest mount | `/mnt/hgfs/workspace` |
| VM hostname | `zyc-virtual-machine` |
| VM SSH | `zyc@192.168.111.128` |
| VMX shared-folder entry | `sharedFolder4`: `D:\ZYC\A-gas\workspace` → guest name `workspace` |
| House01 wind CSV root (host) | `D:\ZYC\A-gas\workspace\GADEN_files\scenarios\House01\wind_simulations` |
| House01 wind CSV root (guest) | `/mnt/hgfs/workspace/GADEN_files/scenarios/House01/wind_simulations` |
| Native (converted) wind root (guest) | `/home/zyc/rmfe_cl_env/H01/wind` |
| CTT context manifest (guest) | `/home/zyc/CTT_H01_NATIVE_WIND_CONTEXTS_20260830/context_manifest.json` |

The dataset was already present in the shared folder. **No Zenodo re-download
was performed.**

## 2. Wind realization structure

House01 ships four GADEN/OpenFOAM wind configurations. Each configuration is a
time series of **11 static CFD wind snapshots** (`*_0.csv` … `*_10.csv`), each a
full 3-D vector field over the House01 environment grid.

| config | direction | speed | frames |
|---|---|---|---|
| `1,3-2,4_fast` | 1,3 → 2,4 | fast | 0..10 (11) |
| `1,3-2,4_slow` | 1,3 → 2,4 | slow | 0..10 (11) |
| `2,4-1_fast` | 2,4 → 1 | fast | 0..10 (11) |
| `2,4-1_slow` | 2,4 → 1 | slow | 0..10 (11) |

Total: **44 primary wind CSVs**. Each frame also has legacy split `*_U/_V/_W`
component files; these are the old GADEN split format and must pass through the
frozen converter before the modern GADEN core accepts them.

## 3. Converter (byte-level provenance)

The `rmfe_wind_converter` converts `config_<frame>.csv` → binary
`wind_iteration_<frame>` accepted by the modern GADEN core.

- binary: `/home/zyc/rmfe_wind_converter_install_v4/rmfe_wind_converter/lib/rmfe_wind_converter/rmfe_wind_converter`
- source: `/home/zyc/rmfe_wind_converter_src/rmfe_wind_converter.cpp`
- grid cells: **327294**; frames per config: **11**
- **Verification**: a byte-level re-run of `2,4-1_fast` on 2026-08-30 reproduces
  the existing `/home/zyc/rmfe_cl_env/H01/wind/wind_iteration_*` hashes exactly
  (`wind_iteration_1 = c9f9d44a…`, `wind_iteration_10 = 3d161a7a…`).

## 4. Consumption status

The frozen `CTT_H01_NATIVE_STATIC_WIND_CONTEXTS_V1` manifest maps CTT context
`c` (0..9) to the immutable original `2,4-1_fast` frame `c+1`
(`wind_iteration_{c+1}`), repeated into native slots 0..10.

| context | split | source frame | binary iteration | binary SHA-256 |
|---|---|---|---|---|
| 0 | train | 1 | wind_iteration_1 | c9f9d44a… |
| 1 | test (diagnostic-only) | 2 | wind_iteration_2 | 7077e5de… |
| 2 | test (diagnostic-only) | 3 | wind_iteration_3 | a314adf0… |
| 3 | train | 4 | wind_iteration_4 | 1df0613e… |
| 4 | validation | 5 | wind_iteration_5 | 6048ca23… |
| 5 | train | 6 | wind_iteration_6 | fe61217b… |
| 6 | train | 7 | wind_iteration_7 | dccfe0ad… |
| 7 | validation | 8 | wind_iteration_8 | e621dad0… |
| 8 | train | 9 | wind_iteration_9 | a0b87056… |
| 9 | train | 10 | wind_iteration_10 | 3d161a7a… |

Therefore **10 frames are consumed** (`2,4-1_fast` frames 1..10). Contexts 1 and
2 are permanently diagnostic-only and may never be reused as confirmatory.

## 5. Fresh eligibility

**34 frames are eligible-fresh**:

- `2,4-1_fast` frame 0 (`wind_iteration_0`) — never mapped to any CTT context;
- `1,3-2,4_fast` frames 0..10 (11 frames);
- `1,3-2,4_slow` frames 0..10 (11 frames);
- `2,4-1_slow` frames 0..10 (11 frames).

Independence caveat: frame 0 is byte-identical across `1,3-2,4_fast`,
`2,4-1_fast`, `2,4-1_slow` (shared initial condition); only `1,3-2,4_slow`
frame 0 differs. Frames 1..10 diverge per config. For maximum held-out wind
media, fresh logical contexts should be drawn from **frames 1..10 of the three
unused configs** (30 distinct diverged fields).

### Prior native exercise (transparency)

All four configs were previously exercised by the **native `main_v8` PMFS
forward simulator** in the TADM/PMFS C0 context bank
(`house1_c0_context_bank_20260818`, 2026-08-20). This is a native forward
export of a *different* method (PMFS baseline), not CTT neural M1
training/validation/diagnosis, so it does **not** consume the configs for the
CTT neural M1 confirmatory test. Recorded here for full provenance.

## 6. Proposed fresh mapping (preregistered; lock at PHASE 2)

Logical IDs are labels only. Proposed mapping, to be frozen before any fresh
confirmatory data is opened:

| logical ID | purpose | config | frame |
|---|---|---|---|
| 10 | confirmatory | `1,3-2,4_fast` | 1 |
| 11 | confirmatory | `1,3-2,4_slow` | 1 |
| 12 | confirmatory | `2,4-1_slow` | 1 |
| 13 | confirmatory | `1,3-2,4_fast` | 10 |
| 14 | closed-loop | `1,3-2,4_slow` | 10 |
| 15 | closed-loop | `2,4-1_slow` | 10 |

## 7. Map / scene hashes

| artifact | SHA-256 |
|---|---|
| `OccupancyGrid3D.csv` | `846003ffbbc8e99aa322cf189356399412763710e937bb5e5316186afccf17cb` |
| `occupancy.pgm` | `41922bd418b6b48dd6e2525783269be76a495322fffe37920f63b6fcc402f646` |
| `occupancy.yaml` | `291dcbdf9bde61874ebd3a0139b0948d8d53a452a313401bcd70646120e4b31f` |

## 8. Verdict

```text
FRESH_WIND_AVAILABLE
```

34 eligible-fresh H01 wind frames exist (requirement: 6). No copying,
renaming, rotating, perturbing, or noise injection was performed. The full
per-frame SHA-256 table is in
`experiments/cg_pc_ctt/ctt_final_hazard_20260830/FRESH_WIND_INVENTORY_20260830.json`.
