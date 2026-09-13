# Single-channel real-flight contract

## Primary small flight

- Release medium: evaporated ethanol.
- Sensor input: exactly one VOC concentration scalar from the FKT-AQI-L.
- PMFS comparison: native PMFS and MC-SCSP receive the same timestamps, scalar
  samples, wind/pose stream, path, map and compute budget.
- The six-channel instrument is operated as a one-channel instrument for the
  algorithm. Other channels may be logged for safety/diagnostics but cannot
  enter either algorithm or select a result.
- No source shut-off, repeated release library, environment-specific training,
  or post-truth calibration is required.

## Secondary experiment

A smoke cake is evaluated separately through PM2.5. It is labelled an aerosol
robustness experiment, not direct validation of an ethanol/butane gas plume
model. Results from VOC and PM2.5 are never pooled.

## Hardware facts that must be obtained from the vendor before flight

1. Whether VOC and each named gas are available as separate time-stamped values
   over the data interface or only as a fused AQI/status field.
2. VOC sensing principle, units, range, resolution, zeroing procedure and whether
   its calibration gas is isobutylene, ethanol or another compound.
3. Configurable output period and the true per-channel update period.
4. Pump flow rate, inlet tubing length/diameter and any internal averaging.
5. VOC rise and recovery time under pump operation. The label-level `T90 <= 15 s`
   is insufficient to freeze a first-order response constant.
6. Raw data protocol and clock/timestamp behaviour.

Until these are answered, the software bridge may record raw values but must not
apply a guessed lag correction or convert VOC readings into absolute ethanol
concentration.

