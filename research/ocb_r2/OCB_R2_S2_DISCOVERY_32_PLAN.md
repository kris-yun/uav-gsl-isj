# OCB-R2 S2 — H01/H02 Discovery-32 Plan

## Purpose

Generate and quality-control the **32 already-frozen H01/H02 discovery runs** under the benchmark-frozen OCB-R2 generator, then permit discovery-only offline mechanism analysis.

This phase must not open the H01/H02 independent-confirmation partition or House03 sealed confirmation.

## Frozen generator

Binary SHA256:

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

Qualification:

- `OCB_R2_GENERATOR_REFOUNDATION_PASS`
- `OCB_R2_S1_H12_STRUCTURAL_PASS`

Any binary hash change requires STOP and renewed A(S1)->B(S2)->C(S1) qualification.

## Frozen split

Use the already-committed OCB-R2 master manifest and seed lineage.

S2 contains only the 32 rows labeled H01/H02 discovery.

Do not:

- redraw seeds;
- move runs between discovery and confirmation;
- replace an unfavorable seed;
- use H03;
- inspect H01/H02 confirmation scientific output.

Before generation, create and commit:

`evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv`

The runlist must be frozen before any S2 scientific output is inspected.

## Generation policy

Use the same frozen generator for all 32 runs.

For every run, preserve:

- source xyz
- gas type
- occupancy asset/hash
- wind asset/hash
- current native simulator timeline
- all physics parameters
- master_seed from the frozen manifest
- output/provenance sidecars

Only configuration-specific inputs and the preassigned master_seed may differ according to the manifest.

## Storage policy

Prefer sequential or small-batch execution:

`run -> validate -> SHA256 inventory -> archive -> verify archive -> remove VM raw leaf -> next`

Archive root:

`C:\GADEN_OCB_R2_ARCHIVE\s2_discovery`

Never delete a VM raw run before the copied archive has passed file-count and SHA256 verification.

Keep large raw plume data out of Git. Commit manifests, hashes, QC and reports only.

## Per-run structural/QC gate

Every discovery run must pass:

1. frozen generator SHA256 exact
2. process success
3. run manifest complete
4. master_seed exact
5. record_count = 1803
6. native timeline valid and monotonic
7. wind-index sequence valid for that configuration
8. input asset hashes exact
9. scientific output inventory complete
10. no unexpected corrupt / zero-byte files
11. parsed scientific values finite
12. non-empty plume states after the expected initial empty record
13. archive file count exact
14. archive SHA256 verification exact

If a run fails for infrastructure/asset reasons, do not substitute another seed. Diagnose and preserve the original run identity.

## Data-production decision

Only if all 32 frozen discovery runs pass structural/QC requirements:

`OCB_R2_S2_DISCOVERY_DATASET_PASS`

Otherwise:

`OCB_R2_S2_DISCOVERY_DATASET_HOLD`

A HOLD does not authorize use of confirmation/H03 to compensate.

## Discovery-only scientific analysis

Only after `OCB_R2_S2_DISCOVERY_DATASET_PASS` may the 32 discovery runs be used for method/mechanism work.

Allowed:

- offline mechanism diagnostics;
- testing whether the previously identified cross-time/dependence signal survives controlled stochastic realizations;
- comparing complete marginal evidence versus temporal-coupling increments;
- designing the main method and its two auxiliary modules;
- selecting formulas/hyperparameters/gates using discovery only;
- failure analysis and method revision within discovery.

Forbidden:

- opening confirmation scientific output;
- opening H03 scientific output;
- tuning to confirmation/H03;
- closed-loop claims;
- presenting discovery performance as final validation.

## Method-freeze deliverable after discovery analysis

Before S4 confirmation is generated/opened, create a method-freeze package containing at least:

- final mathematical definition
- feature/input definition
- training or fitting procedure
- hyperparameters
- seed-handling policy
- source-ranking rule
- PMFS probability-map fusion/output rule
- all ablations to be reported
- success/failure gates
- code commit/hash
- exact scripts/commands

Decision:

`OCB_R2_S3_METHOD_FREEZE_READY`

Only then may S4 independent confirmation be opened.

## H03 seal

Throughout S2 and discovery analysis:

`H03 = SEALED_NOT_RUN`

Do not generate or inspect prospective H03 plume output.

## Required outputs

At minimum:

- `evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RUNLIST_32.tsv`
- per-run manifests/timelines/QC/hash inventories
- `evidence/ocb_r2/OCB_R2_S2_DISCOVERY_RESULTS.tsv`
- `research/ocb_r2/OCB_R2_S2_DISCOVERY_DATASET_REPORT.md`

If discovery scientific analysis proceeds after dataset PASS, place mechanism/method evidence in a separate discovery-analysis directory so structural data qualification and scientific conclusions remain distinct.

## Stop boundary

After the 32-run dataset qualification and any explicitly requested discovery-only analysis:

- do not generate/open S4 confirmation automatically;
- do not run H03;
- do not start closed-loop experiments.

Report the result and stop.
