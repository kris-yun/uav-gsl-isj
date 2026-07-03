"""BPFM Planner — uses BPFM particle posterior for action selection.

Combines BPFM posterior with information-gain waypoint selection.
The particle flow provides a better posterior than static grids,
especially when gas is intermittent.
"""
import sys, os
import numpy as np

_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from bpfm.bpfm_estimator import BPFMEstimator

EPS = 1e-12


class BPFMPlanner:
    """Planner using BPFM particle posterior.

    Action selection: KLD-based waypoint scoring over BPFM posterior.
    Mode selection: entropy-adaptive (explore vs exploit).
    """

    def __init__(self, grid, occ_2d, emin, cell_size,
                 n_candidates=12, n_particles=200, **kwargs):
        self.grid = np.asarray(grid, dtype=np.float64)
        self.occ_2d = occ_2d
        self.emin = np.asarray(emin, dtype=np.float64)
        self.cell_size = cell_size
        self.n_candidates = n_candidates

        self.estimator = BPFMEstimator(
            grid, occ_2d, emin, cell_size,
            n_particles=n_particles, **kwargs)

        self.hit_memory = []
        self.last_hit_step = -100

    def __call__(self, state, est, obs_history, step):
        # Sync observation to BPFM estimator
        if obs_history:
            last = obs_history[-1]
            wind = np.asarray(last["wind"][:2])
            x = np.asarray(state.pos[:2])
            hit = float(last.get("gas", 0.0)) > 0.01
            self.estimator.update(x, wind, hit)
            if hit:
                self.hit_memory.append(x.copy())
                if len(self.hit_memory) > 5:
                    self.hit_memory.pop(0)
                self.last_hit_step = step

        post = self.estimator.posterior()
        Hn = self.estimator.entropy_norm()
        gas = float(obs_history[-1].get("gas", 0.0)) if obs_history else 0.0
        wind = np.asarray(obs_history[-1]["wind"][:2]) if obs_history else np.array([1.0, 0.0])
        wn = np.linalg.norm(wind)
        wind_hat = wind / max(wn, EPS)

        # Generate candidates
        candidates = []
        radius = 3.0 if Hn > 0.5 else 2.0
        for i in range(self.n_candidates):
            angle = 2 * np.pi * i / self.n_candidates
            target = state.pos[:2] + np.array([np.cos(angle), np.sin(angle)]) * radius
            candidates.append(target)

        # MAP and particle centroid
        candidates.append(self.estimator.map_estimate()[:2])
        candidates.append(self.estimator.particle_centroid()[:2])

        # Upwind candidates when recently hit
        if gas > 0.01:
            candidates.append(state.pos[:2] - wind_hat * 2.0)
            candidates.append(state.pos[:2] - wind_hat * 4.0)

        # Lost plume: go back to last hit
        if step - self.last_hit_step > 8 and self.hit_memory:
            candidates.append(self.hit_memory[-1])

        # Score candidates with KLD
        best_target = candidates[0]
        best_score = -float('inf')
        for target in candidates:
            score = self._kld_score(target, post)
            if score > best_score:
                best_score = score
                best_target = target

        # Mode selection
        if Hn > 0.7 or (step - self.last_hit_step > 15 and Hn > 0.5):
            mode, speed = "fast", 0.8
        elif gas > 0.01 and float(post.max()) > 0.15:
            mode, speed = "slow", 0.2
        elif float(post.max()) > 0.30:
            mode, speed = "hover", 0.0
        else:
            mode, speed = "slow", 0.25

        return best_target, {
            "name": "bpfm", "mode": mode, "speed": speed,
            "kld": best_score, "n_particles": self.estimator.n_particles,
        }

    def _kld_score(self, target, post):
        dists = np.linalg.norm(self.grid - target[None, :], axis=1)
        p_hit_local = np.exp(-dists / 3.0)
        p_hit_local /= p_hit_local.sum() + EPS
        post_new = post * (1 + p_hit_local)
        post_new /= post_new.sum() + EPS
        return float(np.sum(post_new * np.log((post_new + EPS) / (post + EPS))))
