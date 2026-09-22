# Information-loss chain

```text
GADEN 3D wind snapshots + 3D filament snapshots (oracle, 1 s / 0.5 s)
    -> robot-local gas sensor output and wind/pose samples (0.2 s traces)
       LOSS: off-trajectory 3D field, other spatial locations, future truth
    -> stop-and-measure buffered samples -> completed hit/no-hit and PMFS hit map
       LOSS: within-block order, individual sample values in accepted artifacts,
             detailed temporal correlation; only completed-block evidence drives map
    -> PMFS 2D estimated wind grid + source-update candidate simulation
       LOSS: intermediate estimated grids are overwritten; candidate simulation
             uses one fixed current 2D grid, not GADEN's 3D time sequence
    -> candidate warmup + 200 recording steps × 0.2 s, five new filaments/step
       LOSS: warmup path, each filament path, per-step active set and occupied cells
    -> cumulative hitMap[cell] / 200 (binary per-step cell occupancy frequency)
       LOSS: time order, lag, covariance and transient structure; no concentration
    -> native score / posterior + context_bank source_update_0001
       LOSS: full native candidate map file absent in accepted bank; only
             observed-support slice survives in candidate_support_alignment.csv
```

The code proof is `runSimulation` calling `simulateSourceInPosition(source, result.hitMap, true, settings.iterationsToRecord, settings.deltaTime, ...)` at `internal/Simulations.cpp:903`, then the recording loop at `6719-6768` and `hitMap[i] = hitMap[i] / timesteps` at `6771-6775`. The loop counts each cell at most once per step via `updated[index] < t`. It is a frequency map, **not** gas exposure and not a full per-timestep hit-map tensor.

The timeline is not one clock: GADEN output cadence 0.5 s gas / 1 s wind, robot traces 0.2 s, and each candidate's independent 40 s internal model rollout. Mapping internal step `t` to a future robot location would invent a causal alignment. No source truth or future wind/gas/trajectory may be used by the shadow export.
