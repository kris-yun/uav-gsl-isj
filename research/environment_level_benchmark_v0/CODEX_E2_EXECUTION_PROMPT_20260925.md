# CODEX TASK — E2 Minimal Cross-Environment Benchmark Acquisition

Branch:
`research/generalization-refoundation-v0`

Authoritative inputs:
- `research/environment_level_benchmark_v0/E2_MINIMAL_FILLIN_CHARTER_20260925.md`
- E1 final commit `b3be882043fee8b2a6becb56507433cdcf2d111b`.

## Scope

Acquire exactly the staged seven-environment benchmark defined in E2.

Total authorized new plume runs: **168**.

This is benchmark infrastructure, not a mechanism experiment.

## Hard scientific restrictions

- Do not run LSC/WCIG/IPTO/M4 or any new mechanism analysis.
- Do not change source/probe contracts.
- Do not expose scientific summaries from SEALED_DEV_HOLDOUT or SEALED_FINAL_HOUSE.
- Do not generate any reserve environment.
- Do not add seeds because a plume looks weak or a statistic looks noisy.

## Environment roles

OPEN_DISCOVERY:
1. H01 `1,3-2,4_fast`
2. H02 `3,5-1_slow`
3. H02 `4,5-3_slow`

SEALED_DEV_HOLDOUT:
4. H01 `2,4-1_fast`
5. H02 `3,5-1_fast`

SEALED_FINAL_HOUSE:
6. H03 `1-2,5_fast`
7. H03 `5-3_fast`

## Acquisition

For each environment:
- six E1-frozen sources;
- four independent realizations/source;
- deterministic seed formula from E2 charter;
- source z=0.20 m;
- retain complete raw concentration cube;
- hash all inputs/outputs.

## Sealing

For OPEN_DISCOVERY:
- extract and package frozen 10x30 vectors only after all runs are complete and hashed.

For both sealed role groups:
- automated infrastructure QC only;
- final user-visible/report output must contain only PASS/FAIL QC, run/file counts, metadata and hashes;
- do not print or package human-readable concentration summaries, source-level pooled vectors, source-rank metrics, pairwise distinguishability or plots.

Raw sealed data may remain on VM in a clearly marked sealed path for later one-time unsealing.

## Stop rule

Stop immediately if:
- source/probe geometry differs from E1;
- a canonical wind hash differs from frozen provenance;
- deterministic seed uniqueness fails;
- a required environment cannot generate valid runs under the frozen source z/geometry.

Do not repair scientific inputs after outcome inspection.

## Final deliverables

- branch / final commit;
- `E2_RUN_MANIFEST.tsv`;
- `E2_ENVIRONMENT_MANIFEST.tsv`;
- `E2_OPEN_DISCOVERY_10x30.npy` and index metadata;
- sealed dev/final hash manifests;
- `E2_QC_SUMMARY.json`;
- SHA256 manifest;
- review package path / bytes / SHA256;
- exact count of completed new plume runs.

Final decision must be exactly one:
- `E2_PASS_BENCHMARK_ACQUIRED_AND_SEALED`
- `E2_FAIL_BENCHMARK_ACQUISITION_INCOMPLETE`

Stop after E2. Do not perform mechanism discovery.