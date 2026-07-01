"""Benchmark: OP-GSL vs Infotaxis on simplified plume environment.
Fair comparison: same plume model, same start position, same time budget.
"""
import sys
import os
import numpy as np
import math
import csv

sys.path.insert(0, os.path.dirname(__file__))
from infotaxis import InfotaxisAgent, InfotaxisConfig
from op_gsl import OPGSLAgent, OPGSLConfig


class SimplePlumeSim:
    """Simplified indoor plume simulator for benchmarking."""

    def __init__(self, source_pos, wind_dir, wind_speed=0.5, noise_std=0.01):
        self.source = np.array(source_pos)
        self.wind_dir = np.array(wind_dir) / np.linalg.norm(wind_dir)
        self.wind_speed = wind_speed
        self.noise_std = noise_std

    def sample(self, pos):
        """Get gas concentration at position."""
        pos = np.array(pos)
        delta = pos - self.source
        dist = np.linalg.norm(delta) + 0.1

        # Wind alignment: higher concentration downwind
        alignment = np.dot(delta[:2], self.wind_dir[:2]) / dist

        # Gaussian plume model
        expected = 1.0 / (dist * dist + 1.0)
        if alignment > 0:
            expected *= (1.0 + alignment)

        # Add noise
        noise = np.random.normal(0, self.noise_std)
        return max(0, expected + noise)


def run_experiment(agent, plume, start_pos, time_budget, dt=1.0):
    """Run a single experiment and return metrics."""
    pos = np.array(start_pos, dtype=float)
    wind = plume.wind_dir * plume.wind_speed

    trajectory = [pos.copy()]
    gas_readings = []
    errors = []
    source = plume.source

    steps = int(time_budget / dt)
    for step in range(steps):
        # Sample gas
        gas = plume.sample(pos)
        gas_readings.append(gas)

        # Update agent
        agent.update(gas, tuple(pos), tuple(wind))

        # Get action
        action = agent.choose_action(tuple(pos), tuple(wind))

        # Move
        action_dist = getattr(agent, 'action_dist', 0.5)
        new_x = pos[0] + action[0] * action_dist
        new_y = pos[1] + action[1] * action_dist
        pos = np.array([new_x, new_y, pos[2]])
        trajectory.append(pos.copy())

        # Record error
        est = agent.get_estimated_source()
        error = math.sqrt((est[0] - source[0]) ** 2 + (est[1] - source[1]) ** 2)
        errors.append(error)

    # Final estimate
    est = agent.get_estimated_source()
    final_error = math.sqrt((est[0] - source[0]) ** 2 + (est[1] - source[1]) ** 2)

    return {
        'final_error': final_error,
        'min_error': min(errors),
        'errors': errors,
        'trajectory': trajectory,
        'gas_readings': gas_readings,
        'steps': steps,
    }


def main():
    print("=" * 70)
    print("OP-GSL vs Infotaxis Benchmark")
    print("=" * 70)

    # Experiment parameters
    time_budget = 300.0
    uav_speed = 1.0
    n_seeds = 5

    # Scenario: House01-like
    source = (-0.4, -2.9, 0.0)
    wind_dir = (1.0, 0.5, 0.0)
    wind_speed = 0.5

    # Start positions
    starts = [
        (-1.5, -2.5, 0.3),  # near source
        (-5.0, -5.0, 0.3),  # far start
        (0.0, 0.0, 0.3),    # center
    ]

    results = {}

    for start_idx, start in enumerate(starts):
        start_label = f"start_{start_idx}"
        print(f"\n--- Start {start_idx}: {start} ---")

        for seed in range(n_seeds):
            np.random.seed(seed)

            # Infotaxis
            inf_config = InfotaxisConfig()
            inf_agent = InfotaxisAgent(config=inf_config)
            plume = SimplePlumeSim(source, wind_dir, wind_speed)
            inf_result = run_experiment(inf_agent, plume, start, time_budget)

            # OP-GSL
            np.random.seed(seed)  # reset seed for fair comparison
            op_config = OPGSLConfig()
            op_agent = OPGSLAgent(config=op_config, time_budget=time_budget, uav_speed=uav_speed)
            plume = SimplePlumeSim(source, wind_dir, wind_speed)
            op_result = run_experiment(op_agent, plume, start, time_budget)

            key = f"{start_label}_seed{seed}"
            results[key] = {
                'inf_final': inf_result['final_error'],
                'inf_min': inf_result['min_error'],
                'op_final': op_result['final_error'],
                'op_min': op_result['min_error'],
            }

            print(f"  Seed {seed}: Inf={inf_result['final_error']:.3f}m, OP={op_result['final_error']:.3f}m")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    inf_errors = [r['inf_final'] for r in results.values()]
    op_errors = [r['op_final'] for r in results.values()]

    print(f"Infotaxis: {np.mean(inf_errors):.3f} +/- {np.std(inf_errors):.3f}m")
    print(f"OP-GSL:    {np.mean(op_errors):.3f} +/- {np.std(op_errors):.3f}m")

    improvement = (np.mean(inf_errors) - np.mean(op_errors)) / np.mean(inf_errors) * 100
    print(f"Improvement: {improvement:.1f}%")

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), 'benchmark_results.csv')
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['scenario', 'seed', 'infotaxis_final', 'infotaxis_min', 'opgsl_final', 'opgsl_min'])
        for key, r in results.items():
            writer.writerow([key, key.split('_seed')[1], r['inf_final'], r['inf_min'], r['op_final'], r['op_min']])
    print(f"\nResults saved to {out_path}")


if __name__ == '__main__':
    main()
