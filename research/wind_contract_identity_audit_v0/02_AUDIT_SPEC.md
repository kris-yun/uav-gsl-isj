# Read-only audit specification

## Local assets

Use these existing VM assets only:

- `/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/wind_value_server.py`
- `/home/zyc/ros2_ws/src/vgr_bridge/vgr_bridge/vgr_sim_node.py`
- `/mnt/hgfs/workspace/GADEN_files/scenarios/House01`
- House01 config id: `2,4-1_fast`
- existing successful R1 run:
  `/home/zyc/native_pmfs_recovery_v1/runs/NATIVE_RECOVERY_R1_House01_S0_20260923T071027Z`

Do not start ROS, GADEN, gaden_player, PMFS, or any simulator.

## Phase A — prove the two wind adapters' data contract

Read and hash `wind_value_server.py` and `vgr_sim_node.py`.

Record, with source line ranges:

- file(s) loaded for House01 config `2,4-1_fast`;
- number and names of wind states/files;
- x/y/z coordinate convention;
- interpolation / nearest-cell rule;
- whether either adapter changes sign or rotates the vector;
- whether either adds noise;
- how the anemometer message `wind_speed` and `wind_direction` are formed;
- exact z used by the R1 anemometer and exact z used by Native PMFS
  `/wind_value` requests, recoverable from existing logs/TF export if present;
- any time/state-index rule used by the VGR sensor.

If the two adapters do not ultimately read the same underlying wind state
family, stop with `WIND_CONTRACT_DIFFERENT_ASSETS`.

## Phase B — probe all 11 states, no time assumption

Using **the exact loader/interpolation semantics of `wind_value_server.py`**,
evaluate every available House01 wind state at the four R1 event positions:

A = (-3.17, -1.75)
B = (-5.60, -0.83)
C = (-6.20, -5.93)
D = (-4.10, -0.53)

Use the exact R1 anemometer z if it is recoverable. If not, probe both:
- the z used by `/wind_value` in the R1 run;
- robot/flight z = 0.3 m,
and mark this as a z-contract audit, not a free tuning parameter.

Write `wind_state_probe.csv` with exactly:

`wind_state,x,y,z,u,v,speed,direction,source_file`

for all 11 states × four sites × each predeclared z arm.

## Phase C — event/state identity matching

Run the supplied `analyze_wind_state_match.py` against:
- `event_vectors.csv`
- `wind_state_probe.csv`

The analyzer never reads source truth.

Interpretation:

- `MATCH_SEQUENCE_RECOVERED`:
  each of the 20 events has a clearly best compatible state and the matched
  state sequence is temporally coherent under the adapter's documented state
  update/loop rule.
- `SAME_ASSETS_BUT_NO_EVENT_MATCH`:
  same underlying assets are proven, but event vectors cannot be explained by
  the 11 states at the correct z within the sensor/averaging semantics.
- `WIND_CONTRACT_DIFFERENT_ASSETS`:
  adapters load different wind families or incompatible coordinate/vector
  semantics.
- `HOLD_Z_OR_TIME_SEMANTICS_UNRESOLVED`:
  exact z or adapter timing cannot be recovered from existing files/logs.

No source localization rank is evaluated in this audit.
