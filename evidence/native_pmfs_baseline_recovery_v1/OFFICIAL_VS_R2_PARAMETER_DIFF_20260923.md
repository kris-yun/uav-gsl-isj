# Native PMFS baseline recovery: package and parameter audit

**Checkpoint:** audit only. No recovery run or rank result is claimed here.

## Source identity

The local reference was `D:\ZYC\A-gas\ASCi\GasSourceLocalization-humble.zip`, read without modification. Its SHA256 is `627f0e97a40331e437f1f6bbd4a6662b88bb5b8f56b3445fbf3eb15febe1a7b4`. Its sole top-level directory is `GasSourceLocalization-humble`; it contains no embedded `.git` metadata, so the ZIP itself does not identify a commit. Relevant PMFS and launch files were extracted to a separate read-only reference directory for inspection.

The comparison reference is `MAPIRlab/GasSourceLocalization`, branch `humble`, commit `4e141e162551e674f2f30ddb8859136c72139aac`. All **27 compared committed blobs** (the PMFS implementation directory, PMFS launch files, and `gsl_server/CMakeLists.txt`) are byte-identical to their ZIP entries. The ZIP's `main_simbot_launch.py` Git blob is `ad0159dc9a7d9395f050a7d50b6a1f7a0c8bf9db`, matching the upstream blob. [Per-file SHA256 table](OFFICIAL_PACKAGE_FILE_FINGERPRINTS_20260923.tsv) and [machine-readable provenance](OFFICIAL_PACKAGE_PROVENANCE_20260923.json) record the scope. This establishes PMFS-source parity for the compared files, not identity of every file in the 398 MB ZIP.

The frozen R2 contract was read from `reference/run_meaci_case_20260824.sh` (SHA256 `5ed3355005ac812bf64ce2d061665d67b207455ff34ca6deda21dc025ca95ce7`) and its archived launch file (SHA256 `0cd1ae4ad852bf548fd1ebc131e7f46f0d6d20603a2e4e71ae37c6831e40f2c9`). The archived launch SHA matches the H01 runtime manifest in `evidence/hcmc_v1/independent_raw_native_20260922_verified/H01_R2026092201/runtime_manifest.json`. The manifest identifies a different runtime binary (`b06c2036da91ef22285d1cb5d4d08172e828956fc5844d8a2044a4221a8c2cce`); source or build parity of that binary with the official ZIP is **not established** by this audit. The old raw evidence and runner were not edited.

## Effective PMFS parameter differences

The [full TSV](OFFICIAL_VS_R2_PARAMETER_DIFF_20260923.tsv) has 136 rows: every GSL parameter explicitly present in the official PMFS launch node, plus every declared R2 launch argument and explicit frozen-runner argument. Each row has exactly one of the charter's five categories. R2 values are the frozen runner defaults; environment overrides and actual runtime values require per-run verification. Rows that are launch metadata or separate GrGSL settings are retained for completeness rather than represented as active PMFS mechanics.

| Parameter | Official PMFS example | Frozen R2 runner default | Category |
| --- | ---: | ---: | --- |
| `useWindGroundTruth` | `true` | `false` | PMFS forward |
| `stepsSourceUpdate` | 3 | 10 | PMFS forward |
| `maxRegionSize` | 5 | 5 | PMFS forward |
| `sourceDiscriminationPower` | 0.3 | 1.0 | PMFS forward |
| `refineFraction` | 0.1 | 0.25 | PMFS forward |
| `deltaTime` | 0.1 | 0.2 | PMFS forward |
| `noiseSTDev` | 0.5 | 0.5 | PMFS forward |
| `iterationsToRecord` | 200 | 200 | PMFS forward |
| `maxWarmupIterations` | 500 | 3 | PMFS forward |
| `minWarmupIterations` | 200 effective default | 1 | PMFS forward |
| `blurSigmaX/Y` | 1.5 / 1.5 | 0 / 0 | PMFS forward |
| `hitPriorProbability` | 0.3 | 0.1 | PMFS hit map |
| `maxUpdatesPerStop` | 5 | 8 | PMFS hit map |
| `kernelSigma` | 1.5 | 0.5 | PMFS hit map |
| `kernelStretchConstant` | 1.5 | 1.5 | PMFS hit map |
| `confidenceMeasurementWeight` | 1.0 | 0.5 | PMFS hit map |
| `confidenceSigmaSpatial` | 1.0 | 0.5 | PMFS hit map |
| `localEstimationWindowSize` | 2 (PMFSLib default) | 2 | PMFS hit map |
| `scale` | 25 | 3 | VGR map adapter |
| `convergence_thr` | 1.5 | -1.0 | evaluation/stopping protocol |

The official launch contains a `SetLaunchConfiguration(minWarmupIterations=0)`, but it does **not** pass that value in the GSL node's parameter dictionary. `PMFSLib::GetSimulationSettings` therefore reads its default of **200**. Treating the unattached launch variable as the effective value would create a false discrepancy. The same PMFSLib code supplies `localEstimationWindowSize=2` when the launch omits it.

The official example has `useWindGroundTruth=True`, but its `gsl_server/CMakeLists.txt` defaults `USE_GADEN OFF`. With that compile setting, `PMFSLib::EstimateWind` compiles out the ground-truth branch and uses `/WindEstimation` regardless of the launch value. Thus the recovery binary must be built with `USE_GADEN` enabled and the branch must be observed at runtime. The official example's launch text alone does not prove a particular historical author's executable used ground-truth wind.

## Deviation disposition for a recovery runner

- **Official PMFS algorithm/forward parameters:** restore all effective official values in the Native arm, including hit-map and simulator settings. The R1 wind-only arm deliberately keeps the frozen R2 values for diagnostic decomposition; it is not a valid Native baseline. `infoTaxis`, `use_infotaxis`, and `allowMovementRepetition` occur in the shared official launch but need a call-site check before treating them as PMFS behavior.
- **VGR environment adapter:** retain House-specific VGR data, source/start coordinates, flight height, launch bridge, and map reduction `scale=3` only with a verified map-resolution/candidate-geometry rationale. The official `scale=25` belongs to the different PMFS example map; substituting it on VGR would change the candidate grid rather than restore a comparable source model. Record both grid metadata and exact candidate support in R0/R1.
- **Measurement/sensor protocol:** retain the frozen VGR dynamic sensor model, timestamp deduplication, settling and block settings so all three replay arms consume identical observations. These are environment differences, not official PMFS-source claims.
- **Budget/evaluation protocol:** retain the 300 s budget, fixed seed bookkeeping, and VGR stopping contract. `convergence_thr=-1` disables the official distance-based declaration criterion; this change must be declared and identical across compared VGR arms. Source truth coordinates may enter only post-freeze evaluation/logging, never forward simulation, candidate selection, or tuning.
- **Research instrumentation only:** context-bank export and hashes may remain if passive. PFDI, TNQC, TADM, P2, and posterior-guidance controls must be absent or explicitly disabled in the primary Native arm. The old R2 launcher declares many optional modules; their presence as arguments is not proof they were active. Validate runtime flags and code path before R0.

`GMRF-wind` is external and not pinned by the official ZIP. The exact source/build/binary provenance of any GMRF component used by R2 or an R1 adapted arm still needs recording. No GMRF-derived wind may enter the Native candidate simulator.

## Audit gate

**AUDIT PASS for the compared official PMFS files and parameter inventory.** **R0/R1 pending:** the recovery binary, `/wind_value` service type and response, actual wind path, numerical wind-field parity, candidate geometry, and replay have not yet been validated. Old six-run R2 evidence should be described as **VGR-adapted PMFS (GMRF-wind forward)** until recovery proves otherwise.
