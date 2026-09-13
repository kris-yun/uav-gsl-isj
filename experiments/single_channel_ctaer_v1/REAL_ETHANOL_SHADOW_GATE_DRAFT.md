# Draft: one-flight ethanol/VOC shadow gate

Status: design draft; freeze as a numbered preregistration only when the flight
date, map and source-blind candidate support are available.

## Physical design

- Source: one continuously evaporating ethanol source; start once and do not
  require source shutdown or repeated modulation.
- Gas input: the FKT-AQI-L exported 1 Hz VOC concentration only.
- State inputs: UAV-controller pose/altitude and the same wind input available
  to classic PMFS, aligned to the VOC timestamps.
- Route: classic PMFS controls the UAV.  CTAER cannot change any waypoint.
- Source location: hidden from PMFS/CTAER and opened only by the evaluator after
  all candidate scores are saved.
- No source-response library, second chemical channel, pump, neural training,
  House switch, or post-flight parameter fitting.

Smoke cake is not interchangeable with this test.  It primarily exercises the
PM2.5/aerosol channel, whereas the frozen algorithm and simulated evidence use
a scalar gas/VOC response.

## Frozen shadow arms

1. classic PMFS output produced during flight;
2. ICRA-2026 global ordinal comparator;
3. frozen TAORL forward-windowed score;
4. frozen CTAER shared-tau forward-minus-reverse score;
5. sign-reversed CTAER control.

Every arm receives the same recorded path and the same 1 Hz VOC samples.

## Proposed one-flight screening gate

All conditions should be frozen before source truth is opened:

1. sensor/pose/wind clocks pass the declared alignment tolerance;
2. CTAER true-source normalized rank is at most 0.10;
3. CTAER true-source rank beats TAORL and global ordinal ranking;
4. CTAER true-source rank beats the sign-reversed control;
5. the true candidate has positive reverse-minus-forward evidence;
6. CTAER MAP error is below the same-trajectory classic PMFS final error.

Failure stops same-flight tuning.  Pass supports only `INDEPENDENT_REAL_DOMAIN_DEVELOPMENT_REPLICATION`.

## Minimum files to retain

- original device-exported history table, byte-for-byte;
- UAV pose/altitude telemetry with timestamps;
- wind trace with timestamps and coordinate convention;
- map/candidate support and coordinate transform;
- hidden source-location record opened by evaluator only;
- classic PMFS posterior/estimate trace;
- frozen CTAER commit, command, result JSON and SHA-256 manifest.

