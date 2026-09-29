# OCB-R1 foundation audit: runner, timebase and provenance

Date: 2026-09-29
Status: **FOUNDATION HOLD — zero GADEN runs authorized or executed in OCB-R1**.

The read-only audit generated the required six-source/twelve-configuration
catalog, 96-row seed manifest, split manifest and input SHA256 inventory. It
also exposed two pre-execution blockers. No concentration values or mechanism
scores were read.

## Original-configuration runner contract

All 12 original ROS2 launch files were parsed directly from the VM scenario
tree and cross-checked against the original gas-simulation directory names.
There are two configured physical source xyz positions per House, each with
its original gas type and fast/slow wind pair. The 12 launch configurations
share the same non-source simulator parameters. In particular, original
`sim_time=1000.0 s`, `time_step=0.1 s`, writer interval `0.5 s`, wind interval
`1.0 s`, and wind loop states 1–10. The earlier E2 runner's `sim_time=300 s`
and uniform `gas_type=10` must not be reused for this original-config bank.

The command constructor in `prepare_ocb_r1_audit_vm.py` resolves each launch
default and builds 96 planned CLI invocations. It checks, for every planned
invocation, that the **only changed ROS parameter is `results_location`** and
that the only environment override is `GADEN_RNG_SEED`. Source xyz, gas type,
wind input prefix, occupancy and all other launch parameters are unchanged.
`RUNNER_COMMAND_CONTRACT.json` records the original/effective parameter maps
and complete argv for independent review. This is a static command audit;
the executable was not started. Output paths remain under the literal
`<APPROVED_OUTPUT_ROOT>` placeholder, so the audit did not create a data root.

The deterministic seed formula is `2026900000 + 100*config_index + replicate`,
where `config_index=0..11` follows the catalog order and `replicate=1..8`.
All 96 seeds are unique and do not overlap the frozen E2C 120/144 manifests.
Roles are 32 H01/H02 discovery, 32 H01/H02 sealed stochastic confirmation,
and 32 sealed House03 external-House confirmation. The physical independent
source count remains six, not twelve.

## Common observation and writer records

The E1 probe contract SHA256 is unchanged. Each House has 30 source-blind
`z=0.20 m` probes; each 2x2 native-grid footprint is within that House's
occupancy dimensions. The original source heights differ across configurations,
which does not change the common observation-height rule. The same ten
writer-record IDs `100,150,...,550` exist in every historical directory.

For the **pinned seed-capable binary** (`4127b9ba...`), its writer source hash
matches the earlier E2C timebase provenance. A 1000 s control-flow
reconstruction yields 1,803 saved records; the ten selected IDs have exactly
the previously certified E2C `(record ID, float32 clock, wind index)` tuples.
The ten clocks span about 55.10–292.31 s, not 100–550 physical seconds.

The original released gas directories each contain **2,000** saved records,
not 1,803. Their historical executable/writer time map is not proven equal to
the pinned binary's map. Thus the selected IDs are valid for a prospective
common run under the pinned binary, while precise historical-record time
equivalence remains **uncertified**. This difference must be retained in
provenance; it cannot be erased by calling both files `iteration_100`.

## Blocking asset and storage findings

The original House02 launch path for `4,5-3_fast` is incomplete: states 5–9
are missing 19 wind files in the primary directory; its state-5 `.csv` also
differs from the nested House02 copy. The `4,5-3_slow` primary wind directory
is missing all 44 state/component files. Total: **63 missing primary wind
files and one conflicting file**. Read-only hashes found a nested copy for
each missing file, but the audit did not substitute paths, copy files or
repair the canonical assets. `PRE_RUN_SHA256.tsv` marks each missing,
conflicting and backup file explicitly. This blocks a strict launch-path
replay of all 12 original configurations.

Capacity is another pre-run issue. At audit time the VM root filesystem had
233,787,392 bytes available and `/mnt/hgfs/workspace` had 2,095,513,600
bytes. One original House01 1000 s gas directory occupies 163,819,973 bytes.
Using that single directory as an order-of-magnitude reference, 96 retained
raw runs would need roughly 15.7 GB, before extracted arrays and checksums.
This is an estimate, not a measured output size for the 96 proposed runs.
No approved output volume with demonstrated capacity has been identified.

## Decision

`OCB_R1_FOUNDATION_HOLD_WIND_ASSET_INTEGRITY`

The catalog, seeds, split and command contract are frozen as a **plan only**.
Do not generate any of the 96 plumes. Before acquisition, the missing and
conflicting wind assets must be resolved with documented hashes and an
approved storage plan. The historical 2,000-record versus pinned 1,803-record
timebase distinction must stay explicit. Do not change a source position,
gas type, wind family or frozen seed to work around these findings.

Machine-readable evidence is in `evidence/ocb_r1/`; all VM input paths and
hashes are in `PRE_RUN_SHA256.tsv`.
