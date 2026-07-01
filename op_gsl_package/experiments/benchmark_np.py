"""Benchmark: NP-GSL vs OP-GSL vs Infotaxis
Fair comparison on simplified plume environment.
"""
import sys
import os
import numpy as np
import math
import csv

sys.path.insert(0, os.path.dirname(__file__))
from infotaxis import InfotaxisAgent, InfotaxisConfig
from op_gsl import OPGSLAgent, OPGSLConfig
from np_gsl import NPGSLAgent, NPGSLConfig


class SimplePlumeSim:
    """Simplified indoor plume simulator."""
    def __init__(self, source_pos, wind_dir, wind_speed=0.5, noise_std=0.01):
        self.source = np.array(source_pos)
        self.wind_dir = np.array(wind_dir) / np.linalg.norm(wind_dir)
        self.wind_speed = wind_speed
        self.noise_std = noise_std

    def sample(self, pos):
        pos = np.array(pos)
        delta = pos - self.source
        dist = np.linalg.norm(delta) + 0.1
        alignment = np.dot(delta[:2], self.wind_dir[:2]) / dist
        expected = 1.0 / (dist * dist + 1.0)
        if alignment > 0:
            expected *= (1.0 + alignment)
        noise = np.random.normal(0, self.noise_std)
        return max(0, expected + noise)


def run_experiment(agent, plume, start_pos, time_budget, dt=1.0):
    """Run a single experiment."""
    pos = np.array(start_pos, dtype=float)
    wind = plume.wind_dir * plume.wind_speed
    errors = []
    source = plume.source
    steps = int(time_budget / dt)

    for step in range(steps):
        gas = plume.sample(pos)
        agent.update(gas, tuple(pos), tuple(wind))
        action = agent.choose_action(tuple(pos), tuple(wind))
        action_dist = getattr(agent, 'action_dist', 0.5)
        new_x = pos[0] + action[0] * action_dist
        new_y = pos[1] + action[1] * action_dist
        pos = np.array([new_x, new_y, pos[2]])
        est = agent.get_estimated_source()
        error = math.sqrt((est[0] - source[0]) ** 2 + (est[1] - source[1]) ** 2)
        errors.append(error)

    est = agent.get_estimated_source()
    final_error = math.sqrt((est[0] - source[0]) ** 2 + (est[1] - source[1]) ** 2)
    return {
        'final_error': final_error,
        'min_error': min(errors),
        'errors': errors,
    }


def main():
    print("=" * 70)
    print("NP-GSL vs OP-GSL vs Infotaxis Benchmark")
    print("=" * 70)

    time_budget = 300.0
    uav_speed = 1.0
    n_seeds = 5

    source = (-0.4, -2.9, 0.0)
    wind_dir = (1.0, 0.5, 0.0)
    wind_speed = 0.5

    starts = [
        (-1.5, -2.5, 0.3),  # near source
        (-5.0, -5.0, 0.3),  # far start
        (0.0, 0.0, 0.3),    # center
    ]

    all_results = []

    for start_idx, start in enumerate(starts):
        start_label = f"start_{start_idx}"
        print(f"\n--- Start {start_idx}: {start} ---")

        for seed in range(n_seeds):
            np.random.seed(seed)
            inf_agent = InfotaxisAgent()
            plume = SimplePlumeSim(source, wind_dir, wind_speed)
            inf_result = run_experiment(inf_agent, plume, start, time_budget)

            np.random.seed(seed)
            op_agent = OPGSLAgent(time_budget=time_budget, uav_speed=uav_speed)
            plume = SimplePlumeSim(source, wind_dir, wind_speed)
            op_result = run_experiment(op_agent, plume, start, time_budget)

            np.random.seed(seed)
            np_agent = NPGSLAgent(time_budget=time_budget, uav_speed=uav_speed)
            plume = SimplePlumeSim(source, wind_dir, wind_speed)
            np_result = run_experiment(np_agent, plume, start, time_budget)

            row = {
                'scenario': start_label,
                'seed': seed,
                'inf_final': inf_result['final_error'],
                'op_final': op_result['final_error'],
                'np_final': np_result['final_error'],
            }
            all_results.append(row)

            print(f"  Seed {seed}: Inf={inf_result['final_error']:.3f}m, OP={op_result['final_error']:.3f}m, NP={np_result['final_error']:.3f}m")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    inf_errors = [r['inf_final'] for r in all_results]
    op_errors = [r['op_final'] for r in all_results]
    np_errors = [r['np_final'] for r in all_results]

    print(f"Infotaxis: {np.mean(inf_errors):.3f} +/- {np.std(inf_errors):.3f}m")
    print(f"OP-GSL:    {np.mean(op_errors):.3f} +/- {np.std(op_errors):.3f}m")
    print(f"NP-GSL:    {np.mean(np_errors):.3f} +/- {np.std(np_errors):.3f}m")

    op_imp = (np.mean(inf_errors) - np.mean(op_errors)) / max(np.mean(inf_errors), 0.001) * 100
    np_imp = (np.mean(inf_errors) - np.mean(np_errors)) / max(np.mean(inf_errors), 0.001) * 100
    print(f"OP improvement over infotaxis: {op_imp:.1f}%")
    print(f"NP improvement over infotaxis: {np_imp:.1f}%")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), 'benchmark_np_results.csv')
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['scenario', 'seed', 'inf_final', 'op_final', 'np_final'])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nResults saved to {out_path}")


if __name__ == '__main__':
    main()
