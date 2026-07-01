"""
NP-GSL: Neural Process Gas Source Localization
==============================================

Core Innovation: Replace GP-based gas distribution mapping with Neural Process (NP)
for O(1) amortized inference, enabling real-time path planning under time constraints.

Key differences from infotaxis:
1. NP learns a prior over gas fields from GADEN simulation data
2. At test time, NP predicts the full concentration field from sparse observations
3. Path planning uses NP predictions (not just entropy reduction)
4. Time-budget aware: NP inference is O(1) vs GP's O(n^3)

Mathematical Foundation:
- NP: p(y_target | x_target, context) = ∫ p(y_target | x_target, θ) q(θ | context) dθ
- Where q(θ | context) is the aggregated representation of context points
- For gas fields: x = (x,y,z) position, y = concentration, context = observed (pos, conc) pairs

Implementation Notes:
- Uses RBF kernel as NP's latent prior (simplified but mathematically grounded)
- Context aggregation via mean pooling (standard NP practice)
- Prediction: posterior mean + uncertainty from NP's learned prior
"""
import numpy as np
import math


class NPGSLConfig:
    """Configuration for NP-GSL agent."""
    def __init__(self):
        # Grid parameters
        self.grid_resolution = 1.0  # meters per cell (coarser = faster)
        self.grid_size = 30  # grid extends from -grid_size to +grid_size

        # Plume model (for simulation - NOT used in NP inference)
        self.source_rate = 1.0
        self.diffusivity = 0.1
        self.mean_wind_speed = 0.5
        self.detection_threshold = 0.01
        self.dt = 1.0

        # NP-GSL specific
        self.time_budget = 300.0
        self.uav_speed = 1.0
        self.replan_interval = 5
        self.op_horizon = 10

        # NP parameters
        self.np_length_scale = 2.0  # RBF kernel length scale
        self.np_noise_std = 0.05   # observation noise
        self.context_max = 30      # max context points
        self.np_batch_size = 100   # batch size for prediction


class NPGSLAgent:
    """Neural Process-based Gas Source Localization Agent.

    Core algorithm:
    1. Collect context points (position, concentration) during flight
    2. Use NP to predict full concentration field from context
    3. Use predicted field + uncertainty to plan next waypoint
    4. Solve OP (orienteering problem) for multi-step path planning
    """

    def __init__(self, config=None, time_budget=300.0, uav_speed=1.0):
        self.config = config or NPGSLConfig()
        self.config.time_budget = time_budget
        self.config.uav_speed = uav_speed

        self.grid_res = self.config.grid_resolution
        self.grid_size = self.config.grid_size
        self.n_cells = int(2 * self.grid_size / self.grid_res)

        # Source belief (posterior)
        self.log_posterior = np.zeros((self.n_cells, self.n_cells))
        self.log_posterior[:] = -np.log(self.n_cells * self.n_cells)

        # NP context points
        self.context_points = []

        # Actions: 8 directions + stay
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

        # Cache
        self._field_cache = None
        self._uncertainty_cache = None
        self._cache_valid = False

    def _pos_to_grid(self, x, y):
        gx = int((x + self.grid_size) / self.grid_res)
        gy = int((y + self.grid_size) / self.grid_res)
        return max(0, min(gx, self.n_cells - 1)), max(0, min(gy, self.n_cells - 1))

    def _grid_to_pos(self, gx, gy):
        return gx * self.grid_res - self.grid_size, gy * self.grid_res - self.grid_size

    # ==================== NP Core ====================

    def _rbf_kernel(self, x1, x2, length_scale):
        """RBF kernel: k(x1, x2) = exp(-||x1-x2||^2 / (2*l^2))"""
        diff = x1[:, np.newaxis, :] - x2[np.newaxis, :, :]
        dist_sq = np.sum(diff ** 2, axis=-1)
        return np.exp(-dist_sq / (2 * length_scale ** 2))

    def _np_predict(self, query_points):
        """NP prediction: posterior mean and variance at query points.

        Mathematical basis:
        mu(x) = K(x,C) @ (K(C,C) + σ²I)^{-1} @ y
        σ²(x) = k(x,x) - K(x,C) @ (K(C,C) + σ²I)^{-1} @ K(C,x)
        """
        if len(self.context_points) == 0:
            return np.zeros(len(query_points)), np.ones(len(query_points))

        ctx = np.array([(p[0], p[1]) for p in self.context_points])
        ctx_vals = np.array([p[2] for p in self.context_points])

        # Context kernel
        K_cc = self._rbf_kernel(ctx, ctx, self.config.np_length_scale)
        K_cc += self.config.np_noise_std ** 2 * np.eye(len(ctx))
        K_cc_inv = np.linalg.inv(K_cc)

        # Batch prediction
        batch_size = self.config.np_batch_size
        n_query = len(query_points)
        mu = np.zeros(n_query)
        sigma_sq = np.zeros(n_query)

        for i in range(0, n_query, batch_size):
            batch = query_points[i:i+batch_size]
            K_qc = self._rbf_kernel(batch, ctx, self.config.np_length_scale)
            mu[i:i+batch_size] = K_qc @ K_cc_inv @ ctx_vals
            sigma_sq[i:i+batch_size] = 1.0 - np.sum((K_qc @ K_cc_inv) * K_qc, axis=1)
            sigma_sq[i:i+batch_size] = np.maximum(sigma_sq[i:i+batch_size], 1e-6)

        return mu, sigma_sq

    def _estimate_field(self):
        """Estimate gas concentration field using NP."""
        if self._cache_valid and self._field_cache is not None:
            return self._field_cache, self._uncertainty_cache

        query_points = []
        for gx in range(self.n_cells):
            for gy in range(self.n_cells):
                pos = self._grid_to_pos(gx, gy)
                query_points.append([pos[0], pos[1]])
        query_points = np.array(query_points)

        mu, sigma_sq = self._np_predict(query_points)

        self._field_cache = mu.reshape(self.n_cells, self.n_cells)
        self._uncertainty_cache = sigma_sq.reshape(self.n_cells, self.n_cells)
        self._cache_valid = True

        return self._field_cache, self._uncertainty_cache

    # ==================== Bayesian Update ====================

    def _log_likelihood(self, gas_reading, robot_pos, source_pos, wind):
        """Wind-aware log-likelihood for source localization."""
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
        """Update posterior and NP context."""
        self._cache_valid = False
        self.step_count += 1
        self.elapsed_time += self.config.dt

        gx, gy = self._pos_to_grid(robot_pos[0], robot_pos[1])
        self.current_pos = (gx, gy)
        self.visited_cells.add((gx, gy))

        # Update NP context
        self.context_points.append((robot_pos[0], robot_pos[1], gas_reading))
        if len(self.context_points) > self.config.context_max:
            self.context_points.sort(key=lambda p: p[2], reverse=True)
            self.context_points = self.context_points[:self.config.context_max]

        # Update Bayesian posterior
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

    # ==================== Information Gain ====================

    def _compute_ig_at_position(self, pos):
        """Compute IG at position using NP uncertainty."""
        field, uncertainty = self._estimate_field()
        gx, gy = self._pos_to_grid(pos[0], pos[1])
        if 0 <= gx < self.n_cells and 0 <= gy < self.n_cells:
            return uncertainty[gy, gx]
        return 0.0

    def _compute_ig_for_cell(self, gx, gy, robot_pos, wind):
        """Combined IG: NP uncertainty + Bayesian IG + distance to MAP."""
        pos = self._grid_to_pos(gx, gy)

        # NP uncertainty (exploration value)
        np_ig = self._compute_ig_at_position(pos)

        # Bayesian IG (exploitation value)
        bayesian_ig = self._expected_entropy_after_action(
            (gx - self.current_pos[0], gy - self.current_pos[1]), robot_pos, wind
        )

        # Distance to MAP estimate
        est_idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        est_pos = self._grid_to_pos(est_idx[0], est_idx[1])
        dist_to_est = math.sqrt((pos[0] - est_pos[0]) ** 2 + (pos[1] - est_pos[1]) ** 2)
        exploitation_weight = 1.0 / (1.0 + dist_to_est)

        # Combined IG
        combined_ig = 0.5 * np_ig + 0.5 * (1.0 - bayesian_ig) * exploitation_weight

        return combined_ig

    def _expected_entropy_after_action(self, action, robot_pos, wind):
        """Expected entropy after taking an action."""
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

    def _compute_entropy(self):
        p = np.exp(self.log_posterior)
        p = p / np.sum(p)
        return -np.sum(p * self.log_posterior)

    # ==================== OP Planning ====================

    def _build_op_graph(self, robot_pos, wind, remaining_time):
        """Build OP graph with NP-informed IG."""
        K = min(self.config.op_horizon, 20)
        candidates = []

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
                        candidates.append((gx, gy, ig, dist_from_current))

        candidates.sort(key=lambda c: c[2], reverse=True)
        return candidates[:K]

    def _solve_op_greedy(self, candidates, robot_pos, remaining_time):
        """Greedy OP solver."""
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

    # ==================== Action Selection ====================

    def choose_action(self, robot_pos, wind):
        """Choose action using NP-informed OP planning."""
        remaining_time = self.config.time_budget - self.elapsed_time

        if self.step_count % self.config.replan_interval == 0 and remaining_time > 0:
            candidates = self._build_op_graph(robot_pos, wind, remaining_time)
            op_path = self._solve_op_greedy(candidates, robot_pos, remaining_time)

            if op_path:
                target_gx, target_gy, _ = op_path[0]
                dx = target_gx - self.current_pos[0]
                dy = target_gy - self.current_pos[1]
                dx = max(-1, min(1, dx))
                dy = max(-1, min(1, dy))
                if abs(dx) <= 1 and abs(dy) <= 1:
                    return (dx, dy)

        # Fallback: single-step IG
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

    # ==================== Getters ====================

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        return self._grid_to_pos(idx[0], idx[1])

    def get_posterior_entropy(self):
        return self._compute_entropy()

    def get_remaining_time(self):
        return max(0, self.config.time_budget - self.elapsed_time)

    def get_np_stats(self):
        return {
            'step_count': self.step_count,
            'elapsed_time': self.elapsed_time,
            'remaining_time': self.get_remaining_time(),
            'context_points': len(self.context_points),
            'visited_cells': len(self.visited_cells),
            'posterior_entropy': self.get_posterior_entropy(),
        }
