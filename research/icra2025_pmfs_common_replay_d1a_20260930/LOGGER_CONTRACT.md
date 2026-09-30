# D1A common Native observation foundation — execution freeze

User instruction: 2026-09-30 review accepted; D1A only, no U-Net training/inference.
Branch: research/icra2025-pmfs-common-replay-d1a-20260930.
Prior local adapter commit9a12cc69833d04cce5c8859ed51764956eeabe92 is retained.

## Scope / fixed targets

Use exactly S2 32 + S2X32 discovery archives. No generator execution, no historical49-run pairing, no confirmation/H03. Frozen runlist has exact original seed/source/gas/context/generator/archive provenance. Raw record checksums are verified without concentration decoding before execution.

## Native and backend

Use the existing recovered Native core already deployed for Native arm, BRG disabled, USE_GADEN=1; no experimental correction, no AOD/3D/dependence. Existing motion/nav-fix VGR overlay is retained. PMFS arithmetic expressions, planner, source update and stopping are unchanged. Only logger additions are compiled from isolated object/archive copies; no protected ROS src/build/install is written.

Freeze existing measurement protocol: settle0, block10, maxUpdatesPerStop5, source update every3 moves, Native threshold defaults. Retain existing Native variance threshold0.5 and maxSearchTime300s; do not disable early declaration to force observations to300s. The last finite available Native belief at or before300s is the endpoint; record actual native termination separately. This is a300s maximum budget, not permission to continue after Native declares. All source-estimate arithmetic uses Native `ExpectedValue(...,0.05)` including its original sort/tie order.

Source-blind initial poses: House01(-3.17,-1.75), House02(-0.5,-2.5), inherited Native geometry; fixed flight plane0.3m from original Native launch. Navigation seed0 for all cases, distinct from immutable GADEN master seeds. No tuning by endpoint. Real-time factor1, OMP/OpenBLAS/MKL threads1. Replay is causal hold of actual RECORD_TIMELINE, not cyclic/seed-offset replay, not writer-ID=seconds. Native wind-value service is retained with its original full-field interface; its calls are logged. D1A makes no claim that the future U-Net architecture consumes that full field; D1B must explicitly address this conditional-information advantage.

## Logger schema and raw preservation

The new completed-block hook runs after native aggregation and before unchanged processGasAndWindMeasurements. It has no topic publication, no clock write, no sensor/RNG draw, no state/planner/source write. ON/OFF only changes optional output path. Both modes retain the existing equal baseline telemetry needed for parity: source/variance maps, Native expected location, sensor/pose/wind streams, measurement summaries and event IDs.

`events.tsv` fields:

- run_id, event_id, measurement_cycle_id;
- simulator physical_time_s, measurement window_start_s/window_end_s;
- map x/y/z, quaternion x/y/z/w;
- raw_gas_samples_ppm (JSON array), gas_value_used_ppm, gas_units=ppm, gas_threshold_ppm, hit/miss;
- raw_local_wind_speed_samples_m_s and raw_map_downwind_direction_samples_rad (JSON arrays), Native speed/direction aggregates;
- wind angle convention (map-frame counterclockwise flow/downwind), world downwind direction, derived robot-local direction, official device clockwise degree and integer quantization;
- validity/dropout fields; callback sample counts;
- current archive wind_state_id at last causal record, list of record/wind IDs spanning block;
- source_update_id available at the event, and any new update produced by that event;
- original raw-record/timeline provenance references.

The arrays are raw samples accepted by Native aggregation, not ideal noiseless GADEN. Separate sensor_trace.csv retains true raw GADEN ppm plus delivered FOPDT output; distinguish those quantities. Capture timestamp arrays for gas callbacks. Existing trace precision and callback-clock vs publication-clock limitations remain explicit; do not invent dropped-message timestamps or claim per-sample wind-header pairing if unavailable. A completed event with invalid/nonfinite data is QC failure. A partial window past300s is not silently completed or consumed in final comparison.

`source_estimate_trace.tsv` after each source update (plus initial/terminal diagnostics): update ID/time, sourceProbability SHA256, Native official top5% expected XY, same Native estimate semantics, MAP XY, full-posterior meanXY, entropy, variance, candidate count, raw RNG stream digest, stage. Preserve full source/variance snapshots for recovery, not only hashes.

`source_posterior_300s` is the last valid available map≤300s, with storage order/free-cell axis. Hash uses little-endian float64 bytes; it is not rounded CSV. Final result stores declared/timeout/failure, source estimate and physical cutoff/available time; no U-Net comparison/score.

`provenance.json`: target archive/run/seed/context/input hashes; installed original and logger binary/source hashes; unchanged core object hashes; all argv/environment/runtime imports; actual timebase and source-coordinate label provenance. Per-file SHA256 inventory covers the complete output bundle.

## Wind proof

VGR publishes atan2(v,u) in map frame. Native Algorithm::windCallback explicitly names it downWind_direction. Official paper Eq3 defines positive raster as upwind; its code rotates a robot-local vector by quaternion before the dot-product raster. Thus transform **negative flow vector into robot frame**, then negate atan2 angle for device clockwise degree. This follows the two explicit conventions, not an unexplainedπ correction to PMFS.

Exact-integer angles within1e-10 are canonicalized for floating roundoff; arbitrary angles retain official int-degree truncation.32 cardinal/quadrant×quaternion tests verify upwind orientation and every non-boundary raster pixel. Zero wind contributes no raster. Evidence frozen before target use; no U-Net inference is used for parity.

## Non-invasive gate and run budget

Four fixed cases cfg00r01/cfg03r01/cfg04r01/cfg07r01, both Houses/sources, fast+slow. Run OFF and ON with identical Native binary/seed/params/input archive. Compare physical trajectory tuples, accepted event sequence/count, posterior byte hash, Native endpoint, stop reason, and RNG returned-value count/digest. RNG logger reads exact returned values, adds no draw; its audit is common to both modes. No random source is seeded differently to force agreement.

Any difference -> D1A_LOGGER_NONINVASIVE_FAIL, stop without retry or relaxed tolerance. If all4pass, ON smoke runs count among64; run remaining60onceON. No duplicate scientific target execution after an ON success. Preserve all failed artifacts. Infrastructure stop is reported separately from scientific methods; never fabricate PASS or switch targets.

## Storage / STOP

Restore one existing archive to the VM replay staging at a time; do not regenerate. Preserve unique originals onC. Verify output copy SHA256 onC before removing task-owned staging copies. No protected original raw/input/build/install cleanup. If capacity is insufficient, HOLD rather than delete existing evidence.

Git includes only logger scripts/diffs/freeze/QC/reports. Scientific bundles under C:/GADEN_OCB_R2_ARCHIVE/d1a_native_common_replay and mirrored current OCB evidence receipts. Even on64/64PASS, STOP; no D1B/model evaluation, no weight selection or training.
