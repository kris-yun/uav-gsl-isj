# H0 P0 historical-event provenance

## Verified identity

- Branch: `research/ts-p3t-h0-temporal-closure-20261001`.
- Frozen handoff base: `b51aaa979e1e303fbb1457ba87244f21574a6d4c`.
- Authoritative archive: `/mnt/hgfs/workspace/TNQC_V5_R2_HOUSE123_SEED01_OFFLINE_HOLD_20260921_FINAL.tar.gz`.
- Archive bytes: 140607059.
- Archive SHA256: `81c72910b2fc912e5e0a9340d3f6b1ba20024da510ef58eb95da2ff1d8055708`; exact match to its historical sidecar.
- All 61 selected artifacts match the archive manifest and extracted VM copy.
- 60 retained files and 5 frozen source files were independently rehashed locally.
- No HCMC, recovery run, or later repeated run was substituted.

## Missing completed-block inputs

All four cases ran `pfdi_mode=off`, `tadm_enabled=false`. Their resolved parameters contain no `measurement_trace_file` or `continuous_measurement_samples_file`. The archive inventories contain no measurement/event export for these cases.

The exact source archive verifies two independent disabled logging paths:

1. `Common/States/StopAndMeasureState.cpp`: measurement and sample trace paths default to the empty string; output requires a nonempty path. Console averages use `{:.2}`, i.e. two significant digits, not full float precision.
2. `PMFS/PMFS.cpp`: `recordPCACIEvent` requires `tadmEnabled` and a supported non-off mode. Neither condition is satisfied here.

The GSL log does retain 128 completed-block average lines before the terminal source update in each case. These establish that measurements occurred; they are not a full-precision event stream. The log timestamp is wall time, while the requested windows use simulator time. Source-update timing is retained only at the five source updates.

`sensor_trace.csv` and `wind_trace.csv` record simulator publication steps, with six decimal places for sensor/wind values and four for pose. They omit callback-to-measurement-block membership and the exact transformed/circular-averaged wind consumed by Native. State gating, independent gas/wind callbacks, and timer boundaries are part of the archived `StopAndMeasureState` code. Ten samples per block alone does not uniquely recover those inputs.

## Why rounding matters for this contract

Native `EstimateHitProbabilities` depends on wind speed and direction, as well as hit and robot grid cell. `sigma_y = 0.5 + 1.5 * windSpeed` and the kernel rotation depends on downwind direction. For example the log display `0.027` permits multiple wind speeds at two significant digits; it cannot establish an input error small enough for `1e-10` logOdds parity. The six-decimal publication trace supplies more information, but does not provide the missing block membership or full-precision callback values.

No map was reconstructed using guessed windows, rounded log means, or parameters fitted to the saved terminal map. Copying the saved map and reporting zero difference would be a circular parity check.

## Gate result

`TS_P3T_H0_INVALID_STOP`.

The archived terminal maps, masks, times and hashes are available. Reconstruction parity is **not computable**, so all max-absolute-error values are null, not zero. This is an input sufficiency failure; no measured numerical mismatch was claimed.

O40 and Oupdate bounds can be reported from source-update timing. Their exact event counts, memory-age fractions, maps, candidate scores, truth ranks and margins remain unavailable. The empty score TSV is intentionally header-only.

## Execution boundary

New GADEN=0; new candidate forward=0; training=0; H03 observation content=0; closed loop=0; truth scientific evaluation=0. Existing ROS2 src/build/install and historical archives were not changed. H1 and subsequent methods were not started.
