# OCB-R2 S1 — H01/H02 Structural Smoke Matrix Plan

## Purpose

Validate that all eight H01/H02 source×wind configurations can run under the same frozen prospective generator contract before any larger data production or method analysis.

This phase is **structural only**.

It must not answer whether a localization or innovation method works.

## Frozen generator

Binary SHA256:

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

Qualification decision:

`OCB_R2_GENERATOR_REFOUNDATION_PASS`

If the binary SHA256 changes for any reason, stop S1 and re-run A(S1)->B(S2)->C(S1) qualification.

## Pre-run requirements

1. Build `evidence/ocb_r2/OCB_R2_MASTER_MANIFEST_96.tsv` by inheriting the already frozen 96 unique seeds as OCB-R2 `master_seed` values.
2. Do not redraw seeds.
3. Preserve partition membership:
   - H01/H02 discovery: 32
   - H01/H02 confirmation: 32
   - H03 sealed confirmation: 32
4. Create `SEED_MANIFEST_LINEAGE.md` documenting one-to-one lineage from the original frozen seed manifest.
5. Create and commit `OCB_R2_S1_RUNLIST_8.tsv` **before** looking at any S1 plume output.
6. Select one S1 seed per configuration by a mechanical predeclared rule, e.g. first frozen seed in manifest order.
7. H03 is static-audit only and remains `SEALED_NOT_RUN`.

## H03 seal

For H03, this phase may inspect only configuration metadata:

- source xyz
- wind asset path/hash
- occupancy path/hash
- gas type
- launch parameters
- output template
- master-seed availability

Do not generate new H03 scientific plume output.

## Storage safety

Before each run, check root free space.

Prefer:

`run one -> validate -> archive -> verify archive hashes -> delete local raw copy -> next run`

Keep approximately 1 GiB or more root safety margin.

The A/B/C qualification raw outputs may be moved to Windows C: archival storage only after destination file count and hashes have been revalidated. Do not delete the only verified copy.

## Per-run hard contract

Before launch:

- frozen binary SHA256 exact
- expected configuration from S1 runlist
- expected master_seed
- expected source/wind/occupancy/gas metadata

After launch require:

1. process success
2. run manifest present
3. master_seed exact
4. generator hash exact
5. record count = 1803
6. first/last native timeline values match generator contract
7. timeline monotonic
8. wind-index sequence valid for the frozen configuration
9. input asset hashes match manifest
10. scientific output inventory complete
11. no unexpected zero-byte/corrupt output
12. all parsed concentration values finite
13. non-empty times contain plume signal
14. provenance sidecar complete

Do not require different houses to have identical wind-index sequences; require consistency with their own frozen wind configuration.

## Forbidden analysis in S1

Do not compute or inspect:

- PMFS source score
- localization error
- source ranking
- dependence score
- innovation metrics
- seed quality
- method benefit
- cherry-picking criteria

Do not replace a failed seed because its plume looks unfavorable.

## Outputs

Create:

- `evidence/ocb_r2/OCB_R2_MASTER_MANIFEST_96.tsv`
- `evidence/ocb_r2/SEED_MANIFEST_LINEAGE.md`
- `evidence/ocb_r2/OCB_R2_S1_RUNLIST_8.tsv`
- `evidence/ocb_r2/H03_SEALED_STATIC_READINESS.tsv`
- `evidence/ocb_r2/OCB_R2_S1_STRUCTURAL_SMOKE_RESULTS.tsv`
- `research/ocb_r2/OCB_R2_S1_STRUCTURAL_SMOKE_REPORT.md`

Large raw plume output must stay out of Git.

## Decision gate

PASS only if all eight H01/H02 runs satisfy:

- 8/8 process success
- 8/8 provenance contract
- 8/8 record/timeline contract
- 8/8 input asset contract
- 8/8 basic scientific sanity
- 8/8 frozen binary SHA256 exact

Then report:

`OCB_R2_S1_H12_STRUCTURAL_PASS`

Otherwise:

`OCB_R2_S1_H12_STRUCTURAL_FAIL_STOP`

Regardless of PASS:

- do not continue automatically to S2;
- do not run H03;
- do not run PMFS;
- do not start the 96-run batch.

## Required final S1 summary

Report only:

- frozen_generator_sha256
- S1_runlist_frozen_commit
- H01 configs X/X PASS
- H02 configs X/X PASS
- record_contract X/8
- asset_contract X/8
- provenance_contract X/8
- scientific_sanity X/8
- H03_status = SEALED_NOT_RUN
- disk_free_after
- decision
