# House01 R1 wind contract identity audit

## Scope and provenance

Read-only, source-blind audit. No ROS node, GADEN, gaden_player, PMFS,
raw-query executable, plume simulation, network or localization scorer was run.
The supplied analyzer and event CSV are unchanged. This audit does not read a
source-truth evaluation file or promote either previously stopped hypothesis.

Original ZIP SHA256:
`4d5a578caee49c7f19a848c6fd3217fa1b98cced287611ffe15128eb69b5bc0f`.
`ASSET_INVENTORY.json` records source paths, sizes and SHA256 for both 11-state
wind families and the copied adapter/core sources. Wind data remain on the VM;
the review includes all required probe values, nearest-point records and hashes.

| Copied source | SHA256 |
| --- | --- |
| wind_value_server.py | e94becb2d72f82b9e040bb7a12d2b7132dc85283176cf0ee0b309b4804347116 |
| vgr_sim_node.py | 2b5d69d5a7cb00def5f462e1f0bc985eb9ca27a4bdad0bd3774abcd7e9204ed5 |
| sim_timebase.py | a104873911f23c27dba39001d1919092a5f58195f03e37f86fc76b0040c4351f |
| house1_raw_query.cpp | 1ceb45870c405f05eaae9a7dfd32b7beab77c3517706904ce23ff2b7d1d0aaeb |
| vgr_native_pmfs_recovery_20260923.launch.py | 880ed605ac04a7d6e5ccfd31801ef8f594065995fb03888da79effd0ee73f932 |

The wind server and recovery launch hashes agree with the historical R1 runtime
manifest. The current VGR bridge and core sources were read and hashed; R1 did
not record an independent VGR source hash. Historical runtime logs and traces
are therefore used to verify its actual backend, height and replay behavior.

## Forward wind adapter

`assets/wind_value_server.py:11-34` loads
`House01/wind_simulations/2,4-1_fast/2,4-1_fast_N.csv`, N=0..10.
The reader skips split-component files, parses N numerically, takes columns
0..2 as (u,v,w) and columns 3..5 as (x,y,z). Coordinates are used directly in
metres. `:44-56` always selects **min(wind_data.keys()) = 0**, calculates 3D
Euclidean distance and returns the first `numpy.argmin` row. There is no
interpolation, time update, vector sign change, rotation or added noise.

Thus the last `/wind_value` response is still CSV state 0. It is not a
time-selected snapshot of the sensor's then-current wind.

## Actual R1 sensor adapter

The historical launch excerpt, original launch arguments and manifest identify
`gas_backend=raw_house1_snapshot`; the legacy CSV branch in VGR was inactive.
`assets/vgr_sim_node.py:534-567` selects the recorded realization under the same
House01/config directory and starts the existing raw-query reader. `:740-779`
uses the wind returned by that reader, not `_get_wind_at_position()`.

`assets/house1_raw_query.cpp:31-50` loads all 11 binary `wind_iteration_N` files
under the selected realization's `wind` directory. **Lexical** ordering gives
file IDs `[0,1,10,2,3,4,5,6,7,8,9]`; a sequence index is not a numeric file ID.
`assets/WindSequence.cpp:133-170,211-237` decodes the legacy layout as three
consecutive double arrays and stores their components as float32.
`assets/Simulation.cpp:87-100`, `assets/Environment.cpp:59-62` and
`assets/MathUtils.hpp:13-16` select the containing raster voxel, with x-fastest
linear indexing. This is not continuous interpolation.

`assets/vgr_sim_node.py:930-934` publishes map-frame flow direction
`atan2(v,u)` and speed `norm((u,v))`. There is no wind noise or pi correction on
this active path. Gas sensor noise parameters do not perturb wind.
`assets/Algorithm.cpp:126-151` retains the flow direction and transforms it to
map; the received message already has frame `map`, so no rotation is added.

## Heights: resolved and different

The entire historical wind trace records **z=0.30 m**. The flight-height launch
argument also equals 0.30 m. This is the physical location sampled by the sensor.

The recovery launch `:80` sets `anemometer_frame="map"`.
`assets/PMFSLib.cpp:324-352` obtains map-to-anemometer TF translation z and puts
that value into every `/wind_value` request. With map-to-map this is **z=0**.
The original launch log line 316 explicitly says `anemometer z is 0`.
The sensor and candidate forward therefore sampled different height planes.

The primary frozen match uses only the recovered sensor height 0.30 m:
`wind_state_probe.csv` contains 11 states x 4 sites = 44 rows.
`forward_z_probe.csv` contains the separately labelled 44-row z=0 diagnostic.
The z=0 diagnostic is not pooled into the frozen event matcher and cannot be
selected opportunistically to improve an event match.

## Underlying wind family check

At all 44 specified state/site pairs at z=0.30 m, converting CSV components to
float32 reproduces the corresponding numbered binary components; maximum
observed component difference is `9.71445146547012e-17` from text parsing.
The binary diagnostic uses only direct file decoding, never the executable.
This establishes matching wind values at the audited locations, not a proof
that every voxel of both representations is globally identical.

The 824 recorded trace samples at these four sites match those binary vectors
with maximum 2D error `3.8999096908829904e-7 m/s`, consistent with six-decimal
trace storage. There is no evidence here for a different wind family or a pi
flip. The proven differences are height and time/state selection.

## Time and measurement aggregation

`assets/sim_timebase.py:40-49` defines seeded replay:
`usable=max_iteration-1=1998`, `offset=7919 % 1998=1925`,
`gas_frame=(1925+step)%1998`. Every stored trace row obeys this rule.
`assets/PlaybackSimulation.cpp:136-138,258-260,298-300` then sets the wind
sequence index from the stored frame's `windIndex` field. No wind_time_step
assumption was invented. The forward server has no equivalent timing rule.

The historical run configured `measurement_block_samples=10`.
`assets/StopAndMeasureState.cpp:36-58,111-126` consumes ten readings.
`assets/Math.hpp:89-102,105-122` separately averages speed arithmetically and
direction circularly. The effective vector constructed from these two means
is generally **not any one raw state vector**.

`BLOCK_AVERAGING_DIAGNOSTIC.json` retains the closest ten-consecutive-reading
window for each event, using the documented operations without fitting weights.
Every closest window mixes several file IDs. Maximum mean speed error is
`2.9802322554228766e-8 m/s`, maximum direction error is
`4.172325134277344e-7 rad`. These demonstrate compatibility with mixed-state
averaging; they do not identify the actual receipt windows. Repeated patterns
yield windows at earlier times, and the independently closest windows are not
monotone in event order. Exact block receipt boundaries were not logged.

## Frozen matcher and decision boundary

The supplied analyzer was run once, unchanged, on `event_vectors.csv` and the
44-row primary probe. Its 20 nearest **single-state** file IDs are:

`5,4,3,3,8,4,10,4,3,1,4,5,7,6,6,9,5,5,5,3`.

These IDs are ordering diagnostics, not a recovered physical state sequence.
The frozen contract requires a clearly compatible state for each event **and**
documented temporal coherence. That requirement was not established.
We do not invent an angular threshold, a wind timestep, alternate z, averaging
weights or a new PASS predicate after viewing the diagnostics.

Decision: **HOLD_Z_OR_TIME_SEMANTICS_UNRESOLVED**.
Height itself is resolved; the unresolved part is event-block to actual
time-window/wind-state assignment. Do not reinterpret this as
`SAME_ASSETS_BUT_NO_EVENT_MATCH`: mixed-state averaging does explain the event
vectors. Do not call it `WIND_CONTRACT_DIFFERENT_ASSETS`: same-numbered winds
agree at the audited locations. Do not claim `MATCH_SEQUENCE_RECOVERED` from
the nearest single-state list. No localization experiment follows.
