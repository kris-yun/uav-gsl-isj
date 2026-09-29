# OCB-R2 generator qualification result

Decision: **`OCB_R2_GENERATOR_REFOUNDATION_PASS`** for the frozen single-worker
House02 configured source 1 / `3,5-1_slow` qualification. This authorizes no
96-run acquisition or algorithm experiment.

| Check | Result |
|---|---:|
| A(S1), B(S2), C(S1) record counts | 1803 / 1803 / 1803 |
| First / last native internal time | 0 / 999.502991 s |
| A vs B time, wind-index, deterministic metadata | exact / exact / exact |
| A vs C time, wind-index, deterministic metadata | exact / exact / exact |
| A vs C scientific iteration bytes | 1803/1803 exact |
| A vs B differing scientific iteration bytes | 1802/1803 (initial empty record identical) |
| A vs B filament-count difference | 0 in every record |
| A vs B filament centroid distance | median 0.497707 m, q95 0.616480 m |
| Full independent hash inventory | 5409/5409 scientific files verified |
| Wind conversion inventory | 33/33 inputs and 11/11 outputs verified |

S1=`2026900501`; S2=`2026900502`. The distinct-seed field difference is
spatial: deterministic release gives the same filament count trajectory, while
positions differ in nearly every record. The first empty record is expected
to match. `FIELD_DIFFERENCE_SUMMARY.json` reports the numerical field summary;
`VALIDATION_RESULT.json` contains every hard gate.

Complete A/B/C raw iteration outputs and copied wind fields remain at
`/home/zyc/ocb_r2_validation/RUN_{A,B,C}` on the VM. Each run has a complete
SHA256 inventory, native timeline, and run manifest committed here; three
representative records per run are included under `samples/`. The scientific
payload gate used the full 1803 records, not these samples. No experiment
source/wind/occupancy input or existing ROS installation was overwritten.

Historical status remains `OCB_R1_HISTORICAL_PARITY_UNRECOVERABLE` and
`CURRENT_1803_BINARY_NOT_ELIGIBLE_FOR_OCB_R1_REFERENCE`. The 44/44 wind
lineage check supports wind asset provenance only. OCB-R2 is a new prospective
generator with native current timing, not a historical seed replay.

Patch-scope reporting: `NOT_ONLY` if the field is interpreted literally,
because the isolated source also adds read-only timeline instrumentation;
there are **zero new plume-physics changes**, and the already existing seed
initialization retains its engines and distributions.
