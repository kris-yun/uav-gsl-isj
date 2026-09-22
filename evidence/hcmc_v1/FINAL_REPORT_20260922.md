# HCMC V1 independent offline validation — final report

## Decision

`HCMC_V1_INDEPENDENT_OFFLINE_NO_GO`

This is a scientific NO-GO, not an execution HOLD. Six new stochastic GADEN plume realizations were generated and six valid 300 s Native trajectories were recorded. Under the frozen HCMC V1 rule, `H01_R2026092201` has zero valid candidates and zero finite positive HCMC mass. Its HCMC posterior and endpoint error are therefore undefined. The preregistered six-case primary gate cannot be evaluated without changing the method, so no fallback, parameter adjustment, Native/HCMC fusion, or HCMC closed loop was performed.

## Scope and freezes

- Frozen source revision: `6afc592a5b43093efad7a4bda0c48c0cbb8a7cec`.
- Data classification: `TRUE_INDEPENDENT_PLUME_VALIDATION`.
- HCMC code SHA-256: `67971746c132d708b41e7bb4ab40ddaabfd828bdf91e14623685331f3134f62e`.
- Linked-native endpoint SHA-256: `9d0954c32021f6b808ba4bec06e98ea9fe8193b25cc4ed33d4189330d40c9ac6`.
- R2 execution runtime SHA-256: `b06c2036da91ef22285d1cb5d4d08172e828956fc5844d8a2044a4221a8c2cce`.
- Truth was not loaded during the source-blind definability audit (`truth_inputs_loaded=false`).
- The only runtime source change was the exact three-file terminal lifecycle correction from frozen commit `b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`; it restores the deadline `RESULT IS` anchor and does not alter PMFS/HCMC scientific logic.

## Independent realization identities

| Case | Plume seed | Navigation seed | Gas-realization content SHA-256 |
|---|---:|---:|---|
| H01_R2026092201 | 2026092201 | 2 | `f374d95e1c541d6b84dba38624f2e5131e316fad426215937d01b6ee23cc1c72` |
| H01_R2026092202 | 2026092202 | 3 | `0f49480a37d5e95f59066602ceee882d3dcb90d94095ba4c72ceb9e32aeb0a1d` |
| H02_R2026092211 | 2026092211 | 2 | `6ad203fd3be068bd2279a85835e5188af7d3bbe4a4b5c58b6ae4f2551e54d83f` |
| H02_R2026092212 | 2026092212 | 3 | `dc61389dd6a9af40dc42704b41454108404322a7d8e3262fa66c4ceb0e61c852` |
| H03_R2026092221 | 2026092221 | 2 | `35797a8b4543ea7e9cea1e0158a8266da605a64ea99327512568338201a5b78b` |
| H03_R2026092222 | 2026092222 | 3 | `1dfe20a0e05c69428f90bc1080d044200ed237c1cc1febafb3e13a3510436589` |

Each realization contains 1,803 contiguous frames (`0..1802`). Identical seed generation was byte-identical and distinct plume seeds produced distinct content hashes. House01 retained `raw_house1_snapshot`; House02/House03 retained `gaden_player`.

## Primary endpoint matrix

| Case | Native error (m) | HCMC V1 error (m) | Native endpoint parity | HCMC status |
|---|---:|---:|---|---|
| H01_R2026092201 | 4.5967302383 | undefined | pass, delta 0.0032697617 m | `UNDEFINED_ALL_CANDIDATES_INVALID` |
| H01_R2026092202 | 4.2738039607 | 4.9959088678 | pass, delta 0.0038039607 m | defined |
| H02_R2026092211 | 6.9340917225 | 2.8659894743 | pass, delta 0.0040917225 m | defined |
| H02_R2026092212 | 4.3578692040 | 2.4257448754 | pass, delta 0.0021307960 m | defined |
| H03_R2026092221 | 7.9527234694 | 8.2402171868 | pass, delta 0.0027234694 m | defined |
| H03_R2026092222 | 7.9607924195 | 8.4551885288 | pass, delta 0.0007924195 m | defined |

Native six-case mean is `6.012668502394403 m`. HCMC six-case mean, pooled improvement, non-worse count, six-case false-confident-collapse count, random-leaf control, spatial-shuffle control, and anti-metric-gaming diagnostics are all `NOT_EVALUABLE` because the real HCMC posterior is undefined in one frozen case.

For transparency only, the five defined cases have HCMC mean `5.39660978660079 m`, corresponding Native mean `6.295856155216992 m`, diagnostic improvement `14.28314666736869%`, non-worse `2/5`, and false-confident collapse `1/5`. These partial figures do not replace the preregistered six-case gate.

## Source-blind failure mechanism

At H01_R2026092201's selected update (`t=195.500216873 s`), the final bank has 121 leaves but zero valid HCMC candidates and zero valid slope comparisons. After frozen confidence filtering, the measured field is constant at `0.09999968582848939`. The frozen rule assigns invalid-candidate density zero; total rank mass is therefore zero. No Native or uniform fallback is permitted.

The other cases have 75, 118, 109, 114, and 114 valid candidates respectively. This establishes that the failure is a method-domain definability failure on a valid independent plume/trajectory, not a missing file, recorder failure, endpoint mismatch, or use of truth during fitting.

## Execution integrity

- All six accepted Native runs contain exactly 1,500 contiguous rows in each sensor, pose, and wind trace, covering 0.2–300.0 s.
- All six have a complete final context bank, matching launch/runtime/realization hashes, terminal status, and logged Native endpoint.
- Linked-native parity passes all six at the frozen 0.011 m tolerance.
- Earlier invalid attempts are preserved separately and excluded; see `EXECUTION_ATTEMPTS_20260922.md`.
- Discovery replay remains replay-only evidence: linked-native HCMC mean `2.431575906400006 m`, improvement `56.227731501943104%`, non-worse `6/6`.

## Evidence locations

- Repository evidence: `evidence/hcmc_v1/`.
- VM independent plume data: `/home/zyc/hcmc_v1_independent_data_20260922`.
- VM accepted Native runs: `/home/zyc/hcmc_v1_native_runs_20260922`.
- VM excluded attempts: `/home/zyc/hcmc_v1_native_runs_20260922/failed_attempts`.
- VM source-blind freeze: `/home/zyc/hcmc_v1_source_blind_definability_20260922/PRE_TRUTH_DEFINABILITY_FREEZE.json`.
- VM final diagnostics: `/home/zyc/hcmc_v1_independent_nogo_result_20260922.json` and `/home/zyc/hcmc_v1_independent_nogo_matrix_20260922.csv`.

No HCMC closed loop was run and no HCMC V2 was created.
