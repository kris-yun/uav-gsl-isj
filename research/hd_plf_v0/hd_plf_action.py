"""Source-blind gain-invariant action selection for the two HD-PLF template arms.

This module does not update a source belief, read an observation, or navigate.
The caller supplies Native PMFS probabilities and candidate amplitude maps in
exactly the same legal source order, plus reachable goals from the Native/VGR
navigation grid. Only the u versus rawu map is allowed to change between arms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


MOVE_COST_PER_M = 0.01
MIN_ANCHOR_RADIUS_M = 0.60
MAX_ANCHOR_RADIUS_M = 1.20
MAX_PATH_LENGTH_M = 2.70


@dataclass(frozen=True)
class GoalCandidate:
    cell_index: int
    x_m: float
    y_m: float
    path_length_m: float


@dataclass(frozen=True)
class GoalValue:
    goal: GoalCandidate
    pair_separation: float
    separation_gain: float
    travel_penalty: float
    action_value: float


@dataclass(frozen=True)
class ActionDecision:
    goal_xy: tuple[float, float]
    reason: str
    arm: str
    selected: GoalValue | None
    ranked_goals: tuple[GoalValue, ...]
    history_separation: float | None


class HDPLFActionSelector:
    """Choose a model-discriminative stop while leaving Native PMFS inference alone."""

    def __init__(self, arm: str, amplitude_maps: np.ndarray):
        if arm not in ("LF-u", "LF-rawu"):
            raise ValueError("arm must be LF-u or LF-rawu")
        maps = np.array(amplitude_maps, dtype=np.float64, copy=True)
        if maps.ndim != 2 or maps.shape[0] < 2 or maps.shape[1] < 1:
            raise ValueError("expected source x map-cell amplitude array")
        if not np.isfinite(maps).all() or (maps < 0).any():
            raise ValueError("amplitude maps must be finite and nonnegative")
        maps.setflags(write=False)
        self.arm = arm
        self.maps = maps

    @staticmethod
    def _pair_separation(views: np.ndarray, q: np.ndarray) -> float:
        """Sum q[a]q[b](1-cos(view[a],view[b])**2), a<b.

        A zero vector has undefined angle and contributes zero separation
        conservatively. Predicted source amplitudes are nonnegative, so the
        squared cosine matches positive-gain collinearity.
        """
        norms = np.linalg.norm(views, axis=1)
        valid = norms > 0
        unit = np.zeros_like(views)
        unit[valid] = views[valid] / norms[valid, None]
        # Identity: sum_{a<b} q_a q_b[1-(v_a·v_b)^2]
        # = 1/2[(sum_valid q)^2 - ||sum_valid q v v^T||_F^2].
        # This is O(S*K^2), avoiding an SxS matrix at full Native support.
        valid_mass = float(q[valid].sum())
        second_moment = (unit * q[:, None]).T @ unit
        value = .5 * (valid_mass * valid_mass - float(np.square(second_moment).sum()))
        return max(0.0, value)  # floating roundoff only

    def choose(
        self,
        native_goal_xy: tuple[float, float],
        anchor_xy: tuple[float, float],
        history_cells: Sequence[int],
        native_source_probability: Sequence[float],
        reachable_goals: Sequence[GoalCandidate],
    ) -> ActionDecision:
        """Return one feasible next goal and diagnostics; no truth is an input.

        `history_cells` contains distinct cells at completed real stop windows.
        `reachable_goals` carries unchanged navigation/BFS path lengths.
        Invalid bank alignment or map data fails closed to the Native goal.
        """
        native = (float(native_goal_xy[0]), float(native_goal_xy[1]))

        def fallback(reason: str) -> ActionDecision:
            return ActionDecision(native, reason, self.arm, None, (), None)

        if not all(math.isfinite(v) for v in (*native, *anchor_xy)):
            return fallback("fallback_invalid_geometry")
        q = np.asarray(native_source_probability, dtype=np.float64)
        if (q.ndim != 1 or len(q) != self.maps.shape[0] or
                not np.isfinite(q).all() or (q < 0).any() or q.sum() <= 0):
            return fallback("fallback_invalid_native_probability")
        q = q / q.sum()
        if np.count_nonzero(q) < 2:
            return fallback("fallback_one_supported_hypothesis")
        history = tuple(int(cell) for cell in history_cells)
        if (not history or len(set(history)) != len(history) or
                any(cell < 0 or cell >= self.maps.shape[1] for cell in history)):
            return fallback("fallback_invalid_actual_memory")

        baseline = self._pair_separation(self.maps[:, history], q)
        values: list[GoalValue] = []
        for goal in reachable_goals:
            if (goal.cell_index < 0 or goal.cell_index >= self.maps.shape[1] or
                    goal.cell_index in history or
                    not all(math.isfinite(v) for v in (goal.x_m, goal.y_m, goal.path_length_m))):
                continue
            radius = math.hypot(goal.x_m - anchor_xy[0], goal.y_m - anchor_xy[1])
            if not (MIN_ANCHOR_RADIUS_M - 1e-9 <= radius <= MAX_ANCHOR_RADIUS_M + 1e-9):
                continue
            if not (0 <= goal.path_length_m <= MAX_PATH_LENGTH_M + 1e-9):
                continue
            view = self.maps[:, (*history, goal.cell_index)]
            separation = self._pair_separation(view, q)
            penalty = MOVE_COST_PER_M * goal.path_length_m
            values.append(GoalValue(goal, separation, separation - baseline,
                                    penalty, separation - penalty))
        if not values:
            return fallback("fallback_no_reachable_local_goal")
        values.sort(key=lambda v: (-v.action_value, v.goal.path_length_m,
                                   v.goal.x_m, v.goal.y_m, v.goal.cell_index))
        best = values[0]
        return ActionDecision((best.goal.x_m, best.goal.y_m),
                              "hd_plf_gain_invariant_goal", self.arm, best,
                              tuple(values), baseline)
