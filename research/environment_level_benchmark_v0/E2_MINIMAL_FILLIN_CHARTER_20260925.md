# E2 — Minimal Cross-Environment Benchmark Fill-In

Date: 2026-09-25

Status: **DATA INFRASTRUCTURE ACQUISITION — 168 PLUME RUNS AUTHORIZED AFTER E1**

Upstream:
- `E0_PARTIAL_ASSETS_REQUIRE_MINIMAL_FILL_IN`;
- `E1_PASS_CROSS_HOUSE_CONTRACT_READY_FOR_FILLIN_DESIGN`.

## 1. Purpose

E2 builds one reusable environment-level benchmark.

It is NOT an experiment for LSC, WCIG, IPTO, M4, or any other candidate mechanism.

No scientific mechanism is allowed to PASS/FAIL during E2.

## 2. Frozen observation/source contract

Use exactly the E1 contracts at commit `b3be882043fee8b2a6becb56507433cdcf2d111b`:
- 30 FPS probes/House;
- 10 times: 100,150,200,250,300,350,400,450,500,550;
- 6 source cells/House = 3 frozen adjacent pairs;
- source/observation z = 0.20 m;
- full raw concentration cube retained for every run.

No source/probe substitution is permitted.

## 3. Seven acquisition environments

### OPEN_DISCOVERY

1. House01 / `1,3-2,4_fast`
2. House02 / `3,5-1_slow`
3. House02 / `4,5-3_slow`

These three environments may be used for the next mechanism-discovery stage.

### SEALED_DEV_HOLDOUT

4. House01 / `2,4-1_fast`
5. House02 / `3,5-1_fast`

Generate and hash now, but do not expose scientific concentration summaries, pairwise metrics, source scores, or plots to the primary thread until a candidate mechanism and its thresholds are frozen using OPEN_DISCOVERY only.

### SEALED_FINAL_HOUSE

6. House03 / `1-2,5_fast`
7. House03 / `5-3_fast`

The entire House03 scientific content remains sealed from mechanism discovery and development.

## 4. Acquisition depth

For every environment:
- 6 frozen sources;
- 4 independent plume realizations/source;
- 24 runs/environment.

Total:
`7 × 6 × 4 = 168 new plume runs`.

House totals:
- House01: 48;
- House02: 72;
- House03: 48.

## 5. Deterministic seed contract

Assign environment indices in the exact order listed above, 0..6.
Assign source indices by frozen E1 source-panel row order within House, 0..5.
Assign replicate index 0..3.

Use:
`seed = 2026110000 + 1000*environment_index + 10*source_index + replicate_index`.

Record both requested seed and simulator-resolved seed/provenance.

Any simulator limitation requiring a different seed encoding must be documented before the first plume run and preserve one-to-one deterministic mapping.

## 6. Raw-data requirement

Retain the complete concentration field/cube required for future re-extraction.

Do not retain only the 300-value pooled vector.

For every run hash:
- raw concentration cube;
- run metadata;
- source xyz;
- wind directory and wind-file SHA manifest;
- seed;
- extraction contract version.

## 7. Open-data extraction

For OPEN_DISCOVERY only, after all 72 runs are complete and hashed:
- extract the frozen 10×30 vector;
- verify finite/nonnegative;
- package source/wind/seed metadata;
- do not compute a new scientific mechanism during E2.

## 8. Sealed-holdout protocol

For SEALED_DEV_HOLDOUT and SEALED_FINAL_HOUSE:

Allowed automated QC:
- run completed;
- expected file/cube dimensions;
- all values finite;
- all values nonnegative;
- file nonempty / required frames present;
- hashes and metadata consistent.

Forbidden before unsealing:
- pooled 10×30 scientific vectors in human-readable report;
- source-wise concentration means/variances;
- energy/Bhattacharyya/LSC metrics;
- source classification/ranking/proper score;
- visualizations of concentration by source;
- hard/easy source-pair labels.

QC output for sealed environments must be PASS/FAIL only plus file/hash metadata.

## 9. Replacement policy

A run may be replaced only for a preregistered infrastructure/QC failure:
- crash/incomplete output;
- invalid dimensions;
- NaN/Inf;
- corrupted/missing file;
- seed collision/provenance failure.

A scientifically weak/zero plume is NOT automatically replaceable unless a zero-plume invalidity criterion was frozen before acquisition.

Any replacement uses the next deterministic spare replicate suffix and must be documented.

## 10. Reserve environments — do not generate

Keep the following canonical winds untouched as future environment-level reserves:

House01:
- `1,3-2,4_slow`;
- `2,4-1_slow`.

House02:
- `4,5-3_fast`.

House03:
- `1-2,5_slow`;
- `5-3_slow`.

These reserves are specifically protected against repeated mechanism-search overfitting.

## 11. E2 deliverables

1. `E2_RUN_MANIFEST.tsv` — all 168 runs;
2. `E2_ENVIRONMENT_MANIFEST.tsv` — seven environments and role labels;
3. `E2_OPEN_DISCOVERY_10x30.npy` plus indexing metadata;
4. sealed holdout hash manifests only;
5. `E2_QC_SUMMARY.json` containing infrastructure QC only;
6. `E2_SHA256SUMS.txt`;
7. provenance and any pre-run infrastructure patch note;
8. review package.

## 12. E2 decision

E2 returns only:
- `E2_PASS_BENCHMARK_ACQUIRED_AND_SEALED`, or
- `E2_FAIL_BENCHMARK_ACQUISITION_INCOMPLETE`.

No scientific mechanism decision is permitted.

## 13. What happens after E2

After E2 PASS:

1. use only the three OPEN_DISCOVERY environments to ask what properties survive environment variation;
2. formulate at most one candidate mechanism with frozen thresholds;
3. unseal the two DEV_HOLDOUT environments once for that candidate;
4. if it fails, STOP that candidate and protect the remaining ungenerated reserve winds for a future candidate;
5. House03 remains sealed until one mainline candidate survives development holdout.

This staged environment budget is intended to prevent the repeated `single-environment signal -> theory -> cross-environment failure` cycle.