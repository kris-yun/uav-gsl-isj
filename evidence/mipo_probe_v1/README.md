# MIPO V1 raw probe export

Data-only export from the six frozen native R2 House01/02/03 seed0/1 realizations. No planner changes, 300-second closed loop, seed2/3 use, frequency/amplitude selection, direction estimate, gain or localization metric.

`anchors.csv` was frozen before any patch query. The exporter selects maximum horizontal obstacle clearance from actual native poses within +/-15 seconds, expanding once to +/-30 seconds only if 0.70 m is unavailable. Clearance is distance to the closed obstacle-cell squares in the frozen occupancy slice at the native pose altitude, with outside-map space blocked. Ties use absolute target-time offset then earliest timestamp. Occupancy is 0=free, 1/2=blocked. Spatial offsets are global x/y axes, not wind-relative.

Each valid anchor has 49 spatial points and 160 raw samples, from relative time 0.0 through 31.8 seconds at 0.2-second spacing. CSVs are time-major, then dx, then dy. The original R2 seeded snapshot mapping is retained. `snapshot_id` is the actual gas snapshot filename. House01's unchanged raw helper exposes a wind index; FrameQuery does not expose that separate identifier, so `wind_snapshot_id=NA` is documented rather than invented.

House01 is queried directly through its frozen helper. House02/03 use their frozen player in manual-iteration mode with a namespaced query-only client. Neither robot navigation nor a planner is started. Backend-invalid data are retained as NA with error text; anchors are never moved in response to returned gas/wind.

`sensor_model.json` records the actual runtime sensor configuration, including node-level overrides of profile defaults. Raw concentration is exported without an added filter or interpolator. A sensor trajectory before the anchor is not defined for the counterfactual fixed grid points, so no sensor state reset is invented and `sensor_ppm` is omitted.

`truth_eval.json` is written by an isolated script only after raw export and integrity audit complete. Anchor selection, queries and preprocessing never read it. Original GADEN directory names may embed source-coordinate text; they are opaque provenance identifiers, not parsed as truth. Source-coordinate fields exist only in the evaluation sidecar.

`gaden_content_sha256.json` records content hashes of every queried gas snapshot, occupancy file, and all wind files in the selected realizations. `gaden_data_listing.json` inventories all realization files and byte sizes. The content-manifest SHA and listing SHA are in `manifest.json`; they are not presented as a hash of every unqueried gas snapshot.

`SHA256SUMS.json` covers every other output file, excluding itself. Run `python scripts/checksums.py verify evidence/mipo_probe_v1` from the repository root to verify. Integrity checks are row counts, duplicate keys, monotonic sample times, finite available values, occupancy flags, frozen time mapping and file hashes only.

The exact preparation/query/finalization commands are recorded in `exact_command.txt`. The one preparation parser correction accepted occupancy headers such as `#env_min(m)`; it occurred before anchors were written or queries started and did not change the anchor rule.
