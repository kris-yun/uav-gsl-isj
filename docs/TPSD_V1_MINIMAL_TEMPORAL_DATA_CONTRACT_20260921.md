# TPSD V1 minimal temporal-data export contract

Purpose: provide the missing causal time series needed for a faithful offline
test of Temporal Primacy Source Decorrelation.

The existing frozen six-case context bank already contains the candidate
spatial fields and source posteriors. Do not duplicate those files.

Export only the missing native time series from the same authoritative R2 runs:

- House01 seed0/1
- House02 seed0/1
- House03 seed0/1

For every case preserve the original 5-Hz rows and export:

## pose_trace.csv

- t_sim_s
- x, y, z
- yaw if available

## sensor_trace.csv

Every original column, especially:

- t_sim_s
- raw GADEN concentration
- processed sensor concentration
- binary gas-present / threshold result if present
- sensor dynamic state if present

## wind_trace.csv

If wind is already in sensor or pose trace, do not invent a duplicate file.
Otherwise export:

- t_sim_s
- wind_x, wind_y, wind_z

## source_update markers

The existing context-bank source_update_timing.csv remains authoritative.
Do not regenerate it.

## Provenance

For each exported file record:

- original absolute VM path;
- byte size;
- SHA256;
- runtime Git SHA;
- run UUID;
- case ID.

Do not use source truth, endpoint error, TNQC score, DRPE score, or any
scientific result in the export.

Do not compute TPSD scores on the VM.

The downstream screen will align the native trajectory with the already-frozen
candidate_support_alignment fields and construct instantaneous candidate
Bernoulli evidence locally.
