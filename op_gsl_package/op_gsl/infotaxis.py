"""Infotaxis baseline implementation.
Based on Vergassola et al. (2007) "Infotaxis as a strategy for searching without gradient"
Adapted for GADEN/GSL benchmark framework.
"""
import numpy as np
import math

class InfotaxisConfig:
    def __init__(self):
        # Grid parameters
        self.grid_resolution = 0.5  # meters per cell
        self.grid_size = 30  # 30x30 grid
        
        # Plume model parameters (simplified filament model)
        self.source_rate = 1.0  # Q: emission rate (a.u.)
        self.diffusivity = 0.1  # D: diffusion coefficient
        self.mean_wind_speed = 0.5  # typical wind speed
        
        # Detection threshold
        self.detection_threshold = 0.01
        
        # Time step for entropy computation
        self.dt = 1.0  # seconds


class InfotaxisAgent:
    """Infotaxis search algorithm.
    
    Core idea: at each step, choose the action that maximizes
    the expected reduction in entropy of the source position posterior.
    """
    
    def __init__(self, config=None):
        self.config = config or InfotaxisConfig()
        self.grid_res = self.config.grid_resolution
        self.grid_size = self.config.grid_size
        
        # Source position grid (discrete)
        self.n_cells = int(2 * self.grid_size / self.grid_res)
        self.log_posterior = np.zeros((self.n_cells, self.n_cells))
        # Uniform prior (log space)
        self.log_posterior[:] = -np.log(self.n_cells * self.n_cells)
        
        # Possible actions: 8 directions + stay
        self.actions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
            (0, 0)
        ]
        self.action_dist = self.grid_res  # distance per action
        
    def _pos_to_grid(self, x, y):
        """Convert world coords to grid indices."""
        gx = int((x + self.grid_size) / self.grid_res)
        gy = int((y + self.grid_size) / self.grid_res)
        gx = max(0, min(gx, self.n_cells - 1))
        gy = max(0, min(gy, self.n_cells - 1))
        return gx, gy
    
    def _grid_to_pos(self, gx, gy):
        """Convert grid indices to world coords."""
        x = gx * self.grid_res - self.grid_size
        y = gy * self.grid_res - self.grid_size
        return x, y
    
    def _log_likelihood(self, gas_reading, robot_pos, source_pos, wind):
        """Compute log P(reading | source_pos) using simplified plume model.
        
        Uses advection-diffusion likelihood:
        - Higher concentration when source is upwind
        - Exponential decay with distance
        """
        dx = robot_pos[0] - source_pos[0]
        dy = robot_pos[1] - source_pos[1]
        dist = math.sqrt(dx*dx + dy*dy) + 0.1  # avoid div by zero
        
        # Wind alignment: positive if source is upwind of robot
        wind_norm = math.sqrt(wind[0]**2 + wind[1]**2) + 1e-6
        wind_dx = wind[0] / wind_norm
        wind_dy = wind[1] / wind_norm
        alignment = (dx * wind_dx + dy * wind_dy) / dist
        
        # Expected concentration (simplified Gaussian plume)
        expected_conc = self.config.source_rate / (dist * dist + 1.0)
        if alignment > 0:
            expected_conc *= (1.0 + alignment)  # upwind bonus
        
        # Log-likelihood: Gaussian around expected concentration
        if gas_reading > self.config.detection_threshold:
            # Hit: high likelihood near source
            log_lik = -0.5 * ((gas_reading - expected_conc) ** 2) / (expected_conc + 0.01)
            log_lik -= 0.5 * dist  # distance penalty
        else:
            # Miss: slightly negative everywhere, more negative far from source
            log_lik = -0.1 * dist
        
        return log_lik
    
    def update(self, gas_reading, robot_pos, wind):
        """Update posterior with new observation."""
        rgx, rgy = self._pos_to_grid(robot_pos[0], robot_pos[1])
        
        for sx in range(self.n_cells):
            for sy in range(self.n_cells):
                src_pos = self._grid_to_pos(sx, sy)
                log_lik = self._log_likelihood(gas_reading, robot_pos, src_pos, wind)
                self.log_posterior[sx, sy] += log_lik
        
        # Normalize in log space
        max_log = np.max(self.log_posterior)
        self.log_posterior -= max_log
        log_sum = np.log(np.sum(np.exp(self.log_posterior)))
        self.log_posterior -= log_sum
    
    def _compute_entropy(self):
        """Compute Shannon entropy of current posterior."""
        p = np.exp(self.log_posterior)
        p = p / np.sum(p)
        entropy = -np.sum(p * (self.log_posterior - np.log(np.sum(np.exp(self.log_posterior)))))
        return entropy
    
    def _expected_entropy_after_action(self, action, robot_pos, wind):
        """Estimate expected entropy after taking an action.
        
        This is an approximation: we assume a binary hit/miss model.
        E[H'] = P(hit) * H(posterior | hit) + P(miss) * H(posterior | miss)
        """
        # New position after action
        new_x = robot_pos[0] + action[0] * self.action_dist
        new_y = robot_pos[1] + action[1] * self.action_dist
        new_pos = (new_x, new_y)
        
        # P(hit) = integral of posterior * likelihood of hit
        p_hit = 0.0
        for sx in range(self.n_cells):
            for sy in range(self.n_cells):
                src_pos = self._grid_to_pos(sx, sy)
                dx = new_pos[0] - src_pos[0]
                dy = new_pos[1] - src_pos[1]
                dist = math.sqrt(dx*dx + dy*dy) + 0.1
                expected_conc = self.config.source_rate / (dist * dist + 1.0)
                p_hit_cell = min(expected_conc / (self.config.detection_threshold + 0.01), 1.0)
                p_hit += np.exp(self.log_posterior[sx, sy]) * p_hit_cell
        
        p_hit = min(max(p_hit, 0.01), 0.99)
        p_miss = 1.0 - p_hit
        
        # Approximate entropy change
        # Hit reduces entropy more than miss
        current_entropy = self._compute_entropy()
        entropy_after_hit = current_entropy * 0.5  # rough estimate
        entropy_after_miss = current_entropy * 0.95
        
        expected_entropy = p_hit * entropy_after_hit + p_miss * entropy_after_miss
        return expected_entropy
    
    def choose_action(self, robot_pos, wind):
        """Choose action that minimizes expected posterior entropy."""
        best_action = self.actions[0]
        best_entropy = float('inf')
        
        for action in self.actions:
            # Check if action is valid (within bounds)
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
        """Return the position with highest posterior probability."""
        idx = np.unravel_index(np.argmax(self.log_posterior), self.log_posterior.shape)
        return self._grid_to_pos(idx[0], idx[1])
    
    def get_posterior_entropy(self):
        """Return current posterior entropy."""
        return self._compute_entropy()
