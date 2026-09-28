"""Opt-in HD-PLF local controller; Native PMFS inference remains external.

The frozen encounter-memory state machine handles the first measured hit,
A-B-A validation, optional C sample, revocation and original task budget.
This sibling controller replaces only its B waypoint choice with the
gain-invariant LF-u or LF-rawu action. It is not wired into ROS/VGR yet.
"""

from __future__ import annotations

from pathlib import Path
from sys import path as import_path
from typing import Iterable, Sequence

import numpy as np

from hd_plf_action import ActionDecision, GoalCandidate, HDPLFActionSelector

_MEMORY_DIR = Path(__file__).resolve().parents[1] / "verified_local_encounter_v0"
if str(_MEMORY_DIR) not in import_path:
    import_path.insert(0, str(_MEMORY_DIR))
from local_action_policy import Decision, LocalActionPolicy, PathLength, StopEvent, XY  # noqa: E402


class HDPLFLocalController(LocalActionPolicy):
    """AOD-guided departure, frozen measured-event memory and revocation."""

    def __init__(self, arm: str, amplitude_maps: np.ndarray):
        super().__init__("verified_local")
        self.action = HDPLFActionSelector(arm, amplitude_maps)
        self.last_action_decision: ActionDecision | None = None
        self._native_q: Sequence[float] | None = None
        self._actual_history_cells: Sequence[int] | None = None
        self._reachable_goals: Sequence[GoalCandidate] | None = None

    def decide(
        self,
        native_goal_xy: XY,
        now_s: float,
        event: StopEvent | None,
        free_centers: Iterable[XY],
        path_length: PathLength,
        *,
        native_source_probability: Sequence[float],
        actual_history_cells: Sequence[int],
        reachable_goals: Sequence[GoalCandidate],
    ) -> Decision:
        self._native_q = native_source_probability
        self._actual_history_cells = actual_history_cells
        self._reachable_goals = reachable_goals
        try:
            return super().decide(native_goal_xy, now_s, event, free_centers, path_length)
        finally:
            self._native_q = None
            self._actual_history_cells = None
            self._reachable_goals = None

    def _candidate_b(self, anchor: XY, native: XY, free_centers: Iterable[XY],
                     path_length: PathLength) -> XY | None:
        assert self._native_q is not None
        assert self._actual_history_cells is not None
        assert self._reachable_goals is not None
        result = self.action.choose(native, anchor, self._actual_history_cells,
                                    self._native_q, self._reachable_goals)
        self.last_action_decision = result
        if result.selected is None:
            return None
        # Fail closed if the action-side geometry disagrees with the frozen
        # navigation callback or the VGR free-center list.
        goal = result.goal_xy
        if not any(self._distance(goal, center) <= 1e-9 for center in free_centers):
            return None
        if not self._reachable(goal, path_length):
            return None
        return goal
