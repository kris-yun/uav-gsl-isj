"""Benchmark: OPGSLv2 vs Infotaxis vs old OPGSL"""
import sys, os, numpy as np, math, csv
sys.path.insert(0, os.path.dirname(__file__))
from infotaxis import InfotaxisAgent
from opgsl_v2 import OPGSLv2Agent


class PlumeSim:
    def __init__(self, src, wd, ws=0.5, noise=0.01):
        self.src = np.array(src)
        self.wd = np.array(wd) / np.linalg.norm(wd)
        self.ws, self.noise = ws, noise

    def sample(self, pos):
        d = np.array(pos) - self.src
        dist = np.linalg.norm(d) + 0.1
        align = np.dot(d[:2], self.wd[:2]) / dist
        e = 1.0 / (dist*dist + 1.0)
        if align > 0: e *= (1.0 + align)
        return max(0, e + np.random.normal(0, self.noise))


def run(agent, plume, start, T=300):
    pos = np.array(start, dtype=float)
    wind = plume.wd * plume.ws
    errs = []
    for _ in range(T):
        gas = plume.sample(pos)
        agent.update(gas, tuple(pos), tuple(wind))
        act = agent.choose_action(tuple(pos), tuple(wind))
        d = getattr(agent, 'action_dist', 0.5)
        pos = np.array([pos[0]+act[0]*d, pos[1]+act[1]*d, pos[2]])
        est = agent.get_estimated_source()
        errs.append(math.sqrt((est[0]-plume.src[0])**2 + (est[1]-plume.src[1])**2))
    est = agent.get_estimated_source()
    return math.sqrt((est[0]-plume.src[0])**2 + (est[1]-plume.src[1])**2), min(errs)


def main():
    print("="*70)
    print("OPGSLv2 vs Infotaxis (Clean Benchmark)")
    print("="*70)

    src = (-0.4, -2.9, 0.0)
    wd, ws = (1.0, 0.5, 0.0), 0.5
    starts = [(-1.5, -2.5, 0.3), (-5.0, -5.0, 0.3), (0.0, 0.0, 0.3)]
    T, n_seeds = 300, 5

    rows = []
    for si, st in enumerate(starts):
        print(f"\n--- Start {si}: {st} ---")
        for seed in range(n_seeds):
            np.random.seed(seed)
            r_inf = run(InfotaxisAgent(), PlumeSim(src, wd, ws), st, T)

            np.random.seed(seed)
            r_opgsl = run(OPGSLv2Agent(time_budget=T), PlumeSim(src, wd, ws), st, T)

            rows.append({'start': si, 'seed': seed, 'inf': r_inf[0], 'opgsl': r_opgsl[0]})
            print(f"  S{seed}: Inf={r_inf[0]:.3f} OPGSLv2={r_opgsl[0]:.3f}")

    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    inf_mean = np.mean([r['inf'] for r in rows])
    opgsl_mean = np.mean([r['opgsl'] for r in rows])
    print(f"Infotaxis: {inf_mean:.3f} +/- {np.std([r['inf'] for r in rows]):.3f}")
    print(f"OPGSLv2:   {opgsl_mean:.3f} +/- {np.std([r['opgsl'] for r in rows]):.3f}")
    imp = (inf_mean - opgsl_mean) / max(inf_mean, 0.001) * 100
    print(f"Improvement: {imp:+.1f}%")


if __name__ == '__main__':
    main()
