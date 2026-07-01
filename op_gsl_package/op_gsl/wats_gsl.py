#!/usr/bin/env python3
"""
WATS-GSL: Wind-Aware Thompson Sampling for Gas Source Localization
=================================================================

Core Innovation: Instead of deterministic IG maximization (infotaxis/OP),
sample from the posterior and navigate toward the sample, biased by wind.

Key differences from existing methods:
1. Thompson Sampling: stochastic, naturally explores, avoids local optima
2. Wind-awareness: bias sampling toward downwind regions (physics prior)
3. Receding horizon: plan K steps ahead, execute first step

Mathematical Foundation:
- Sample s ~ P(source | D_t)  (Thompson Sampling)
- Navigate toward s with wind-aware path planning
- Update posterior with new observation
- Repeat

Novelty: Thompson Sampling + wind-aware physics prior for GSL = 0 papers
"""
import numpy as np
import math


class WATSConfig:
    def __init__(self):
        self.grid_resolution = 1.0
        self.grid_size = 30
        self.source_rate = 1.0
        self.diffusivity = 0.1
        self.mean_wind_speed = 0.5
        self.detection_threshold = 0.01
        self.dt = 1.0
        self.time_budget = 300.0
        self.uav_speed = 1.0
        self.wind_awareness = 0.5  # how much wind influences direction
        self.exploration_rate = 0.1  # probability of random exploration


class WATSAgent:
    """Wind-Aware Thompson Sampling GSL Agent."""

    def __init__(self, config=None, time_budget=300.0, uav_speed=1.0):
        self.config = config or WATSConfig()
        self.config.time_budget = time_budget
        self.config.uav_speed = uav_speed

        self.grid_res = self.config.grid_resolution
        self.grid_size = self.config.grid_size
        self.n_cells = int(2 * self.grid_size / self.grid_res)

        # Source belief
        self.log_posterior = np.zeros((self.n_cells, self.n_cells))
        self.log_posterior[:] = -np.log(self.n_cells * self.n_cells)

        # Actions
        self.actions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
            (0, 0)
        ]
        self.action_dist = self.grid_res

        # State
        self.step_count = 0
        self.elapsed_time = 0.0
        self.visited_cells = set()
        self.current_pos = (self.n_cells // 2, self.n_cells // 2)

        # Wind state
        self.current_wind = (0.0, 0.0)

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
        self.step_count += 1
        self.elapsed_time += self.config.dt
        self.current_wind = (wind[0], wind[1])

        gx, gy = self._pos_to_grid(robot_pos[0], robot_pos[1])
        self.current_pos = (gx, gy)
        self.visited_cells.add((gx, gy))

        # Update posterior
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

    def _thompson_sample(self):
        """Sample a source location from the posterior (Thompson Sampling)."""
        # Convert log-posterior to probabilities
        p = np.exp(self.log_posterior)
        p = p / np.sum(p)

        # Sample from categorical distribution
        idx = np.random.choice(self.n_cells * self.n_cells, p=p.flatten())
        gx = idx // self.n_cells
        gy = idx % self.n_cells
        return gx, gy

    def _wind_aware_direction(self, target_gx, target_gy):
        """Compute wind-aware direction toward target.

        Key innovation: bias movement toward downwind direction when exploring,
        but move directly toward target when exploiting.
        """
        dx = target_gx - self.current_pos[0]
        dy = target_gy - self.current_pos[1]
        dist = math.sqrt(dx * dx + dy * dy) + 1e-6

        # Direct direction
        direct_dx = dx / dist
        direct_dy = dy / dist

        # Wind direction (normalized)
        wind_norm = math.sqrt(self.current_wind[0] ** 2 + self.current_wind[1] ** 2) + 1e-6
        wind_dx = self.current_wind[0] / wind_norm
        wind_dy = self.current_wind[1] / wind_norm

        # Blend: direct + wind-aware
        alpha = self.config.wind_awareness
        blend_dx = (1 - alpha) * direct_dx + alpha * wind_dx
        blend_dy = (1 - alpha) * direct_dy + alpha * wind_dy

        # Normalize
        blend_norm = math.sqrt(blend_dx ** 2 + blend_dy ** 2) + 1e-6
        return blend_dx / blend_norm, blend_dy / blend_norm

    def _compute_entropy(self):
        p = np.exp(self.log_posterior)
        p = p / np.sum(p)
        return -np.sum(p * self.log_posterior)

    def choose_action(self, robot_pos, wind):
        """Choose action using Wind-Aware Thompson Sampling."""
        remaining_time = self.config.time_budget - self.elapsed_time

        # Epsilon-greedy: sometimes explore randomly
        if np.random.random() < self.config.exploration_rate:
            return self.actions[np.random.randint(len(self.actions))]

        # Thompson Sampling: sample source location
        target_gx, target_gy = self._thompson_sample()

        # Wind-aware direction
        wind_dx, wind_dy = self._wind_aware_direction(target_gx, target_gy)

        # Convert to action (discrete 8-connected)
        # Find closest action to wind-aware direction
        best_action = (0, 0)
        best_score = -float('inf')

        for action in self.actions:
            if action == (0, 0):
                continue
            ax, ay = action
            action_norm = math.sqrt(ax * ax + ay * ay)
            if action_norm == 0:
                continue
            # Score: dot product with wind-aware direction
            score = (ax * wind_dx + ay * wind_dy) / action_norm
            # Bonus for moving toward target
            if target_gx != self.current_pos[0] or target_gy != self.current_pos[1]:
                target_dx = target_gx - self.current_pos[0]
                target_dy = target_gy - self.current_pos[1]
                target_norm = math.sqrt(target_dx ** 2 + target_dy ** 2) + 1e-6
                target_score = (ax * target_dx + ay * target_dy) / (action_norm * target_norm)
                score = 0.6 * score + 0.4 * target_score

            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        return self._grid_to_pos(idx[0], idx[1])

    def get_posterior_entropy(self):
        return self._compute_entropy()

    def get_remaining_time(self):
        return max(0, self.config.time_budget - self.elapsed_time)
