# OCB-R2 S2X — matched-source crossover discovery extension

Date: 2026-09-29

Status: **PREREGISTERED / NOT RUN**

Parent state:

- `OCB_R2_S2_DISCOVERY_DATASET_PASS`
- `OCB_R2_D0_HOLD_COMPARABILITY`
- D0A showed that each qualified S2 non-source stratum contains four stochastic
  realizations of only one source location.
- H01/H02 confirmation and House03 remain sealed.

Frozen generator SHA256:

`ec840fa1f87fca7b7d3af3014895a642562acaacb86e5950ddb07e732adc3688`

## 1. Purpose

S2X is a **benchmark-design repair**, not a method experiment.

The existing 32 S2 discovery runs are valid stochastic data, but source changes
are entangled with wind family and gas type. S2X adds only the missing source
half of each already-qualified non-source condition.

After S2X, every one of the eight H01/H02 discovery strata will contain:

- exactly one House / occupancy contract;
- exactly one wind asset and wind-state timeline;
- exactly one gas type;
- exactly one frozen generator/timebase contract;
- **two source locations from the same House**;
- four independent stochastic realizations per source.

This creates an 8-stratum, matched two-source discovery panel without opening
confirmation or House03.

## 2. Source crossover table

The non-source condition is inherited from the existing S2 row. Only source
xyz is crossed to the other configured source in the same House.

| context | House | existing S2 source | S2X crossed source | wind | gas |
|---|---|---|---|---|---:|
| X00 | H01 | S1 = (-0.6, 1.95, 0.4) | S2 = (-0.4, -2.9, -0.3) | 1,3-2,4_fast | 13 |
| X01 | H01 | S1 | S2 | 1,3-2,4_slow | 13 |
| X02 | H01 | S2 = (-0.4, -2.9, -0.3) | S1 = (-0.6, 1.95, 0.4) | 2,4-1_fast | 10 |
| X03 | H01 | S2 | S1 | 2,4-1_slow | 10 |
| X04 | H02 | S1 = (0, -1, 0.2) | S2 = (1, -2.3, -0.1) | 3,5-1_fast | 10 |
| X05 | H02 | S1 | S2 | 3,5-1_slow | 10 |
| X06 | H02 | S2 = (1, -2.3, -0.1) | S1 = (0, -1, 0.2) | 4,5-3_fast | 13 |
| X07 | H02 | S2 | S1 | 4,5-3_slow | 13 |

Gas type is part of the non-source condition and therefore **must not follow the
crossed source's historical launch**. It stays fixed to the S2 context.

Likewise wind asset, occupancy asset, timebase, save semantics and every
non-source launch parameter stay fixed to the S2 context.

## 3. New discovery seeds

Do not reuse any seed from the original 96-row manifest.

Freeze exactly these new master-seed blocks before the first S2X plume:

- X00: `2026910001..2026910004`
- X01: `2026910101..2026910104`
- X02: `2026910201..2026910204`
- X03: `2026910301..2026910304`
- X04: `2026910401..2026910404`
- X05: `2026910501..2026910504`
- X06: `2026910601..2026910604`
- X07: `2026910701..2026910704`

These are discovery-only seeds, disjoint from all original discovery,
confirmation and H03 seeds.

Do **not** use the same RNG seed on the two source hypotheses in a stratum.
That would create a common-random-number pairing unavailable to a real
localization system and could leak realization structure into the source
comparison.

## 4. Required pre-run freeze

Before running GADEN, create and commit:

`evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv`

Required columns:

- run_id
- crossover_context
- house
- source_id
- source_x/y/z
- wind_id
- wind_asset
- occupancy
- gas_type
- master_seed
- frozen_generator_sha256
- parent_s2_config_index
- parent_s2_contract_sha256
- output_path
- status

Also commit:

`evidence/ocb_r2/s2x/OCB_R2_S2X_INPUT_SHA256.tsv`

No scientific plume payload may be inspected before the runlist and input
hashes are frozen.

## 5. Structural smoke before the full 32

Run one crossed-source realization from each fast context first:

- X00 / replicate 1
- X02 / replicate 1
- X04 / replicate 1
- X06 / replicate 1

Inspect **structural/provenance fields only**:

- generator SHA unchanged;
- explicit requested seed recorded;
- 1803 records;
- first time 0;
- last time approximately 999.502991 s;
- wind-index sequence matches the parent S2 context;
- occupancy/wind/gas hashes match the parent context;
- source xyz equals the frozen crossed source;
- finite filament output;
- archive-copy SHA verification passes.

Do not compute concentration maps, source scores or dependence metrics.

If all four pass, continue the remaining 28 without changing parameters.
If any fail, stop S2X and repair infrastructure only.

## 6. Production and archival

Generate exactly 32 new crossed-source runs.

Preferred archive destination:

`C:\GADEN_OCB_R2_ARCHIVE\s2x_matched_source`

Because VM root space is limited:

1. run one S2X case;
2. finish structural QC;
3. inventory/hash the complete raw run;
4. copy it to the host archive;
5. verify archive hashes against the VM inventory;
6. only then delete the VM raw leaf;
7. preserve compact provenance/QC evidence in Git.

Do not modify or overwrite:

- the original S2 archive;
- the frozen generator;
- ROS2 `src/build/install`;
- original wind assets;
- H01/H02 confirmation;
- House03.

## 7. S2X dataset gate

### `OCB_R2_S2X_MATCHED_SOURCE_DATASET_PASS`

Requires all:

1. 32/32 crossed runs complete;
2. frozen generator SHA unchanged;
3. all 32 have the qualified 1803-record timebase;
4. all wind/occupancy/gas contracts exactly match their parent S2 context;
5. source xyz is the intended crossed source;
6. all archive copies hash-verify before VM cleanup;
7. no original confirmation/H03 run was generated or opened.

After combining S2 and S2X metadata, each of the eight non-source strata must
contain exactly two source locations x four realizations.

If this final 8/8 comparability assertion fails, report
`OCB_R2_S2X_COMPARABILITY_FAIL` and stop.

## 8. Scientific boundary

S2X PASS is still **dataset qualification only**.

Do not compute:

- PMFS posterior;
- source ranking;
- M0;
- P/Q-time;
- dependency residual;
- closed-loop localization.

After S2X PASS, rerun D0A on the combined S2+S2X panel.

Only if the new D0A returns source-comparability PASS may an observation
operator and D0 score contract be frozen.

## 9. Important low-candidate warning

The matched panel has only two source positions per non-source stratum.

Therefore a future D0 must not equate binary top-1 success with a full
gas-source-localization benchmark. It is a **mechanism gate**.

The future D0 should report truth-vs-alternative margins in addition to top-1,
because a strong marginal model may already classify both source positions
perfectly. A marginal ceiling is a valid result; do not add new source
locations after seeing the D0 result without opening a new, separately
preregistered benchmark-design stage.

## 10. Required outputs

- `evidence/ocb_r2/s2x/OCB_R2_S2X_RUNLIST_32.tsv`
- `evidence/ocb_r2/s2x/OCB_R2_S2X_INPUT_SHA256.tsv`
- `evidence/ocb_r2/s2x/OCB_R2_S2X_RESULTS.tsv`
- `evidence/ocb_r2/s2x/OCB_R2_S2X_ARCHIVE_PROOF.json`
- `research/ocb_r2/OCB_R2_S2X_MATCHED_SOURCE_REPORT.md`

STOP after the S2X dataset decision. Do not score D0 in the same execution.
