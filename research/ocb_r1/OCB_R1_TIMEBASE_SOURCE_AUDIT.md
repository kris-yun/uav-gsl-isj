# OCB-R1 timebase source audit (read only)

## Provenance boundary

The historical ROS1 executable and its build directory were not located in the known VM `/home/zyc/ros2_ws` and `/opt/ros` binary locations. The archived ROS1 source at GADEN commit `2b5d1218d25cf8af6a789e99cd57ab0db07bce8e` (2021-11-25) is a **source candidate**, not a binary attestation. Its serialized format agrees with the historical 2022 zlib `iteration_*` headers (`int32 version=1` and the embedded wind index). The file sequence is exactly 0–1999. A read-only replay of that source's wind loop matches all 25 inspected historical wind indices, including first/middle/last and the ten frozen observation IDs. This is strong behavioral corroboration, but historical files do not serialize simulation time or integration step. `BINARY_PROVENANCE.tsv` records the missing executable explicitly.

The pinned current ROS2 executable SHA256 is `4127b9ba4f42186ba2d6d33c84fba8d4b92749da59b83750fa4847dbd9957ce1`. Its GADEN parent HEAD is `17adaf650a4f11d29aa049cf0661e9f9ea2e636f`, and embedded gaden_core HEAD is `9e93c36ae1af74f6a62c42f1c9d7b813153222ed`. This working source tree has modifications, so the source revision alone does not attest to the executable. The pinned binary's clock-control behavior had previously matched 566/566 records of an instrumented 300 s run; this audit did not execute it.

## Historical ROS1 writer

Source object `gaden_filament_simulator/src/filament_simulator.cpp` at the historical candidate commit:

- constructor lines 69–73: `sim_time=0.0` (double), `current_simulation_step=0`, `last_saved_step=-1`, wind forced to load on startup;
- `loadNodeParameters()` lines 170–176 and 250–252: `max_sim_time`, `time_step`, `results_time_step`, `results_min_time`; `numSteps=floor(max_sim_time/time_step)`;
- `main()` lines 1002–1049: wind update, filament release and move, then save if `sim_time>=results_min_time` and `floor(sim_time/results_time_step)!=last_saved_step`, then increment `sim_time += time_step` and step counter. The loop ends at `current_simulation_step<numSteps`; ROS is only the liveness check, not the saved simulation clock;
- `save_state_to_file()` lines 915–975: increments `last_saved_step`, names `iteration_<counter>`, writes zlib-compressed version-1 state including wind index, but no simulation time or integration step.

The ROS1 House02 launch `.../House02/launch/3,5-1_slow/GADEN_ros1.launch` pins `sim_time=1000` (line 39), `time_step=0.1` (line 40), wind step `1` (line 59), looping 1–10 (lines 61–63), `save_results=1`, `results_time_step=0.5`, `results_min_time=0.0` (lines 70–72). The other source/wind configurations require their own launch inputs, but this audited representative exactly matches the inspected saved sequence.

Conditional on the archived source being the generating code, for integration step `n=0..9999`, `t_n` is the iterative binary64 sum of `0.1`. A write occurs when `floor(t_n/0.5)` differs from the number of earlier writes minus one. The saved state has already completed that step's filament move; the clock label is the pre-increment `t_n`. Consequently `t_old(k)` is the `t_n` of the kth write, not always precisely `0.5*k` due binary64 accumulation: record 0 is 0, record 200 is 100.09999999999859, and record 1999 is 999.5000000001587 s. There are 2000 writes. The measured interrecord gap in this replay ranges 0.4–0.6 s.

`HISTORICAL_FILE_HEADERS.tsv` lists the first 5, middle 5, last 5, and all ten target records, including file metadata and embedded wind index. `HISTORICAL_RECORD_TIMES.tsv` gives their **derived, conditional** clock times. Filesystem mtime was recorded only as auxiliary provenance.

## Current ROS2 writer

Source `/home/zyc/hcmc_gaden_seed_build_20260922/src/GADEN/gaden_common/third_party/gaden_core/src/RunningSimulation.cpp`:

- `RunningSimulation::AdvanceTimestep()` lines 78–104: release, move, write when `currentTime > lastSaveTime + saveDeltaTime`, wind update, then `currentTime += deltaTime` and `currentIteration++`;
- `RunningSimulation.hpp` lines 74–82: the clock and last-save time are `float`, the latter initialized `-FLT_MAX`; saved record counter starts at zero;
- `SaveResults()` lines 357–451: names `iteration_<last_saved_step>`, serializes state, compresses/writes output, then increments the counter. No simulation timestamp is serialized;
- `filament_simulator.cpp` lines 87–103: ROS params set `deltaTime`, wind interval, `saveDeltaTime`; `pre_calculate_concentrations` defaults false; lines 148–154 loop while `GetCurrentTime()<maxSimTime`.

The ROS2 House02 launch at the same scenario path pins `sim_time=1000.0`, `time_step=0.1`, wind interval `1.0`, and `results_time_step=0.5`. The prospective record clock is the iterated binary32 sum `t_{n+1}=float32(t_n+float32(0.1))`. Save 0 occurs at `t_0=0`; later writes use the strict `>` condition. For this 1000 s configuration the source replay yields exactly **1803** records, index 0–1802, ending at clock 999.5029907226562 s. Save gaps are 0.5000001192–0.6000061035 s. This explains the 2000 vs 1803 difference quantitatively: the source revision changed from a floor-bin writer on a binary64 clock to a strict interval writer on an accumulating binary32 clock. The dt and nominal 0.5 s save parameter did not change; no 197 files are hidden or duplicated.

The read-only replay code is `replay_timebase_source.py`, with `CLOCK_REPLAY_SUMMARY.json` and sampled clocks in `CLOCK_TRACE_SAMPLES.tsv`. It uses the existing `research/e2c_r1/audit_e2_timebase.py` binary32 control-flow replay, which was checked against the 566-record instrumented 300 s clock log. No simulator was run for this audit.

## Ten-record mapping and decision

`RECORD_MAPPING_10.tsv` separates an **exact** current record ID from a *nearest* current record ID. All ten frozen historical IDs 100,150,...,550 have **no exact binary clock match**. Under the historical-source candidate, nearest-output absolute errors are max **0.2998046875 s**, median **0.2022613525 s**, mean **0.1822698975 s**. Only **1/10** nearest-output records has the same embedded/derived active wind index. In the old source, wind is advanced before saving and uses `>=`; in the new source it is advanced after saving and uses `>`. Thus output cadence alone cannot restore both clock and wind-state semantics. These are measured differences in the writer clock labels, not an accepted tolerance and not proof of equal plume age. The old executable absence and the missing embedded time prevent an unconditional assertion about the historical time axis.

Decision: **`TIMEBASE_APPROXIMATE_HOLD`**. The exact old clock is conditional on a behaviorally well-corroborated source candidate; the current writer provides only nearest-time correspondence for the ten targets. Do not use the nearest mapping for OCB-R1 science without a separately frozen tolerance and a physical-time definition. `OCB_R1_RUN_HOLD` remains.

## Save cadence and physics

For the pinned current configuration with `pre_calculate_concentrations=false`, the save branch only reads the post-move filament and wind state, serializes/compresses it, updates output buffers, the file counter, and `lastSaveTime`. It does not call an RNG, change solver `deltaTime`, trigger wind advancement, or feed a value into `AddFilaments()`/`MoveFilaments()`; wind advancement is a separate branch after save (`RunningSimulation.cpp` lines 78–104, 357–451). Thus **`SAVE_CADENCE_PHYSICS_INDEPENDENT=PASS` for this source-level control flow**. This does not make output-cadence recovery valid: changing `saveDeltaTime` cannot force the current binary32 simulation clock to take the historical binary64 values. No launch parameter was changed, and no recovery run was made.
