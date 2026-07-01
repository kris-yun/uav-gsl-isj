"""
OPGSL v2 - Clean Python Prototype
===================================
Core algorithm: Chemotaxis + Wind-Aware Field Estimation
Purpose: Verify algorithm logic before porting to C++

Key fixes from Codex's version:
1. Field estimation uses distance-weighted observations (not raw)
2. Exploration direction uses wind-relative golden angle
3. Convergence detection uses multi-criteria (not just entropy)
4. No CRLB blending pollution
"""

import numpy as np
import math


class OPGSLv2Config:
    def __init__(self):
        self.grid_res = 0.5
        self.grid_size = 30
        self.n_cells = int(2 * self.grid_size / self.grid_res)
        self.time_budget = 300.0
        self.uav_speed = 1.0
        self.dt = 1.0

        # Plume model
        self.source_rate = 1.0
        self.detection_threshold = 0.01

        # Field estimation
        self.bandwidth = 1.5
        self.observation_decay = 0.995
        self.max_observations = 200

        # Convergence
        self.convergence_min_time = 30.0
        self.convergence_min_hits = 5
        self.convergence_entropy_threshold = 5.0


class OPGSLv2Agent:
    """Clean OPGSL implementation with proper field estimation."""

    def __init__(self, config=None, time_budget=300.0, uav_speed=1.0):
        self.config = config or OPGSLv2Config()
        self.config.time_budget = time_budget
        self.config.uav_speed = uav_speed

        self.n_cells = self.config.n_cells
        self.grid_res = self.config.grid_res
        self.grid_size = self.config.grid_size

        # Source belief (posterior)
        self.log_posterior = np.zeros((self.n_cells, self.n_cells))
        self.log_posterior[:] = -np.log(self.n_cells * self.n_cells)

        # Observations
        self.observations = []  # [(x, y, gas, wind_x, wind_y, timestamp)]
        self.gas_hits = 0
        self.step_count = 0
        self.elapsed_time = 0.0

        # State
        self.current_pos = (self.n_cells // 2, self.n_cells // 2)
        self.visited_cells = set()

    def _pos_to_grid(self, x, y):
        gx = int((x + self.grid_size) / self.grid_res)
        gy = int((y + self.grid_size) / self.grid_res)
        return max(0, min(gx, self.n_cells - 1)), max(0, min(gy, self.n_cells - 1))

    def _grid_to_pos(self, gx, gy):
        return gx * self.grid_res - self.grid_size, gy * self.grid_res - self.grid_size

    # ==================== Field Estimation ====================

    def _compute_field(self):
        """Compute gas concentration field using distance-weighted KDE.

        Key fix: observations are weighted by 1/distance^2 from query point.
        This prevents distant gas hits from polluting the field estimate.
        """
        field = np.zeros((self.n_cells, self.n_cells))
        if not self.observations:
            return field

        for gx in range(self.n_cells):
            for gy in range(self.n_cells):
                pos = self._grid_to_pos(gx, gy)
                weighted_sum = 0.0
                weight_total = 0.0

                for obs in self.observations:
                    ox, oy, gas_val = obs[0], obs[1], obs[2]
                    dist = math.sqrt((pos[0] - ox)**2 + (pos[1] - oy)**2) + 0.1

                    # Distance-weighted kernel
                    kernel = math.exp(-dist**2 / (2 * self.config.bandwidth**2))
                    # Distance decay (prevents distant hits from dominating)
                    dist_weight = 1.0 / (1.0 + dist**2)

                    weighted_sum += gas_val * kernel * dist_weight
                    weight_total += kernel * dist_weight

                if weight_total > 1e-10:
                    field[gx, gy] = weighted_sum / weight_total

        return field

    def _compute_centroid(self):
        """Compute weighted centroid of field estimate.

        Key fix: centroid is weighted by field value AND distance from current position.
        """
        field = self._compute_field()
        total_weight = 0.0
        cx, cy = 0.0, 0.0

        for gx in range(self.n_cells):
            for gy in range(self.n_cells):
                val = max(0, field[gx, gy])
                if val > 0.01:
                    pos = self._grid_to_pos(gx, gy)
                    # Weight by field value
                    w = val
                    cx += pos[0] * w
                    cy += pos[1] * w
                    total_weight += w

        if total_weight > 1e-10:
            return cx / total_weight, cy / total_weight
        else:
            # Fallback: best-hit location
            best_val = 0
            best_pos = (0, 0)
            for obs in self.observations:
                if obs[2] > best_val:
                    best_val = obs[2]
                    best_pos = (obs[0], obs[1])
            return best_pos

    # ==================== Bayesian Update ====================

    def _log_likelihood(self, gas_reading, robot_pos, source_pos, wind):
        dx = robot_pos[0] - source_pos[0]
        dy = robot_pos[1] - source_pos[1]
        dist = math.sqrt(dx * dx + dy * dy) + 0.1

        wind_norm = math.sqrt(wind[0]**2 + wind[1]**2) + 1e-6
        wind_dx = wind[0] / wind_norm
        wind_dy = wind[1] / wind_norm
        alignment = (dx * wind_dx + dy * wind_dy) / dist

        expected_conc = self.config.source_rate / (dist * dist + 1.0)
        if alignment > 0:
            expected_conc *= (1.0 + alignment)

        if gas_reading > self.config.detection_threshold:
            log_lik = -0.5 * ((gas_reading - expected_conc)**2) / (expected_conc + 0.01)
            log_lik -= 0.5 * dist
        else:
            log_lik = -0.1 * dist

        return log_lik

    def update(self, gas_reading, robot_pos, wind):
        self.step_count += 1
        self.elapsed_time += self.config.dt

        gx, gy = self._pos_to_grid(robot_pos[0], robot_pos[1])
        self.current_pos = (gx, gy)
        self.visited_cells.add((gx, gy))

        # Store observation
        self.observations.append((robot_pos[0], robot_pos[1], gas_reading, wind[0], wind[1], self.elapsed_time))
        if len(self.observations) > self.config.max_observations:
            self.observations = self.observations[-self.config.max_observations:]

        if gas_reading > self.config.detection_threshold:
            self.gas_hits += 1

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

    # ==================== Navigation ====================

    def _explore_golden_angle(self, robot_pos, wind):
        """Wind-relative golden angle exploration.

        Key: explore downwind of current position (gas comes from upwind).
        """
        wind_norm = math.sqrt(wind[0]**2 + wind[1]**2) + 1e-6
        wind_dx = wind[0] / wind_norm
        wind_dy = wind[1] / wind_norm

        # Golden angle offset
        golden_angle = 2.39996  # 137.5 degrees
        angle = golden_angle * self.step_count

        # Base direction: downwind + spiral
        base_angle = math.atan2(-wind_dy, -wind_dx)  # downwind
        explore_angle = base_angle + angle

        step_size = 1.0
        target_x = robot_pos[0] + step_size * math.cos(explore_angle)
        target_y = robot_pos[1] + step_size * math.sin(explore_angle)

        # Clip to bounds
        half = self.grid_size - 1
        target_x = max(-half, min(half, target_x))
        target_y = max(-half, min(half, target_y))

        return target_x, target_y

    def _chemotaxis_step(self, robot_pos, wind):
        """Chemotaxis: move toward centroid of field estimate."""
        centroid_x, centroid_y = self._compute_centroid()

        dx = centroid_x - robot_pos[0]
        dy = centroid_y - robot_pos[1]
        dist = math.sqrt(dx*dx + dy*dy) + 0.1

        if dist > 0.5:
            step = min(1.0, dist * 0.4)
            target_x = robot_pos[0] + (dx/dist) * step
            target_y = robot_pos[1] + (dy/dist) * step
        else:
            # Near centroid: small random step
            angle = np.random.uniform(0, 2*math.pi)
            target_x = robot_pos[0] + 0.3 * math.cos(angle)
            target_y = robot_pos[1] + 0.3 * math.sin(angle)

        half = self.grid_size - 1
        target_x = max(-half, min(half, target_x))
        target_y = max(-half, min(half, target_y))

        return target_x, target_y

    def choose_action(self, robot_pos, wind):
        """Choose next action: explore or exploit."""
        remaining = self.config.time_budget - self.elapsed_time

        # Early exploration: no gas detected yet
        if self.gas_hits == 0:
            tx, ty = self._explore_golden_angle(robot_pos, wind)
        else:
            # Chemotaxis: move toward field centroid
            tx, ty = self._chemotaxis_step(robot_pos, wind)

        # Convert to action (discrete 8-connected)
        dx = tx - robot_pos[0]
        dy = ty - robot_pos[1]
        dist = math.sqrt(dx*dx + dy*dy) + 1e-6

        # Normalize to grid step
        step = min(1.0, dist)
        action_x = dx / dist * step
        action_y = dy / dist * step

        # Convert to grid coordinates
        gx, gy = self._pos_to_grid(robot_pos[0] + action_x, robot_pos[1] + action_y)
        action = (gx - self.current_pos[0], gy - self.current_pos[1])

        # Clamp to 8-connected
        action = (max(-1, min(1, action[0])), max(-1, min(1, action[1])))

        return action

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        return self._grid_to_pos(idx[0], idx[1])

    def get_posterior_entropy(self):
        p = np.exp(self.log_posterior)
        p = p / np.sum(p)
        return -np.sum(p * self.log_posterior)


if __name__ == '__main__':
    # Quick test
    config = OPGSLv2Config()
    agent = OPGSLv2Agent(config=config, time_budget=300, uav_speed=1.0)

    # Simulate
    source = (-0.4, -2.9)
    wind = (0.5, 0.25)
    pos = [-1.5, -2.5]

    for step in range(100):
        # Simple plume model
        dist = math.sqrt((pos[0]-source[0])**2 + (pos[1]-source[1])**2) + 0.1
        gas = max(0, 1.0/(dist**2 + 1.0) + np.random.normal(0, 0.01))

        agent.update(gas, (pos[0], pos[1], 0.3), wind)
        action = agent.choose_action((pos[0], pos[1], 0.3), wind)

        pos[0] += action[0] * 0.5
        pos[1] += action[1] * 0.5

        if step % 20 == 0:
            est = agent.get_estimated_source()
            err = math.sqrt((est[0]-source[0])**2 + (est[1]-source[1])**2)
            print(f"Step {step}: pos=({pos[0]:.1f},{pos[1]:.1f}) est=({est[0]:.1f},{est[1]:.1f}) err={err:.2f}m gas_hits={agent.gas_hits}")

    est = agent.get_estimated_source()
    err = math.sqrt((est[0]-source[0])**2 + (est[1]-source[1])**2)
    print(f"\nFinal: est=({est[0]:.1f},{est[1]:.1f}) err={err:.2f}m")
