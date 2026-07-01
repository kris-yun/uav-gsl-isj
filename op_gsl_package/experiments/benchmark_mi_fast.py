"""
MI-PP Optimized: Fast Mutual Information Path Planning
Key optimization: subsample grid, cache computations, reduce candidates
"""
import numpy as np
import math
import time


class MI_PP_Fast:
    """Optimized MI-PP with subsampling."""

    def __init__(self, grid_size=20, resolution=1.0, time_budget=300, uav_speed=1.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.time_budget = time_budget
        self.uav_speed = uav_speed
        self.map_half = grid_size * resolution / 2.0

        # Belief (log space)
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)

        # Precompute grid positions
        self.grid_x = np.array([i * resolution - self.map_half for i in range(grid_size)])
        self.grid_y = np.array([j * resolution - self.map_half for j in range(grid_size)])

        # Parameters
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4

        # State
        self.step_count = 0
        self.elapsed_time = 0.0
        self.gas_hits = 0

    def _hit_prob_vectorized(self, sensor_x, sensor_y, wind_x, wind_y):
        """Vectorized hit probability for entire grid."""
        dx = sensor_x - self.grid_x[:, None]
        dy = sensor_y - self.grid_y[None, :]
        dist = np.sqrt(dx**2 + dy**2) + 0.01

        ws = max(math.sqrt(wind_x**2 + wind_y**2), 0.1)
        wx = wind_x / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        wy = wind_y / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)

        d_down = dx * wx + dy * wy
        d_cross = np.abs(dx * wy - dy * wx)

        sy = self.sigma_y * np.sqrt(np.maximum(d_down, 0.01))
        sz = self.sigma_z * np.sqrt(np.maximum(d_down, 0.01))

        p = self.Q / (2 * math.pi * sy * sz * ws) * np.exp(-d_cross**2 / (2 * sy**2))
        return np.clip(p, 0, 0.99)

    def _normalize_belief(self):
        max_log = np.max(self.log_belief)
        self.log_belief -= max_log
        log_sum = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= log_sum

    def _entropy(self):
        p = np.exp(self.log_belief)
        return -np.sum(p * self.log_belief)

    def update(self, gas_reading, robot_x, robot_y, wind_x, wind_y):
        """Update belief with new observation."""
        self.step_count += 1
        self.elapsed_time += 1.0
        if gas_reading > 0.01:
            self.gas_hits += 1

        p_hit = self._hit_prob_vectorized(robot_x, robot_y, wind_x, wind_y)

        if gas_reading > 0.01:
            self.log_belief += np.log(p_hit + 1e-10)
        else:
            self.log_belief += np.log(1 - p_hit + 1e-10)

        self._normalize_belief()

    def choose_action(self, robot_x, robot_y, wind_x, wind_y):
        """Choose action using MI-PP or fallback."""
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

        # MI-PP: compute MI for candidates (subsampled)
        H_current = self._entropy()
        candidates = []

        # Subsample: only check nearby cells
        for di in range(-3, 4):
            for dj in range(-3, 4):
                if di == 0 and dj == 0:
                    continue
                x = robot_x + di * self.resolution
                y = robot_y + dj * self.resolution
                dist = math.sqrt(di**2 + dj**2) * self.resolution

                if dist > 0.3 and dist <= remaining * self.uav_speed:
                    # Compute expected entropy after observation at (x, y)
                    p_hit = self._hit_prob_vectorized(x, y, wind_x, wind_y)
                    p_hit_total = np.sum(np.exp(self.log_belief) * p_hit)
                    p_hit_total = min(max(p_hit_total, 0.01), 0.99)

                    # Approximate posterior entropy (fast)
                    # H(hit) ≈ H_current * 0.5, H(miss) ≈ H_current * 0.95
                    expected_H = p_hit_total * H_current * 0.5 + (1 - p_hit_total) * H_current * 0.95
                    mi = H_current - expected_H

                    # Wind bonus
                    wind_norm = math.sqrt(wind_x**2 + wind_y**2) + 1e-6
                    alignment = (di * wind_x + dj * wind_y) / (dist * wind_norm)
                    if alignment > 0:
                        mi += 0.3 * alignment * mi

                    candidates.append((mi, x, y, dist))

        if not candidates:
            return (0, 0)

        # Greedy selection: pick best MI/distance ratio
        candidates.sort(key=lambda c: c[0] / max(c[3], 0.1), reverse=True)
        best = candidates[0]

        return self._to_action(robot_x, robot_y, best[1], best[2])

    def _to_action(self, rx, ry, tx, ty):
        dx = tx - rx
        dy = ty - ry
        dist = math.sqrt(dx**2 + dy**2) + 1e-6
        return (dx/dist, dy/dist)

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return (self.grid_x[idx[0]], self.grid_y[idx[1]])


class InfotaxisAgent:
    """Baseline: single-step infotaxis (same grid resolution)."""

    def __init__(self, grid_size=20, resolution=1.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.map_half = grid_size * resolution / 2.0
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)
        self.grid_x = np.array([i * resolution - self.map_half for i in range(grid_size)])
        self.grid_y = np.array([j * resolution - self.map_half for j in range(grid_size)])
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4
        self.step_count = 0
        self.gas_hits = 0

    def _hit_prob_vectorized(self, sx, sy, wx, wy):
        dx = sx - self.grid_x[:, None]
        dy = sy - self.grid_y[None, :]
        dist = np.sqrt(dx**2 + dy**2) + 0.01
        ws = max(math.sqrt(wx**2 + wy**2), 0.1)
        wnx = wx / (math.sqrt(wx**2 + wy**2) + 1e-6)
        wny = wy / (math.sqrt(wx**2 + wy**2) + 1e-6)
        d_down = dx * wnx + dy * wny
        d_cross = np.abs(dx * wny - dy * wnx)
        sy_val = self.sigma_y * np.sqrt(np.maximum(d_down, 0.01))
        sz_val = self.sigma_z * np.sqrt(np.maximum(d_down, 0.01))
        p = self.Q / (2 * math.pi * sy_val * sz_val * ws) * np.exp(-d_cross**2 / (2 * sy_val**2))
        return np.clip(p, 0, 0.99)

    def update(self, gas, rx, ry, wx, wy):
        self.step_count += 1
        if gas > 0.01:
            self.gas_hits += 1
        p = self._hit_prob_vectorized(rx, ry, wx, wy)
        if gas > 0.01:
            self.log_belief += np.log(p + 1e-10)
        else:
            self.log_belief += np.log(1 - p + 1e-10)
        mx = np.max(self.log_belief)
        self.log_belief -= mx
        ls = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= ls

    def choose_action(self, rx, ry, wx, wy):
        """Single-step entropy reduction."""
        if self.gas_hits == 0:
            wind_norm = math.sqrt(wx**2 + wy**2) + 1e-6
            wnx = wx / wind_norm
            wny = wy / wind_norm
            angle = 2.39996 * self.step_count
            base = math.atan2(-wny, -wnx)
            tx = rx + 0.8 * math.cos(base + angle)
            ty = ry + 0.8 * math.sin(base + angle)
            dx, dy = tx - rx, ty - ry
            d = math.sqrt(dx**2 + dy**2) + 1e-6
            return (dx/d, dy/d)

        # Greedy: pick neighbor with highest expected IG
        best_action = (0, 0)
        best_H = float('inf')
        H_current = -np.sum(np.exp(self.log_belief) * self.log_belief)

        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                x = rx + di * self.resolution
                y = ry + dj * self.resolution
                p_hit = self._hit_prob_vectorized(x, y, wx, wy)
                p_total = np.sum(np.exp(self.log_belief) * p_hit)
                p_total = min(max(p_total, 0.01), 0.99)
                expected_H = p_total * H_current * 0.5 + (1 - p_total) * H_current * 0.95
                if expected_H < best_H:
                    best_H = expected_H
                    best_action = (di, dj)

        return best_action

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return (self.grid_x[idx[0]], self.grid_y[idx[1]])


def run(agent, source, wind, start, T=300, seed=0):
    np.random.seed(seed)
    pos = list(start)
    errors = []
    t0 = time.time()

    for t in range(T):
        # Compute gas reading
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

    wall_time = time.time() - t0
    est = agent.get_estimated_source()
    return {
        'final_error': errors[-1],
        'min_error': min(errors),
        'wall_time': wall_time,
        'gas_hits': agent.gas_hits,
    }


def main():
    print("="*70)
    print("MI-PP vs Infotaxis (Optimized)")
    print("="*70)

    scenarios = [
        {'name': 'House01', 'source': (-0.4, -2.9), 'wind': (0.3, 0.15)},
        {'name': 'House02', 'source': (0.5, 1.0), 'wind': (-0.2, 0.4)},
        {'name': 'House03', 'source': (-1.5, 2.0), 'wind': (0.5, -0.3)},
    ]
    starts = [(-1.5, -2.5), (-3.0, -3.0), (0.0, 0.0)]
    T = 300
    n_seeds = 3

    all_inf, all_mi = [], []

    for sc in scenarios:
        print(f"\n--- {sc['name']} ---")
        sc_inf, sc_mi = [], []

        for si, start in enumerate(starts):
            inf_errs, mi_errs = [], []
            inf_times, mi_times = [], []

            for seed in range(n_seeds):
                r = run(InfotaxisAgent(), sc['source'], sc['wind'], start, T, seed)
                inf_errs.append(r['final_error'])
                inf_times.append(r['wall_time'])

                r = run(MI_PP_Fast(), sc['source'], sc['wind'], start, T, seed)
                mi_errs.append(r['final_error'])
                mi_times.append(r['wall_time'])

            sc_inf.extend(inf_errs)
            sc_mi.extend(mi_errs)

            imp = (np.mean(inf_errs) - np.mean(mi_errs)) / max(np.mean(inf_errs), 0.001) * 100
            print(f"  Start {si}: Inf={np.mean(inf_errs):.2f}({np.mean(inf_times):.1f}s) MI-PP={np.mean(mi_errs):.2f}({np.mean(mi_times):.1f}s) imp={imp:+.1f}%")

        all_inf.extend(sc_inf)
        all_mi.extend(sc_mi)

    print(f"\n{'='*70}")
    print("OVERALL")
    print("="*70)
    print(f"Infotaxis: {np.mean(all_inf):.3f} +/- {np.std(all_inf):.3f}")
    print(f"MI-PP:     {np.mean(all_mi):.3f} +/- {np.std(all_mi):.3f}")
    imp = (np.mean(all_inf) - np.mean(all_mi)) / max(np.mean(all_inf), 0.001) * 100
    print(f"Improvement: {imp:+.1f}%")


if __name__ == '__main__':
    main()
