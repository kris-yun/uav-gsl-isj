# Six accepted Native runs: raw independent-plume context banks

This package is a byte-verified copy of the six accepted runs under `/home/zyc/hcmc_v1_native_runs_20260922/`. It is raw development material for analyzing the frozen `HCMC_V1_INDEPENDENT_OFFLINE_NO_GO` result. It is **not** a new experiment, a HCMC closed loop, or a six-run/five-update bank.

## Critical inventory correction

Each accepted 300 s Native run contains **exactly one** recorded source update, `context_bank/source_update_0001/`. There are no `source_update_0002` through `source_update_0005` directories. `source_update_timing.csv` also has one data row in each case. The screenshot's premise that five complete updates had already been retained per new plume is not supported by the files. No missing updates were reconstructed or simulated.

| Accepted case | House | Recorded source updates | New-plume content SHA-256 |
|---|---|---:|---|
| `H01_R2026092201` | House01 | 1 | `f374d95e1c541d6b84dba38624f2e5131e316fad426215937d01b6ee23cc1c72` |
| `H01_R2026092202` | House01 | 1 | `0f49480a37d5e95f59066602ceee882d3dcb90d94095ba4c72ceb9e32aeb0a1d` |
| `H02_R2026092211` | House02 | 1 | `6ad203fd3be068bd2279a85835e5188af7d3bbe4a4b5c58b6ae4f2551e54d83f` |
| `H02_R2026092212` | House02 | 1 | `dc61389dd6a9af40dc42704b41454108404322a7d8e3262fa66c4ceb0e61c852` |
| `H03_R2026092221` | House03 | 1 | `35797a8b4543ea7e9cea1e0158a8266da605a64ea99327512568338201a5b78b` |
| `H03_R2026092222` | House03 | 1 | `1dfe20a0e05c69428f90bc1080d044200ed237c1cc1febafb3e13a3510436589` |

The hashes above identify the generated GADEN gas-realization contents, not the run directories. See `../INDEPENDENT_DATA_FREEZE_20260922.json` for generator, realization, and binding provenance. This package does not include the 761 MB plume data themselves; those remain on the VM under `/home/zyc/hcmc_v1_independent_data_20260922/`.

## Contents

For each case, `context_bank/source_update_0001/` contains the five nonempty scientific CSVs: `candidate_manifest.csv`, `candidate_support_alignment.csv`, `measured_hit_probability.csv`, `source_posterior.csv`, and `estimated_wind.csv`. The `candidate_maps/` directory was empty in all six source runs and is not represented by Git. Each run also contains `context_bank/source_update_timing.csv`, `context_bank/context_bank_contract.json`, `runtime_manifest.json`, `run_status.json`, `official_gsl_results.csv`, `official_navigation_path.csv`, the sensor/pose/wind traces, and `launch.log` (including the terminal result).

`RAW_SHA256SUMS.txt` records SHA-256 for all 98 copied source files. It was computed on the VM before transfer and independently verified against the extracted Windows files. `ACCEPTED_RAW_CONTEXT.tar.gz` contains the same six accepted run trees; its SHA-256 is `bbed3eaa45442e539843f8f45bab5fa0f796623417fa4c6320089cf47ed54957`.

The archive and browsable copy explicitly exclude `failed_attempts/`, aggregate `results/` (which mix failed attempts), ephemeral `tmp/`, `ros_log/`, and Linux-only `scenario_bind/` symlinks. Original accepted run files were not modified. Archive and Git contents were sourced from the same accepted directories. `.gitattributes` disables text normalization here so CSV bytes remain identical to the VM copies.

The prior six discovery cases are **not** in this package. Do not infer from this package alone that the old six and new six form 12 independent plume realizations. Read the [final validation report](../FINAL_REPORT_20260922.md) and [source-blind definability freeze](../PRE_TRUTH_DEFINABILITY_FREEZE_20260922.json) before interpreting any HCMC score.
