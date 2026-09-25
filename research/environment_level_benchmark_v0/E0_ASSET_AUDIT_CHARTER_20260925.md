# E0 — Environment-Level Benchmark Asset Audit

Date: 2026-09-25

Status: **ZERO-SIMULATION INVENTORY ONLY**

Purpose: determine what environment-level GADEN plume data already exist before any new benchmark generation.

## 1. Environment universe

Canonical operator set from the frozen inventory:

### House01
- `1,3-2,4_fast`
- `1,3-2,4_slow`
- `2,4-1_fast`
- `2,4-1_slow`

### House02
- `3,5-1_fast`
- `3,5-1_slow`
- `4,5-3_fast`
- `4,5-3_slow`

### House03
- `1-2,5_fast`
- `1-2,5_slow`
- `5-3_fast`
- `5-3_slow`

Total canonical environments/operators: 12.

## 2. Audit only — no generation

For each of the 12 environments, recursively inventory existing gas simulations and report:
- source coordinates / source ID if recoverable;
- gas type/source-position contract;
- plume seed or independent-realization identifier;
- simulation length / available iterations;
- concentration output availability;
- compatibility with the frozen D1R 10-time ×30-probe extractor;
- relevant file hashes;
- whether the run already appeared in previous evidence branches.

Do not create, rerun, modify, rename, or repair plume simulations during E0.

## 3. Required summary table

One row per environment with:
- `house`;
- `wind`;
- `N_existing_source_positions`;
- `N_existing_independent_realizations_total`;
- min/median/max realizations per source;
- `N_sources_extractable_under_D1R_operator`;
- whether at least 4 sources have >=4 independent realizations;
- whether at least 6 sources have >=4 independent realizations;
- whether the environment can participate in an environment-held-out mechanism benchmark with zero new runs.

## 4. Do not count pseudoreplicates

Multiple output files from one plume run are not independent realizations.

Wind iterations inside one canonical wind are not separate environments.

Different source positions inside one wind are not separate environments.

Report separately:
- N_environment;
- N_source;
- N_realization.

## 5. Benchmark design only after E0

After E0, the primary thread may design the smallest fill-in benchmark that creates enough independent environments for leave-environment-out discovery.

No target run count is preregistered before the inventory.

Do not automatically choose 144/162/216 runs.

Reuse existing valid data wherever possible.

## 6. Desired future benchmark properties

The future benchmark should allow:
- environment-held-out discovery from day one;
- at least one entire House untouched during mechanism development;
- wind-family-held-out tests within development Houses;
- proper source probability metrics, not field MSE alone;
- comparison of environment-invariant versus environment-conditioned hypotheses;
- no target-environment dense source bank as a deployment assumption.

## 7. Deliverables

1. `E0_ENVIRONMENT_ASSET_INVENTORY.tsv`
2. `E0_ENVIRONMENT_SUMMARY.json`
3. `E0_REUSE_MAP.md`
4. `E0_DATA_GAPS.md`
5. hashes/provenance note.

Final E0 decision is one of:
- `E0_EXISTING_ASSETS_SUFFICIENT_FOR_ENVIRONMENT_BENCHMARK`
- `E0_PARTIAL_ASSETS_REQUIRE_MINIMAL_FILL_IN`
- `E0_EXISTING_ASSETS_TOO_SPARSE_FOR_VALID_GENERALIZATION_STUDY`.

No scientific mechanism PASS/FAIL is allowed at E0.