# BRG V1 case 009 navigation repair result

## Repair and integrity

The original 12 pilot runs remain archived. Their path-planning callback raised
`AttributeError: 'PosixPath' object has no attribute 'header'`, so those runs
cannot be treated as a valid active-navigation algorithm comparison.

The deployed VGR module used `nav_msgs.msg.Path as RosPath` in its planning
callback, retaining `pathlib.Path` for files. The deployed Native planner now
reports `PMFS_NO_VALID_PLAN` and returns if no candidate passes `checkGoal`.
The binder now stops on callback exceptions and records planning integrity.
The two source patches are included with this report; both pre-fix binaries
and source files were preserved on the VM.

Before gas replay, the actual imported VGR module passed a ROS
`ComputePathToPose` action test with the frozen case 009 House01 map: the
reachable non-origin goal `(-4.1,-2.03)` returned four poses with the exact
endpoint and `map` frame; an out-of-bounds goal returned an empty path.
The test imported
`/home/zyc/brg_closedloop_20260927/vgr_execution_v2/vgr_bridge/vgr_sim_node.py`
with SHA256 `c67e442dc4cfceb9e448651398d996b867eb751b757cd7ab457f4f69d82d95f5`.
The rebuilt and deployed `gsl_actionserver_node` SHA256 was
`5c9eb17a0c6f5fab338ec06ea0ce786a8239cf2ad60c290115bd161c25ef4e9f`.

## Frozen two-run check

Both arms used case `House01_1,3-2,4_fast_pmfs_26_36_seed1453872`, 596
Native-legal candidates with bank ID
`ce18a95c7bb44cda91395c6febf19b967ebf477e6bd174c7f5e2ed7e048509b7`,
the same 300 s budget, source, plume, sensor and start. BRG used the existing
checkpoint SHA256
`ee57607060f7241bdc24edb2d71e97a2b6c5c0de1901b2d1462d5034dc5c2289`.
No model training or new GADEN plume generation occurred.

| Arm | Geometric success | Final source error | Paths returned / goals succeeded | Path length | Measurements | Distinct measurement positions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Native | 0 | 1.6091 m | 12 / 12 | 50.45 m | 63 | 13 |
| BRG | 0 | 12.0446 m | 11 / 11 | 42.03 m | 57 | 12 |

Each arm had zero callback exceptions, zero no-valid-plan events, and zero
default `(0,0)` goals. Both ended by the 300 s time budget with no algorithm
success declaration. Their source maps changed during navigation (four
distinct recorded maps each). The BRG sidecar logged 57 successful `STEP`
responses. The independently reproducible counts are in
`NAVFIX_TWO_RUN_AUDIT.json`; full navigation, pose, observation, belief,
sidecar, and ROS logs are in the two raw archives.

The repaired run establishes a valid VGR interactive-navigation comparison
for this one inspected development case. BRG did not improve localization on
it. The saved BRG checkpoint also has development NLL 6.5056, worse than the
uniform 596-candidate reference 6.3902; fixing navigation does not change
that earlier training result. This two-run check does not estimate a campaign
success rate or justify a general claim about other cases or methods.

No GRU, ungated, additional cases, new plume, or further training were run.
