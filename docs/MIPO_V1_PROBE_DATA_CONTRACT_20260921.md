# MIPO V1 Probe Data Contract

Date: 2026-09-21

Purpose: collect a reusable, source-blind local spatiotemporal gas/wind data
cube for testing **Motion-Induced Plume Observability (MIPO)**.

This is a mechanism screen only. It does not modify PMFS, TNQC, DRPE, the
online planner, or the frozen R2 runtime.

Base execution identity:

`b24da77fd24bd5ea2cbb33caf856f80b9d7670e4`

## 1. Cases

Use the same six frozen development environments:

- House01 seed0
- House01 seed1
- House02 seed0
- House02 seed1
- House03 seed0
- House03 seed1

Do not consume seed2/seed3.

## 2. Source-blind anchor selection

Target simulation times:

`60 s, 150 s, 240 s`.

For each target, choose an anchor from the corresponding frozen native R2
trajectory without using source truth.

Deterministic rule:

1. consider native poses within +/-15 s of the target;
2. require the center itself to be free;
3. compute obstacle clearance from the frozen occupancy map;
4. choose the pose with maximum clearance;
5. ties: choose the smallest absolute time offset, then earliest timestamp;
6. if no candidate has >=0.70 m clearance, expand once to +/-30 s;
7. if still unavailable, mark the anchor INVALID rather than inventing a new
   position.

Do not use source coordinates, native endpoint error, TNQC/DRPE scores, or gas
magnitude to select anchors.

Freeze anchor x/y/z and anchor sim_time in `anchors.csv` before querying the
probe patches.

## 3. Local spatiotemporal patch

For every valid anchor, query a global-axis 7x7 square patch:

`dx,dy in {-0.6,-0.4,-0.2,0,0.2,0.4,0.6} m`.

Use the anchor altitude z.

Query duration:

`32.0 s`

starting at the frozen anchor sim_time.

Temporal sampling:

`dt = 0.2 s` (5 Hz)

for 160 samples per spatial point.

Do not interpolate or smooth before export.

For every row export:

- case_id
- House
- seed
- anchor_id
- anchor_target_time_s
- anchor_sim_time_s
- frame/sample index
- rel_time_s
- query_sim_time_s
- center_x_m, center_y_m, center_z_m
- dx_m, dy_m
- query_x_m, query_y_m, query_z_m
- occupancy/free flag
- GADEN concentration ppm at that point/time
- wind_x_mps, wind_y_mps, wind_z_mps at that point/time
- GADEN frame/snapshot identifier
- exact query backend name/version if available

If the existing gas backend cannot return one of these fields, write NA and
explain it in the manifest. Do not fabricate it.

## 4. Sensor-model metadata

Export `sensor_model.json` describing the exact R2 gas measurement path:

- whether PMFS consumes direct GADEN concentration or a transformed/noisy
  sensor output;
- gas threshold;
- any filtering/lag/noise parameters;
- source file + Git SHA for the implementation.

If a deterministic existing sensor model can be replayed without changing
scientific code, also export `sensor_ppm` for each patch row.

If not, raw GADEN concentration is sufficient for this mechanism screen;
record that limitation explicitly.

## 5. Source truth separation

Create a separate file:

`truth_eval.json`

with the six source coordinates and scenario identifiers.

No query, anchor choice, patch construction, filtering or preprocessing may
read this file.

It exists only so the downstream evaluator can test source relevance after
source-blind probe features have been frozen.

## 6. Provenance

Export:

- `manifest.json`
- `anchors.csv`
- `sensor_model.json`
- `truth_eval.json`
- query/export script(s)
- exact command line
- stdout/stderr log
- runtime Git SHA
- ros2_package tree SHA
- GADEN data path + content hash/listing
- map/occupancy hash
- baseline native trajectory hashes
- SHA256SUMS for every output file.

## 7. Preferred file layout

```
evidence/mipo_probe_v1/
  README.md
  manifest.json
  anchors.csv
  sensor_model.json
  truth_eval.json
  scripts/
    export_mipo_patch.py
  raw/
    House01_seed0_anchor060.csv.gz
    House01_seed0_anchor150.csv.gz
    House01_seed0_anchor240.csv.gz
    ...
  logs/
    export.log
  SHA256SUMS.json
```

Plain CSV is acceptable if small. gzip is preferred for the raw patch files.

## 8. Integrity-only checks Codex may perform

Codex may verify only:

- expected row count for each valid anchor:
  `49 * 160 = 7840` rows;
- no duplicate (time,dx,dy) keys;
- monotonic query time;
- occupancy flags present;
- finite gas/wind values where backend reports them;
- all hashes match.

Do NOT compute MIPO gain, source direction, observability score, best
frequency, best amplitude, or source-localization performance on the VM.

The scientific analysis will be done separately after the raw data are pushed.
