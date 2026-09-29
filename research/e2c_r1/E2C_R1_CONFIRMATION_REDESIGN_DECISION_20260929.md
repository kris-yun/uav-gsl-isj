# E2C-R1 confirmation redesign decision — 2026-09-29

Decision: **PAUSE THE 120-RUN CAMPAIGN AND REDESIGN THE CONFIRMATION PANEL BEFORE ANY NEW GADEN RUN.**

This amendment does not invalidate the pre-run freeze at commit `38bbf1ce`.
It supersedes only the authorization to execute that source panel. The reason is
the metadata-only prior-exposure audit:

- all 8 proposed House03 source IDs appeared previously in the AOD F1 truth panel;
- House02 proposed confirmation source `pmfs_26_35` appeared previously in R0.

Because zero new GADEN runs have started, this is the cheapest point to protect
the final confirmation claim.

## Scientific rule

Historical exposure is not a problem for DISCOVERY sources. It is a problem for
a set labeled "untouched confirmation".

The revised benchmark should distinguish three levels:

1. **DISCOVERY** — historical exposure allowed.
2. **SOURCE-UNSEEN CONFIRMATION** — source IDs must not appear in any prior
   scientific truth/source panel used in this project; new plume seeds and new
   E2C observations are also required.
3. **ENVIRONMENT-UNSEEN CONFIRMATION** — would require a genuinely new House /
   environment not previously used in method development. The current
   H01/H02/H03 repository cannot honestly provide this label for House03 because
   House03 has already been studied historically.

Therefore the strongest claim available from the current three-House program is:
"held-out House03 common-contract confirmation on historically unexposed source
locations and new realizations", not "previously unseen House".

## Revised run-count target

H01:
- keep 6 existing E2 sources as DISCOVERY;
- add 4 new realizations/source = 24 new runs;
- choose 2 historically unexposed confirmation sources by an outcome-blind
  geometry rule and generate 8 realizations/source = 16 runs.
Total H01 new runs = 40.

H02:
- keep 6 existing E2 sources as DISCOVERY;
- add 4 new realizations/source = 24 new runs;
- discard the current proposed confirmation pair from the final confirmation
  role and select a completely new pair with BOTH source IDs historically
  unexposed; generate 8 realizations/source = 16 runs.
Total H02 new runs = 40.

H03:
- do NOT use the current 8 source IDs as the final untouched source-level
  confirmation panel;
- keep the existing E2 H03 assets sealed/archived as historically exposed
  auxiliary data;
- select 8 historically unexposed source IDs by a deterministic geometry-only
  rule fixed before scientific values are read;
- generate 8 new independent realizations/source.
Total H03 new runs = 64.

Revised total = **144 new GADEN runs**.

## Mandatory pre-run exposure audit

Before selecting any replacement source:

1. Build `PRIOR_SOURCE_EXPOSURE_UNION.tsv` from repository metadata only.
2. Include every source ID that has appeared in any prior scientific truth panel,
   source panel, validation target, or method-outcome report, grouped by House.
3. Freeze and hash that union before source selection.
4. Selection code may use geometry/occupancy and the frozen exclusion set only.
5. It may not read historical performance, rank, Top1, error, or method labels.

## Mandatory new freeze

Before first simulation, commit:
- revised `SOURCE_PANEL_8x3.tsv`;
- revised seed manifest;
- revised split manifest;
- exposure-union TSV and provenance;
- deterministic source-selection audit;
- proof that every confirmation source ID is absent from the exposure union;
- unchanged E2 timebase/probe/extractor hashes.

No source may be substituted after observing plume output.

## Stop boundary

Do not start any simulation until this revised freeze is committed and verified.
Do not run Ordinal, AOD, CENTERED, TCMA, AEC, PMFS-Clean, VGR, or any mechanism
analysis during the redesign.
