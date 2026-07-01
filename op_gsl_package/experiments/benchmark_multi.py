"""Multi-scenario WATS-GSL vs Infotaxis benchmark."""
import sys, os, numpy as np, math
sys.path.insert(0, os.path.dirname(__file__))
from infotaxis import InfotaxisAgent
from wats_gsl import WATSAgent


class Plume:
    def __init__(self, src, wd, ws=0.5):
        self.src = np.array(src)
        self.wd = np.array(wd) / np.linalg.norm(wd)
        self.ws = ws
    def sample(self, pos):
        d = np.array(pos) - self.src
        dist = np.linalg.norm(d) + 0.1
        align = np.dot(d[:2], self.wd[:2]) / dist
        e = 1.0 / (dist*dist + 1.0)
        if align > 0: e *= (1.0 + align)
        return max(0, e + np.random.normal(0, 0.01))


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
    scenarios = [
        {'name': 'House01', 'src': (-0.4, -2.9), 'wd': (1.0, 0.5)},
        {'name': 'House02', 'src': (0.5, 1.0), 'wd': (-0.5, 1.0)},
        {'name': 'House03', 'src': (-1.5, 2.0), 'wd': (0.8, -0.6)},
    ]
    starts = [(-1.5, -2.5, 0.3), (-5.0, -5.0, 0.3), (0.0, 0.0, 0.3)]
    T = 300
    n_seeds = 5

    print("=" * 70)
    print("WATS-GSL vs Infotaxis: Multi-Scenario Benchmark")
    print("=" * 70)

    all_inf, all_wats = [], []
    for sc in scenarios:
        src_3d = (sc['src'][0], sc['src'][1], 0.0)
        print(f"\n--- {sc['name']} (source={sc['src']}, wind={sc['wd']}) ---")
        sc_inf, sc_wats = [], []
        for si, st in enumerate(starts):
            inf_f, wats_f = [], []
            for seed in range(n_seeds):
                np.random.seed(seed)
                r = run(InfotaxisAgent(), Plume(src_3d, sc['wd']), st, T)
                inf_f.append(r[0])
                np.random.seed(seed)
                r = run(WATSAgent(time_budget=T), Plume(src_3d, sc['wd']), st, T)
                wats_f.append(r[0])
            sc_inf.extend(inf_f)
            sc_wats.extend(wats_f)
            imp = (np.mean(inf_f) - np.mean(wats_f)) / max(np.mean(inf_f), 0.001) * 100
            print(f"  Start {si}: Inf={np.mean(inf_f):.2f} WATS={np.mean(wats_f):.2f} imp={imp:+.1f}%")
        all_inf.extend(sc_inf)
        all_wats.extend(sc_wats)
        print(f"  {sc['name']} avg: Inf={np.mean(sc_inf):.2f} WATS={np.mean(sc_wats):.2f}")

    print(f"\n{'='*70}")
    print("OVERALL")
    print("=" * 70)
    print(f"Infotaxis: {np.mean(all_inf):.2f} +/- {np.std(all_inf):.2f}")
    print(f"WATS-GSL:  {np.mean(all_wats):.2f} +/- {np.std(all_wats):.2f}")
    imp = (np.mean(all_inf) - np.mean(all_wats)) / max(np.mean(all_inf), 0.001) * 100
    print(f"Improvement: {imp:+.1f}%")


if __name__ == '__main__':
    main()
