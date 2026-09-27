# Pre-scoring infrastructure audit

No scored 384-run campaign has started. All checks below are software binding
checks on already-OPEN existing assets, not new scientific gates.

## Actual motion backend

The recovered launch uses ROS2 GADEN `frame_query` and a VGR motion/action
backend. It does not launch Gazebo. Gazebo and Nav2 are installed in the VM,
but the inspected Gazebo launch belongs to a tutorial robot/world. The PX4
workspace is an archived stub. A Gazebo physical-UAV result cannot be claimed
from this VGR launch. User has been asked to bind the intended backend.

## Candidate support contradiction found by running the actual Native binary

The frozen AOD bank has 624 model candidates. The actual Native initialization
at the fixed House03 start (2.0, 0.0) invokes `PruneUnreachableCells` and leaves
615 free source cells. Grid metadata agrees with that 615 count.

The nine bank cells removed by Native are:
577, 622, 624, 700, 746, 792, 1002, 1048, 1094.

Grid dimensions/origin/resolution otherwise match the bank. Thus the package's
requirements of full624 and exact Native legal support conflict for the actual
runtime. No candidate has been silently removed from a neural bank; Native
pruning has not been changed. Formal scoring awaits an explicit contract
resolution. Model-only full OPEN bank generation can continue independently.

## Source estimate

The old generic benchmark used the terminal robot pose as the PMFS estimate.
The isolated adapter now reads the actual PMFS probability map estimate using
the same Native top-5-percent probability-weighted estimator for every arm.
Robot proximity remains auxiliary. Belief JSONL is read-only instrumentation.

## Physical time and readiness

All 96 existing realizations have their own `RESULT_TIME_MAP.tsv`; they are not
constant-0.5-second frame clocks. The adapter performs causal snapshot hold
using the recorded writer times. An arbitrary 8-second wall-clock startup
timer was removed in the isolated launch. Simulation now starts after the
Native initialized belief is recorded at simulation/search time zero. The
motion clock may advance after the observation horizon to allow action cleanup,
but no gas/wind evidence beyond the frozen 300 s budget is admitted.

## Primary endpoint clarification

The user's clarification in amendment/06_GEOMETRIC_SUCCESS_CLARIFICATION.md
supersedes the original instruction to count every timeout as geometric failure.
Geometry, declaration, timeout and navigation proximity remain separate fields.
