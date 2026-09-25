# 01 — INPUT AND PROVENANCE CONTRACT

## A. Authoritative starting point

Expected anchor:

- branch: `research/stochastic-benchmark-refoundation-20260924`
- commit: `e527beea07c33cdbc362d156545409245f029968`
- decision: `R0_PASS_STOCHASTIC_BENCHMARK_USABLE`

Codex must verify locally.

If the commit is absent, do not silently substitute a nearby commit.

## B. Expected scientific unit

Independent unit = **one complete stochastic plume realization for one source**.

Expected panel:

- 18 sources
- 16 realizations/source
- 288 complete realizations total

Pairwise distances, temporal points, probes, blocks, or shuffled pseudo-records are **not** independent repetitions.

## C. Expected ordered observation object

Prior audit described the R0 object as 10×30 = 300 ordered values per realization.

This is an expected contract, not permission to guess a reshape.

Required provenance must establish:

- which axis is time;
- which axis is probe/query/support;
- ordering of t0..t9;
- ordering of 30 within-time entries;
- exact observable definition;
- threshold / support rule if binary;
- no hidden source-truth-derived filtering.

If only a flat 300-vector exists without recoverable order, STOP.

## D. Canonical cache schema

Codex may create a read-only-derived cache:

`canonical_r0.npz`

Required arrays/metadata:

- `X`: shape `[18,16,10,30]`, numeric
- `source_ids`: shape `[18]`
- `realization_ids`: shape `[18,16]`
- `source_xy`: shape `[18,2]` if available, else omit
- `time_index`: `[0..9]`
- `probe_index`: `[0..29]`
- `observable_name`: scalar string
- `base_commit`: scalar string
- `input_sha256_json`: scalar JSON string mapping input files to hashes

No smoothing, threshold changes, scaling, imputation, augmentation, or denoising is allowed when creating the canonical cache.

Casting to float64 for computation is okay if raw hashes and original dtype are recorded.

## E. Independence audit

For every source:

- 16 realization IDs must be unique;
- raw content hashes must not contain identical duplicate realizations unless R0 explicitly documented why;
- if two realizations are bit-identical or numerically identical beyond expected initialization, flag;
- do not “fix” duplicate seeds by adding jitter.

If pseudoreplication invalidates the 16-run contract, STOP.

## F. Data leakage prohibitions

- eval realization cannot fit scaler/PCA/OAS for its fold;
- truth coordinate cannot enter feature construction;
- source coordinate can be used only for final MAP spatial-error evaluation;
- SHUFFLED null cannot touch eval data;
- no final test result may select preprocessing.
