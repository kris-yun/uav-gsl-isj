"""
Module 1: Wind-Conditioned Robust Intermittency Filter (WC-RIF)
Origin: Robust statistics (Ge Quanbo MCC, IEEE TSP 2025) + GSL-specific innovations

Core idea: Replace standard Bayesian update with wind-conditioned correntropy update
that is robust to non-Gaussian sensor noise and intermittency.

Test: Compare WC-RIF + infotaxis vs standard infotaxis on GADEN-like plume.
If improvement < 10%, discard this module.
"""
import numpy as np
import math
import time


class WCRIFAgent:
    """Wind-Conditioned Robust Intermittency Filter agent."""

    def __init__(self, grid_size=20, resolution=1.0, time_budget=300, uav_speed=1.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.time_budget = time_budget
        self.uav_speed = uav_speed
        self.map_half = grid_size * resolution / 2.0

        # Belief (log space)
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)

        # Precompute grid
        self.grid_x = np.array([i * resolution - self.map_half for i in range(grid_size)])
        self.grid_y = np.array([j * resolution - self.map_half for j in range(grid_size)])

        # WC-RIF parameters
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4
        self.sigma_base = 0.3          # base kernel bandwidth
        self.beta_wind = 0.5           # wind sensitivity
        self.alpha_intermittency = 0.3  # intermittency sensitivity
        self.gamma_entropy = 0.1       # entropy adaptation rate
        self.target_entropy = 3.0      # target entropy for adaptation

        # State
        self.step_count = 0
        self.elapsed_time = 0.0
        self.gas_hits = 0
        self.hit_history = []          # recent hit/miss history
        self.window_size = 10          # sliding window for intermittency

    def _hit_prob(self, sx, sy, sensor_x, sensor_y, wind_x, wind_y):
        """Gaussian plume hit probability."""
        dx = sensor_x - sx
        dy = sensor_y - sy
        dist = math.sqrt(dx*dx + dy*dy) + 0.01

        ws = max(math.sqrt(wind_x**2 + wind_y**2), 0.1)
        wx = wind_x / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        wy = wind_y / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)

        d_down = dx * wx + dy * wy
        d_cross = abs(dx * wy - dy * wx)

        sy_val = self.sigma_y * math.sqrt(max(d_down, 0.01))
        sz_val = self.sigma_z * math.sqrt(max(d_down, 0.01))

        p = self.Q / (2 * math.pi * sy_val * sz_val * ws) * math.exp(-d_cross**2 / (2 * sy_val**2))
        return min(max(p, 0), 0.99)

    def _wind_alignment(self, sx, sy, sensor_x, sensor_y, wind_x, wind_y):
        """Compute wind alignment: +1 = downwind, -1 = upwind."""
        dx = sensor_x - sx
        dy = sensor_y - sy
        dist = math.sqrt(dx*dx + dy*dy) + 0.01
        ws = math.sqrt(wind_x**2 + wind_y**2) + 1e-6
        return (dx * wind_x + dy * wind_y) / (dist * ws)

    def _cauchy_kernel(self, d, sigma):
        """Cauchy kernel: G_σ(d) = 1/(π(1 + d²/σ²))"""
        return 1.0 / (math.pi * (1.0 + (d/sigma)**2))

    def _normalize_belief(self):
        mx = np.max(self.log_belief)
        self.log_belief -= mx
        ls = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= ls

    def _entropy(self):
        p = np.exp(self.log_belief)
        return -np.sum(p * self.log_belief)

    def update(self, gas_reading, robot_x, robot_y, wind_x, wind_y):
        """Update belief using WC-RIF."""
        self.step_count += 1
        self.elapsed_time += 1.0

        # Track intermittency
        hit = gas_reading > 0.01
        if hit:
            self.gas_hits += 1
        self.hit_history.append(1 if hit else 0)
        if len(self.hit_history) > self.window_size:
            self.hit_history.pop(0)

        # Compute intermittency weight
        hit_rate = np.mean(self.hit_history) if self.hit_history else 0.0
        w_inter = (1.0 - self.alpha_intermittency) + self.alpha_intermittency * hit_rate

        # Adaptive sigma based on entropy
        H = self._entropy()
        sigma_adaptive = self.sigma_base * (1.0 + self.gamma_entropy * H)

        # Update belief for each grid cell
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx = self.grid_x[i]
                sy = self.grid_y[j]

                # Wind alignment
                alignment = self._wind_alignment(sx, sy, robot_x, robot_y, wind_x, wind_y)

                # Wind-conditioned sigma
                sigma_eff = sigma_adaptive * (1.0 + self.beta_wind * alignment)

                # Expected concentration
                p_hit = self._hit_prob(sx, sy, robot_x, robot_y, wind_x, wind_y)

                # Observation residual
                if hit:
                    residual = abs(1.0 - p_hit)
                else:
                    residual = abs(0.0 - p_hit)

                # WC-RIF update: Cauchy kernel with wind-conditioned sigma
                kernel_val = self._cauchy_kernel(residual, sigma_eff)

                # Weighted update
                if hit:
                    log_update = math.log(max(kernel_val * w_inter, 1e-10))
                else:
                    log_update = math.log(max((1.0 - kernel_val) * w_inter + (1 - w_inter) * 0.5, 1e-10))

                self.log_belief[i, j] += log_update

        self._normalize_belief()

    def choose_action(self, robot_x, robot_y, wind_x, wind_y):
        """Choose action using wind-aware exploration or exploitation."""
        remaining = self.time_budget - self.elapsed_time

        # No gas: explore downwind
        if self.gas_hits == 0:
            wind_norm = math.sqrt(wind_x**2 + wind_y**2) + 1e-6
            wx = wind_x / wind_norm
            wy = wind_y / wind_norm
            golden_angle = 2.39996
            angle = golden_angle * self.step_count
            base_angle = math.atan2(-wy, -wx)
            explore_angle = base_angle + angle
            tx = robot_x + 0.8 * math.cos(explore_angle)
            ty = robot_y + 0.8 * math.sin(explore_angle)
            return self._to_action(robot_x, robot_y, tx, ty)

        # Exploit: move toward MAP estimate with entropy-weighted exploration
        map_idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        map_x = self.grid_x[map_idx[0]]
        map_y = self.grid_y[map_idx[1]]

        # Add exploration noise proportional to entropy
        H = self._entropy()
        H_max = np.log(self.grid_size * self.grid_size)
        exploration_weight = min(H / H_max, 1.0)

        # Blend: move toward MAP + random exploration
        angle_to_map = math.atan2(map_y - robot_y, map_x - robot_x)
        random_angle = np.random.uniform(0, 2 * math.pi)
        blend_angle = (1 - exploration_weight) * angle_to_map + exploration_weight * random_angle

        step_size = 0.5
        tx = robot_x + step_size * math.cos(blend_angle)
        ty = robot_y + step_size * math.sin(blend_angle)

        return self._to_action(robot_x, robot_y, tx, ty)

    def _to_action(self, rx, ry, tx, ty):
        dx = tx - rx
        dy = ty - ry
        dist = math.sqrt(dx**2 + dy**2) + 1e-6
        return (dx/dist, dy/dist)

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return (self.grid_x[idx[0]], self.grid_y[idx[1]])


class StandardBayesianAgent:
    """Baseline: standard Bayesian update (no robustness, no intermittency)."""

    def __init__(self, grid_size=20, resolution=1.0, time_budget=300, uav_speed=1.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.time_budget = time_budget
        self.map_half = grid_size * resolution / 2.0
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)
        self.grid_x = np.array([i * resolution - self.map_half for i in range(grid_size)])
        self.grid_y = np.array([j * resolution - self.map_half for j in range(grid_size)])
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4
        self.step_count = 0
        self.elapsed_time = 0.0
        self.gas_hits = 0

    def _hit_prob(self, sx, sy, sensor_x, sensor_y, wind_x, wind_y):
        dx = sensor_x - sx
        dy = sensor_y - sy
        dist = math.sqrt(dx*dx + dy*dy) + 0.01
        ws = max(math.sqrt(wind_x**2 + wind_y**2), 0.1)
        wx = wind_x / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        wy = wind_y / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        d_down = dx * wx + dy * wy
        d_cross = abs(dx * wy - dy * wx)
        sy_val = self.sigma_y * math.sqrt(max(d_down, 0.01))
        sz_val = self.sigma_z * math.sqrt(max(d_down, 0.01))
        p = self.Q / (2 * math.pi * sy_val * sz_val * ws) * math.exp(-d_cross**2 / (2 * sy_val**2))
        return min(max(p, 0), 0.99)

    def update(self, gas, rx, ry, wx, wy):
        self.step_count += 1
        self.elapsed_time += 1.0
        if gas > 0.01: self.gas_hits += 1
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx = self.grid_x[i]
                sy = self.grid_y[j]
                p = self._hit_prob(sx, sy, rx, ry, wx, wy)
                if gas > 0.01:
                    self.log_belief[i, j] += math.log(p + 1e-10)
                else:
                    self.log_belief[i, j] += math.log(1 - p + 1e-10)
        mx = np.max(self.log_belief)
        self.log_belief -= mx
        ls = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= ls

    def choose_action(self, rx, ry, wx, wy):
        if self.gas_hits == 0:
            wn = math.sqrt(wx**2 + wy**2) + 1e-6
            angle = 2.39996 * self.step_count
            base = math.atan2(-wy/wn, -wx/wn)
            tx = rx + 0.8 * math.cos(base + angle)
            ty = ry + 0.8 * math.sin(base + angle)
            dx, dy = tx - rx, ty - ry
            d = math.sqrt(dx**2 + dy**2) + 1e-6
            return (dx/d, dy/d)
        # Move toward MAP
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        mx = self.grid_x[idx[0]]
        my = self.grid_y[idx[1]]
        dx, dy = mx - rx, my - ry
        d = math.sqrt(dx**2 + dy**2) + 1e-6
        return (dx/d, dy/d)

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return (self.grid_x[idx[0]], self.grid_y[idx[1]])


def run(agent, source, wind, start, T=300, seed=0):
    np.random.seed(seed)
    pos = list(start)
    errors = []
    t0 = time.time()
    for t in range(T):
        dx = pos[0] - source[0]
        dy = pos[1] - source[1]
        dist = math.sqrt(dx*dx + dy*dy) + 0.1
        ws = max(math.sqrt(wind[0]**2 + wind[1]**2), 0.1)
        wx = wind[0] / (math.sqrt(wind[0]**2 + wind[1]**2) + 1e-6)
        wy = wind[1] / (math.sqrt(wind[0]**2 + wind[1]**2) + 1e-6)
        d_down = dx * wx + dy * wy
        d_cross = abs(dx * wy - dy * wx)
        sy = 0.8 * math.sqrt(max(d_down, 0.01))
        sz = 0.4 * math.sqrt(max(d_down, 0.01))
        p = 1.0 / (2 * math.pi * sy * sz * ws) * math.exp(-d_cross**2 / (2 * sy**2))
        p = min(max(p, 0), 0.99)
        gas = 1 if np.random.random() < p else 0
        agent.update(gas, pos[0], pos[1], wind[0], wind[1])
        action = agent.choose_action(pos[0], pos[1], wind[0], wind[1])
        pos[0] += action[0] * 0.5
        pos[1] += action[1] * 0.5
        est = agent.get_estimated_source()
        errors.append(math.sqrt((est[0]-source[0])**2 + (est[1]-source[1])**2))
    wall = time.time() - t0
    return {'final_error': errors[-1], 'min_error': min(errors), 'wall_time': wall, 'gas_hits': agent.gas_hits}


def main():
    print("="*70)
    print("WC-RIF vs Standard Bayesian (Module 1 Test)")
    print("="*70)

    scenarios = [
        {'name': 'House01', 'source': (-0.4, -2.9), 'wind': (0.3, 0.15)},
        {'name': 'House02', 'source': (0.5, 1.0), 'wind': (-0.2, 0.4)},
        {'name': 'House03', 'source': (-1.5, 2.0), 'wind': (0.5, -0.3)},
    ]
    starts = [(-1.5, -2.5), (-3.0, -3.0), (0.0, 0.0)]
    T = 300
    n_seeds = 3

    all_base, all_wcrif = [], []

    for sc in scenarios:
        print(f"\n--- {sc['name']} ---")
        sc_base, sc_wcrif = [], []

        for si, start in enumerate(starts):
            base_errs, wcrif_errs = [], []
            for seed in range(n_seeds):
                r = run(StandardBayesianAgent(), sc['source'], sc['wind'], start, T, seed)
                base_errs.append(r['final_error'])
                r = run(WCRIFAgent(), sc['source'], sc['wind'], start, T, seed)
                wcrif_errs.append(r['final_error'])
            sc_base.extend(base_errs)
            sc_wcrif.extend(wcrif_errs)
            imp = (np.mean(base_errs) - np.mean(wcrif_errs)) / max(np.mean(base_errs), 0.001) * 100
            print(f"  Start {si}: Base={np.mean(base_errs):.2f} WC-RIF={np.mean(wcrif_errs):.2f} imp={imp:+.1f}%")

        all_base.extend(sc_base)
        all_wcrif.extend(sc_wcrif)

    print(f"\n{'='*70}")
    print("OVERALL")
    print("="*70)
    print(f"Standard Bayesian: {np.mean(all_base):.3f} +/- {np.std(all_base):.3f}")
    print(f"WC-RIF:            {np.mean(all_wcrif):.3f} +/- {np.std(all_wcrif):.3f}")
    imp = (np.mean(all_base) - np.mean(all_wcrif)) / max(np.mean(all_base), 0.001) * 100
    print(f"Improvement: {imp:+.1f}%")
    if imp > 10:
        print("MODULE 1 WC-RIF: PASS (>10% improvement)")
    else:
        print("MODULE 1 WC-RIF: FAIL (<10% improvement)")


if __name__ == '__main__':
    main()
