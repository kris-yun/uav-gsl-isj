"""
MI-PP: Mutual Information Path Planning for Gas Source Localization
Cross-domain origin: Sensor network optimization (Schur-MI, IROS 2026)
Physical basis: Gas plumes have wind-dependent spatial correlation
Mathematical basis: MI(X;Y) = H(X) - H(X|Y), path-level information gain

Key innovation vs infotaxis:
- Infotaxis: single-step entropy reduction (greedy)
- MI-PP: path-level mutual information with wind-aware exploration
"""
import numpy as np
import math


class MI_PP_Agent:
    """Mutual Information Path Planning agent."""

    def __init__(self, grid_size=40, resolution=0.5, time_budget=300, uav_speed=1.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.time_budget = time_budget
        self.uav_speed = uav_speed
        self.map_half = grid_size * resolution / 2.0

        # Belief over source location (log space)
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)

        # Parameters
        self.Q = 1.0        # source emission rate
        self.sigma_y = 0.8  # cross-wind spread
        self.sigma_z = 0.4  # vertical spread
        self.min_wind = 0.1

        # State
        self.step_count = 0
        self.elapsed_time = 0.0
        self.gas_hits = 0

    def _grid_to_pos(self, i, j):
        return i * self.resolution - self.map_half, j * self.resolution - self.map_half

    def _pos_to_grid(self, x, y):
        i = int((x + self.map_half) / self.resolution)
        j = int((y + self.map_half) / self.resolution)
        return max(0, min(i, self.grid_size-1)), max(0, min(j, self.grid_size-1))

    def _hit_prob(self, sx, sy, sensor_x, sensor_y, wind_x, wind_y):
        """Gaussian plume hit probability."""
        dx = sensor_x - sx
        dy = sensor_y - sy
        dist = math.sqrt(dx*dx + dy*dy) + 0.01

        ws = max(math.sqrt(wind_x**2 + wind_y**2), self.min_wind)
        wx = wind_x / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        wy = wind_y / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)

        d_down = dx * wx + dy * wy
        d_cross = abs(dx * wy - dy * wx)

        sy = self.sigma_y * math.sqrt(max(d_down, 0.01))
        sz = self.sigma_z * math.sqrt(max(d_down, 0.01))

        p = self.Q / (2 * math.pi * sy * sz * ws) * math.exp(-d_cross**2 / (2 * sy**2))
        return min(max(p, 0), 0.99)

    def _normalize_belief(self):
        max_log = np.max(self.log_belief)
        self.log_belief -= max_log
        log_sum = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= log_sum

    def _entropy(self, log_belief=None):
        if log_belief is None:
            log_belief = self.log_belief
        p = np.exp(log_belief)
        p = p / np.sum(p)
        return -np.sum(p * log_belief)

    def _expected_entropy_after_obs(self, x, y, wind_x, wind_y):
        """Compute E_z[H[source | D_t, z]] = P(hit)*H(hit) + P(miss)*H(miss)"""
        n = self.grid_size

        # Compute P(hit)
        p_hit_total = 0.0
        for i in range(n):
            for j in range(n):
                sx, sy = self._grid_to_pos(i, j)
                b = np.exp(self.log_belief[i, j])
                p_hit = self._hit_prob(sx, sy, x, y, wind_x, wind_y)
                p_hit_total += b * p_hit
        p_hit_total = min(max(p_hit_total, 0.01), 0.99)

        # Compute posterior if hit/miss
        log_post_hit = self.log_belief.copy()
        log_post_miss = self.log_belief.copy()
        for i in range(n):
            for j in range(n):
                sx, sy = self._grid_to_pos(i, j)
                p_hit = self._hit_prob(sx, sy, x, y, wind_x, wind_y)
                log_post_hit[i, j] += math.log(p_hit + 1e-10)
                log_post_miss[i, j] += math.log(1 - p_hit + 1e-10)

        H_hit = self._entropy(log_post_hit)
        H_miss = self._entropy(log_post_miss)

        return p_hit_total * H_hit + (1 - p_hit_total) * H_miss

    def update(self, gas_reading, robot_x, robot_y, wind_x, wind_y):
        """Update belief with new observation."""
        self.step_count += 1
        self.elapsed_time += 1.0
        if gas_reading > 0.01:
            self.gas_hits += 1

        # Update belief
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx, sy = self._grid_to_pos(i, j)
                p_hit = self._hit_prob(sx, sy, robot_x, robot_y, wind_x, wind_y)
                if gas_reading > 0.01:
                    self.log_belief[i, j] += math.log(p_hit + 1e-10)
                else:
                    self.log_belief[i, j] += math.log(1 - p_hit + 1e-10)

        self._normalize_belief()

    def choose_action(self, robot_x, robot_y, wind_x, wind_y):
        """Choose next action using MI-PP."""
        remaining = self.time_budget - self.elapsed_time

        # If no gas detected, explore downwind
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

        # MI-PP: compute MI for candidate waypoints
        H_current = self._entropy()
        candidates = []

        for di in range(-5, 6):
            for dj in range(-5, 6):
                if di == 0 and dj == 0:
                    continue
                x = robot_x + di * self.resolution
                y = robot_y + dj * self.resolution
                dist = math.sqrt(di**2 + dj**2) * self.resolution

                if dist > 0.5 and dist <= remaining * self.uav_speed:
                    H_after = self._expected_entropy_after_obs(x, y, wind_x, wind_y)
                    mi = H_current - H_after

                    # Wind bonus: prefer downwind exploration
                    wind_norm = math.sqrt(wind_x**2 + wind_y**2) + 1e-6
                    alignment = (di * wind_x + dj * wind_y) / (dist * wind_norm)
                    if alignment > 0:
                        mi += 0.3 * alignment * mi

                    candidates.append((mi, x, y, dist))

        if not candidates:
            return (0, 0)

        # Greedy path construction
        candidates.sort(key=lambda c: c[0], reverse=True)
        remaining_budget = remaining * self.uav_speed
        px, py = robot_x, robot_y
        selected = []

        for _ in range(min(len(candidates), 5)):
            best_mi = -1e9
            best_idx = -1
            for idx, (mi, x, y, dist) in enumerate(candidates):
                if idx in [s[0] for s in selected]:
                    continue
                travel = math.sqrt((x-px)**2 + (y-py)**2)
                if travel > 0.1 and travel <= remaining_budget:
                    efficiency = mi / travel
                    if efficiency > best_mi:
                        best_mi = efficiency
                        best_idx = idx

            if best_idx < 0:
                break

            mi, x, y, dist = candidates[best_idx]
            selected.append((best_idx, x, y))
            px, py = x, y
            remaining_budget -= dist

        if selected:
            _, tx, ty = selected[0]
            return self._to_action(robot_x, robot_y, tx, ty)

        return (0, 0)

    def _to_action(self, rx, ry, tx, ty):
        dx = tx - rx
        dy = ty - ry
        dist = math.sqrt(dx**2 + dy**2) + 1e-6
        return (dx/dist, dy/dist)

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return self._grid_to_pos(idx[0], idx[1])


class InfotaxisAgent:
    """Baseline: single-step infotaxis."""

    def __init__(self, grid_size=40, resolution=0.5):
        self.grid_size = grid_size
        self.resolution = resolution
        self.map_half = grid_size * resolution / 2.0
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)
        self.step_count = 0
        self.gas_hits = 0
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4
        self.min_wind = 0.1

    def _grid_to_pos(self, i, j):
        return i * self.resolution - self.map_half, j * self.resolution - self.map_half

    def _hit_prob(self, sx, sy, sensor_x, sensor_y, wind_x, wind_y):
        dx = sensor_x - sx
        dy = sensor_y - sy
        dist = math.sqrt(dx*dx + dy*dy) + 0.01
        ws = max(math.sqrt(wind_x**2 + wind_y**2), self.min_wind)
        wx = wind_x / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        wy = wind_y / (math.sqrt(wind_x**2 + wind_y**2) + 1e-6)
        d_down = dx * wx + dy * wy
        d_cross = abs(dx * wy - dy * wx)
        sy = self.sigma_y * math.sqrt(max(d_down, 0.01))
        sz = self.sigma_z * math.sqrt(max(d_down, 0.01))
        p = self.Q / (2 * math.pi * sy * sz * ws) * math.exp(-d_cross**2 / (2 * sy**2))
        return min(max(p, 0), 0.99)

    def update(self, gas_reading, robot_x, robot_y, wind_x, wind_y):
        self.step_count += 1
        if gas_reading > 0.01:
            self.gas_hits += 1
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx, sy = self._grid_to_pos(i, j)
                p = self._hit_prob(sx, sy, robot_x, robot_y, wind_x, wind_y)
                if gas_reading > 0.01:
                    self.log_belief[i, j] += math.log(p + 1e-10)
                else:
                    self.log_belief[i, j] += math.log(1 - p + 1e-10)
        max_log = np.max(self.log_belief)
        self.log_belief -= max_log
        log_sum = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= log_sum

    def choose_action(self, robot_x, robot_y, wind_x, wind_y):
        """Single-step entropy reduction (greedy)."""
        n = self.grid_size
        best_action = (0, 0)
        best_entropy = float('inf')

        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                x = robot_x + di * self.resolution
                y = robot_y + dj * self.resolution

                # Expected entropy after observation at (x, y)
                p_hit_total = 0.0
                for i in range(n):
                    for j in range(n):
                        sx, sy = self._grid_to_pos(i, j)
                        b = np.exp(self.log_belief[i, j])
                        p_hit = self._hit_prob(sx, sy, x, y, wind_x, wind_y)
                        p_hit_total += b * p_hit
                p_hit_total = min(max(p_hit_total, 0.01), 0.99)

                # Simplified: entropy reduction proportional to p_hit
                H = -np.sum(np.exp(self.log_belief) * self.log_belief)
                expected_H = H * (0.5 * p_hit_total + 0.95 * (1 - p_hit_total))

                if expected_H < best_entropy:
                    best_entropy = expected_H
                    best_action = (di, dj)

        return best_action

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return self._grid_to_pos(idx[0], idx[1])


def run_experiment(agent, source, wind, start, T=300, seed=0):
    """Run single experiment."""
    np.random.seed(seed)
    pos = list(start)
    errors = []

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
        p_hit = 1.0 / (2 * math.pi * sy * sz * ws) * math.exp(-d_cross**2 / (2 * sy**2))
        p_hit = min(max(p_hit, 0), 0.99)
        gas = 1 if np.random.random() < p_hit else 0

        # Update agent
        agent.update(gas, pos[0], pos[1], wind[0], wind[1])

        # Choose action
        action = agent.choose_action(pos[0], pos[1], wind[0], wind[1])

        # Move
        pos[0] += action[0] * 0.5  # step size
        pos[1] += action[1] * 0.5

        # Record error
        est = agent.get_estimated_source()
        error = math.sqrt((est[0] - source[0])**2 + (est[1] - source[1])**2)
        errors.append(error)

    return {
        'final_error': errors[-1],
        'min_error': min(errors),
        'errors': errors,
        'steps': T,
        'gas_hits': agent.gas_hits,
    }


def main():
    print("=" * 70)
    print("MI-PP vs Infotaxis: Fair Comparison")
    print("=" * 70)

    # Scenarios
    scenarios = [
        {'name': 'House01', 'source': (-0.4, -2.9), 'wind': (0.3, 0.15)},
        {'name': 'House02', 'source': (0.5, 1.0), 'wind': (-0.2, 0.4)},
        {'name': 'House03', 'source': (-1.5, 2.0), 'wind': (0.5, -0.3)},
    ]

    starts = [(-1.5, -2.5), (-3.0, -3.0), (0.0, 0.0)]
    T = 300
    n_seeds = 5

    all_inf, all_mi = [], []

    for sc in scenarios:
        print(f"\n--- {sc['name']} (source={sc['source']}, wind={sc['wind']}) ---")
        sc_inf, sc_mi = [], []

        for si, start in enumerate(starts):
            inf_errors, mi_errors = [], []

            for seed in range(n_seeds):
                # Infotaxis
                agent_inf = InfotaxisAgent()
                r_inf = run_experiment(agent_inf, sc['source'], sc['wind'], start, T, seed)
                inf_errors.append(r_inf['final_error'])

                # MI-PP
                agent_mi = MI_PP_Agent()
                r_mi = run_experiment(agent_mi, sc['source'], sc['wind'], start, T, seed)
                mi_errors.append(r_mi['final_error'])

            sc_inf.extend(inf_errors)
            sc_mi.extend(mi_errors)

            imp = (np.mean(inf_errors) - np.mean(mi_errors)) / max(np.mean(inf_errors), 0.001) * 100
            print(f"  Start {si}: Inf={np.mean(inf_errors):.2f} MI-PP={np.mean(mi_errors):.2f} imp={imp:+.1f}%")

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
