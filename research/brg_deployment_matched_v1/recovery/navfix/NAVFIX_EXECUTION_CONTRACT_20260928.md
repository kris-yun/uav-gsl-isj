# BRG V1 navigation repair check

The original three-case, four-arm VGR pilot remains preserved. Its 12 runs had
planner callback exceptions and default `(0, 0)` goals, so their geometric
outcomes do not measure normal active navigation. The frozen development-set
NLL results and existing network checkpoints remain unchanged.

This infrastructure revision changes only:

1. The deployed VGR callback uses `nav_msgs.msg.Path as RosPath` when returning
   a navigation path; filesystem `pathlib.Path` keeps its existing name.
2. The deployed Native planner reports `PMFS_NO_VALID_PLAN` and returns if no
   candidate passes `checkGoal`, instead of sending a default goal.
3. The evaluation binder stops on a planning callback exception and records
   path request, path response, issued goal, movement, and observation counts.

Before any gas replay, the actual imported VGR module must pass a callback
check using the frozen House01 case 009 occupancy map. A reachable non-origin
goal must return a nonempty ROS `Path` with the correct endpoint and `map`
frame; an unreachable goal must return an empty path.

Only frozen case 009 may then be rerun: one Native and one BRG run with the
existing checkpoint, 300 s budget, same source, seed, start, support, plume,
sensor, and stopping rule. New output stems begin with `navfix_` so they cannot
overwrite prior pilot logs. Do not retrain, generate plume, run GRU/ungated,
or expand the campaign. These two inspected development runs are a repair
verification, not fresh confirmation.

The Native run must complete with at least one nonempty path, issued goal,
actual movement, and observation before proceeding to BRG. Either callback
exception or zero valid navigation invalidates the run and stops the check.
