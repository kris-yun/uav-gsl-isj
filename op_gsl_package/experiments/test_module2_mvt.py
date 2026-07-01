"""
Module 2: Marginal Value Theorem Decision (MVT-D)
Origin: Ecology - Optimal Foraging Theory (Charnov 1976)

Core idea: UAV decides when to leave current search region based on
diminishing returns - when local information gain rate drops below
global average, move to a new region.

Test: MVT-D + WC-RIF vs WC-RIF alone.
If improvement < 10%, discard this module.
"""
import numpy as np
import math
import time


class WCRIF_MVT_Agent:
    """WC-RIF with MVT-based region leaving decision."""

    def __init__(self, grid_size=20, resolution=1.0, time_budget=300, uav_speed=1.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.time_budget = time_budget
        self.uav_speed = uav_speed
        self.map_half = grid_size * resolution / 2.0

        # Belief
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)
        self.grid_x = np.array([i * resolution - self.map_half for i in range(grid_size)])
        self.grid_y = np.array([j * resolution - self.map_half for j in range(grid_size)])

        # WC-RIF parameters
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4
        self.sigma_base = 0.3
        self.beta_wind = 0.5
        self.alpha_intermittency = 0.3

        # MVT parameters
        self.region_radius = 3.0      # meters
        self.mvt_window = 20          # steps to compute local IG rate
        self.leave_threshold = 0.5    # leave when local_rate < threshold × global_rate

        # State
        self.step_count = 0
        self.elapsed_time = 0.0
        self.gas_hits = 0
        self.hit_history = []
        self.window_size = 10
        self.ig_history = []          # information gain history
        self.current_region_center = None
        self.steps_in_region = 0
        self.region_ig_sum = 0.0

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

    def _wind_alignment(self, sx, sy, sensor_x, sensor_y, wind_x, wind_y):
        dx = sensor_x - sx
        dy = sensor_y - sy
        dist = math.sqrt(dx*dx + dy*dy) + 0.01
        ws = math.sqrt(wind_x**2 + wind_y**2) + 1e-6
        return (dx * wind_x + dy * wind_y) / (dist * ws)

    def _cauchy_kernel(self, d, sigma):
        return 1.0 / (math.pi * (1.0 + (d/sigma)**2))

    def _normalize_belief(self):
        mx = np.max(self.log_belief)
        self.log_belief -= mx
        ls = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= ls

    def _entropy(self):
        p = np.exp(self.log_belief)
        return -np.sum(p * self.log_belief)

    def _compute_local_ig_rate(self, robot_x, robot_y):
        """Compute local information gain rate in current region."""
        if self.current_region_center is None:
            return 0.0
        dist = math.sqrt((robot_x - self.current_region_center[0])**2 +
                         (robot_y - self.current_region_center[1])**2)
        if dist > self.region_radius:
            return 0.0
        if len(self.ig_history) < 2:
            return 1.0  # default: keep exploring
        # Recent IG rate
        recent = self.ig_history[-min(self.mvt_window, len(self.ig_history)):]
        return np.mean(recent)

    def _compute_global_ig_rate(self):
        """Compute global average information gain rate."""
        if len(self.ig_history) < 5:
            return 1.0
        return np.mean(self.ig_history)

    def _should_leave_region(self, robot_x, robot_y):
        """MVT decision: leave when local rate < threshold × global rate."""
        local_rate = self._compute_local_ig_rate(robot_x, robot_y)
        global_rate = self._compute_global_ig_rate()
        return local_rate < self.leave_threshold * global_rate

    def update(self, gas_reading, robot_x, robot_y, wind_x, wind_y):
        self.step_count += 1
        self.elapsed_time += 1.0

        hit = gas_reading > 0.01
        if hit:
            self.gas_hits += 1
        self.hit_history.append(1 if hit else 0)
        if len(self.hit_history) > self.window_size:
            self.hit_history.pop(0)

        # Track information gain
        H_before = self._entropy()

        # WC-RIF update
        hit_rate = np.mean(self.hit_history) if self.hit_history else 0.0
        w_inter = (1.0 - self.alpha_intermittency) + self.alpha_intermittency * hit_rate
        H = self._entropy()
        sigma_adaptive = self.sigma_base * (1.0 + 0.1 * H)

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx = self.grid_x[i]
                sy = self.grid_y[j]
                alignment = self._wind_alignment(sx, sy, robot_x, robot_y, wind_x, wind_y)
                sigma_eff = sigma_adaptive * (1.0 + self.beta_wind * alignment)
                p_hit = self._hit_prob(sx, sy, robot_x, robot_y, wind_x, wind_y)
                residual = abs((1.0 if hit else 0.0) - p_hit)
                kernel_val = self._cauchy_kernel(residual, sigma_eff)
                if hit:
                    log_update = math.log(max(kernel_val * w_inter, 1e-10))
                else:
                    log_update = math.log(max((1.0 - kernel_val) * w_inter + (1 - w_inter) * 0.5, 1e-10))
                self.log_belief[i, j] += log_update

        self._normalize_belief()

        # Track IG
        H_after = self._entropy()
        ig = max(H_before - H_after, 0)
        self.ig_history.append(ig)

        # MVT region tracking
        if self.current_region_center is None:
            self.current_region_center = (robot_x, robot_y)
        dist = math.sqrt((robot_x - self.current_region_center[0])**2 +
                         (robot_y - self.current_region_center[1])**2)
        if dist > self.region_radius:
            # Entered new region
            self.current_region_center = (robot_x, robot_y)
            self.steps_in_region = 0
            self.region_ig_sum = 0.0
        else:
            self.steps_in_region += 1
            self.region_ig_sum += ig

    def choose_action(self, robot_x, robot_y, wind_x, wind_y):
        remaining = self.time_budget - self.elapsed_time

        # No gas: explore downwind
        if self.gas_hits == 0:
            wind_norm = math.sqrt(wind_x**2 + wind_y**2) + 1e-6
            wx = wind_x / wind_norm
            wy = wind_y / wind_norm
            angle = 2.39996 * self.step_count
            base = math.atan2(-wy, -wx)
            tx = robot_x + 0.8 * math.cos(base + angle)
            ty = robot_y + 0.8 * math.sin(base + angle)
            return self._to_action(robot_x, robot_y, tx, ty)

        # MVT decision: should we leave current region?
        should_leave = self._should_leave_region(robot_x, robot_y)

        if should_leave:
            # Leave: move to highest uncertainty region
            H_max = np.log(self.grid_size * self.grid_size)
            exploration_weight = min(self._entropy() / H_max, 1.0)
            map_idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
            map_x = self.grid_x[map_idx[0]]
            map_y = self.grid_y[map_idx[1]]

            # Move away from current region center
            if self.current_region_center is not None:
                away_angle = math.atan2(robot_y - self.current_region_center[1],
                                        robot_x - self.current_region_center[0])
            else:
                away_angle = np.random.uniform(0, 2 * math.pi)

            tx = robot_x + 0.8 * math.cos(away_angle)
            ty = robot_y + 0.8 * math.sin(away_angle)
            return self._to_action(robot_x, robot_y, tx, ty)
        else:
            # Stay: exploit current region
            map_idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
            map_x = self.grid_x[map_idx[0]]
            map_y = self.grid_y[map_idx[1]]
            dx, dy = map_x - robot_x, map_y - robot_y
            d = math.sqrt(dx**2 + dy**2) + 1e-6
            return (dx/d, dy/d)

    def _to_action(self, rx, ry, tx, ty):
        dx = tx - rx
        dy = ty - ry
        dist = math.sqrt(dx**2 + dy**2) + 1e-6
        return (dx/dist, dy/dist)

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
    return {'final_error': errors[-1], 'min_error': min(errors), 'wall_time': time.time()-t0}


def main():
    print("="*70)
    print("WC-RIF + MVT vs WC-RIF alone (Module 2 Test)")
    print("="*70)

    scenarios = [
        {'name': 'House01', 'source': (-0.4, -2.9), 'wind': (0.3, 0.15)},
        {'name': 'House02', 'source': (0.5, 1.0), 'wind': (-0.2, 0.4)},
        {'name': 'House03', 'source': (-1.5, 2.0), 'wind': (0.5, -0.3)},
    ]
    starts = [(-1.5, -2.5), (-3.0, -3.0), (0.0, 0.0)]
    T = 300
    n_seeds = 3

    # Import WC-RIF from module 1
    import importlib.util
    spec = importlib.util.spec_from_file_location("module1", "/tmp/test_module1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    all_wcrif, all_mvt = [], []

    for sc in scenarios:
        print(f"\n--- {sc['name']} ---")
        sc_wcrif, sc_mvt = [], []

        for si, start in enumerate(starts):
            wcrif_errs, mvt_errs = [], []
            for seed in range(n_seeds):
                r = run(mod.WCRIFAgent(), sc['source'], sc['wind'], start, T, seed)
                wcrif_errs.append(r['final_error'])
                r = run(WCRIF_MVT_Agent(), sc['source'], sc['wind'], start, T, seed)
                mvt_errs.append(r['final_error'])
            sc_wcrif.extend(wcrif_errs)
            sc_mvt.extend(mvt_errs)
            imp = (np.mean(wcrif_errs) - np.mean(mvt_errs)) / max(np.mean(wcrif_errs), 0.001) * 100
            print(f"  Start {si}: WC-RIF={np.mean(wcrif_errs):.2f} MVT={np.mean(mvt_errs):.2f} imp={imp:+.1f}%")

        all_wcrif.extend(sc_wcrif)
        all_mvt.extend(sc_mvt)

    print(f"\n{'='*70}")
    print("OVERALL")
    print("="*70)
    print(f"WC-RIF:     {np.mean(all_wcrif):.3f} +/- {np.std(all_wcrif):.3f}")
    print(f"WC-RIF+MVT: {np.mean(all_mvt):.3f} +/- {np.std(all_mvt):.3f}")
    imp = (np.mean(all_wcrif) - np.mean(all_mvt)) / max(np.mean(all_wcrif), 0.001) * 100
    print(f"Improvement: {imp:+.1f}%")
    if imp > 10:
        print("MODULE 2 MVT: PASS (>10% improvement)")
    else:
        print("MODULE 2 MVT: FAIL (<10% improvement)")


if __name__ == '__main__':
    main()
