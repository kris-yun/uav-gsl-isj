"""Benchmark: WATS-GSL vs NP-GSL vs OP-GSL vs Infotaxis"""
import sys, os, numpy as np, math, csv
sys.path.insert(0, os.path.dirname(__file__))
from infotaxis import InfotaxisAgent
from op_gsl import OPGSLAgent
from np_gsl import NPGSLAgent
from wats_gsl import WATSAgent, WATSConfig


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
    print("WATS-GSL vs NP-GSL vs OP-GSL vs Infotaxis")
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
            r_op = run(OPGSLAgent(time_budget=T), PlumeSim(src, wd, ws), st, T)

            np.random.seed(seed)
            r_np = run(NPGSLAgent(time_budget=T), PlumeSim(src, wd, ws), st, T)

            np.random.seed(seed)
            r_wats = run(WATSAgent(time_budget=T), PlumeSim(src, wd, ws), st, T)

            rows.append({'start': si, 'seed': seed,
                         'inf': r_inf[0], 'op': r_op[0], 'np': r_np[0], 'wats': r_wats[0]})
            print(f"  S{seed}: Inf={r_inf[0]:.3f} OP={r_op[0]:.3f} NP={r_np[0]:.3f} WATS={r_wats[0]:.3f}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for m in ['inf', 'op', 'np', 'wats']:
        vals = [r[m] for r in rows]
        print(f"{m.upper():>5}: {np.mean(vals):.3f} +/- {np.std(vals):.3f}m")

    inf_mean = np.mean([r['inf'] for r in rows])
    for m in ['op', 'np', 'wats']:
        m_mean = np.mean([r[m] for r in rows])
        imp = (inf_mean - m_mean) / max(inf_mean, 0.001) * 100
        print(f"{m.upper()} vs Inf: {imp:+.1f}%")

    out = os.path.join(os.path.dirname(__file__), 'benchmark_all.csv')
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"\nSaved to {out}")


if __name__ == '__main__':
    main()
