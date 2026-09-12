# M1R code lineage: historical result to current callable implementation

Read-only source/configuration inspection at `75b3adca0cf79930add72cffa6d399721ab42e28`, 2026-09-12. This document is the only new file from this inspection. No VM, bank payload, build, or new closed-loop run was used.

**Finding:** the M1R source-scoring change associated with the historical result is real and remains callable. It is not the current launch default, and `pfdi_mode=cer_ratio_m1` alone does not restore the historical persistence law. Source availability does not prove that the historical improvement is reproducible with the current binary, nor establish its causal mechanism.

## 1. Version ledger

| Version/evidence | Observed implementation or runtime identity | What can be claimed |
|---|---|---|
| 8 September M1R runtime | Manifest declares `c62a54a+cer-ratio-working-tree`; algorithm SHA-256 `62df6d257bda7123dea67c3142b877fc3b8a8d8550012c18bfd3f456925ee533`. H01 manifest lines 7–11; H02/H03 manifests declare the same mode/source/binary. | Historical runtime identity is recorded, but its source label includes an uncommitted tree. |
| First preserved source `8dd5977` | `PMFS.cpp:99–102,253–254,367–373`: enables event evidence and contrastive ratio, one transport member, records every internal measurement block. `Simulations.cpp:6478–6498`: initializes previous concentration to zero per candidate/member evaluation, then updates it after each block. | Preserved historical source-level binding; no historical rolling flag was needed or present. |
| Later source `c41fdb3` | `Simulations.cpp:474–475,6708–6709`: non-sequential mode starts at event zero and uses the fixed window-boundary concentration. For M1R that boundary concentration is zero at every event. | This is a semantic change in the persistence input; it must not be projected backward onto the 8 September run. |
| Instrumentation commit `3b0957d`, retained in current HEAD | Adds `m1r_v41_historical_rolling_persistence`; `PMFS.cpp:125–128` defaults false and permits true only with `cer_ratio_m1`; `Simulations.cpp:6680–6681,6717–6731` chooses rolling or boundary input. | Current code can restore the historical M1R observation-law branch explicitly. This is not a claim of whole-program or binary identity. |
| 12 September instrumented runtime | Manifest declares `c41fdb3+m1r-v41-instrumented`, binary SHA-256 `006fd79a950f48bb76308174573048b26e37c3815466cf69ba22bcbddf1e2a52`. All three preserved algorithm launch files set the historical flag true. | New instrumented development replication. Existing comparison explicitly says historical equivalence is false; binary and observation/trajectory records differ. |

Historical line numbers above refer to `git show <revision>:<path>`, not current files. File paths: `ros2_package/src/gsl_server/algorithms/PMFS/PMFS.cpp` and `ros2_package/src/gsl_server/algorithms/PMFS/internal/Simulations.cpp`.

Provenance authority: `docs/PMFS_M1R_IMPLEMENTATION_FREEZE_20260912.md:7–14`; `evidence/m1r_freeze/M1R_IMPLEMENTATION_MANIFEST.json:3–8` records the first preserved commit and `historical_binary_bytes_available=false`. The source/binary relationship therefore remains `PASS_WITH_PROVENANCE_LIMIT`.

## 2. Current executable call path

| Stage | Current source location | Effect for `cer_ratio_m1` |
|---|---|---|
| Mode and settings | `PMFS.cpp:105–149`; `PMFS.hpp:102–111` | Event evidence and ratio true; centered log odds, sequential assimilation, physical-stop-only, post-warmup-only and transport pooling false; one member. |
| Pass settings to simulator | `PMFS.cpp:312–319`; `internal/Simulations.hpp:91–99,173–180`; `internal/Simulations.cpp:363–380` | Historical flag reaches and is stored by `Simulations`; it is not an unused launch argument. |
| Record observations | `PMFS.cpp:441–451`; `internal/Simulations.cpp:386–401` | Every completed internal measurement block is eligible. Historical M1R does not switch to one factor per physical stop. |
| Initialize context | `internal/Simulations.cpp:574–577,6577–6594,6605–6633` | Valid first-level candidates define arithmetic-mean hit probability at each event cell. Current context is organized per member; M1R has one member. |
| Compute candidate score | `internal/Simulations.cpp:6641–6656,6678–6731` | Bernoulli log likelihood uses `logit(p_persist)+logit(p_sim)-logit(p_context)`, with probability clipping to `[1e-4,1-1e-4]`; rolling flag changes the previous-concentration input. |
| Replace native score | `internal/Simulations.cpp:836–868,6788–6819` | Ratio mode bypasses native map likelihood, then assigns event likelihood to `result.sourceProb`, per-cell source values, and `LeafScore.score`. This is actual inference, not shadow logging. |
| Native refinement/consumption | `internal/Simulations.cpp:574–589,677–684,751–771` | Ratio scores feed PMFS refinement and normalization; refined candidates also receive ratio scores. No CTPI planner is enabled by this mode (`PMFS.cpp:152–156`). |

The historical counterparts already initialized context/applied the scores at `8dd5977:Simulations.cpp:491–492` and replaced `result.sourceProb`/leaf scores at `6516–6527`.

**Precise default semantics:** with `cer_ratio_m1` and rolling=false, `eventEvidenceSequentialAssimilation=false` makes `eventEvidenceWindowStart=0` (`Simulations.cpp:476–477`). The previous concentration is therefore zero, not the persistence probability. At threshold `0.1`, persistence is the nonzero normal-tail probability `0.5*erfc(log1p(0.1)/sqrt(2))`, approximately `0.462`. With rolling=true, the first event still starts from concentration zero and each later event uses the preceding recorded block concentration. Neither path is a fitted latent FOPDT state.

## 3. Runtime settings versus defaults

| Setting | 8 September M1R | 12 September instrumented M1R | Current entry-point default |
|---|---|---|---|
| Mode / arm | `cer_ratio_m1` / `M1R` | Same | launch: `UNSET` / `UNSET`; runner requires arm |
| Method identity | `CTPI_G2_M1_M2` / `ctpi_two_module` | Same | `CTPI_CREL_TSDC_PIP` / `ctpi_three_module`; this default identity does not allow M1R |
| Historical rolling flag | No parameter; rolling hardcoded | true | false in runner, launch and C++ |
| Seed | 12 | algorithm 12, sensor 12 | launch seed 0; runner requires algorithm seed and defaults sensor seed 12 |
| Horizon | 240 s | 240 s | direct launch 300 s; runner 240 s |
| Source-update interval | 3 | 3 | direct launch 10; runner requires explicit value |
| Warmup max/min | 3 / 1 | 3 / 1 | direct launch 500 / 200; runner requires explicit values |
| Context export / lightweight audit | false / parameter absent | true / true | false / false |

These generic launch defaults (method identity, seed, horizon, update interval and warmup) were already present at `8dd5977:launch.py:207–208,234,236,247,252–253,287`; they are differences from the historical **run**, not newly introduced default regressions. The later persistence implementation and its opt-in restoration are the material semantic lineage change.

Current default references: `closed_loop/ctpi/vgr_gsl_pmfs_ctpi_fasttrack.launch.py:63–77,224–226,251–254,265–271,305,322–325`; `closed_loop/ctpi/run_ctpi_fasttrack_case_safe_20260903.sh:12–29,37–43,97,342–343`. The historical batch explicitly supplied the run settings and method identity at `tools/cstar_run_cer_ratio_house123_seed12_20260908.sh:15–21`.

Runtime sources (algorithm parameter files):

- Historical H01: `evidence/cstar_cer_ratio_house123_seed12_20260908/H01_seed12_M1R/tmp/launch_params_z3v5yyvx:8–9,39–45,56–58,84–87`.
- Instrumented H01: `evidence/m1r_instrumented_20260912/H01_seed12_M1R/tmp/launch_params_ll6rw3ei:8–9,37–47,58–60,86–89`.
- Instrumented H02/H03: same mode/rolling settings at `H02_seed12_M1R/tmp/launch_params_afedjh4l:37–38,58` and `H03_seed12_M1R/tmp/launch_params_kp53z88s:37–38,58`, under `evidence/m1r_instrumented_20260912/`.
- Historical and instrumented H01 formal manifests: `evidence/cstar_cer_ratio_house123_seed12_20260908/H01_seed12_M1R/formal_runtime_manifest.json:7–11,18–29`; `evidence/m1r_instrumented_20260912/H01_seed12_M1R/formal_runtime_manifest.json:5–13,20–31`.

## 4. Configuration fragment for preserving source-level reproduction

This is a documentation fragment for the existing safe runner, not a command executed by this inspection. House geometry, realization, bridge/preflight binding, install root, and a fresh run directory still have to come from the corresponding preserved manifest and runner contract.

```bash
ARM=M1R
METHOD=CTPI_G2_M1_M2
METHOD_FAMILY=ctpi_two_module
SEED=12
SENSOR_SEED=12
TIMEOUT_SEC=240.0
STEPS_SOURCE_UPDATE=3
MAX_WARMUP_ITERATIONS=3
MIN_WARMUP_ITERATIONS=1
M1R_V41_HISTORICAL_ROLLING_PERSISTENCE=true
```

The runner maps `ARM=M1R` to `pfdi_mode=cer_ratio_m1` and passes the rolling parameter through launch to C++. To match the instrumented **logging configuration**, also use `CONTEXT_BANK_EXPORT_ENABLED=true`, a fresh explicit export directory, and `M1R_V41_LIGHTWEIGHT_AUDIT=true`; C++ requires export plus historical rolling for lightweight audit (`PMFS.cpp:184–189`). These export flags are not required merely to activate the historical scoring law. Do not apply the rolling flag to A0 or `cer_ratio_m1_m2`: current C++ rejects both.

Preserve `8dd5977`, the historical run folders, source/blob manifest, and both recorded binary digests as separate identities. Any rebuilt current executable must receive its actual source/tree and binary digest. Label it source-law restoration or new instrumented replication, never the original binary or historical exact replay. Existing evidence already records this limit at `evidence/m1r_mechanism/M1R_HISTORICAL_REPLICATION_COMPARISON.json:2–5,30–34`.
