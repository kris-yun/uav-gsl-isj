"""
WC-RIF Analysis on Real GADEN Sensor Data
==========================================
Reads sensor_trace.csv from OPGSL experiments and applies WC-RIF filtering.
Compares: raw Bayesian update vs WC-RIF robust update.

Usage: python3 analyze_wcrif.py <sensor_trace.csv> <source_x> <source_y>
"""
import sys
import numpy as np
import math
import csv


class WCRIFBelief:
    """WC-RIF belief update on real sensor data."""

    def __init__(self, grid_size=40, resolution=0.5, map_half=10.0):
        self.grid_size = grid_size
        self.resolution = resolution
        self.map_half = map_half
        self.log_belief = np.zeros((grid_size, grid_size))
        self.log_belief[:] = -np.log(grid_size * grid_size)
        self.grid_x = np.array([i * resolution - map_half for i in range(grid_size)])
        self.grid_y = np.array([j * resolution - map_half for j in range(grid_size)])

        # WC-RIF parameters
        self.Q = 1.0
        self.sigma_y = 0.8
        self.sigma_z = 0.4
        self.sigma_base = 0.3
        self.beta_wind = 0.5
        self.alpha_intermittency = 0.3

        # State
        self.hit_history = []
        self.window_size = 10

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

    def _cauchy_kernel(self, d, sigma):
        return 1.0 / (math.pi * (1.0 + (d/sigma)**2))

    def _normalize(self):
        mx = np.max(self.log_belief)
        self.log_belief -= mx
        ls = np.log(np.sum(np.exp(self.log_belief)))
        self.log_belief -= ls

    def _entropy(self):
        p = np.exp(self.log_belief)
        return -np.sum(p * self.log_belief)

    def update_wcrif(self, gas_reading, rx, ry, wx, wy):
        """WC-RIF update: Cauchy kernel + wind-conditioned sigma + intermittency."""
        hit = gas_reading > 0.01
        self.hit_history.append(1 if hit else 0)
        if len(self.hit_history) > self.window_size:
            self.hit_history.pop(0)

        hit_rate = np.mean(self.hit_history) if self.hit_history else 0.0
        w_inter = (1.0 - self.alpha_intermittency) + self.alpha_intermittency * hit_rate
        H = self._entropy()
        H_max = np.log(self.grid_size * self.grid_size)
        sigma_adaptive = self.sigma_base * (1.0 + 0.1 * H / H_max)

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx = self.grid_x[i]
                sy = self.grid_y[j]
                # Wind alignment
                dist = math.sqrt((rx-sx)**2 + (ry-sy)**2) + 0.01
                ws = math.sqrt(wx**2 + wy**2) + 1e-6
                alignment = ((rx-sx)*wx + (ry-sy)*wy) / (dist * ws)
                # Wind-conditioned sigma
                sigma_eff = sigma_adaptive * (1.0 + self.beta_wind * alignment)
                # Hit probability
                p_hit = self._hit_prob(sx, sy, rx, ry, wx, wy)
                # Residual
                residual = abs((1.0 if hit else 0.0) - p_hit)
                # Cauchy kernel
                kernel_val = self._cauchy_kernel(residual, sigma_eff)
                # Update
                if hit:
                    log_update = math.log(max(kernel_val * w_inter, 1e-10))
                else:
                    miss_weight = (1.0 - kernel_val) * w_inter + (1 - w_inter) * 0.5
                    log_update = math.log(max(miss_weight, 1e-10))
                self.log_belief[i, j] += log_update
        self._normalize()

    def update_standard(self, gas_reading, rx, ry, wx, wy):
        """Standard Bayesian update (baseline)."""
        hit = gas_reading > 0.01
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                sx = self.grid_x[i]
                sy = self.grid_y[j]
                p_hit = self._hit_prob(sx, sy, rx, ry, wx, wy)
                if hit:
                    self.log_belief[i, j] += math.log(max(p_hit, 1e-10))
                else:
                    self.log_belief[i, j] += math.log(max(1 - p_hit, 1e-10))
        self._normalize()

    def get_estimated_source(self):
        idx = np.unravel_index(np.argmax(self.log_belief), self.log_belief.shape)
        return (self.grid_x[idx[0]], self.grid_y[idx[1]])


def analyze_trace(trace_path, source_x, source_y, method='wcrif'):
    """Analyze a sensor_trace.csv file with WC-RIF or standard Bayesian."""
    agent = WCRIFBelief()
    errors = []
    steps = 0

    with open(trace_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rx = float(row['x'])
                ry = float(row['y'])
                gas = float(row['measured_gas_ppm'])
                # Wind not in trace - use default
                wx, wy = 0.3, 0.15

                if method == 'wcrif':
                    agent.update_wcrif(gas, rx, ry, wx, wy)
                else:
                    agent.update_standard(gas, rx, ry, wx, wy)

                est = agent.get_estimated_source()
                err = math.sqrt((est[0] - source_x)**2 + (est[1] - source_y)**2)
                errors.append(err)
                steps += 1
            except (ValueError, KeyError):
                continue

    if not errors:
        return None

    return {
        'final_error': errors[-1],
        'min_error': min(errors),
        'steps': steps,
        'errors': errors,
    }


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 analyze_wcrif.py <trace.csv> <source_x> <source_y>")
        sys.exit(1)

    trace_path = sys.argv[1]
    source_x = float(sys.argv[2])
    source_y = float(sys.argv[3])

    print(f"Analyzing: {trace_path}")
    print(f"Source: ({source_x}, {source_y})")

    # Run both methods on same data
    r_wcrif = analyze_trace(trace_path, source_x, source_y, 'wcrif')
    r_standard = analyze_trace(trace_path, source_x, source_y, 'standard')

    if r_wcrif and r_standard:
        print(f"\nResults ({r_wcrif['steps']} steps):")
        print(f"  Standard Bayesian: {r_standard['final_error']:.3f}m (min: {r_standard['min_error']:.3f}m)")
        print(f"  WC-RIF:            {r_wcrif['final_error']:.3f}m (min: {r_wcrif['min_error']:.3f}m)")
        imp = (r_standard['final_error'] - r_wcrif['final_error']) / max(r_standard['final_error'], 0.001) * 100
        print(f"  Improvement: {imp:+.1f}%")
    else:
        print("No valid data found in trace file")


if __name__ == '__main__':
    main()
