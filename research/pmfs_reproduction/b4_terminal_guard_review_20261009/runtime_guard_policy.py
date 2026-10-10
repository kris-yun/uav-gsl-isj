"""External process safety only. Never enforces a ROS search budget from goal time.

PMFS owns maxSearchTime=300 and its official success/failure decision.
All wall arguments are monotonic seconds relative to the same monotonic origin.
"""
from dataclasses import dataclass

@dataclass
class RuntimeGuard:
    started_wall: float
    initial_ros_ns: int
    wall_limit_s: float = 345.0
    clock_stall_limit_s: float = 15.0
    result_grace_s: float = 2.0
    maximum_clock_rate: float = 20.0
    jump_allowance_s: float = 2.0

    def __post_init__(self):
        self.last_wall = self.started_wall
        self.last_ros_ns = self.initial_ros_ns
        self.last_clock_advance_wall = self.started_wall
        self.pending_reason = None
        self.pending_since = None
        self.permanent_clock_fault = None

    def observe(self, wall, ros_ns, *, result_done=False, process_fault=None):
        # The actual action future wins over simultaneous watchdog/process events.
        if result_done:
            return {'action':'RESULT', 'reason':'NATIVE_ACTION_RESULT'}
        if wall < self.last_wall:
            raise ValueError('External wall clock must be monotonic')
        elapsed = wall-self.started_wall
        wall_delta = wall-self.last_wall
        ros_delta = (ros_ns-self.last_ros_ns)/1e9
        if ros_delta < -1e-6:
            self.permanent_clock_fault = 'ROS_CLOCK_BACKWARD_JUMP'
        elif ros_delta > self.jump_allowance_s+self.maximum_clock_rate*wall_delta:
            self.permanent_clock_fault = 'ROS_CLOCK_FORWARD_JUMP'
        if ros_delta > 0:
            self.last_clock_advance_wall = wall
        self.last_wall,self.last_ros_ns = wall,ros_ns
        # Begin draining results before the independent hard wall deadline.
        if elapsed >= self.wall_limit_s-self.result_grace_s:
            reason='NATIVE_GOAL_WALL_LIMIT_345S'
        elif self.permanent_clock_fault:
            reason=self.permanent_clock_fault
        elif process_fault:
            reason='GSL_OR_REQUIRED_PROCESS_EXIT'
        elif wall-self.last_clock_advance_wall >= self.clock_stall_limit_s-self.result_grace_s:
            reason='ROS_CLOCK_STALLED'
        else:
            self.pending_reason=self.pending_since=None
            return {'action':'WAIT', 'reason':'WAIT_NATIVE_ACTION'}
        if reason != self.pending_reason:
            self.pending_reason,self.pending_since=reason,wall
        if elapsed >= self.wall_limit_s or wall-self.pending_since >= self.result_grace_s:
            return {'action':'STOP', 'reason':reason}
        return {'action':'DRAIN', 'reason':reason}
