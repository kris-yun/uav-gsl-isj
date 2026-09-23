# CODEX W0.5 — GADEN Multi-Source Field Generation Cost Benchmark

Date: 2026-09-23  
Branch: \`research/wind-referenced-plume-world-model-v1\`  
Priority: **feasibility audit only — do not train a neural model**

## 0. Goal

Determine whether a small multi-source, time-resolved GADEN plume-field dataset can be generated cheaply enough to support the M3 stochastic plume world-model candidate.

This is **not** a performance experiment and must not use truth-source rank.

Use House02 only.

## 1. Existing local anchors

Known canonical scenario root:

\`/mnt/hgfs/workspace/GADEN_files/scenarios/House02\`

Known existing independent realization:

\`/home/zyc/hcmc_v1_independent_data_20260922/H02_R2026092211/FilamentSimulation_gasType_10_sourcePosition_0.00_-1.00_0.20\`

Existing run metadata showed:
- environment dimensions: 83 × 119 × 26;
- cell size: 0.1 m;
- GADEN player rate: 1 Hz.

Do not modify or overwrite any existing realization.

## 2. First inspect, do not run

Record:

- installed \`gaden\` / \`gaden_core\` source commit if available;
- whether Python bindings \`gaden_py\` are already usable;
- the exact House02 environment/wind configuration used by H02_R2026092211;
- simulation YAML/parameters for that realization;
- gas source parameters;
- available free-space/occupancy grid;
- sensor height used by the robot.

Do not upgrade GADEN or dependencies for this audit.

## 3. Preferred generation path

If current installed \`gaden_core\` supports the public API:

\`\`\`cpp
RunningSimulation
Simulation::SampleConcentration(point)
Simulation::SampleWind(point)
GasSource::sourcePosition
\`\`\`

prefer **in-memory RunningSimulation with saveResults=false**.

Reason:
- upstream GADEN documentation states result compression/saving is a major cost;
- for this benchmark we need only selected 2-D slices, not a full playback archive.

If Python bindings are unavailable, use a minimal C++ helper or existing ROS/GADEN interfaces. Do not reinstall the whole stack merely to satisfy the preferred path.

## 4. Two source positions only

### Source A
Use the existing House02 source position:

\`(0.00, -1.00, 0.20)\`

for a reproducibility/cost anchor.

### Source B
Choose one additional valid free-space source position **without using localization truth performance**.

Preferred deterministic rule:
- construct a free-cell list at the same source/sensor-relevant height;
- divide the map bounding box into four quadrants;
- choose the free cell nearest the center of a quadrant that does not contain Source A;
- resolve ties lexicographically.

Record the exact rule and selected coordinate before running.

Do not scan source positions for good localization results.

## 5. Minimal simulation contract

For each source:

- one stochastic seed initially;
- 60 s physical simulation;
- use the same House02 environment and wind configuration;
- preserve the existing H02 gas/filament parameters unless an incompatibility is documented;
- \`saveResults=false\` when using RunningSimulation;
- no robot/navigation process is needed.

## 6. Field sampling

Goal: obtain a small 2-D concentration sequence at robot sensor height.

Start with:
- a coarse spatial stride of 0.2–0.3 m rather than every 0.1 m cell;
- sample only free cells;
- physical times: 20, 30, 40, 50, 60 s.

For each sampled cell/time, save:

\`x,y,z,t,concentration,wind_u,wind_v,wind_w,occupancy/source metadata\`

Do not enable GADEN \`preCalculateConcentrations=true\` unless direct sampling is prohibitively slow and you explicitly document why.

## 7. Required cost measurements

For each source record separately:

- environment/config load time;
- simulation-only wall time;
- concentration-grid sampling wall time;
- total wall time;
- peak RAM if practical;
- number of free sampled points per slice;
- output bytes;
- number of active filaments at the final sample if API exposes it.

The key decision is whether grid sampling or gas simulation dominates.

## 8. Basic physical sanity checks

No source-localization metric.

For each slice report:

- concentration min/median/max;
- nonzero-cell fraction;
- concentration-weighted centroid;
- mean wind magnitude;
- fraction of concentration mass in occupied cells (should be zero/negligible under the simulator contract).

Create a small PNG or CSV summary only if easy; raw numeric evidence is more important than visualization.

## 9. Optional reproducibility micro-check

Only if the first two runs are cheap:

- repeat Source B with a second stochastic seed;
- report field correlation / normalized difference at the five sampled times.

This is useful for estimating whether a stochastic world model has real distributional variability to learn.

## 10. Hard decision rule

### PASS
Advance M3 data feasibility if:

- two source positions can be generated and sampled without infrastructure problems;
- total cost extrapolates to a practical pilot of roughly 4–8 source positions per House × 2 seeds;
- fields contain meaningful spatial stochastic structure.

### HOLD
If only source generation or sampling is slow but there is an obvious engineering acceleration (coarser points, fewer times, C++ batch query), report HOLD and quantify it.

### NO-GO
Demote M3 if a small multi-source field dataset would require impractical compute/storage, or if the installed GADEN stack cannot expose usable fields without rebuilding the project substantially.

Do not start neural training in this task.

## 11. Required outputs

Commit under:

\`evidence/wind_referenced_plume_world_model_v1/w05_gaden_multisource_benchmark/\`

At minimum:

- \`W05_DECISION.md\`
- \`environment_provenance.json\`
- \`source_design.json\`
- \`cost_metrics.csv\`
- \`sourceA_fields.csv.gz\`
- \`sourceB_fields.csv.gz\`
- logs / helper script used.

Commit and push after the benchmark.

Stop after W0.5.
