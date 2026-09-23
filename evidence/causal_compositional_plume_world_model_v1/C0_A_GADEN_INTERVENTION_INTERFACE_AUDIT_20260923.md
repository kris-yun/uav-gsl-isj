# C0-A GADEN Intervention-Generation Interface Audit

Date: 2026-09-23  
Branch: `research/causal-compositional-plume-world-model-v1`

## Decision

`C0-A = POSITIVE INTERFACE SIGNAL`

The existing project generator already supports a clean **source intervention** without recomputing CFD wind.

## 1. Existing generator

Repository script:

`reference/generate_hcmc_v1_realizations.sh`

uses the GADEN filament simulator with explicit ROS parameters for:

- occupancy grid;
- wind data directory;
- source x/y/z;
- plume RNG seed;
- gas simulation parameters.

For each House the current generator reuses a canonical wind directory and changes only the plume RNG seed across independent realizations.

## 2. Source intervention is clean

The source is supplied through:

- `source_position_x`;
- `source_position_y`;
- `source_position_z`.

Therefore an M4 source intervention can be implemented as:

[
do(S=s')
]

while keeping fixed:

- `OccupancyGrid3D.csv`;
- exact `wind_data` directory;
- gas type;
- release/filament settings;
- numerical time step;
- all other simulator parameters.

No CFD/wind recomputation is required.

This is exactly the intervention structure required by C0.

## 3. Wind is independently addressable

The generator passes:

`-p wind_data:=".../wind"`

as a separate parameter.

Therefore a wind intervention is also structurally possible:

[
do(W=W')
]

provided the same House has a second physically valid wind directory.

The next VM audit must inventory all candidate wind directories for the selected House.

### Preferred wind intervention

Use two independently generated/canonical wind configurations from the same House.

### Fallback

If only one physical wind field exists:
- use a source-blind speed scaling benchmark only as a preliminary mechanism test;
- do not call it a full physical wind-intervention validation.

## 4. Existing formal generation contract

Current independent plume generator uses:

- `sim_time = 1000.0 s`;
- `time_step = 0.1 s`;
- `num_filaments_sec = 7`;
- `filament_noise_std = 0.01`;
- `filament_growth_gamma = 15.0`;
- `save_results = 1`;
- `results_time_step = 0.5 s`;
- `writeConcentrations = false`.

For 1000 s cases the script requires at least 1501 stored `iteration_*` frames.

The saved realization is therefore a filament-state trajectory, not a precomputed dense concentration movie.

## 5. Important implication

For M4/M5 pilot generation, do **not** regenerate wind.

Reuse the same House occupancy + wind field and vary:

- source position;
- plume seed.

This cleanly separates source mechanism from stochastic plume realization.

## 6. Required cost benchmark before 2×2 generation

Codex/VM should run one **new source position** with the same House/wind at three durations:

- 30 s;
- 120 s;
- 300 s.

For each record:

- wall-clock time;
- CPU utilization;
- peak RAM;
- output disk size;
- iteration count;
- average active filament count if available.

Do not start 1000 s × many source cases before this benchmark.

## 7. Data format choice

For M4 C0, the final learning target need not save dense concentration grids every simulation step.

Preferred pilot:

1. run/save native filament states;
2. at a small fixed set of predeclared times reconstruct/sample concentration at sensor-height grid;
3. store only the resulting compact 2-D slices needed for training.

This avoids the GADEN warning that full precomputed concentration maps are much larger/slower.

## 8. Required same-House wind inventory

Before selecting House:

List, for House01/02/03:

- all available wind configuration directories;
- grid dimensions;
- number of wind iterations;
- mean/median/max wind speed;
- hashes.

Select the House with:
- at least two physically valid distinct wind fields;
- same occupancy geometry;
- manageable generation time.

No source-truth information is needed.

## 9. C0 minimal factorial after cost pass

For one chosen House:

- S1, S2 source positions;
- W1, W2 physical wind configs;
- 2 plume seeds each.

Total full 2×2 dataset:

[
2	imes2	imes2=8
]

realizations.

Start with shorter simulation duration sufficient for a stable field pilot; only move to 1000 s if the first compositional signal is positive.

## 10. Kill / fallback

If:
- no House has a second physical wind configuration; or
- generation wall-clock is impractical;

then M4 should be marked `HOLD` until intervention data can be produced.

Do not replace real wind intervention with arbitrary rotations through obstacle geometry and then make a causal-world-model claim.
