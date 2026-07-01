"""OP-GSL: Orienteering-based Gas Source Localization.
Based on InfotaxisAgent, replaced single-step greedy with multi-step OP planning.
Key innovation: time-budget-aware path planning using information gain as reward.
"""
import numpy as np
import math
import heapq
from collections import defaultdict


class OPGSLConfig:
    def __init__(self):
        # Grid parameters
        self.grid_resolution = 0.5
        self.grid_size = 30

        # Plume model
        self.source_rate = 1.0
        self.diffusivity = 0.1
        self.mean_wind_speed = 0.5
        self.detection_threshold = 0.01
        self.dt = 1.0

        # OP-GSL specific
        self.time_budget = 300.0        # seconds
        self.uav_speed = 1.0            # m/s
        self.replan_interval = 5        # replan every N steps
        self.op_horizon = 10            # max waypoints in OP solution
        self.exploration_bonus = 0.1    # bonus for unvisited high-IG areas


class OPGSLAgent:
    """Orienteering-based Gas Source Localization.

    Core: at each replan, solve a mini-OP to find the best path through
    high-IG waypoints within remaining time budget.
    """

    def __init__(self, config=None, time_budget=300.0, uav_speed=1.0):
        self.config = config or OPGSLConfig()
        self.config.time_budget = time_budget
        self.config.uav_speed = uav_speed

        self.grid_res = self.config.grid_resolution
        self.grid_size = self.config.grid_size
        self.n_cells = int(2 * self.grid_size / self.grid_res)

        # Log-posterior (source belief)
        self.log_posterior = np.zeros((self.n_cells, self.n_cells))
        self.log_posterior[:] = -np.log(self.n_cells * self.n_cells)

        # Actions: 8 directions + stay
        self.actions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
            (0, 0)
        ]
        self.action_dist = self.grid_res

        # State tracking
        self.step_count = 0
        self.elapsed_time = 0.0
        self.visited_cells = set()
        self.current_pos = (self.n_cells // 2, self.n_cells // 2)

        # Precomputed IG cache
        self._ig_cache = {}
        self._ig_cache_valid = False

    def _pos_to_grid(self, x, y):
        gx = int((x + self.grid_size) / self.grid_res)
        gy = int((y + self.grid_size) / self.grid_res)
        return max(0, min(gx, self.n_cells - 1)), max(0, min(gy, self.n_cells - 1))

    def _grid_to_pos(self, gx, gy):
        return gx * self.grid_res - self.grid_size, gy * self.grid_res - self.grid_size

    def _log_likelihood(self, gas_reading, robot_pos, source_pos, wind):
        dx = robot_pos[0] - source_pos[0]
        dy = robot_pos[1] - source_pos[1]
        dist = math.sqrt(dx * dx + dy * dy) + 0.1

        wind_norm = math.sqrt(wind[0] ** 2 + wind[1] ** 2) + 1e-6
        wind_dx = wind[0] / wind_norm
        wind_dy = wind[1] / wind_norm
        alignment = (dx * wind_dx + dy * wind_dy) / dist

        expected_conc = self.config.source_rate / (dist * dist + 1.0)
        if alignment > 0:
            expected_conc *= (1.0 + alignment)

        if gas_reading > self.config.detection_threshold:
            log_lik = -0.5 * ((gas_reading - expected_conc) ** 2) / (expected_conc + 0.01)
            log_lik -= 0.5 * dist
        else:
            log_lik = -0.1 * dist

        return log_lik

    def update(self, gas_reading, robot_pos, wind):
        """Update posterior with new observation."""
        self._ig_cache_valid = False
        self.step_count += 1
        self.elapsed_time += self.config.dt

        gx, gy = self._pos_to_grid(robot_pos[0], robot_pos[1])
        self.current_pos = (gx, gy)
        self.visited_cells.add((gx, gy))

        for sx in range(self.n_cells):
            for sy in range(self.n_cells):
                src_pos = self._grid_to_pos(sx, sy)
                log_lik = self._log_likelihood(gas_reading, robot_pos, src_pos, wind)
                self.log_posterior[sx, sy] += log_lik

        # Normalize
        max_log = np.max(self.log_posterior)
        self.log_posterior -= max_log
        log_sum = np.log(np.sum(np.exp(self.log_posterior)))
        self.log_posterior -= log_sum

    def _compute_entropy(self):
        p = np.exp(self.log_posterior)
        p = p / np.sum(p)
        return -np.sum(p * self.log_posterior)

    def _expected_entropy_after_action(self, action, robot_pos, wind):
        """Expected entropy after taking an action (single-step IG)."""
        new_x = robot_pos[0] + action[0] * self.action_dist
        new_y = robot_pos[1] + action[1] * self.action_dist
        new_pos = (new_x, new_y)

        p_hit = 0.0
        for sx in range(self.n_cells):
            for sy in range(self.n_cells):
                src_pos = self._grid_to_pos(sx, sy)
                dx = new_pos[0] - src_pos[0]
                dy = new_pos[1] - src_pos[1]
                dist = math.sqrt(dx * dx + dy * dy) + 0.1
                expected_conc = self.config.source_rate / (dist * dist + 1.0)
                p_hit_cell = min(expected_conc / (self.config.detection_threshold + 0.01), 1.0)
                p_hit += np.exp(self.log_posterior[sx, sy]) * p_hit_cell

        p_hit = min(max(p_hit, 0.01), 0.99)
        p_miss = 1.0 - p_hit

        current_entropy = self._compute_entropy()
        entropy_after_hit = current_entropy * 0.5
        entropy_after_miss = current_entropy * 0.95

        return p_hit * entropy_after_hit + p_miss * entropy_after_miss

    def _compute_ig_for_cell(self, gx, gy, robot_pos, wind):
        """Compute information gain for visiting a specific cell."""
        new_pos = self._grid_to_pos(gx, gy)
        action = (gx - self.current_pos[0], gy - self.current_pos[1])
        if abs(action[0]) > 1 or abs(action[1]) > 1:
            # Multi-step: approximate IG as sum of single-step gains
            dist = math.sqrt(action[0] ** 2 + action[1] ** 2)
            steps = int(math.ceil(dist))
            total_ig = 0.0
            for s in range(steps):
                frac = (s + 1) / steps
                interp_pos = (
                    robot_pos[0] + (new_pos[0] - robot_pos[0]) * frac,
                    robot_pos[1] + (new_pos[1] - robot_pos[1]) * frac
                )
                # Approximate single-step IG at interpolated position
                p_hit = 0.0
                for sx in range(0, self.n_cells, 3):  # subsample for speed
                    for sy in range(0, self.n_cells, 3):
                        src_pos = self._grid_to_pos(sx, sy)
                        dx = interp_pos[0] - src_pos[0]
                        dy = interp_pos[1] - src_pos[1]
                        dist_s = math.sqrt(dx * dx + dy * dy) + 0.1
                        expected_conc = self.config.source_rate / (dist_s * dist_s + 1.0)
                        p_hit += np.exp(self.log_posterior[sx, sy]) * min(expected_conc / 0.01, 1.0)
                p_hit = min(max(p_hit, 0.01), 0.99)
                total_ig += p_hit * 0.5 + (1 - p_hit) * 0.05
            return total_ig / steps
        else:
            return self._expected_entropy_after_action(action, robot_pos, wind)

    def _build_op_graph(self, robot_pos, wind, remaining_time):
        """Build OP graph: candidate waypoints with IG rewards."""
        # Select top-K cells by IG as candidate waypoints
        K = min(self.config.op_horizon, 20)
        candidates = []

        # Get estimated source position (MAP)
        est_idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        est_pos = self._grid_to_pos(est_idx[0], est_idx[1])

        # Sample candidates: near MAP + unvisited high-IG cells
        for dx in range(-5, 6):
            for dy in range(-5, 6):
                gx = self.current_pos[0] + dx
                gy = self.current_pos[1] + dy
                if 0 <= gx < self.n_cells and 0 <= gy < self.n_cells:
                    pos = self._grid_to_pos(gx, gy)
                    dist_from_current = math.sqrt(dx * dx + dy * dy) * self.grid_res
                    max_dist = remaining_time * self.config.uav_speed

                    if dist_from_current <= max_dist and dist_from_current > 0:
                        ig = self._compute_ig_for_cell(gx, gy, robot_pos, wind)
                        # Exploration bonus for unvisited cells
                        if (gx, gy) not in self.visited_cells:
                            ig *= (1.0 + self.config.exploration_bonus)
                        candidates.append((gx, gy, ig, dist_from_current))

        # Sort by IG and take top-K
        candidates.sort(key=lambda c: c[2], reverse=True)
        return candidates[:K]

    def _solve_op_greedy(self, candidates, robot_pos, remaining_time):
        """Greedy OP solver: select path maximizing total IG within time budget."""
        if not candidates:
            return []

        budget = remaining_time * self.config.uav_speed
        selected = []
        current = self.current_pos
        remaining_budget = budget
        used = set()

        for _ in range(min(len(candidates), self.config.op_horizon)):
            best = None
            best_ratio = -1

            for gx, gy, ig, dist in candidates:
                if (gx, gy) in used:
                    continue
                # Distance from current position to this candidate
                dx = gx - current[0]
                dy = gy - current[1]
                travel_dist = math.sqrt(dx * dx + dy * dy) * self.grid_res

                if travel_dist <= remaining_budget and travel_dist > 0:
                    ratio = ig / travel_dist
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best = (gx, gy, ig, travel_dist)

            if best is None:
                break

            gx, gy, ig, dist = best
            selected.append((gx, gy, ig))
            used.add((gx, gy))
            current = (gx, gy)
            remaining_budget -= dist

        return selected

    def choose_action(self, robot_pos, wind):
        """Choose action using OP planning or single-step infotaxis fallback."""
        remaining_time = self.config.time_budget - self.elapsed_time

        # Replan every N steps
        if self.step_count % self.config.replan_interval == 0 and remaining_time > 0:
            # Build OP graph and solve
            candidates = self._build_op_graph(robot_pos, wind, remaining_time)
            op_path = self._solve_op_greedy(candidates, robot_pos, remaining_time)

            if op_path:
                # Move toward first waypoint in OP path
                target_gx, target_gy, _ = op_path[0]
                dx = target_gx - self.current_pos[0]
                dy = target_gy - self.current_pos[1]

                # Clamp to single-step
                dx = max(-1, min(1, dx))
                dy = max(-1, min(1, dy))

                if abs(dx) <= 1 and abs(dy) <= 1:
                    return (dx, dy)

        # Fallback: single-step infotaxis
        best_action = self.actions[0]
        best_entropy = float('inf')

        for action in self.actions:
            new_x = robot_pos[0] + action[0] * self.action_dist
            new_y = robot_pos[1] + action[1] * self.action_dist
            if abs(new_x) > self.grid_size or abs(new_y) > self.grid_size:
                continue

            expected_ent = self._expected_entropy_after_action(action, robot_pos, wind)
            if expected_ent < best_entropy:
                best_entropy = expected_ent
                best_action = action

        return best_action

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        return self._grid_to_pos(idx[0], idx[1])

    def get_posterior_entropy(self):
        return self._compute_entropy()

    def get_remaining_time(self):
        return max(0, self.config.time_budget - self.elapsed_time)

    def get_op_stats(self):
        """Return OP planning statistics."""
        return {
            'step_count': self.step_count,
            'elapsed_time': self.elapsed_time,
            'remaining_time': self.get_remaining_time(),
            'visited_cells': len(self.visited_cells),
            'posterior_entropy': self.get_posterior_entropy(),
        }
